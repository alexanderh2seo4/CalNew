"""Registered grouped training-only pleasantness source normalization check.

Run numerical work through the isolated SSH compute wrapper. The two fixed
candidate representations are compared to verified existing grouped current-v3
predictions; this script never computes development-test endpoint scores.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import platform
import shutil
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.model_selection import GroupKFold
from threadpoolctl import threadpool_limits

from calnew.io import digest, file_digest, write_json
from calnew.pipeline.blocks import BlockCache
from calnew.pipeline.paper_benchmark import Context, FRACTIONS, random_split
from calnew.pipeline.semantic import SEMANTIC_BASE
from calnew.pipeline.semantic_balanced import BalancedDescriptorTransfer, array_sha256, verify_balanced_targets
from calnew.pipeline.stages import stack
from nose_intensity_experiment import metrics
from nose_semantic_experiment import RESERVED, SHA256, SOURCE, load_corpus


def atomic_npz(path, **values):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, name = tempfile.mkstemp(dir=path.parent, suffix=".npz")
    os.close(handle)
    try:
        np.savez_compressed(name, **values)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def common_baseline_modules(baseline):
    plan = json.loads((baseline/"selection-plan.json").read_text())
    checked = {}
    for name, expected in plan["code_sha256"].items():
        path = Path(name.replace("\\", "/"))
        if path.name.startswith("."):
            continue
        if not (str(path).replace("\\", "/").startswith("src/")
                or path.name in ("nose_intensity_experiment.py", "nose_semantic_experiment.py")):
            continue
        archived = baseline/"source-code"/path
        if not archived.exists() or file_digest(archived) != expected or file_digest(path) != expected:
            raise ValueError(f"Common baseline source changed: {path}")
        checked[path.as_posix()] = expected
    if "src/calnew/pipeline/semantic.py" not in checked:
        raise ValueError("Baseline semantic module has no verified archived identity")
    return plan, checked


def baseline_fold(baseline, plan, repeat, fold, train_ids, held_ids, eval_ids, y):
    path = baseline/f"keller-repeat-{repeat}-fold-{fold}.npz"
    record = json.loads(path.with_suffix(".json").read_text())
    identity = {"train_ids": train_ids.tolist(), "held_ids": held_ids.tolist(),
        "evaluate_ids": eval_ids.tolist(), "targets": y.tolist(), "code_sha256": plan["code_sha256"]}
    if (record["identity"] != identity or not record["grouped_outer_fold_verified"]
            or record["sha256"] != file_digest(path)):
        raise ValueError("Grouped current-v3 baseline fold identity/checksum differs")
    with np.load(path, allow_pickle=False) as data:
        current = data["current"].copy()
    if current.shape != (len(eval_ids),) or not np.isfinite(current).all():
        raise ValueError("Non-finite/misaligned current-v3 baseline")
    return current, {"path": str(path), "sha256": record["sha256"],
        "ids_targets_fold_and_common_source_verified": True}


def cached_source(transfer, ctx, excluded, eval_ids, representation, out, resource_sha):
    identity = {"resources_sha256": resource_sha, "representation": representation,
        "excluded_connectivities": sorted({str(m).split("-")[0] for m in excluded}),
        "evaluate_ids": eval_ids.tolist(), "source_seed": 173}
    path = out/"source-feature-cache"/(digest(identity)+".npz")
    metadata = path.with_suffix(".json")
    if path.exists() and metadata.exists():
        record = json.loads(metadata.read_text())
        if record["identity"] != identity or record["sha256"] != file_digest(path):
            raise ValueError("Balanced source feature cache provenance differs")
        with np.load(path, allow_pickle=False) as data:
            values = data["features"].copy()
    else:
        model = transfer.fit(excluded, representation)
        rows = ctx.rows(eval_ids)
        source = np.column_stack([ctx.B["rdkit"][rows], ctx.B["fingerprint"][rows]])
        values = transfer.predict(model, source)
        atomic_npz(path, features=values)
        record = {"identity": identity, "sha256": file_digest(path), "source_fit": model[2]}
        write_json(metadata, record)
    if values.shape != (len(eval_ids), 128) or not np.isfinite(values).all():
        raise ValueError("Invalid balanced source cached features")
    return values, {"path": str(path), "sha256": record["sha256"], "source_fit": record["source_fit"]}


def crossfit(transfer, ctx, train_ids, held_ids, eval_ids, seed, name, out, resource_sha):
    groups = np.array([str(m).split("-")[0] for m in train_ids])
    values = np.full((len(train_ids), 128), np.nan, np.float32)
    records = []
    for inner, (a, b) in enumerate(GroupKFold(3, shuffle=True, random_state=seed).split(train_ids, groups=groups)):
        if set(groups[a]) & set(groups[b]):
            raise ValueError("Source feature crossfit folds share connectivity")
        values[b], record = cached_source(transfer, ctx, np.r_[held_ids, train_ids[b]],
            train_ids[b], name, out, resource_sha)
        records.append({"inner_fold": inner, "train_ids": train_ids[a].tolist(),
            "feature_ids": train_ids[b].tolist(), **record})
    held, record = cached_source(transfer, ctx, held_ids, eval_ids, name, out, resource_sha)
    records.append({"inner_fold": "held", "feature_ids": eval_ids.tolist(), **record})
    if not np.isfinite(values).all():
        raise ValueError("Incomplete balanced crossfit source features")
    return values, held, records


def run(args):
    if platform.node().lower() != os.environ.get("CALNEW_COMPUTE_HOST", "").lower():
        raise ValueError("This experiment is restricted to the authorized SSH compute host")
    out, baseline = Path(args.out), Path(args.baseline)
    if (out/"results.json").exists() or (out.exists() and not args.resume):
        raise ValueError("Choose a fresh output or explicitly resume an incomplete experiment")
    out.mkdir(parents=True, exist_ok=True)
    baseline_plan, common_hashes = common_baseline_modules(baseline)
    own = [Path(__file__), Path("src/calnew/pipeline/semantic_balanced.py")]
    hashes = dict(common_hashes)
    for path in own:
        relative = path.resolve().relative_to(Path.cwd().resolve())
        hashes[relative.as_posix()] = file_digest(path)
    plan = {"host": platform.node(), "scope": "Original Keller split42 training260 only",
        "outer_cv": "Three connectivity GroupKFold5 repeats, seeds100/101/102",
        "source_feature_crossfit": "Connectivity GroupKFold3, seeds300+repeat*5+fold",
        "representations": {"idf_average": "Allowed-source IDF weighted L1 descriptor mean projected to128",
            "idf_unit": "Same allowed-source IDF projection, normalized to unit Euclidean length"},
        "idf": "log((1+allowed source rows)/(1+allowed source document frequency))+1; computed anew after each exclusion",
        "source_model": {"kind": "ExtraTrees", "n_estimators": 100, "min_samples_leaf": 4,
            "max_features": .3, "random_state": 173, "threads": 2},
        "endpoint_model": {"kind": "ExtraTrees", "n_estimators": 500, "min_samples_leaf": 2,
            "max_features": .3, "random_state": 42, "threads": 2,
            "features": "SEMANTIC_BASE + log dilution + new128 source features"},
        "candidate_predictions": "Each head and its fixed 50% blend with CURRENT v3",
        "selection": "Mean Pearson gain>=.01; positive>=2/3 repeats; no increase in mean MAE; highest passing mean Pearson",
        "baseline": str(baseline), "baseline_plan_sha256": file_digest(baseline/"selection-plan.json"),
        "common_baseline_module_hashes_verified": True, "code_sha256": hashes,
        "test_based_selection": False, "main_validation_test_targets_scored": False,
        "reserved_targets_fitted_or_scored": False, "new_source_capacity_tuning": False}
    if args.resume and json.loads((out/"selection-plan.json").read_text()) != plan:
        raise ValueError("Resume registration changed")
    write_json(out/"selection-plan.json", plan)
    for relative, expected in hashes.items():
        path = Path(relative)
        dest = out/"source-code"/path
        dest.parent.mkdir(parents=True, exist_ok=True)
        if args.resume and dest.exists() and file_digest(dest) != expected:
            raise ValueError("Archived experiment source changed")
        shutil.copy2(path, dest)
    checks = verify_balanced_targets()
    write_json(out/"normalization-checks.json", checks)
    ctx = Context(Path(json.loads(Path("data/current.json").read_text())["snapshot"]), RESERVED)
    molecules, labels = load_corpus(ctx, out)
    word_path = Path("data/features/nose-descriptor-minilm.npz")
    word_manifest = json.loads(word_path.with_suffix(".json").read_text())
    if word_manifest["sha256"] != file_digest(word_path) or word_manifest["corpus_sha256"] != SHA256:
        raise ValueError("Pinned generic word vector/source identity differs")
    terms = sorted(pd.read_csv(SOURCE, usecols=["TARGET_Descriptor"]).TARGET_Descriptor.unique())
    with np.load(word_path, allow_pickle=False) as data:
        if data["terms"].tolist() != terms:
            raise ValueError("Word vector vocabulary order differs")
        words = data["vectors"].copy()
    source_blocks = BlockCache(Path("data/features")).blocks(("rdkit", "fingerprint"), molecules.smiles.tolist())
    source = np.column_stack([source_blocks["rdkit"], source_blocks["fingerprint"]])
    transfer = BalancedDescriptorTransfer(molecules, labels, source, words, threads=2)
    resources = {"snapshot": str(ctx.snapshot),
        "snapshot_sha256": {name: file_digest(ctx.snapshot/name) for name in ("observations.parquet", "molecules.parquet", "stimuli.parquet")},
        "source_archive_sha256": file_digest(SOURCE), "word_vectors_sha256": file_digest(word_path),
        "word_manifest": word_manifest, "reserved_partitions_sha256": {
            str(run/name): file_digest(run/name) for run in RESERVED for name in ("split.json", "run.json")},
        "source_ids_sha256": array_sha256(transfer.ids), "source_features_sha256": array_sha256(source),
        "source_labels_sha256": digest({"shape": labels.shape, "data": array_sha256(labels.data),
            "indices": array_sha256(labels.indices), "indptr": array_sha256(labels.indptr)}),
        "projection_sha256": array_sha256(transfer.projection), "task_universe_sha256": digest(ctx.universe),
        "task_blocks_sha256": {name: array_sha256(ctx.B[name]) for name in SEMANTIC_BASE},
        "code_sha256": hashes, "dependencies": {name: importlib.metadata.version(name)
            for name in ("numpy", "scipy", "pandas", "scikit-learn", "rdkit")},
        "python": platform.python_version()}
    resource_sha = digest(resources)
    if args.resume and json.loads((out/"resource-manifest.json").read_text()) != resources:
        raise ValueError("Resume data/features/dependencies changed")
    write_json(out/"resource-manifest.json", resources)
    frame = ctx.keller
    tr, va, te = random_split(len(frame), FRACTIONS["keller"], 42)
    all_ids = frame.molecule_id.to_numpy()
    ids, fixed_held = all_ids[tr], all_ids[np.r_[va, te]]
    y = frame.pleasantness.to_numpy()[tr]
    groups = np.array([str(m).split("-")[0] for m in ids])
    if set(groups) & {str(m).split("-")[0] for m in fixed_held}:
        raise ValueError("Keller primary train/main-held connectivity overlap")
    rows = ctx.rows(ids)
    base = np.column_stack([stack(ctx.B, SEMANTIC_BASE)[rows], frame.x.to_numpy()[tr, None]])
    predictions = {name: np.full((3, len(y)), np.nan) for name in ("current", "idf_average", "idf_unit", "blend_idf_average", "blend_idf_unit")}
    folds = []
    started = time.time()
    print(f"Balanced source: {len(molecules)} molecules; grouped pleasantness cohort {len(ids)}", flush=True)
    for repeat in range(3):
        for fold, (a, b) in enumerate(GroupKFold(5, shuffle=True, random_state=100+repeat).split(ids, groups=groups)):
            if set(groups[a]) & set(groups[b]):
                raise ValueError("Outer endpoint folds share connectivity")
            held = np.r_[fixed_held, ids[b]]
            current, baseline_evidence = baseline_fold(baseline, baseline_plan, repeat, fold, ids[a], held, ids[b], y[b])
            identity = {"resource_sha256": resource_sha, "train_ids": ids[a].tolist(),
                "held_ids": held.tolist(), "evaluate_ids": ids[b].tolist(),
                "train_targets": y[a].tolist(), "targets": y[b].tolist(), "baseline": baseline_evidence}
            path = out/f"keller-repeat-{repeat}-fold-{fold}.npz"
            metadata = path.with_suffix(".json")
            if args.resume and path.exists() and metadata.exists():
                record = json.loads(metadata.read_text())
                if record["identity"] != identity or record["sha256"] != file_digest(path):
                    raise ValueError("Resume fold/checksum/data identity differs")
                with np.load(path, allow_pickle=False) as data:
                    values = {name: data[name].copy() for name in data.files}
                if not np.array_equal(values["current"], current):
                    raise ValueError("Resume paired current predictions differ")
            else:
                values, source_records = {"current": current}, {}
                for name in transfer.REPRESENTATIONS:
                    print(f"repeat {repeat+1}/3 fold {fold+1}/5 {name}: grouped source crossfit", flush=True)
                    train, test, source_records[name] = crossfit(transfer, ctx, ids[a], held, ids[b],
                        300+repeat*5+fold, name, out, resource_sha)
                    model = ExtraTreesRegressor(n_estimators=500, min_samples_leaf=2, max_features=.3,
                        n_jobs=2, random_state=42).fit(np.column_stack([base[a], train]), y[a])
                    values[name] = model.predict(np.column_stack([base[b], test]))
                    values["blend_"+name] = (current+values[name])/2
                atomic_npz(path, **values)
                record = {"identity": identity, "sha256": file_digest(path), "source_fits": source_records,
                    "outer_connectivity_disjoint_verified": True}
                write_json(metadata, record)
            if set(values) != set(predictions):
                raise ValueError("Checkpoint candidate keys differ")
            for name, p in values.items():
                if p.shape != (len(b),) or not np.isfinite(p).all():
                    raise ValueError("Incomplete/non-finite candidate fold")
                predictions[name][repeat, b] = p
            folds.append(record)
            write_json(out/"fold-progress.json", {"completed_folds": len(folds), "total_folds": 15,
                "latest_repeat": repeat, "latest_fold": fold})
            print(f"repeat {repeat+1}/3 fold {fold+1}/5 complete", flush=True)
        print({name: metrics(y, p[repeat]) for name, p in predictions.items()}, flush=True)
        atomic_npz(out/"keller-inner-oof.npz", ids=ids.astype(str), y=y, **predictions)
    scores = {name: [metrics(y, p) for p in values] for name, values in predictions.items()}
    reference = scores["current"]
    passing = []
    for name, values in scores.items():
        gain = np.array([p["pearson"]-q["pearson"] for p, q in zip(values, reference)])
        if gain.mean() >= .01 and (gain > 0).sum() >= 2 and np.mean([p["mae"] for p in values]) <= np.mean([p["mae"] for p in reference]):
            passing.append(name)
    selected = max(passing, key=lambda name: np.mean([p["pearson"] for p in scores[name]])) if passing else "current"
    write_json(out/"keller-folds.json", folds)
    result = {"host": platform.node(), "resource_sha256": resource_sha, "normalization_checks": checks,
        "seconds": round(time.time()-started), "results": {"keller": {"training_molecules": len(ids),
            "scores": scores, "passing": passing, "selected": selected,
            "primary_train_main_held_connectivity_overlaps": []}},
        "main_validation_test_targets_scored": False, "reserved_targets_fitted_or_scored": False}
    write_json(out/"results.json", result)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="runs/nose-balanced-semantic-grouped-inner-v1")
    parser.add_argument("--baseline", default="runs/nose-parity-pleasantness-grouped-inner-v2")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    with threadpool_limits(limits=2):
        run(args)
