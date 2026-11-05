"""Fixed all-stimulus pleasantness recipes, selected on original training only.

Reuse verified nested features and current-v3 comparator predictions; no source
fitting, main development-test scoring, or reserved-target scoring occurs here.
"""
from __future__ import annotations

import os
import argparse
import json
from pathlib import Path
import platform
import shutil
import time

import numpy as np
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.model_selection import GroupKFold
import torch
from threadpoolctl import threadpool_limits

from calnew.io import digest, file_digest, write_json
from calnew.pipeline.paper_benchmark import FRACTIONS, random_split
from calnew.pipeline.semantic import SEMANTIC_BASE
from calnew.pipeline.stages import HEDONIC_MEMBERS, TabularEnsemble, stack
from nose_balanced_semantic_refine import atomic_npz, baseline_fold, common_baseline_modules
from nose_intensity_experiment import CACHE, cache_identity, metrics
from nose_parity_progress import array_identity, dependency_versions, inspect_run, read_only_context
from nose_semantic_experiment import RESERVED, SHA256, SOURCE


NAMES = ("all_semantic", "all_hedonic", "all_ensemble")


def load_features(ctx, train, held, seed):
    arrays, evidence = {}, {}
    for kind, feature_seed in (("quality", 42), ("semantic", seed)):
        identity = cache_identity(ctx, train, held, feature_seed, kind)
        path = CACHE/(digest(identity)+".npz")
        manifest = path.with_suffix(".json")
        if not path.exists() or not manifest.exists():
            raise ValueError("Required nested feature cache missing; this study never generates it")
        record = json.loads(manifest.read_text())
        if record["identity"] != json.loads(json.dumps(identity)) or record["sha256"] != file_digest(path):
            raise ValueError("Nested cache identity/checksum differs")
        with np.load(path, allow_pickle=False) as data:
            wanted = ("quality", "direction") if kind == "quality" else ("semantic",)
            for name in wanted:
                value = data[name].copy()
                shape = ctx.labels.shape if name == "quality" else ctx.direction.shape if name == "direction" else (len(ctx.universe), 128)
                if value.shape != shape or not np.isfinite(value).all():
                    raise ValueError("Nested cache array shape/finiteness differs")
                arrays[name] = value
        evidence[kind] = {"path": str(path), "sha256": record["sha256"],
            "manifest_sha256": file_digest(manifest), "identity_sha256": digest(identity),
            "arrays": {name: array_identity(arrays[name]) for name in wanted}}
    return arrays, evidence


