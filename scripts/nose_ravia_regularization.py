"""Training-only Ravia comparison of lower-variance tree heads."""
import argparse
import json
import shutil
import time
from pathlib import Path

import numpy as np
import torch
from sklearn.model_selection import GroupKFold
from threadpoolctl import threadpool_limits

from calnew.io import file_digest, write_json
from calnew.pipeline.intensity import RaviaRegularizedTrees
from calnew.pipeline.paper_benchmark import Context, FRACTIONS, random_split
from nose_intensity_experiment import cached_meta, metrics
from nose_semantic_experiment import RESERVED


def run(args):
    out = Path(args.out)
    if (out/"results.json").exists():
        raise ValueError("Choose a new output directory")
    baseline_path = Path(args.baseline)/"ravia-inner-oof.npz"
    out.mkdir(parents=True, exist_ok=True)
    shutil.copy2(__file__, out/"source.py")
    shutil.copy2("src/calnew/pipeline/intensity.py", out/"intensity.py")
    write_json(out/"selection-plan.json", {"candidates": ["regularized", "all_trees", "equal baseline blends"],
        "selection_data": "Original split-42 training only; same three repeated grouped 5-fold assignments as v1",
        "baseline": str(baseline_path), "baseline_sha256": file_digest(baseline_path),
        "registered_regularization": "Boosting depth 2, min_child_weight 5, lambda 10; existing member inputs, epochs/trees unchanged",
        "promotion": "Mean Pearson gain >=0.01; positive in >=2 repeats; MAE <= baseline*1.01",
        "reason": "First representation trial gave no clear Ravia gain; test smaller tree capacity on 91 training molecules",
        "test_based_model_selection": False, "reserved_holdouts_opened": False})
    started = time.time()
    torch.set_num_threads(2)
    ctx = Context(Path(json.loads(Path("data/current.json").read_text())["snapshot"]), RESERVED)
    tr, va, te = random_split(len(ctx.ravia), FRACTIONS["ravia"], 42)
    all_ids = ctx.ravia.molecule_id.to_numpy()
    ids, fixed_held = all_ids[tr], all_ids[np.r_[va, te]]
    y = ctx.ravia.y.to_numpy()[tr]
    with np.load(baseline_path, allow_pickle=False) as data:
        if not np.array_equal(data["ids"], ids) or not np.array_equal(data["y"], y):
            raise ValueError("Baseline IDs/targets differ")
        baseline = data["baseline"].copy()
    if baseline.shape != (3, len(ids)) or not np.isfinite(baseline).all() or np.any(baseline == 0):
        raise ValueError("Baseline OOF predictions are incomplete")
    groups = np.array([i.split("-")[0] for i in ids])
    predictions = {"baseline": baseline, "regularized": np.zeros_like(baseline), "all_trees": np.zeros_like(baseline)}
    for rep in range(3):
        for fold, (a, b) in enumerate(GroupKFold(5, shuffle=True, random_state=100+rep).split(ids, groups=groups)):
            enriched = cached_meta(ctx, ids[a], np.r_[fixed_held, ids[b]])
            ra, rb = ctx.rows(ids[a]), ctx.rows(ids[b])
            for mode in ("regularized", "all_trees"):
                model = RaviaRegularizedTrees(mode, threads=2).fit({n: v[ra] for n, v in enriched.items()}, y[a], groups[a])
                predictions[mode][rep, b] = model.predict({n: v[rb] for n, v in enriched.items()})
            print(f"Ravia regularization repeat {rep+1}/3 fold {fold+1}/5", flush=True)
        print({n: metrics(y, p[rep]) for n, p in predictions.items()}, flush=True)
    for mode in ("regularized", "all_trees"):
        predictions["blend_"+mode] = (baseline+predictions[mode])/2
    scores = {n: [metrics(y, p) for p in values] for n, values in predictions.items()}
    passing = []
    base_r = np.array([v["pearson"] for v in scores["baseline"]])
    base_mae = np.mean([v["mae"] for v in scores["baseline"]])
    for name, values in scores.items():
        gain = np.array([v["pearson"] for v in values])-base_r
        if gain.mean() >= .01 and (gain > 0).sum() >= 2 and np.mean([v["mae"] for v in values]) <= base_mae*1.01:
            passing.append(name)
    selected = max(passing, key=lambda n: np.mean([v["pearson"] for v in scores[n]])) if passing else "baseline"
    np.savez_compressed(out/"ravia-inner-oof.npz", ids=ids.astype(str), y=y, **predictions)
    write_json(out/"results.json", {"results": {"ravia": {"n": len(ids), "scores": scores, "passing": passing, "selected": selected}},
        "baseline_sha256": file_digest(baseline_path), "seconds": round(time.time()-started),
        "source_sha256": file_digest(out/"source.py"), "model_sha256": file_digest(out/"intensity.py"), "reserved_holdouts_opened": False})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    with threadpool_limits(limits=2):
        run(args)
