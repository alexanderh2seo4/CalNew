"""Verify the already-frozen Ravia blend against freshly fitted SSH baselines."""
import json
import platform
from pathlib import Path

import numpy as np
import torch
from sklearn.model_selection import GroupKFold
from threadpoolctl import threadpool_limits

from calnew.io import file_digest, write_json
from calnew.pipeline.paper_benchmark import Context, FRACTIONS, random_split
from calnew.pipeline.stages import RAVIA_MEMBERS, TabularEnsemble
from nose_intensity_experiment import cached_meta, metrics
from nose_semantic_experiment import RESERVED


def run():
    torch.set_num_threads(2)
    out = Path("runs/nose-intensity-ravia-dose-transfer-inner-v1")
    selection = json.loads((out/"results.json").read_text())
    if selection["results"]["ravia"]["selected"] != "blend_proxy_ridge":
        raise ValueError("Expected the frozen proxy-ridge recipe")
    ctx = Context(Path(json.loads(Path("data/current.json").read_text())["snapshot"]), RESERVED)
    tr, va, te = random_split(len(ctx.ravia), FRACTIONS["ravia"], 42)
    all_ids = ctx.ravia.molecule_id.to_numpy()
    ids, held = all_ids[tr], all_ids[np.r_[va, te]]
    y = ctx.ravia.y.to_numpy()[tr]
    groups = np.array([i.split("-")[0] for i in ids])
    with np.load(out/"ravia-inner-oof.npz", allow_pickle=False) as data:
        if not np.array_equal(ids, data["ids"]) or not np.array_equal(y, data["y"]):
            raise ValueError("Frozen training rows changed")
        candidate = data["proxy_ridge"].copy()
    baseline = np.zeros_like(candidate)
    for rep in range(3):
        for fold, (a, b) in enumerate(GroupKFold(5, shuffle=True, random_state=100+rep).split(ids, groups=groups)):
            blocks = cached_meta(ctx, ids[a], np.r_[held, ids[b]])
            ra, rb = ctx.rows(ids[a]), ctx.rows(ids[b])
            model = TabularEnsemble(RAVIA_MEMBERS, seed=42, threads=2).fit({n: v[ra] for n, v in blocks.items()}, y[a], groups[a])
            baseline[rep, b] = np.clip(model.predict({n: v[rb] for n, v in blocks.items()}), 0, 100)
        print(f"SSH baseline verification repeat {rep+1}/3 complete", flush=True)
    scores = {n: [metrics(y, p) for p in values] for n, values in
        {"baseline": baseline, "selected": (baseline+candidate)/2}.items()}
    gain = np.array([s["pearson"]-b["pearson"] for s, b in zip(scores["selected"], scores["baseline"])])
    mae_ratio = np.mean([s["mae"] for s in scores["selected"]])/np.mean([b["mae"] for b in scores["baseline"]])
    passed = bool(gain.mean() >= .01 and (gain > 0).sum() >= 2 and mae_ratio <= 1.01)
    report = {"host": platform.node(), "scores": scores, "mean_pearson_gain": float(gain.mean()),
        "mae_ratio": float(mae_ratio), "passing": passed, "selection_changed": False,
        "frozen_selection_sha256": file_digest(out/"results.json"), "reserved_holdouts_opened": False,
        "scope": "Only original split-42 training rows; confirmation of fixed recipe against fresh SSH baselines"}
    write_json(out/"ssh-baseline-verification.json", report)
    np.savez_compressed(out/"ssh-baseline-verification.npz", ids=ids.astype(str), y=y,
        baseline=baseline, selected=(baseline+candidate)/2)
    print(json.dumps(report, indent=2), flush=True)
    if not passed:
        raise ValueError("The frozen blend did not pass against fresh SSH training baselines")


if __name__ == "__main__":
    with threadpool_limits(limits=2):
        run()
