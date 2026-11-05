"""Training-only test of Keller dose-response transfer for Ravia intensity.

Keller's original split-42 training molecules supply the source labels. Every
Ravia held connectivity is removed from source training. Ravia training features
are cross-fitted again so their own Keller labels cannot enter the proxy values.
The proxy is evaluated at fixed reference doses, not the Ravia presentation dose.
"""
import argparse
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
from xgboost import XGBRegressor

from calnew.io import file_digest, write_json
from calnew.pipeline.intensity import MonotoneDoseTrees
from calnew.pipeline.paper_benchmark import Context, FRACTIONS, random_split
from calnew.pipeline.semantic import SEMANTIC_BASE
from calnew.pipeline.stages import stack
from nose_intensity_experiment import cached_meta, metrics, CACHE
from nose_semantic_experiment import RESERVED

DOSES = (-5., -3., -1.)


def source_model(ctx, source_ids, excluded, threads):
    keep_ids = np.array([i for i in source_ids if i.split("-")[0] not in excluded])
    if set(keep_ids.tolist()) & set(excluded):
        raise ValueError("Keller transfer source contains an excluded molecule")
    mask = np.isin(ctx.data.panel["molecule_ids"], keep_ids)
    rows = ctx.p_rows[mask]
    if set(ctx.connectivity[rows]) & excluded:
        raise ValueError("Keller transfer source contains an excluded connectivity")
    model = MonotoneDoseTrees((SEMANTIC_BASE,), threads=threads).fit(
        {n: ctx.B[n][rows] for n in SEMANTIC_BASE}, ctx.data.panel["x"][mask], ctx.data.panel["intensity"][mask])
    return model, len(keep_ids)


def proxy(model, ctx, ids):
    rows = ctx.rows(ids)
    blocks = {n: ctx.B[n][rows] for n in SEMANTIC_BASE}
    return np.column_stack([model.predict(blocks, np.full(len(ids), dose)) for dose in DOSES])


def crossfit(ctx, source_ids, train_ids, held_ids, test_ids, threads):
    held_conn = {i.split("-")[0] for i in held_ids}
    groups = np.array([i.split("-")[0] for i in train_ids])
    features = np.zeros((len(train_ids), len(DOSES)))
    counts = []
    for _, b in GroupKFold(3, shuffle=True, random_state=300).split(train_ids, groups=groups):
        model, count = source_model(ctx, source_ids, held_conn | set(groups[b]), threads)
        features[b] = proxy(model, ctx, train_ids[b])
        counts.append(count)
    model, count = source_model(ctx, source_ids, held_conn, threads)
    counts.append(count)
    return features, proxy(model, ctx, test_ids), counts


def reindex_windows_caches():
    """Reuse checksummed arrays whose sole identity change is path separators."""
    from calnew.io import digest
    count = 0
    for manifest in list(CACHE.glob("*.json")):
        if manifest.name.startswith("."):
            continue  # macOS archive metadata is not a model manifest
        data = json.loads(manifest.read_text())
        identity = data.get("identity")
        if identity is None or identity["snapshot"] == str(Path(identity["snapshot"])):
            continue
        original = manifest.with_suffix(".npz")
        if file_digest(original) != data["sha256"]:
            raise ValueError("Transferred cache checksum changed")
        identity["snapshot"] = str(Path(identity["snapshot"]))
        target = CACHE/(digest(identity)+".npz")
        if target.exists():
            continue
        shutil.copy2(original, target)
        data["platform_path_migration"] = {"original_manifest": str(manifest), "host": platform.node(),
            "only_changed_identity_field": "snapshot path separator"}
        write_json(target.with_suffix(".json"), data)
        count += 1
    print(f"Reindexed {count} checksummed feature caches for Windows paths", flush=True)


