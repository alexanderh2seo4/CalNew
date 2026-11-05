"""Independently reconstruct completed training-only pleasantness trials on SSH."""
from __future__ import annotations

import os
import argparse
import json
from pathlib import Path
import platform

import numpy as np
from sklearn.model_selection import GroupKFold
import torch
from threadpoolctl import threadpool_limits

from calnew.io import digest, file_digest, write_json
from calnew.pipeline.paper_benchmark import FRACTIONS, random_split
from nose_intensity_experiment import metrics
from nose_parity_progress import read_only_context


def audit(ctx, run):
    root = Path(run)
    result = json.loads((root/"results.json").read_text())
    task = result["results"]["keller"]
    tr, va, te = random_split(len(ctx.keller), FRACTIONS["keller"], 42)
    frame = ctx.keller
    all_ids = frame.molecule_id.to_numpy(dtype=str)
    ids, fixed_held = all_ids[tr], all_ids[np.r_[va, te]]
    y = frame.pleasantness.to_numpy()[tr]
    names = set(task["scores"])
    path = root/"keller-inner-oof.npz"
    with np.load(path, allow_pickle=False) as data:
        if set(data.files) != names | {"ids", "y"} or not np.array_equal(data["ids"], ids) or not np.array_equal(data["y"], y):
            raise ValueError("Original training-only IDs/targets or candidate schema differ")
        predictions = {name: data[name].copy() for name in names}
    if any(value.shape != (3, 260) or not np.isfinite(value).all() for value in predictions.values()):
        raise ValueError("Incomplete or invalid repeated original-training predictions")
    resources = json.loads((root/"resource-manifest.json").read_text())
    if digest(resources) != result["resource_sha256"]:
        raise ValueError("Prefit resource manifest differs from final registered identity")
    groups = np.array([m.split("-")[0] for m in ids])
    records = []
    for repeat in range(3):
        coverage = np.zeros(len(ids), dtype=int)
        for fold, (a, b) in enumerate(GroupKFold(5, shuffle=True, random_state=100+repeat).split(ids, groups=groups)):
            file = root/f"keller-repeat-{repeat}-fold-{fold}.npz"
            record = json.loads(file.with_suffix(".json").read_text())
            expected = {"train_ids": ids[a].tolist(), "held_ids": np.r_[fixed_held, ids[b]].tolist(),
                "evaluate_ids": ids[b].tolist(), "targets": y[b].tolist(), "resource_sha256": result["resource_sha256"]}
            if any(record["identity"].get(key) != value for key, value in expected.items()) or record["sha256"] != file_digest(file):
                raise ValueError("Fold identities, targets, resources or checksum differ")
            if set(groups[a]) & set(groups[b]):
                raise ValueError("Fold shares endpoint connectivity")
            with np.load(file, allow_pickle=False) as saved:
                if set(saved.files) != names or any(not np.array_equal(saved[name], predictions[name][repeat, b]) for name in names):
                    raise ValueError("Fold predictions differ from pooled original-training arrays")
            if "training_stimulus_ids" in record["identity"]:
                panel = ctx.data.panel
                selected = np.isin(panel["molecule_ids"], ids[a]) & np.isfinite(panel["pleasantness"]) & np.isfinite(panel["x"])
                if record["identity"]["training_stimulus_ids"] != panel["molecule_ids"][selected].tolist():
                    raise ValueError("All-stimulus endpoint training boundary differs")
            coverage[b] += 1
            records.append({"repeat": repeat, "fold": fold, "path": str(file), "sha256": record["sha256"]})
        if not np.all(coverage == 1):
            raise ValueError("Original training molecule coverage is not exactly once per repeat")
    scores = {name: [metrics(y, row) for row in value] for name, value in predictions.items()}
    for name, repeats in scores.items():
        if len(task["scores"][name]) != 3 or any(not np.isclose(value[key], task["scores"][name][i][key], rtol=0, atol=1e-12)
                for i, value in enumerate(repeats) for key in value):
            raise ValueError("Final scores differ from retained original-training predictions")
    passing = []
    for name, repeats in scores.items():
        gain = np.array([p["pearson"]-q["pearson"] for p, q in zip(repeats, scores["current"])])
        if gain.mean() >= .01 and (gain > 0).sum() >= 2 and np.mean([p["mae"] for p in repeats]) <= np.mean([p["mae"] for p in scores["current"]]):
            passing.append(name)
    selected = max(passing, key=lambda name: np.mean([p["pearson"] for p in scores[name]])) if passing else "current"
    if sorted(task["passing"]) != sorted(passing) or task["selected"] != selected:
        raise ValueError("Final promotion decision differs from frozen gate")
    summary = {name: {key: {"mean": float(np.mean([r[key] for r in repeats])),
        "sd": float(np.std([r[key] for r in repeats]))} for key in repeats[0]} for name, repeats in scores.items()}
    return {"status": "verified", "training_molecules": 260, "main_test_targets_scored": False,
        "reserved_targets_fitted_or_scored": False, "resource_sha256": result["resource_sha256"],
        "results_sha256": file_digest(root/"results.json"), "oof_sha256": file_digest(path),
        "folds": records, "summary": summary, "passing": passing, "selected": selected,
        "limit": "Verifies saved evidence and source boundary, without recreating source/model fits"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", nargs="+", default=["runs/nose-pleasantness-all-stimuli-inner-v1"])
    parser.add_argument("--out", default="runs/nose-pleasantness-trials-audit-20261002.json")
    args = parser.parse_args()
    if platform.node().lower() != os.environ.get("CALNEW_COMPUTE_HOST", "").lower():
        raise ValueError("This numerical audit is restricted to authorized SSH host")
    torch.set_num_threads(2)
    with threadpool_limits(limits=2):
        context = read_only_context(Path(json.loads(Path("data/current.json").read_text())["snapshot"]))
        result = {"host": platform.node(), "script_sha256": file_digest(Path(__file__)),
            "runs": {run: audit(context, run) for run in args.runs}}
        write_json(Path(args.out), result)
        print(json.dumps({run: {key: value for key, value in record.items() if key != "folds"}
            for run, record in result["runs"].items()}, indent=2), flush=True)