def run(args):
    if platform.node().lower() != os.environ.get("CALNEW_COMPUTE_HOST", "").lower():
        raise ValueError("Run numerical work on authorized SSH host compute-host only")
    out, baseline = Path(args.out), Path(args.baseline)
    if (out/"results.json").exists() or (out.exists() and not args.resume):
        raise ValueError("Use a fresh output directory or explicit incomplete-run resume")
    out.mkdir(parents=True, exist_ok=True)
    baseline_plan, hashes = common_baseline_modules(baseline)
    for path in (Path(__file__), Path("scripts/nose_balanced_semantic_refine.py"),
            Path("scripts/nose_parity_progress.py")):
        hashes[path.resolve().relative_to(Path.cwd().resolve()).as_posix()] = file_digest(path)
    plan = {"host": platform.node(), "scope": "Original Keller split42 training260 only",
        "outer_cv": "Connectivity GroupKFold5, seeds100/101/102",
        "change": "Use every finite pleasantness stimulus of each outer-training molecule, with its nominal log dilution",
        "stimulus_weighting": "Equal weight per stimulus; molecules with more finite stimuli have more endpoint fitting weight",
        "candidates": list(NAMES)+["blend_"+name for name in NAMES],
        "semantic_head": {"kind": "ExtraTrees", "trees": 500, "leaf": 2,
            "max_features": .3, "seed": 42, "features": "SEMANTIC_BASE + dilution + legacy semantic128"},
        "hedonic_head": "Same two existing HEDONIC_MEMBERS and settings; change only training stimulus rows",
        "ensemble": "Half all-semantic and half all-hedonic",
        "blend": "Fixed half candidate and half CURRENT v3",
        "gate": "Mean Pearson gain>=.01; gain positive>=2/3 repeats; no increase mean MAE; highest passing mean Pearson",
        "features": "Existing checksum/identity-verified nested q/d and semantic caches; no new source fits",
        "baseline": str(baseline), "baseline_plan_sha256": file_digest(baseline/"selection-plan.json"),
        "code_sha256": hashes, "main_validation_test_targets_scored": False,
        "reserved_targets_fitted_or_scored": False, "capacity_or_dose_response_tuning": False}
    if args.resume and json.loads((out/"selection-plan.json").read_text()) != plan:
        raise ValueError("Resume registration changed")
    write_json(out/"selection-plan.json", plan)
    for relative, expected in hashes.items():
        target = out/"source-code"/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if args.resume and target.exists() and file_digest(target) != expected:
            raise ValueError("Archived source changed")
        shutil.copy2(relative, target)
    ctx = read_only_context(Path(json.loads(Path("data/current.json").read_text())["snapshot"]))
    audit = inspect_run(ctx, str(baseline))
    task = audit.get("datasets", {}).get("keller", {})
    if task.get("status") != "complete" or not task.get("saved_final_results_verified", {}).get("scores_and_promotion_exact"):
        raise ValueError("Current-v3 comparator is not a complete verified fifteen-fold run")
    write_json(out/"baseline-audit.json", audit)
    tr, va, te = random_split(len(ctx.keller), FRACTIONS["keller"], 42)
    frame = ctx.keller
    all_ids = frame.molecule_id.to_numpy()
    ids, fixed_held = all_ids[tr], all_ids[np.r_[va, te]]
    y = frame.pleasantness.to_numpy()[tr]
    groups = np.array([str(m).split("-")[0] for m in ids])
    if len(ids) != 260 or set(groups) & {str(m).split("-")[0] for m in fixed_held}:
        raise ValueError("Original training cohort or primary connectivity boundary changed")
    panel = ctx.data.panel
    primary_stimuli = np.isin(panel["molecule_ids"], ids)
    finite = np.isfinite(panel["pleasantness"]) & np.isfinite(panel["x"])
    allowed_stimuli = primary_stimuli & finite
    if allowed_stimuli.sum() <= len(ids) or not np.isin(ids, panel["molecule_ids"][allowed_stimuli]).all():
        raise ValueError("Expected multiple finite training stimuli per molecule")
    folds, cache_records = [], {}
    for repeat in range(3):
        for fold, (a, b) in enumerate(GroupKFold(5, shuffle=True, random_state=100+repeat).split(ids, groups=groups)):
            held = np.r_[fixed_held, ids[b]]
            _, evidence = load_features(ctx, ids[a], held, 300+repeat*5+fold)
            cache_records[f"{repeat}-{fold}"] = evidence
            folds.append((repeat, fold, a, b, held))
    resources = {"snapshot": str(ctx.snapshot), "snapshot_sha256": {name: file_digest(ctx.snapshot/name)
            for name in ("molecules.parquet", "observations.parquet", "stimuli.parquet")},
        "reserved_manifest_sha256": {str(run/name): file_digest(run/name) for run in RESERVED for name in ("run.json", "split.json")},
        "source_sha256": file_digest(SOURCE), "source_matches_pin": file_digest(SOURCE) == SHA256,
        "word_vectors_sha256": file_digest(Path("data/features/nose-descriptor-minilm.npz")),
        "universe_sha256": digest(ctx.universe), "settings_sha256": digest(ctx.cfg),
        "blocks": {name: array_identity(value) for name, value in ctx.B.items()},
        "training_ids": ids.tolist(), "primary_targets": array_identity(y),
        "allowed_stimulus_ids": panel["molecule_ids"][allowed_stimuli].tolist(),
        "allowed_stimuli_per_molecule": dict(zip(*[values.tolist() for values in np.unique(panel["molecule_ids"][allowed_stimuli], return_counts=True)])),
        "allowed_stimulus_doses": array_identity(panel["x"][allowed_stimuli]),
        "allowed_stimulus_pleasantness": array_identity(panel["pleasantness"][allowed_stimuli]),
        "feature_cache_records": cache_records, "code_sha256": hashes, "dependencies": dependency_versions()}
    if not resources["source_matches_pin"]:
        raise ValueError("Descriptor source differs from pinned corpus")
    if args.resume and json.loads((out/"resource-manifest.json").read_text()) != resources:
        raise ValueError("Resume data/features/dependencies changed")
    write_json(out/"resource-manifest.json", resources)
    resource_sha = digest(resources)
    predictions = {name: np.full((3, len(ids)), np.nan) for name in ("current",)+NAMES+tuple("blend_"+n for n in NAMES)}
    started = time.time()
    print(f"All-stimulus study: {len(ids)} training molecules, {allowed_stimuli.sum()} finite stimuli", flush=True)
    for repeat, fold, a, b, held in folds:
        if set(groups[a]) & set(groups[b]):
            raise ValueError("Outer folds share connectivity")
        current, comparator = baseline_fold(baseline, baseline_plan, repeat, fold, ids[a], held, ids[b], y[b])
        selected = np.isin(panel["molecule_ids"], ids[a]) & finite
        stimulus_ids = panel["molecule_ids"][selected]
        if set(str(m).split("-")[0] for m in stimulus_ids) & {str(m).split("-")[0] for m in held}:
            raise ValueError("Held stimulus entered endpoint training")
        identity = {"resource_sha256": resource_sha, "train_ids": ids[a].tolist(),
            "held_ids": held.tolist(), "evaluate_ids": ids[b].tolist(), "targets": y[b].tolist(),
            "training_stimulus_ids": stimulus_ids.tolist(), "baseline": comparator}
        path = out/f"keller-repeat-{repeat}-fold-{fold}.npz"
        metadata = path.with_suffix(".json")
        if path.exists() != metadata.exists():
            raise ValueError("Orphan fold prediction/metadata; refuse checkpoint reuse")
        if path.exists():
            record = json.loads(metadata.read_text())
            if not args.resume or record["identity"] != identity or record["sha256"] != file_digest(path):
                raise ValueError("Fold resume identity/checksum differs")
            with np.load(path, allow_pickle=False) as saved:
                values = {name: saved[name].copy() for name in saved.files}
            if not np.array_equal(values["current"], current):
                raise ValueError("Current comparator changed")
        else:
            cached, evidence = load_features(ctx, ids[a], held, 300+repeat*5+fold)
            if evidence != cache_records[f"{repeat}-{fold}"]:
                raise ValueError("Feature cache changed after prefit resource registration")
            enriched = {**ctx.B, "quality": cached["quality"], "direction": cached["direction"]}
            rr, ee = ctx.p_rows[selected], ctx.rows(ids[b])
            dose_train = panel["x"][selected, None]
            dose_eval = frame.x.to_numpy()[tr[b], None]
            target = panel["pleasantness"][selected]
            pick = lambda rows: {n: enriched[n][rows] for _, names in HEDONIC_MEMBERS for n in names}
            h = TabularEnsemble(HEDONIC_MEMBERS, seed=42, threads=2).fit(pick(rr), target,
                ctx.connectivity[rr], columns=dose_train).predict(pick(ee), columns=dose_eval)
            base = stack(ctx.B, SEMANTIC_BASE)
            semantic = cached["semantic"]
            model = ExtraTreesRegressor(n_estimators=500, min_samples_leaf=2, max_features=.3,
                n_jobs=2, random_state=42).fit(np.column_stack([base[rr], dose_train, semantic[rr]]), target)
            s = model.predict(np.column_stack([base[ee], dose_eval, semantic[ee]]))
            values = {"current": current, "all_semantic": s, "all_hedonic": h, "all_ensemble": (s+h)/2}
            values.update({"blend_"+name: (current+values[name])/2 for name in NAMES})
            atomic_npz(path, **values)
            record = {"identity": identity, "sha256": file_digest(path),
                "training_stimuli": int(selected.sum()), "endpoint_held_connectivity_overlap": [],
                "all_fold_features_prefit_registered": True}
            write_json(metadata, record)
        if set(values) != set(predictions):
            raise ValueError("Fold candidate schema differs")
        for name, value in values.items():
            if value.shape != (len(b),) or not np.isfinite(value).all():
                raise ValueError("Non-finite/misaligned candidate predictions")
            predictions[name][repeat, b] = value
        write_json(out/"fold-progress.json", {"completed_folds": repeat*5+fold+1, "total_folds": 15})
        print(f"All-stimulus repeat{repeat+1}/3 fold{fold+1}/5 complete", flush=True)
    if not all(np.isfinite(value).all() for value in predictions.values()):
        raise ValueError("Incomplete original-training prediction coverage")
    scores = {name: [metrics(y, row) for row in value] for name, value in predictions.items()}
    passing = []
    for name, value in scores.items():
        gain = np.array([p["pearson"]-q["pearson"] for p, q in zip(value, scores["current"])])
        if gain.mean() >= .01 and (gain > 0).sum() >= 2 and np.mean([p["mae"] for p in value]) <= np.mean([p["mae"] for p in scores["current"]]):
            passing.append(name)
    selected = max(passing, key=lambda name: np.mean([p["pearson"] for p in scores[name]])) if passing else "current"
    atomic_npz(out/"keller-inner-oof.npz", ids=ids.astype(str), y=y, **predictions)
    result = {"host": platform.node(), "resource_sha256": resource_sha, "seconds": round(time.time()-started),
        "results": {"keller": {"training_molecules": len(ids), "training_stimuli": int(allowed_stimuli.sum()),
            "scores": scores, "passing": passing, "selected": selected}},
        "main_validation_test_targets_scored": False, "reserved_targets_fitted_or_scored": False}
    write_json(out/"results.json", result)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="runs/nose-pleasantness-all-stimuli-inner-v1")
    parser.add_argument("--baseline", default="runs/nose-parity-pleasantness-grouped-inner-v2")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    torch.set_num_threads(2)
    with threadpool_limits(limits=2):
        run(args)
