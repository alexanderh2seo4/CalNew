"""Training-only shared Keller/Ravia study-conditioned intensity experiment.

The Ravia coordinate is always zero and represents its single highest-presentation
endpoint. It is not treated as measured dilution or a validated Ravia dose curve.
The source Keller coordinate uses its actual nominal log dilution. Only original
Keller split-42 training labels enter; held Ravia connectivities are removed.
"""
import json
import platform
import shutil
import time
from pathlib import Path

import numpy as np
import torch
from sklearn.impute import SimpleImputer
from sklearn.model_selection import GroupKFold
from threadpoolctl import threadpool_limits
from xgboost import XGBRegressor

from calnew.io import file_digest, write_json
from calnew.pipeline.paper_benchmark import Context, FRACTIONS, random_split
from calnew.pipeline.semantic import SEMANTIC_BASE
from calnew.pipeline.stages import stack
from nose_intensity_experiment import metrics
from nose_intensity_refine import select
from nose_semantic_experiment import RESERVED


def run():
    out = Path("runs/nose-intensity-ravia-joint-inner-v2")
    if (out/"results.json").exists():
        raise ValueError("Choose a fresh output directory")
    out.mkdir(parents=True, exist_ok=True)
    shutil.copy2(__file__, out/"source.py")
    baseline_path = Path("runs/nose-intensity-ravia-dose-transfer-inner-v1/ssh-baseline-verification.npz")
    write_json(out/"selection-plan.json", {"host": platform.node(),
        "selection_data": "Original Ravia split-42 training only; three repeated grouped five-fold assignments with seeds100,101,102",
        "source": "Original Keller split-42 training only, excluding every held Ravia connectivity",
        "parameters": "XGBoost400, lr.03, depth3, child5, lambda10, subsample.8, columns.3, monotone nominal Keller log dose",
        "source_weights": [.25, 1.], "Ravia_weight": 1.,
        "candidates": "Each source weight: equal blend of joint head with legacy Ravia baseline or current improved Ravia head",
        "inputs": "Structure/fingerprint blocks plus study indicator and dose; Ravia endpoint is fixed surrogate coordinate0, without a validated dose input",
        "promotion": "Mean Pearson gain>=0.01 vs current, positive in>=2 repeats, mean MAE<=current",
        "baseline_sha256": file_digest(baseline_path), "source_sha256": file_digest(out/"source.py"),
        "test_based_model_selection": False, "reserved_holdouts_opened": False})
    torch.set_num_threads(2)
    ctx = Context(Path(json.loads(Path("data/current.json").read_text())["snapshot"]), RESERVED)
    tr, va, te = random_split(len(ctx.ravia), FRACTIONS["ravia"], 42)
    all_ids = ctx.ravia.molecule_id.to_numpy()
    ids, fixed_held, y = all_ids[tr], all_ids[np.r_[va, te]], ctx.ravia.y.to_numpy()[tr]
    with np.load(baseline_path, allow_pickle=False) as data:
        if not np.array_equal(ids, data["ids"]) or not np.array_equal(y, data["y"]):
            raise ValueError("Frozen training IDs/targets changed")
        baseline, current = data["baseline"].copy(), data["selected"].copy()
    ktr, _, _ = random_split(len(ctx.keller), FRACTIONS["keller"], 42)
    source_ids = ctx.keller.molecule_id.to_numpy()[ktr]
    groups = np.array([i.split("-")[0] for i in ids])
    predictions = {"current": current}
    for weight in (.25, 1.):
        for reference in ("legacy", "current"):
            predictions[f"joint_{weight}_{reference}"] = np.zeros_like(current)
    audit, started = [], time.time()
    for rep in range(3):
        for fold, (a, b) in enumerate(GroupKFold(5, shuffle=True, random_state=100+rep).split(ids, groups=groups)):
            held = {i.split("-")[0] for i in np.r_[fixed_held, ids[b]]}
            allowed_source = [i for i in source_ids if i.split("-")[0] not in held]
            mask = np.isin(ctx.data.panel["molecule_ids"], allowed_source)
            sr, ra, rb = ctx.p_rows[mask], ctx.rows(ids[a]), ctx.rows(ids[b])
            if set(ctx.connectivity[np.r_[sr, ra]]) & held:
                raise ValueError("A held connectivity entered joint source/target training")
            source = stack({n: ctx.B[n][sr] for n in SEMANTIC_BASE}, SEMANTIC_BASE)
            target = stack({n: ctx.B[n][ra] for n in SEMANTIC_BASE}, SEMANTIC_BASE)
            test = stack({n: ctx.B[n][rb] for n in SEMANTIC_BASE}, SEMANTIC_BASE)
            xa = np.vstack([np.column_stack([source, np.zeros(len(sr)), ctx.data.panel["x"][mask]]),
                np.column_stack([target, np.ones(len(ra)), np.zeros(len(ra))])])
            xb = np.column_stack([test, np.ones(len(rb)), np.zeros(len(rb))])
            labels = np.r_[ctx.data.panel["intensity"][mask], y[a]]
            imputer = SimpleImputer(strategy="median", keep_empty_features=True).fit(xa)
            for weight in (.25, 1.):
                model = XGBRegressor(n_estimators=400, learning_rate=.03, max_depth=3, min_child_weight=5,
                    reg_lambda=10, subsample=.8, colsample_bytree=.3, n_jobs=2, random_state=42, verbosity=0,
                    monotone_constraints=tuple([0]*(xa.shape[1]-1)+[1]))
                model.fit(imputer.transform(xa), labels, sample_weight=np.r_[np.full(len(sr), weight), np.ones(len(ra))])
                p = np.clip(model.predict(imputer.transform(xb)), 0, 100)
                for reference, old in (("legacy", baseline), ("current", current)):
                    predictions[f"joint_{weight}_{reference}"][rep, b] = (old[rep, b]+p)/2
            audit.append({"repeat": rep, "fold": fold, "source_molecules": len(allowed_source),
                "source_stimuli": len(sr), "target_training": len(ra), "held_connectivities": len(held)})
            print(f"Ravia joint repeat {rep+1}/3 fold {fold+1}/5", flush=True)
        print({n: metrics(y, p[rep]) for n, p in predictions.items()}, flush=True)
        np.savez_compressed(out/"ravia-inner-oof.npz", ids=ids.astype(str), y=y, **predictions)
    scores = {n: [metrics(y, p) for p in values] for n, values in predictions.items()}
    selected, passing = select(scores)
    write_json(out/"results.json", {"results": {"ravia": {"n": len(ids), "selected": selected,
        "passing": passing, "scores": scores}}, "source_audit": audit, "host": platform.node(),
        "seconds": round(time.time()-started), "reserved_holdouts_opened": False})
    print(f"Selected {selected}; passing {passing}", flush=True)


if __name__ == "__main__":
    with threadpool_limits(limits=2):
        run()
