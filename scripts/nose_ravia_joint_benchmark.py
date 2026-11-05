"""Evaluate the frozen shared-study blend against the improved Ravia head."""
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
from calnew.pipeline.dose_transfer import RaviaDoseTransfer
from calnew.pipeline.joint_intensity import JointStudyTrees, RaviaJointIntensity
from calnew.pipeline.paper_benchmark import Context, FRACTIONS, benchmark_split, random_split
from calnew.pipeline.stages import QualityStage, RAVIA_MEMBERS, TabularEnsemble
from nose_intensity_experiment import cached_meta, metrics
from nose_ravia_dose_transfer import crossfit, source_model
from nose_semantic_experiment import RESERVED


def approved(path):
    result = json.loads(path.read_text())["results"]["ravia"]
    name = result["selected"]
    if name != "joint_0.25_current" or name not in result["passing"]:
        raise ValueError("The frozen joint .25/current blend was not selected")
    old, new = result["scores"]["current"], result["scores"][name]
    if len(old) != 3 or len(new) != 3:
        raise ValueError("Three complete training-only repeats are required")
    gain = np.array([n["pearson"]-o["pearson"] for o, n in zip(old, new)])
    if gain.mean() < .01 or (gain > 0).sum() < 2 or np.mean([n["mae"] for n in new]) > np.mean([o["mae"] for o in old]):
        raise ValueError("The stronger promotion criterion was not met")


