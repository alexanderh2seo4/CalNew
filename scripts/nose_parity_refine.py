"""Registered grouped, training-only checks for threshold and pleasantness gaps.

All fits are made inside the ORIGINAL split-42 training cohort. The current
baseline is refitted on exactly the same grouped folds as each candidate.
Main development validation/test and reserved final targets are never scored.
Run this script only through the isolated SSH checkout's compute wrapper.
"""
from __future__ import annotations

import argparse
import json
import platform
import shutil
import time
from pathlib import Path

import numpy as np
import torch
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits
from xgboost import XGBRegressor

from calnew.io import file_digest, write_json
from calnew.pipeline.auxiliary import exclude_touching
from calnew.pipeline.blocks import EXPLICIT_BLOCKS
from calnew.pipeline.paper_benchmark import Context, FRACTIONS, random_split
from calnew.pipeline.semantic import SEMANTIC_BASE
from calnew.pipeline.stages import HEDONIC_MEMBERS, THRESHOLD_MEMBERS, TabularEnsemble, ThresholdStage, stack
from nose_intensity_experiment import cached_meta, cached_semantic, load_transfer, metrics
from nose_semantic_experiment import RESERVED


def boost(depth=3, features=.5):
    return XGBRegressor(n_estimators=400, learning_rate=.03, max_depth=depth,
        min_child_weight=5, reg_lambda=10, subsample=.8, colsample_bytree=features,
        n_jobs=2, random_state=42, verbosity=0)


def ridge(alpha):
    # Every preprocessing step is fitted on this fold's training rows only.
    return make_pipeline(SimpleImputer(strategy="median", keep_empty_features=True), StandardScaler(), Ridge(alpha=alpha))


def water_models(ctx, excluded):
    keep = exclude_touching(ctx.aux, excluded)
    forbidden = {str(i).split("-")[0] for i in excluded}
    if set(ctx.aux.connectivity.to_numpy()[keep]) & forbidden:
        raise ValueError("Held connectivity entered water source training")
    x = stack(ctx.aux_blocks, SEMANTIC_BASE)[keep]
    y = ctx.aux.y.to_numpy()[keep]
    imputer = SimpleImputer(strategy="median", keep_empty_features=True).fit(x)
    xx = imputer.transform(x)
    et = ExtraTreesRegressor(n_estimators=400, min_samples_leaf=4, max_features=.3,
        n_jobs=2, random_state=42).fit(xx, y)
    xgb = boost(features=.3).fit(xx, y)
    return imputer, (et, xgb), int(keep.sum())


def water_predict(ctx, models, ids):
    imputer, members, _ = models
    rows = ctx.rows(ids)
    x = imputer.transform(stack(ctx.B, SEMANTIC_BASE)[rows])
    return np.column_stack([m.predict(x) for m in members])


def water_proxies(ctx, train_ids, held_ids, evaluate_ids, seed):
    groups = np.array([str(i).split("-")[0] for i in train_ids])
    proxies = np.empty((len(train_ids), 2))
    counts = []
    for _, va in GroupKFold(3, shuffle=True, random_state=seed).split(train_ids, groups=groups):
        model = water_models(ctx, np.r_[held_ids, train_ids[va]])
        proxies[va] = water_predict(ctx, model, train_ids[va])
        counts.append(model[2])
    model = water_models(ctx, held_ids)
    counts.append(model[2])
    return proxies, water_predict(ctx, model, evaluate_ids), counts


