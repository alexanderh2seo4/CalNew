"""Evaluate only the frozen training-selected Ravia dose-proxy blend."""
import argparse
import json
import platform
import shutil
import time
from pathlib import Path

import joblib
import numpy as np
import torch
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from calnew.io import file_digest, write_json
from calnew.pipeline.dose_transfer import RaviaDoseTransfer, REFERENCE_DOSES
from calnew.pipeline.paper_benchmark import Context, FRACTIONS, benchmark_split, random_split
from calnew.pipeline.stages import QualityStage, RAVIA_MEMBERS, TabularEnsemble
from nose_intensity_benchmark import approved_selection
from nose_intensity_experiment import cached_meta, metrics
from nose_ravia_dose_transfer import crossfit, source_model
from nose_semantic_experiment import RESERVED


def run(args):
    out = Path(args.out)
    if (out/"results.json").exists():
        raise ValueError("Choose a new output directory")
    recipe = approved_selection(args.selection, "ravia")
    if recipe != "blend_proxy_ridge":
        raise ValueError("This evaluation implements only the frozen proxy-ridge blend")
    out.mkdir(parents=True, exist_ok=True)
    source_hashes = {}
    for source in [Path(__file__), Path("scripts/nose_ravia_dose_transfer.py")]+sorted(Path("src/calnew").rglob("*.py")):
        if source.name.startswith("."):
            continue
        dest = out/"source-code"/source.resolve().relative_to(Path.cwd())
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        source_hashes[str(source)] = file_digest(dest)
    shutil.copy2(args.selection, out/"frozen-selection.json")
    write_json(out/"protocol.json", {"host": platform.node(), "recipe": recipe, "model_seed": 42,
        "split_seeds": list(range(42, 52)), "validation_refit": args.refit_validation,
        "selection_sha256": file_digest(args.selection), "test_based_model_selection": False,
        "source": "Keller original split-42 training only, excluding every held Ravia connectivity and each proxy training fold",
        "proxy_training_folds": 3, "proxy_fold_seed": 300, "reference_doses": REFERENCE_DOSES,
        "ridge_alpha": 10, "blend_weights": [.5, .5], "threads": args.threads,
        "reserved_holdouts_opened": False, "source_sha256": source_hashes})
    torch.set_num_threads(args.threads)
    ctx = Context(Path(json.loads(Path("data/current.json").read_text())["snapshot"]), RESERVED)
    ktr, _, _ = random_split(len(ctx.keller), FRACTIONS["keller"], 42)
    source_ids = ctx.keller.molecule_id.to_numpy()[ktr]
    ids, y = ctx.ravia.molecule_id.to_numpy(), ctx.ravia.y.to_numpy()
    results = {}
    started = time.time()

    def fit(train_ids, held_ids, test_ids, source_ids):
        rows = ctx.rows(train_ids)
        groups = ctx.connectivity[rows]
        pa, _, counts = crossfit(ctx, source_ids, train_ids, held_ids,
            test_ids if len(test_ids) else train_ids, args.threads)
        enriched = cached_meta(ctx, train_ids, held_ids)
        blocks = {n: v[rows] for n, v in enriched.items()}
        target = ctx.ravia.set_index("molecule_id").loc[train_ids, "y"].to_numpy()
        baseline = TabularEnsemble(RAVIA_MEMBERS, seed=42, threads=args.threads).fit(blocks, target, groups)
        ridge = make_pipeline(StandardScaler(), Ridge(alpha=10)).fit(pa, target)
        tree, count = source_model(ctx, source_ids, {i.split("-")[0] for i in held_ids}, args.threads)
        return RaviaDoseTransfer(baseline, tree, ridge), enriched, counts

    for split in range(42, 52):
        tr, va, te = benchmark_split(len(ids), FRACTIONS["ravia"], split, args.refit_validation)
        model, enriched, counts = fit(ids[tr], ids[np.r_[va, te]], ids[te], source_ids)
        rows = ctx.rows(ids[te])
        predictions = model.predict_parts({n: v[rows] for n, v in enriched.items()})
        results[str(split)] = {n: metrics(y[te], predictions[n]) for n in ("baseline", "selected")}
        results[str(split)].update(train=len(tr), validation=len(va), test=len(te), source_molecules_per_fit=counts)
        np.savez_compressed(out/f"split-{split}.npz", ids=ids[te].astype(str), y=y[te], **predictions)
        write_json(out/"partial.json", results)
        print(f"Ravia proxy split {split}: {results[str(split)]}", flush=True)
    summary = {name: {key: {"mean": float(np.mean([r[name][key] for r in results.values()])),
        "sd": float(np.std([r[name][key] for r in results.values()]))} for key in ("pearson", "mae", "rmse")}
        for name in ("baseline", "selected")}
    write_json(out/"results.json", {"dataset": "ravia", "recipe": recipe, "per_split": results, "summary": summary,
        "positive_pearson_splits": sum(r["selected"]["pearson"] > r["baseline"]["pearson"] for r in results.values()),
        "validation_refit": args.refit_validation, "reserved_holdouts_opened": False, "host": platform.node(),
        "seconds": round(time.time()-started)})
    if args.fit_final:
        print("Fitting final Ravia proxy bundle on eligible molecules", flush=True)
        model, _, counts = fit(ids, [], [], ctx.keller.molecule_id.to_numpy())
        rows = ctx.a_rows
        quality = QualityStage(ctx.cfg["quality_blocks"], "fingerprint", seeds=(42,), epochs=ctx.cfg["quality"]["epochs"]).fit(
            {n: ctx.B[n][rows] for n in ctx.cfg["quality_blocks"]}, ctx.labels[rows], ctx.direction[rows])
        artifact = out/"intensity-ravia.joblib"
        joblib.dump({"model": model, "quality": quality, "quality_blocks": ctx.cfg["quality_blocks"],
            "training_ids": ids.astype(str), "source_training_ids": ctx.keller.molecule_id.to_numpy().astype(str)}, artifact, compress=3)
        write_json(out/"serving-ravia.json", {"artifact_sha256": file_digest(artifact), "recipe": recipe,
            "snapshot": str(ctx.snapshot), "training_molecules": len(ids), "source_molecules": len(ctx.keller),
            "source_training_proxy_counts": counts, "reference_log10_doses": REFERENCE_DOSES,
            "validated_endpoint": "Ravia published group-mean intensity at each molecule's most concentrated presentation",
            "monotonicity": "Single endpoint; reference Keller proxy doses are fixed latent features",
            "reserved_holdouts_opened": False, "host": platform.node()})
    print(summary, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection", type=Path, default=Path("runs/nose-intensity-ravia-dose-transfer-inner-v1/results.json"))
    parser.add_argument("--out", required=True)
    parser.add_argument("--refit-validation", action="store_true")
    parser.add_argument("--fit-final", action="store_true")
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args()
    with threadpool_limits(limits=args.threads):
        run(args)