def run(args):
    out = Path(args.out)
    if (out/"results.json").exists():
        raise ValueError("Choose a new output directory")
    out.mkdir(parents=True, exist_ok=True)
    for source in (Path(__file__), Path("src/calnew/pipeline/intensity.py")):
        shutil.copy2(source, out/source.name)
    write_json(out/"selection-plan.json", {"host": platform.node(),
        "selection_data": "Original Ravia split-42 training only, three repeated grouped five-fold assignments (100,101,102)",
        "source": "Original Keller split-42 training only; every held Ravia connectivity removed, with additional three-fold source cross-fitting for Ravia training features",
        "fixed_reference_log10_doses": DOSES,
        "candidates": ["proxy_ridge", "dose_augmented", "equal baseline blends"],
        "registered_head_parameters": {"ridge_alpha": 10, "xgboost": "400 estimators, depth2, child5, lambda10, lr.03, subsample.8, columns.3"},
        "promotion": "Mean Pearson gain >=0.01; positive in >=2 repeats; mean MAE <=baseline*1.01",
        "test_based_model_selection": False, "reserved_holdouts_opened": False,
        "baseline_sha256": file_digest(Path(args.baseline)/"ravia-inner-oof.npz"),
        "source_sha256": file_digest(out/Path(__file__).name)})
    reindex_windows_caches()
    torch.set_num_threads(args.threads)
    ctx = Context(Path(json.loads(Path("data/current.json").read_text())["snapshot"]), RESERVED)
    tr, va, te = random_split(len(ctx.ravia), FRACTIONS["ravia"], 42)
    all_ids = ctx.ravia.molecule_id.to_numpy()
    ids, fixed_held = all_ids[tr], all_ids[np.r_[va, te]]
    y = ctx.ravia.y.to_numpy()[tr]
    ktr, _, _ = random_split(len(ctx.keller), FRACTIONS["keller"], 42)
    source_ids = ctx.keller.molecule_id.to_numpy()[ktr]
    with np.load(Path(args.baseline)/"ravia-inner-oof.npz", allow_pickle=False) as data:
        if not np.array_equal(data["ids"], ids) or not np.array_equal(data["y"], y):
            raise ValueError("Frozen baseline IDs/targets differ")
        baseline = data["baseline"].copy()
    if baseline.shape != (3, len(ids)) or not np.isfinite(baseline).all():
        raise ValueError("Incomplete frozen training baseline")
    predictions = {"baseline": baseline, "proxy_ridge": np.zeros_like(baseline), "dose_augmented": np.zeros_like(baseline)}
    groups = np.array([i.split("-")[0] for i in ids])
    audit = []
    started = time.time()
    for rep in range(3):
        for fold, (a, b) in enumerate(GroupKFold(5, shuffle=True, random_state=100+rep).split(ids, groups=groups)):
            held = np.r_[fixed_held, ids[b]]
            pa, pb, counts = crossfit(ctx, source_ids, ids[a], held, ids[b], args.threads)
            ridge = make_pipeline(StandardScaler(), Ridge(alpha=10)).fit(pa, y[a])
            predictions["proxy_ridge"][rep, b] = np.clip(ridge.predict(pb), 0, 100)
            enriched = cached_meta(ctx, ids[a], held)
            ra, rb = ctx.rows(ids[a]), ctx.rows(ids[b])
            names = SEMANTIC_BASE+("quality", "direction")
            xa = np.column_stack([stack({n: enriched[n][ra] for n in names}, names), pa])
            xb = np.column_stack([stack({n: enriched[n][rb] for n in names}, names), pb])
            imputer = SimpleImputer(strategy="median", keep_empty_features=True).fit(xa)
            model = XGBRegressor(n_estimators=400, max_depth=2, min_child_weight=5, reg_lambda=10,
                learning_rate=.03, subsample=.8, colsample_bytree=.3, n_jobs=args.threads, random_state=42, verbosity=0)
            model.fit(imputer.transform(xa), y[a])
            predictions["dose_augmented"][rep, b] = np.clip(model.predict(imputer.transform(xb)), 0, 100)
            audit.append({"repeat": rep, "fold": fold, "source_molecules_per_fit": counts,
                "held_connectivity_exclusions": len({i.split("-")[0] for i in held})})
            print(f"Ravia dose transfer repeat {rep+1}/3 fold {fold+1}/5; source molecules {counts}", flush=True)
        print({n: metrics(y, p[rep]) for n, p in predictions.items()}, flush=True)
        np.savez_compressed(out/"ravia-inner-oof.npz", ids=ids.astype(str), y=y, **predictions)
        write_json(out/"partial.json", {n: [metrics(y, p) for p in values[:rep+1]] for n, values in predictions.items()})
    for name in ("proxy_ridge", "dose_augmented"):
        predictions["blend_"+name] = (baseline+predictions[name])/2
    scores = {n: [metrics(y, p) for p in values] for n, values in predictions.items()}
    base_r = np.array([p["pearson"] for p in scores["baseline"]])
    base_mae = np.mean([p["mae"] for p in scores["baseline"]])
    passing = []
    for name, values in scores.items():
        gain = np.array([p["pearson"] for p in values])-base_r
        if gain.mean() >= .01 and (gain > 0).sum() >= 2 and np.mean([p["mae"] for p in values]) <= base_mae*1.01:
            passing.append(name)
    selected = max(passing, key=lambda n: np.mean([p["pearson"] for p in scores[n]])) if passing else "baseline"
    np.savez_compressed(out/"ravia-inner-oof.npz", ids=ids.astype(str), y=y, **predictions)
    write_json(out/"results.json", {"results": {"ravia": {"n": len(ids), "scores": scores,
        "passing": passing, "selected": selected}}, "source_audit": audit, "host": platform.node(),
        "seconds": round(time.time()-started), "reserved_holdouts_opened": False})
    print(f"Selected {selected}; passing {passing}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", default="runs/nose-intensity-ravia-inner-v1")
    parser.add_argument("--out", default="runs/nose-intensity-ravia-dose-transfer-inner-v1")
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args()
    with threadpool_limits(limits=args.threads):
        run(args)