def classical_directions(ctx, train_ids, evaluate_ids, seed):
    rows = ctx.rows(train_ids)
    groups = ctx.connectivity[rows]
    x = stack(ctx.B, SEMANTIC_BASE)
    target = ctx.direction[rows]
    if not np.isfinite(target).all():
        raise ValueError("Missing eligible Keller training direction")

    def fit(a, b):
        if len(b) and (set(groups[a]) & set(groups[b])):
            raise ValueError("Direction source folds share connectivity")
        imputer = SimpleImputer(strategy="median", keep_empty_features=True).fit(x[rows[a]])
        center, spread = target[a].mean(0), np.maximum(target[a].std(0), 1e-4)
        model = ExtraTreesRegressor(n_estimators=400, min_samples_leaf=4, max_features=.3,
            random_state=173, n_jobs=2).fit(imputer.transform(x[rows[a]]), (target[a]-center)/spread)
        return imputer, model, center, spread

    def predict(model, rr):
        imputer, learner, center, spread = model
        values = np.maximum(learner.predict(imputer.transform(x[rr]))*spread+center, 0)
        return values/np.maximum(np.linalg.norm(values, axis=1, keepdims=True), 1e-9)

    oof = np.empty_like(target)
    for a, b in GroupKFold(3, shuffle=True, random_state=seed).split(train_ids, groups=groups):
        oof[b] = predict(fit(a, b), rows[b])
    model = fit(np.arange(len(rows)), np.empty(0, dtype=int))
    if set(groups) & set(ctx.connectivity[ctx.rows(evaluate_ids)]):
        raise ValueError("Held connectivity entered classical direction training")
    return oof, predict(model, ctx.rows(evaluate_ids))


def current_threshold(ctx, train_ids, held_ids, evaluate_ids, enriched, y):
    a, b = ctx.rows(train_ids), ctx.rows(evaluate_ids)
    pick = lambda rr: {n: enriched[n][rr] for _, names in THRESHOLD_MEMBERS for n in names}
    keep = exclude_touching(ctx.aux, held_ids)
    auxiliary = ({n: v[keep] for n, v in ctx.aux_blocks.items()}, ctx.aux.y.to_numpy()[keep], 1.)
    members = TabularEnsemble(THRESHOLD_MEMBERS, seed=42, threads=2).fit(pick(a), y, ctx.connectivity[a], auxiliary=auxiliary)
    potency = lambda rr: {n: enriched[n][rr] for n in ctx.cfg["potency_blocks"]}
    fusion = ThresholdStage(ctx.cfg["potency_blocks"], "fingerprint", seeds=tuple(range(420, 425)),
        epochs=ctx.cfg["threshold"]["epochs"]).fit(potency(a), y, ctx.connectivity[a])
    return np.column_stack([fusion.predict(potency(b))["ensemble"], members.predict_members(pick(b))]).mean(1)


def threshold_fold(ctx, train_ids, held_ids, evaluate_ids, enriched, y, seed):
    current = current_threshold(ctx, train_ids, held_ids, evaluate_ids, enriched, y)
    p, q, counts = water_proxies(ctx, train_ids, held_ids, evaluate_ids, seed)
    a, b = ctx.rows(train_ids), ctx.rows(evaluate_ids)
    x = np.column_stack([stack(ctx.B, EXPLICIT_BLOCKS)[a], p])
    z = np.column_stack([stack(ctx.B, EXPLICIT_BLOCKS)[b], q])
    predictions = {"current": current}
    for name, model in (("water_ridge10", ridge(10)), ("water_ridge100", ridge(100)),
            ("water_boost2", make_pipeline(SimpleImputer(strategy="median", keep_empty_features=True), boost(2))),
            ("water_boost3", make_pipeline(SimpleImputer(strategy="median", keep_empty_features=True), boost(3)))):
        values = model.fit(x, y).predict(z)
        predictions[name] = values
        predictions["blend_"+name] = (current+values)/2
    return predictions, {"water_source_counts": counts}


