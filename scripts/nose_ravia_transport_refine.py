"""Training-only test of direct transport features in Keller-to-Ravia calibration.

The hypothesis is that calibrating a diluted Keller response to Ravia's highest
presentation needs additional size/polarity/partition information. The candidate
adds the existing 11 transport descriptors to the three cross-fitted dose proxies.
"""
import json
import platform
import shutil
import time
from pathlib import Path

import numpy as np
import torch
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from calnew.io import file_digest, write_json
from calnew.pipeline.paper_benchmark import Context, FRACTIONS, random_split
from nose_intensity_experiment import metrics
from nose_intensity_refine import select
from nose_ravia_dose_transfer import crossfit
from nose_semantic_experiment import RESERVED


def run():
    out = Path("runs/nose-intensity-ravia-transport-inner-v2")
    if (out/"results.json").exists():
        raise ValueError("Choose a fresh output directory")
    out.mkdir(parents=True, exist_ok=True)
    shutil.copy2(__file__, out/"source.py")
    previous = Path("runs/nose-intensity-ravia-dose-transfer-inner-v1")
    write_json(out/"selection-plan.json", {"host": platform.node(),
        "selection_data": "Original split-42 Ravia training only; three repeated grouped five-fold assignments, seeds100,101,102",
        "candidates": ["equal baseline + transport/proxy ridge alpha10", "equal baseline + transport/proxy ridge alpha100"],
        "inputs": "Three fixed-dose Keller proxies plus the 11 existing transport descriptors; training-median imputation and standardization",
        "hypothesis": "Additional size/polarity/partition features may calibrate diluted Keller responses to a different Ravia presentation protocol",
        "promotion": "Mean Pearson gain >=0.01 versus current improved blend, positive in >=2 repeats, mean MAE <= current blend",
        "source_exclusions": "Keller original split-42 training only; every held Ravia connectivity and own proxy feature fold excluded",
        "baseline_sha256": file_digest(previous/"ssh-baseline-verification.npz"),
        "source_sha256": file_digest(out/"source.py"), "reserved_holdouts_opened": False, "test_based_model_selection": False})
    torch.set_num_threads(2)
    ctx = Context(Path(json.loads(Path("data/current.json").read_text())["snapshot"]), RESERVED)
    tr, va, te = random_split(len(ctx.ravia), FRACTIONS["ravia"], 42)
    all_ids = ctx.ravia.molecule_id.to_numpy()
    ids, fixed_held, y = all_ids[tr], all_ids[np.r_[va, te]], ctx.ravia.y.to_numpy()[tr]
    with np.load(previous/"ssh-baseline-verification.npz", allow_pickle=False) as data:
        if not np.array_equal(ids, data["ids"]) or not np.array_equal(y, data["y"]):
            raise ValueError("Frozen training IDs/targets changed")
        current, baseline = data["selected"].copy(), data["baseline"].copy()
    with np.load(previous/"ravia-inner-oof.npz", allow_pickle=False) as data:
        original_proxy = data["proxy_ridge"].copy()
    predictions = {"current": current, "blend_proxy_transport_ridge10": np.zeros_like(current),
        "blend_proxy_transport_ridge100": np.zeros_like(current)}
    groups = np.array([i.split("-")[0] for i in ids])
    ktr, _, _ = random_split(len(ctx.keller), FRACTIONS["keller"], 42)
    source_ids = ctx.keller.molecule_id.to_numpy()[ktr]
    started = time.time()
    for rep in range(3):
        for fold, (a, b) in enumerate(GroupKFold(5, shuffle=True, random_state=100+rep).split(ids, groups=groups)):
            pa, pb, _ = crossfit(ctx, source_ids, ids[a], np.r_[fixed_held, ids[b]], ids[b], 2)
            old = np.clip(make_pipeline(StandardScaler(), Ridge(alpha=10)).fit(pa, y[a]).predict(pb), 0, 100)
            np.testing.assert_allclose(old, original_proxy[rep, b], rtol=1e-6, atol=1e-4)
            xa = np.column_stack([pa, ctx.B["transport"][ctx.rows(ids[a])]])
            xb = np.column_stack([pb, ctx.B["transport"][ctx.rows(ids[b])]])
            for alpha in (10, 100):
                model = make_pipeline(SimpleImputer(strategy="median", keep_empty_features=True), StandardScaler(), Ridge(alpha=alpha)).fit(xa, y[a])
                candidate = np.clip(model.predict(xb), 0, 100)
                predictions[f"blend_proxy_transport_ridge{alpha}"][rep, b] = (baseline[rep, b]+candidate)/2
            print(f"Ravia transport repeat {rep+1}/3 fold {fold+1}/5", flush=True)
        print({n: metrics(y, p[rep]) for n, p in predictions.items()}, flush=True)
        np.savez_compressed(out/"ravia-inner-oof.npz", ids=ids.astype(str), y=y, **predictions)
    scores = {n: [metrics(y, p) for p in values] for n, values in predictions.items()}
    selected, passing = select(scores)
    write_json(out/"results.json", {"results": {"ravia": {"n": len(ids), "selected": selected,
        "passing": passing, "scores": scores}}, "host": platform.node(), "seconds": round(time.time()-started),
        "reserved_holdouts_opened": False})
    print(f"Selected {selected}; passing {passing}", flush=True)


if __name__ == "__main__":
    with threadpool_limits(limits=2):
        run()
