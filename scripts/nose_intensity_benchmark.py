"""Evaluate a frozen intensity recipe on the existing development splits.

The selection must have passed three training-only repeats before this script
runs. It fits only that recipe and its paired baseline, never alternate heads.
All final reserved molecules remain excluded. Serving fits use eligible rows.
"""
import argparse
import json
import platform
import shutil
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import torch
from threadpoolctl import threadpool_limits

from calnew.io import file_digest, write_json
from calnew.pipeline.intensity import IntensityRecipe
from calnew.pipeline.paper_benchmark import Context, FRACTIONS, benchmark_split
from calnew.pipeline.stages import QualityStage
from nose_intensity_experiment import cached_meta, cached_semantic, load_transfer, metrics
from nose_semantic_experiment import RESERVED, frozen_molecular_vectors


def approved_selection(path, dataset):
    data = json.loads(Path(path).read_text())
    result = data.get("results", data)[dataset]
    name = result["selected"]
    if name == "baseline" or name not in result["passing"]:
        raise ValueError(f"{dataset}: no new recipe passed training-only promotion")
    baseline, candidate = result["scores"]["baseline"], result["scores"][name]
    if len(baseline) != 3 or len(candidate) != 3:
        raise ValueError("Selection requires three complete repeats")
    gains = np.array([p["pearson"]-b["pearson"] for p, b in zip(candidate, baseline)])
    if gains.mean() < .01 or (gains > 0).sum() < 2 or np.mean([p["mae"] for p in candidate]) > 1.01*np.mean([b["mae"] for b in baseline]):
        raise ValueError("Registered intensity promotion criterion was not met")
    return name