def pleasantness_fold(ctx, transfer, train_ids, held_ids, evaluate_ids, enriched, y, seed):
    semantic, source_count = cached_semantic(ctx, transfer, train_ids, held_ids, seed)
    a, b = ctx.rows(train_ids), ctx.rows(evaluate_ids)
    frame = ctx.keller.set_index("molecule_id")
    dose_a, dose_b = frame.loc[train_ids, "x"].to_numpy()[:, None], frame.loc[evaluate_ids, "x"].to_numpy()[:, None]
    pick = lambda rr: {n: enriched[n][rr] for _, names in HEDONIC_MEMBERS for n in names}
    hedonic = TabularEnsemble(HEDONIC_MEMBERS, seed=42, threads=2).fit(pick(a), y, ctx.connectivity[a], columns=dose_a)
    old = hedonic.predict(pick(b), columns=dose_b)
    base_a = np.column_stack([stack(ctx.B, SEMANTIC_BASE)[a], dose_a, semantic[a]])
    base_b = np.column_stack([stack(ctx.B, SEMANTIC_BASE)[b], dose_b, semantic[b]])
    sem_model = ExtraTreesRegressor(n_estimators=500, min_samples_leaf=2, max_features=.3,
        n_jobs=2, random_state=42).fit(base_a, y)
    current = (old+sem_model.predict(base_b))/2
    compact = np.column_stack([stack(ctx.B, EXPLICIT_BLOCKS), enriched["quality"], enriched["direction"], semantic])
    x, z = np.column_stack([compact[a], dose_a]), np.column_stack([compact[b], dose_b])
    predictions = {"current": current}
    for name, model in (("semantic_quality_boost", make_pipeline(SimpleImputer(strategy="median", keep_empty_features=True), boost())),
            ("semantic_quality_ridge100", ridge(100))):
        values = np.clip(model.fit(x, y).predict(z), 0, 100)
        predictions[name] = values
        predictions["blend_"+name] = (current+values)/2
    direction_a, direction_b = classical_directions(ctx, train_ids, evaluate_ids, seed)
    model = make_pipeline(SimpleImputer(strategy="median", keep_empty_features=True), boost())
    values = np.clip(model.fit(np.column_stack([x, direction_a]), y).predict(np.column_stack([z, direction_b])), 0, 100)
    predictions["classical_direction_boost"] = values
    predictions["blend_classical_direction_boost"] = (current+values)/2
    return predictions, {"descriptor_source_count": source_count}