def run(args):
    out = Path(args.out)
    if (out/"results.json").exists():
        raise ValueError("Choose a fresh output directory")
    approved(args.selection)
    if args.resume:
        previous_protocol = json.loads((out/"protocol.json").read_text())
        if previous_protocol["selection_sha256"] != file_digest(args.selection) or previous_protocol["validation_refit"] != args.refit_validation:
            raise ValueError("Resume selection or training protocol changed")
    out.mkdir(parents=True, exist_ok=True)
    sources = {}
    for path in [Path(__file__), Path("scripts/nose_ravia_joint_refine.py"), Path("scripts/nose_ravia_dose_transfer.py"),
            Path("scripts/nose_intensity_experiment.py")]+sorted(Path("src/calnew").rglob("*.py")):
        if path.name.startswith("."):
            continue
        dest = out/("resume-source-code" if args.resume else "source-code")/path.resolve().relative_to(Path.cwd())
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        sources[str(path)] = file_digest(dest)
    if not args.resume:
        shutil.copy2(args.selection, out/"frozen-selection.json")
    write_json(out/("resume-protocol.json" if args.resume else "protocol.json"), {"host": platform.node(), "recipe": "joint_0.25_current",
        "comparison": "Already-improved Ravia dose-transfer head, same original development test assignments",
        "selection_sha256": file_digest(args.selection), "source_sha256": sources,
        "model_seed": 42, "split_seeds": list(range(42, 52)), "validation_refit": args.refit_validation,
        "Keller_source_weight": .25, "Ravia_weight": 1., "blend_weights": [.5, .5],
        "source": "Original Keller split-42 training only, excluding held Ravia connectivities",
        "main_training": "Original Ravia molecule assignments retained; connectivity variants across train/held are counted separately. The auxiliary Keller source excludes every held connectivity.",
        "Ravia_coordinate": "Fixed0 with study indicator1; single highest-presentation endpoint, no validated dilution input",
        "threads": 2, "test_based_model_selection": False, "reserved_holdouts_opened": False})
    torch.set_num_threads(2)
    ctx = Context(Path(json.loads(Path("data/current.json").read_text())["snapshot"]), RESERVED)
    ktr, _, _ = random_split(len(ctx.keller), FRACTIONS["keller"], 42)
    source_ids = ctx.keller.molecule_id.to_numpy()[ktr]
    ids, y = ctx.ravia.molecule_id.to_numpy(), ctx.ravia.y.to_numpy()
    started = time.time()
    results = json.loads((out/"partial.json").read_text()) if args.resume else {}

    def fit(train_ids, held_ids, test_ids, source_ids):
        rows = ctx.rows(train_ids)
        held = {i.split("-")[0] for i in held_ids}
        pa, _, counts = crossfit(ctx, source_ids, train_ids, held_ids, test_ids if len(test_ids) else train_ids, 2)
        enriched = cached_meta(ctx, train_ids, held_ids)
        target = ctx.ravia.set_index("molecule_id").loc[train_ids, "y"].to_numpy()
        blocks = {n: v[rows] for n, v in enriched.items()}
        baseline = TabularEnsemble(RAVIA_MEMBERS, seed=42, threads=2).fit(blocks, target, ctx.connectivity[rows])
        ridge = make_pipeline(StandardScaler(), Ridge(alpha=10)).fit(pa, target)
        source, _ = source_model(ctx, source_ids, held, 2)
        current = RaviaDoseTransfer(baseline, source, ridge)
        kept_ids = [i for i in source_ids if i.split("-")[0] not in held]
        mask = np.isin(ctx.data.panel["molecule_ids"], kept_ids)
        sr = ctx.p_rows[mask]
        if set(ctx.connectivity[sr]) & held:
            raise ValueError("Held connectivity entered auxiliary Keller source training")
        joint = JointStudyTrees(threads=2).fit({n: v[sr] for n, v in ctx.B.items()},
            ctx.data.panel["x"][mask], ctx.data.panel["intensity"][mask], blocks, target, .25)
        return RaviaJointIntensity(current, joint), enriched, counts, len(kept_ids)

    previous_root = Path("runs")/("nose-intensity-ravia-dose-transfer-refit-v1" if args.refit_validation else "nose-intensity-ravia-dose-transfer-v1")
    for split in range(42, 52):
        tr, va, te = benchmark_split(len(ids), FRACTIONS["ravia"], split, args.refit_validation)
        held_conn = {i.split("-")[0] for i in ids[np.r_[va, te]]}
        overlaps = sorted({i.split("-")[0] for i in ids[tr]} & held_conn)
        if str(split) in results:
            with np.load(out/f"split-{split}.npz", allow_pickle=False) as saved:
                if not np.array_equal(saved["ids"], ids[te]) or not np.array_equal(saved["y"], y[te]):
                    raise ValueError("Resume checkpoint assignments/targets changed")
                for name in ("baseline", "selected"):
                    scores = metrics(y[te], saved[name])
                    if any(not np.isclose(v, results[str(split)][name][k], rtol=1e-10, atol=1e-10) for k, v in scores.items()):
                        raise ValueError("Resume checkpoint metrics changed")
            results[str(split)]["target_train_held_connectivity_overlaps"] = overlaps
            print(f"Ravia joint split {split}: verified saved checkpoint", flush=True)
            continue
        model, blocks, counts, source_count = fit(ids[tr], ids[np.r_[va, te]], ids[te], source_ids)
        rows = ctx.rows(ids[te])
        predictions = model.predict_parts({n: v[rows] for n, v in blocks.items()})
        with np.load(previous_root/f"split-{split}.npz", allow_pickle=False) as old:
            if not np.array_equal(ids[te], old["ids"]) or not np.array_equal(y[te], old["y"]):
                raise ValueError("Development test assignments/targets changed")
            previous_difference = float(np.max(np.abs(predictions["baseline"]-old["selected"])))
        results[str(split)] = {n: metrics(y[te], predictions[n]) for n in ("baseline", "selected")}
        results[str(split)].update(train=len(tr), validation=len(va), test=len(te), source_molecules=source_count,
            proxy_source_counts=counts, previous_current_max_difference=previous_difference,
            target_train_held_connectivity_overlaps=overlaps)
        np.savez_compressed(out/f"split-{split}.npz", ids=ids[te].astype(str), y=y[te], **predictions)
        write_json(out/"partial.json", results)
        print(f"Ravia joint split {split}: {results[str(split)]}", flush=True)
    summary = {name: {key: {"mean": float(np.mean([r[name][key] for r in results.values()])),
        "sd": float(np.std([r[name][key] for r in results.values()]))} for key in ("pearson", "mae", "rmse")}
        for name in ("baseline", "selected")}
    write_json(out/"results.json", {"dataset": "ravia", "recipe": "joint_0.25_current", "summary": summary,
        "per_split": results, "positive_pearson_splits": sum(r["selected"]["pearson"]>r["baseline"]["pearson"] for r in results.values()),
        "validation_refit": args.refit_validation, "host": platform.node(), "reserved_holdouts_opened": False,
        "seconds": round(time.time()-started)})
    if args.fit_final:
        print("Fitting final shared-study Ravia bundle", flush=True)
        model, _, counts, source_count = fit(ids, [], [], ctx.keller.molecule_id.to_numpy())
        rows = ctx.a_rows
        quality = QualityStage(ctx.cfg["quality_blocks"], "fingerprint", seeds=(42,), epochs=ctx.cfg["quality"]["epochs"]).fit(
            {n: ctx.B[n][rows] for n in ctx.cfg["quality_blocks"]}, ctx.labels[rows], ctx.direction[rows])
        artifact = out/"intensity-ravia.joblib"
        joblib.dump({"model": model, "quality": quality, "quality_blocks": ctx.cfg["quality_blocks"],
            "training_ids": ids.astype(str), "source_training_ids": ctx.keller.molecule_id.to_numpy().astype(str)}, artifact, compress=3)
        write_json(out/"serving-ravia.json", {"artifact_sha256": file_digest(artifact), "recipe": model.recipe,
            "training_molecules": len(ids), "source_molecules": source_count, "source_proxy_counts": counts,
            "source_weight": .25, "host": platform.node(), "snapshot": str(ctx.snapshot),
            "validated_endpoint": "Ravia published group-mean intensity at each molecule's most concentrated presentation",
            "monotonicity": "Single Ravia endpoint; internal coordinate0 is study-conditioned, not measured dilution",
            "reserved_holdouts_opened": False})
    print(summary, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection", type=Path, default=Path("runs/nose-intensity-ravia-joint-inner-v2/results.json"))
    parser.add_argument("--out", required=True)
    parser.add_argument("--refit-validation", action="store_true")
    parser.add_argument("--fit-final", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    with threadpool_limits(limits=2):
        run(args)