def run(args):
    out = Path(args.out)
    if (out/"results.json").exists() and not args.fit_only:
        raise ValueError("Choose a new output directory")
    if args.fit_only and not (out/"results.json").exists():
        raise ValueError("--fit-only requires a completed evaluation")
    recipe = approved_selection(args.selection, args.dataset)
    if args.resume or args.fit_only:
        old_protocol = json.loads((out/"protocol.json").read_text())
        for key, value in {"dataset": args.dataset, "recipe": recipe,
                "selection_sha256": file_digest(args.selection), "validation_refit": args.refit_validation}.items():
            if old_protocol[key] != value:
                raise ValueError(f"Resume protocol changed: {key}")
    out.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for path in [Path(__file__), Path("scripts/nose_intensity_experiment.py")] + sorted(Path("src/calnew").rglob("*.py")):
        dest = out/("resume-source-code" if args.resume or args.fit_only else "source-code")/path.resolve().relative_to(Path.cwd())
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        hashes[str(path)] = file_digest(dest)
    if not args.resume and not args.fit_only:
        shutil.copy2(args.selection, out/"frozen-selection.json")
    write_json(out/("resume-protocol.json" if args.resume or args.fit_only else "protocol.json"), {"dataset": args.dataset, "recipe": recipe, "selection": str(args.selection),
        "selection_sha256": file_digest(args.selection), "test_based_model_selection": False,
        "split_seeds": list(range(42, 52)), "model_seed": 42, "validation_refit": args.refit_validation,
        "comparison": "Same original development test assignments, paired current baseline fits",
        "reserved_holdouts_opened": False, "code_sha256": hashes, "threads": args.threads,
        "execution_host": platform.node(), "python": sys.version, "platform": platform.platform(),
        "resume": args.resume, "fit_only": args.fit_only})
    started = time.time()
    torch.set_num_threads(args.threads)
    ctx = Context(Path(json.loads(Path("data/current.json").read_text())["snapshot"]), RESERVED)
    needs_semantic = "semantic" in recipe
    transfer, word_manifest = load_transfer(ctx, out, args.threads) if needs_semantic else (None, None)
    molecular_artifact = Path("data/features/unimol1-research/vectors.npz")
    needs_molecular = "molecular" in recipe or recipe.removeprefix("blend_") == "dose_trees"
    molecular, molecular_manifest = frozen_molecular_vectors(molecular_artifact, ctx.smiles) if needs_molecular else (None, None)
    frame = ctx.keller if args.dataset == "keller" else ctx.ravia
    ids = frame.molecule_id.to_numpy()
    y = frame["intensity" if args.dataset == "keller" else "y"].to_numpy()

    def fit(train_ids, held_ids, test_ids):
        enriched = cached_meta(ctx, train_ids, held_ids)
        semantic, count = cached_semantic(ctx, transfer, train_ids, held_ids) if needs_semantic else (None, 0)
        blocks = dict(enriched)
        if molecular is not None:
            blocks["unimol1"] = molecular
        if semantic is not None:
            blocks["semantic"] = semantic
        if args.dataset == "keller":
            selected = np.isin(ctx.data.panel["molecule_ids"], train_ids)
            rows, doses, target = ctx.p_rows[selected], ctx.data.panel["x"][selected], ctx.data.panel["intensity"][selected]
        else:
            rows, doses = ctx.rows(train_ids), None
            target = frame.set_index("molecule_id").loc[train_ids, "y"].to_numpy()
        train = {n: v[rows] for n, v in blocks.items()}
        groups = ctx.connectivity[rows]
        model = IntensityRecipe(args.dataset, recipe, ctx.cfg["potency_blocks"], ctx.cfg["intensity"]["epochs"], threads=args.threads).fit(train, target, groups, doses)
        baseline = model if model.baseline is not None else IntensityRecipe(args.dataset, "baseline", ctx.cfg["potency_blocks"],
            ctx.cfg["intensity"]["epochs"], threads=args.threads).fit(train, target, groups, doses)
        return model, baseline, blocks, count

    results = json.loads((out/"partial.json").read_text()) if args.resume or args.fit_only else {}
    for split in (() if args.fit_only else range(42, 52)):
        tr, va, te = benchmark_split(len(ids), FRACTIONS[args.dataset], split, args.refit_validation)
        if str(split) in results:
            with np.load(out/f"split-{split}.npz", allow_pickle=False) as saved:
                if not np.array_equal(saved["ids"], ids[te]) or not np.array_equal(saved["y"], y[te]):
                    raise ValueError(f"Checkpoint IDs/targets changed for split {split}")
                for name in ("baseline", "selected"):
                    scores = metrics(y[te], saved[name])
                    if any(not np.isclose(scores[k], results[str(split)][name][k], rtol=1e-10, atol=1e-10) for k in scores):
                        raise ValueError(f"Checkpoint metrics changed for split {split}/{name}")
            if (results[str(split)]["train"], results[str(split)]["validation"], results[str(split)]["test"]) != (len(tr), len(va), len(te)):
                raise ValueError(f"Checkpoint partition sizes changed for split {split}")
            print(f"{args.dataset} split {split}: verified saved checkpoint", flush=True)
            continue
        model, baseline, blocks, count = fit(ids[tr], ids[np.r_[va, te]], ids[te])
        rr = ctx.rows(ids[te])
        test = {n: v[rr] for n, v in blocks.items()}
        x = frame.x.to_numpy()[te] if args.dataset == "keller" else None
        p = model.predict(test, x)
        old = baseline.predict_parts(test, x)["baseline"]
        extra = {}
        if args.dataset == "keller":
            # Score every stimulus of the same held molecules; no dose row enters training.
            sel = np.isin(ctx.data.panel["molecule_ids"], ids[te])
            rows = ctx.p_rows[sel]
            bx = {n: v[rows] for n, v in blocks.items()}
            px, iy = ctx.data.panel["x"][sel], ctx.data.panel["intensity"][sel]
            dose_pred, dose_old = model.predict(bx, px), baseline.predict_parts(bx, px)["baseline"]
            extra["all_stimuli"] = {"baseline": metrics(iy, dose_old), "selected": metrics(iy, dose_pred), "n": len(iy)}
            curves = np.stack([model.predict(test, np.full(len(rr), dose)) for dose in np.linspace(-7, 0, 71)])
            if np.min(np.diff(curves, axis=0)) < -1e-5:
                raise ValueError("Selected Keller intensity curve decreased with dose")
            extra["dose_monotonicity_violations"] = 0
        results[str(split)] = {"baseline": metrics(y[te], old), "selected": metrics(y[te], p),
            "train": len(tr), "validation": len(va), "test": len(te), "source_rows": count, **extra}
        np.savez_compressed(out/f"split-{split}.npz", ids=ids[te].astype(str), y=y[te], baseline=old, selected=p)
        write_json(out/"partial.json", results)
        print(f"{args.dataset} split {split}: {results[str(split)]}", flush=True)
    summary = {name: {key: {"mean": float(np.mean([r[name][key] for r in results.values()])),
        "sd": float(np.std([r[name][key] for r in results.values()]))} for key in ("pearson", "mae", "rmse")}
        for name in ("baseline", "selected")}
    write_json(out/"results.json", {"dataset": args.dataset, "recipe": recipe, "per_split": results, "summary": summary,
        "positive_pearson_splits": sum(r["selected"]["pearson"] > r["baseline"]["pearson"] for r in results.values()),
        "word_vectors": word_manifest, "molecular_vectors": molecular_manifest,
        "validation_refit": args.refit_validation, "reserved_holdouts_opened": False, "seconds": round(time.time()-started)})
    if args.fit_final or args.fit_only:
        print(f"{args.dataset}: fitting final serving model on eligible molecules", flush=True)
        model, _, _, count = fit(ids, [], [])
        names = model.feature_names
        quality = None
        if "quality" in names or "direction" in names:
            rows = ctx.a_rows
            quality = QualityStage(ctx.cfg["quality_blocks"], "fingerprint", seeds=(42,), epochs=ctx.cfg["quality"]["epochs"]).fit(
                {n: ctx.B[n][rows] for n in ctx.cfg["quality_blocks"]}, ctx.labels[rows], ctx.direction[rows])
        scaler, semantic_model = transfer.fit([])[:2] if needs_semantic else (None, None)
        bundle = {"model": model, "quality": quality, "quality_blocks": ctx.cfg["quality_blocks"],
            "semantic_scaler": scaler, "semantic_model": semantic_model, "training_ids": ids.astype(str),
            "molecular_artifact": str(molecular_artifact.resolve()), "word_vectors": word_manifest}
        artifact = out/f"intensity-{args.dataset}.joblib"
        joblib.dump(bundle, artifact, compress=3)
        endpoint = ("Keller intensity at nominal paraffin-oil dilution; higher-concentration benchmark and both observed dilutions" if args.dataset == "keller"
            else "Ravia published group-mean intensity at each molecule's most concentrated presentation")
        write_json(out/f"serving-{args.dataset}.json", {"artifact_sha256": file_digest(artifact), "snapshot": str(ctx.snapshot),
            "recipe": recipe, "training_molecules": len(ids), "descriptor_source_rows": count,
            "reserved_holdouts_opened": False, "validated_endpoint": endpoint,
            "monotonicity": "Nondecreasing for all doses, 0–100" if args.dataset == "keller" else "Single endpoint; no dilution curve"})
    print(summary, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--dataset", choices=("keller", "ravia"), required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--refit-validation", action="store_true")
    parser.add_argument("--fit-final", action="store_true")
    parser.add_argument("--resume", action="store_true", help="Verify completed split checkpoints and compute only missing splits")
    parser.add_argument("--fit-only", action="store_true", help="Fit a serving model after a completed evaluation")
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args()
    with threadpool_limits(limits=args.threads):
        run(args)