def run(args):
    out = Path(args.out)
    if (out/"results.json").exists():
        raise ValueError("Choose a fresh output directory")
    if out.exists() and not args.resume:
        raise ValueError("Existing output requires explicit --resume")
    out.mkdir(parents=True, exist_ok=True)
    source_files = [Path(__file__), Path("scripts/nose_intensity_experiment.py"), Path("scripts/nose_semantic_experiment.py")]
    source_files += sorted(Path("src/calnew").rglob("*.py"))
    hashes = {}
    for path in source_files:
        relative = path.resolve().relative_to(Path.cwd())
        dest = out/"source-code"/relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        if args.resume and dest.exists() and file_digest(path) != file_digest(dest):
            raise ValueError("Resume source code changed")
        shutil.copy2(path, dest)
        hashes[str(relative)] = file_digest(dest)
    plan = {"host": platform.node(), "original_split_seed": 42, "fold_seeds": [100, 101, 102],
        "datasets": args.datasets, "selection_data": "Original training cohort only; 3 repeated connectivity GroupKFold5",
        "threshold_candidates": ["water_ridge10", "water_ridge100", "water_boost2", "water_boost3", "fixed equal current blends"],
        "pleasantness_candidates": ["semantic_quality_boost", "semantic_quality_ridge100", "classical_direction_boost", "fixed equal current blends"],
        "baseline": "Fresh current threshold v2 or pleasantness v3, refitted on identical new grouped folds",
        "source_crossfit": "Grouped3, excluding main held and own source-feature validation connectivity",
        "novelty": "Earlier water-proxy screens were exploratory; this study uses two independent source learners, explicit-only air calibration, fully nested current baseline and a frozen gate",
        "promotion": "Mean Pearson gain >=.01; positive in >=2/3 repeats; no increase in mean MAE; choose highest passing mean Pearson",
        "model_seed": 42, "threads": 2, "test_based_selection": False, "reserved_targets_fitted_or_scored": False,
        "code_sha256": hashes}
    if args.resume and json.loads((out/"selection-plan.json").read_text()) != plan:
        raise ValueError("Resume plan changed")
    write_json(out/"selection-plan.json", plan)
    torch.set_num_threads(2)
    ctx = Context(Path(json.loads(Path("data/current.json").read_text())["snapshot"]), RESERVED)
    transfer = load_transfer(ctx, out, 2)[0] if "keller" in args.datasets else None
    results = {}
    started = time.time()
    for dataset in args.datasets:
        frame = ctx.thr if dataset == "abraham" else ctx.keller
        tr, va, te = random_split(len(frame), FRACTIONS[dataset], 42)
        all_ids = frame.molecule_id.to_numpy()
        ids, fixed_held = all_ids[tr], all_ids[np.r_[va, te]]
        y = frame["y" if dataset == "abraham" else "pleasantness"].to_numpy()[tr]
        groups = np.array([str(i).split("-")[0] for i in ids])
        predictions = {}
        folds = []
        for repeat in range(3):
            for fold, (a, b) in enumerate(GroupKFold(5, shuffle=True, random_state=100+repeat).split(ids, groups=groups)):
                if set(groups[a]) & set(groups[b]):
                    raise ValueError("Primary selection folds share connectivity")
                held = np.r_[fixed_held, ids[b]]
                path = out/f"{dataset}-repeat-{repeat}-fold-{fold}.npz"
                metadata_path = path.with_suffix(".json")
                identity = {"train_ids": ids[a].tolist(), "held_ids": held.tolist(), "evaluate_ids": ids[b].tolist(),
                    "targets": y[b].tolist(), "code_sha256": hashes}
                if args.resume and path.exists():
                    record = json.loads(metadata_path.read_text())
                    if record["identity"] != identity or record["sha256"] != file_digest(path):
                        raise ValueError("Resume fold identity/checksum changed")
                    with np.load(path, allow_pickle=False) as data:
                        values = {n: data[n].copy() for n in data.files}
                else:
                    print(f"{dataset} repeat {repeat+1}/3 fold {fold+1}/5: nested features", flush=True)
                    enriched = cached_meta(ctx, ids[a], held)
                    seed = 300+repeat*5+fold
                    function = threshold_fold if dataset == "abraham" else pleasantness_fold
                    inputs = (ctx, ids[a], held, ids[b], enriched, y[a], seed) if dataset == "abraham" else (ctx, transfer, ids[a], held, ids[b], enriched, y[a], seed)
                    values, counts = function(*inputs)
                    if not all(np.isfinite(p).all() and p.shape == (len(b),) for p in values.values()):
                        raise ValueError("Non-finite or misaligned selection predictions")
                    np.savez_compressed(path, **values)
                    record = {"identity": identity, "sha256": file_digest(path), "source_counts": counts,
                        "grouped_outer_fold_verified": True}
                    write_json(metadata_path, record)
                for name, p in values.items():
                    if name not in predictions:
                        predictions[name] = np.full((3, len(y)), np.nan)
                    predictions[name][repeat, b] = p
                folds.append(record)
                print(f"{dataset} repeat {repeat+1}/3 fold {fold+1}/5: complete", flush=True)
            print({n: metrics(y, p[repeat]) for n, p in predictions.items()}, flush=True)
        scores = {n: [metrics(y, p) for p in matrix] for n, matrix in predictions.items()}
        baseline = scores["current"]
        passing = []
        for name, values in scores.items():
            gain = np.array([p["pearson"]-q["pearson"] for p, q in zip(values, baseline)])
            if gain.mean() >= .01 and (gain > 0).sum() >= 2 and np.mean([p["mae"] for p in values]) <= np.mean([p["mae"] for p in baseline]):
                passing.append(name)
        selected = max(passing, key=lambda n: np.mean([p["pearson"] for p in scores[n]])) if passing else "current"
        results[dataset] = {"training_molecules": len(ids), "scores": scores, "passing": passing, "selected": selected,
            "primary_train_main_held_connectivity_overlaps": sorted(set(groups) & {str(i).split("-")[0] for i in fixed_held})}
        np.savez_compressed(out/f"{dataset}-inner-oof.npz", ids=ids.astype(str), y=y, **predictions)
        write_json(out/f"{dataset}-folds.json", folds)
        write_json(out/"partial.json", results)
    write_json(out/"results.json", {"host": platform.node(), "results": results,
        "reserved_targets_fitted_or_scored": False, "seconds": round(time.time()-started)})
    print(results, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--datasets", nargs="+", choices=("abraham", "keller"), default=["abraham", "keller"])
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    with threadpool_limits(limits=2):
        run(args)
