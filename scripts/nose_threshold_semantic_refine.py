"""Registered globally disjoint threshold descriptor transfer; SSH compute only.

Every eligible primary Abraham connectivity is excluded from descriptor source
learning. Two source heads can therefore be fitted once and shared across all
training-only outer folds, without source self-exposure or primary endpoint labels.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import shutil
import tempfile

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.stats import pearsonr
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler
import torch
from threadpoolctl import threadpool_limits

from calnew.io import digest, file_digest, write_json
from calnew.pipeline.blocks import BlockCache, EXPLICIT_BLOCKS
from calnew.pipeline.paper_benchmark import FRACTIONS, random_split
from calnew.pipeline.semantic import SEMANTIC_BASE
from calnew.pipeline.semantic_balanced import BalancedDescriptorTransfer, array_sha256, verify_balanced_targets
from calnew.pipeline.stages import stack
from nose_parity_progress import array_identity, dependency_versions, file_identity, inspect_run, read_only_context
from nose_semantic_experiment import RESERVED, SHA256, SOURCE, load_corpus


CANDIDATES = {name+"_"+head: (name, head)
    for name in BalancedDescriptorTransfer.REPRESENTATIONS for head in ("trees", "ridge100")}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def atomic_npz(path, **values):
    path = Path(path)
    fd, temporary = tempfile.mkstemp(dir=path.parent, suffix=".npz")
    os.close(fd)
    try:
        np.savez_compressed(temporary, **values)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def sparse_identity(values):
    values = values.tocsr(copy=True)
    values.sum_duplicates()
    values.sort_indices()
    return {"shape": list(values.shape), "nnz": int(values.nnz),
        "data": array_identity(values.data), "indices": array_identity(values.indices),
        "indptr": array_identity(values.indptr)}


def score(y, p):
    if y.shape != p.shape or not np.isfinite(p).all():
        raise ValueError("Non-finite or misaligned original-training predictions")
    return {"pearson": float(pearsonr(y, p).statistic), "mae": float(np.abs(y-p).mean()),
        "rmse": float(np.sqrt(np.square(y-p).mean()))}


def common_sources(baseline):
    plan = json.loads((baseline/"selection-plan.json").read_text())
    hashes = {}
    for relative, expected in plan["code_sha256"].items():
        path = Path(relative.replace("\\", "/"))
        if path.name.startswith("."):
            continue
        if not (path.as_posix().startswith("src/") or path.name in (
                "nose_intensity_experiment.py", "nose_semantic_experiment.py")):
            continue
        archived = baseline/"source-code"/path
        if not archived.exists() or file_digest(archived) != expected or file_digest(path) != expected:
            raise ValueError(f"Common baseline source changed: {path}")
        hashes[path.as_posix()] = expected
    if "src/calnew/pipeline/semantic.py" not in hashes:
        raise ValueError("No pinned baseline semantic module")
    for path in (Path(__file__), Path("scripts/nose_parity_progress.py"),
            Path("src/calnew/pipeline/semantic_balanced.py"), Path("scripts/ssh_compute.py")):
        relative = path.resolve().relative_to(Path.cwd().resolve())
        hashes[relative.as_posix()] = file_digest(path)
    return plan, hashes


def cohort(ctx):
    all_ids = ctx.thr.molecule_id.to_numpy(dtype=str)
    if len(all_ids) != 186 or len(set(all_ids)) != 186:
        raise ValueError("Eligible primary threshold cohort changed from 186 unique IDs")
    tr, va, te = random_split(len(all_ids), FRACTIONS["abraham"], 42)
    ids, held = all_ids[tr], all_ids[np.r_[va, te]]
    y = ctx.thr.y.to_numpy()[tr]
    if len(ids) != 111 or not np.isfinite(y).all():
        raise ValueError("Original split42 threshold training111 cohort changed")
    rows = ctx.rows(all_ids)
    source_inputs = np.column_stack([ctx.B["rdkit"][rows], ctx.B["fingerprint"][rows]])
    base = {"trees": stack(ctx.B, SEMANTIC_BASE)[rows],
        "ridge100": stack(ctx.B, EXPLICIT_BLOCKS)[rows]}
    return all_ids, ids, held, y, tr, source_inputs, base


def load_source(ctx, out):
    molecules, labels = load_corpus(ctx, out)
    word_path = Path("data/features/nose-descriptor-minilm.npz")
    word_manifest = json.loads(word_path.with_suffix(".json").read_text())
    if word_manifest["sha256"] != file_digest(word_path) or word_manifest["corpus_sha256"] != SHA256:
        raise ValueError("Pinned word-vector/source identity differs")
    terms = sorted(pd.read_csv(SOURCE, usecols=["TARGET_Descriptor"]).TARGET_Descriptor.unique())
    with np.load(word_path, allow_pickle=False) as data:
        if data["terms"].tolist() != terms:
            raise ValueError("Word-vector vocabulary order differs")
        words = data["vectors"].copy()
    blocks = BlockCache(Path("data/features")).blocks(("rdkit", "fingerprint"), molecules.smiles.tolist())
    source = np.column_stack([blocks["rdkit"], blocks["fingerprint"]])
    transfer = BalancedDescriptorTransfer(molecules, labels, source, words, threads=2)
    return molecules, transfer, words, word_manifest


def source_checks(molecules, transfer, words, excluded):
    checks = verify_balanced_targets()
    targets = {name: transfer.source_targets(excluded, name)
        for name in transfer.REPRESENTATIONS}
    keep = targets["idf_average"][0]
    if not np.array_equal(keep, targets["idf_unit"][0]):
        raise ValueError("Representation source exclusions differ")
    forbidden = {str(i).split("-")[0] for i in excluded}
    if set(transfer.connectivity[keep]) & forbidden:
        raise ValueError("Eligible primary threshold connectivity entered source fitting")
    # Actual forbidden association rows are perturbed, while all allowed rows
    # and the generic vocabulary stay fixed. Neither IDF nor targets may move.
    bad = np.flatnonzero(~keep)
    changed = transfer.labels.multiply(keep[:, None]).tocsr()
    if len(bad):
        changed += sparse.csr_matrix((np.ones(len(bad), np.float32),
            (bad, np.arange(len(bad)) % transfer.labels.shape[1])), shape=transfer.labels.shape)
        if (changed != transfer.labels).nnz == 0:
            raise ValueError("Actual exclusion perturbation did not change any source labels")
    other = BalancedDescriptorTransfer(molecules, changed, transfer.features, words, threads=2)
    for name, (mask, target, idf, audit) in targets.items():
        mask2, target2, idf2, _ = other.source_targets(excluded, name)
        if not (np.array_equal(mask, mask2) and np.array_equal(target, target2)
                and np.array_equal(idf, idf2)):
            raise ValueError("Forbidden actual source labels changed IDF/targets")
        if audit["source_ids_sha256"] != array_sha256(transfer.ids[keep]):
            raise ValueError("Source ID hash differs from actual filtered IDs")
    checks.update({"all186_primary_connectivities_excluded": True,
        "actual_excluded_source_rows": len(bad),
        "actual_forbidden_association_perturbation_changes_no_allowed_idf_or_targets": True,
        "source_idf_and_normalization_are_independent_of_endpoint_targets": True})
    return targets, checks


def resource_identity(ctx, hashes, transfer, words, word_manifest, all_ids, ids, held, y,
        task_source, base, targets):
    keep = targets["idf_average"][0]
    return {"snapshot": str(ctx.snapshot), "snapshot_sha256": {name: file_digest(ctx.snapshot/name)
            for name in ("molecules.parquet", "observations.parquet", "stimuli.parquet")},
        "reserved_partition_sha256": {str(run/name): file_digest(run/name)
            for run in RESERVED for name in ("run.json", "split.json")},
        "source_files": {str(path): file_identity(path) for path in (
            SOURCE, Path("data/raw/li_2025/zenodo-17559514-v1/threshold_data_med.csv"),
            Path("data/features/nose-descriptor-minilm.npz"), Path("data/features/nose-descriptor-minilm.json"))},
        "word_manifest": word_manifest, "word_vectors": array_identity(words),
        "task_universe_sha256": digest(ctx.universe), "settings_sha256": digest(ctx.cfg),
        "task_blocks": {name: array_identity(ctx.B[name]) for name in SEMANTIC_BASE},
        "all186_ids": all_ids.tolist(), "training111_ids": ids.tolist(),
        "main_held_ids": held.tolist(), "training111_targets": array_identity(y),
        "primary_train_main_held_connectivity_overlap": sorted(
            {str(i).split("-")[0] for i in ids} & {str(i).split("-")[0] for i in held}),
        "task_source_inputs": array_identity(task_source),
        "endpoint_base_inputs": {name: array_identity(values) for name, values in base.items()},
        "source_ids_before_primary_exclusion": array_identity(transfer.ids),
        "source_labels_before_primary_exclusion": sparse_identity(transfer.labels),
        "filtered_source_ids": transfer.ids[keep].tolist(),
        "filtered_source_connectivities_sha256": digest(transfer.connectivity[keep].tolist()),
        "filtered_source_features": array_identity(transfer.features[keep]),
        "filtered_source_labels": sparse_identity(transfer.labels[keep]),
        "projection": array_identity(transfer.projection),
        "source_targets": {name: {"audit": values[3], "target": array_identity(values[1]),
            "idf": array_identity(values[2])} for name, values in targets.items()},
        "dependencies": dependency_versions(), "code_sha256": hashes}


def source_features(transfer, targets, all_ids, task_source, out, resource_sha, resume):
    values, evidence = {}, {}
    for name in transfer.REPRESENTATIONS:
        path = out/f"source-{name}.npz"
        identity = {"resource_sha256": resource_sha, "representation": name,
            "evaluate_ids": all_ids.tolist(), "source_target_audit": targets[name][3]}
        if path.exists() and path.with_suffix(".json").exists():
            if not resume:
                raise ValueError("Existing source feature cache requires explicit resume")
            record = json.loads(path.with_suffix(".json").read_text())
            if record["identity"] != identity or record["sha256"] != file_digest(path):
                raise ValueError("Globally disjoint source feature identity/checksum differs")
            with np.load(path, allow_pickle=False) as data:
                if not np.array_equal(data["ids"], all_ids):
                    raise ValueError("Source feature cache evaluation order differs")
                values[name] = data["features"].copy()
        else:
            print(f"Fitting one globally disjoint {name} source model on {int(targets[name][0].sum())} rows", flush=True)
            fitted = transfer.fit(all_ids, name)
            if fitted[2] != targets[name][3]:
                raise ValueError("Source fitting targets differ from prefit registration")
            scaler, _, _ = fitted
            before = digest({key: [array_identity(v) for v in stats] for key, stats in scaler.stats.items()})
            original = scaler.transform({"x": task_source})["x"]
            altered = np.nan_to_num(task_source, nan=0., posinf=0., neginf=0.)*7.+101.
            scaler.transform({"x": altered})
            after = digest({key: [array_identity(v) for v in stats] for key, stats in scaler.stats.items()})
            if before != after or not np.array_equal(original, scaler.transform({"x": task_source})["x"]):
                raise ValueError("Primary held structures changed fitted source normalization")
            values[name] = transfer.predict(fitted, task_source)
            atomic_npz(path, ids=all_ids, features=values[name])
            record = {"identity": identity, "sha256": file_digest(path), "fitted_at_utc": utc_now(),
                "source_fits_in_this_cache": 1, "source_scaler_fit_allowed_source_only": True,
                "primary_held_feature_perturbation_changes_no_source_scaler_state": True,
                "source_scaler_state_sha256": before, "feature_array": array_identity(values[name])}
            write_json(path.with_suffix(".json"), record)
        if values[name].shape != (186, 128) or not np.isfinite(values[name]).all():
            raise ValueError("Invalid source predictions for eligible primary structures")
        evidence[name] = record
        print(f"Globally disjoint {name} source representation complete", flush=True)
    write_json(out/"source-fits.json", {"representations": evidence,
        "total_registered_source_model_fits": 2, "primary_source_connectivity_overlap": [],
        "primary_threshold_or_odor_labels_used_by_new_source_models": False})
    return values


def endpoint_transform(training, evaluation, standardize):
    training = np.where(np.isfinite(training), training, np.nan)
    evaluation = np.where(np.isfinite(evaluation), evaluation, np.nan)
    first = SimpleImputer(strategy="median", keep_empty_features=True).fit(training)
    second = SimpleImputer(strategy="median", keep_empty_features=True).fit(training.copy())
    if not np.array_equal(first.statistics_, second.statistics_):
        raise ValueError("Identical endpoint imputation fits differ")
    train, test = first.transform(training), first.transform(evaluation)
    state = {"imputer_statistics": array_identity(first.statistics_)}
    altered = np.nan_to_num(evaluation, nan=0.)*7.+101.
    first.transform(altered)
    if state["imputer_statistics"] != array_identity(first.statistics_):
        raise ValueError("Held endpoint inputs changed training medians")
    if standardize:
        scaler = StandardScaler().fit(train)
        twin = StandardScaler().fit(train.copy())
        if not (np.array_equal(scaler.mean_, twin.mean_) and np.array_equal(scaler.scale_, twin.scale_)):
            raise ValueError("Identical endpoint scaler fits differ")
        state.update({"mean": array_identity(scaler.mean_), "scale": array_identity(scaler.scale_)})
        scaler.transform(first.transform(altered))
        if state["mean"] != array_identity(scaler.mean_) or state["scale"] != array_identity(scaler.scale_):
            raise ValueError("Held endpoint inputs changed fitted normalization")
        train, test = scaler.transform(train), scaler.transform(test)
    if not np.isfinite(train).all() or not np.isfinite(test).all():
        raise ValueError("Non-finite endpoint transformed features")
    return train, test, {"identical_training_preprocessing_fit_exact": True,
        "held_perturbation_changes_no_fitted_medians_or_scales": True,
        "output_finite": True, "standardized": standardize, "fitted_state": state}


def endpoint_checkpoints(out, ids, held, y, tr, base, source, resource_sha, resume):
    groups = np.array([str(i).split("-")[0] for i in ids])
    features = {name: np.column_stack([base[head][tr], source[representation][tr]])
        for name, (representation, head) in CANDIDATES.items()}
    predictions = {name: np.full((3, len(ids)), np.nan) for name in CANDIDATES}
    records = []
    for repeat in range(3):
        coverage = np.zeros(len(ids), int)
        for fold, (a, b) in enumerate(GroupKFold(5, shuffle=True, random_state=100+repeat).split(ids, groups=groups)):
            if set(groups[a]) & set(groups[b]):
                raise ValueError("Endpoint outer folds share connectivity")
            identity = {"resource_sha256": resource_sha, "train_ids": ids[a].tolist(),
                "held_ids": np.r_[held, ids[b]].tolist(), "evaluate_ids": ids[b].tolist(),
                "train_targets": y[a].tolist(), "targets": y[b].tolist(),
                "features_sha256": {name: array_sha256(x) for name, x in features.items()}}
            path = out/f"abraham-repeat-{repeat}-fold-{fold}.npz"
            if path.exists() and path.with_suffix(".json").exists():
                if not resume:
                    raise ValueError("Existing endpoint checkpoint requires explicit resume")
                record = json.loads(path.with_suffix(".json").read_text())
                if record["identity"] != identity or record["sha256"] != file_digest(path):
                    raise ValueError("Endpoint checkpoint identity/checksum differs")
                with np.load(path, allow_pickle=False) as data:
                    values = {name: data[name].copy() for name in data.files}
            else:
                values, checks = {}, {}
                for name, (_, head) in CANDIDATES.items():
                    train, evaluate, checks[name] = endpoint_transform(features[name][a], features[name][b], head == "ridge100")
                    model = (ExtraTreesRegressor(n_estimators=500, min_samples_leaf=2,
                        max_features=.3, random_state=42, n_jobs=2) if head == "trees" else Ridge(alpha=100.))
                    values[name] = model.fit(train, y[a]).predict(evaluate)
                atomic_npz(path, **values)
                record = {"identity": identity, "sha256": file_digest(path), "endpoint_transform_checks": checks,
                    "outer_connectivity_disjoint_verified": True, "fitted_at_utc": utc_now()}
                write_json(path.with_suffix(".json"), record)
            if set(values) != set(CANDIDATES):
                raise ValueError("Endpoint candidate names differ")
            for name, p in values.items():
                if p.shape != (len(b),) or not np.isfinite(p).all():
                    raise ValueError("Invalid endpoint fold predictions")
                predictions[name][repeat, b] = p
            coverage[b] += 1
            records.append(record)
            print(f"Threshold semantic repeat{repeat+1}/3 fold{fold+1}/5 complete", flush=True)
        if not np.all(coverage == 1):
            raise ValueError("Original threshold training coverage differs")
        print(json.dumps({"repeat": repeat, "standalone_semantic": {
            name: score(y, p[repeat]) for name, p in predictions.items()}}), flush=True)
    atomic_npz(out/"abraham-semantic-oof.npz", ids=ids, y=y, **predictions)
    write_json(out/"semantic-folds.json", records)
    write_json(out/"semantic-results.json", {"status": "semantic_complete_baseline_gate_pending",
        "resource_sha256": resource_sha, "original_training_rows": len(ids),
        "scores": {name: [score(y, p) for p in matrix] for name, matrix in predictions.items()},
        "main_validation_test_targets_scored": False, "reserved_targets_fitted_or_scored": False})
    return predictions


def compare(ctx, baseline, baseline_plan, out, ids, held, y, predictions):
    audit = inspect_run(ctx, baseline)
    if not audit["source_archive"]["current_executable_code_matches_archive"]:
        raise ValueError("Baseline live code differs from archived code")
    write_json(out/"baseline-audit.json", {"observed_at_utc": utc_now(), "baseline": audit,
        "timing": "Baseline evidence audited after baseline fits; new semantic resources pinned before new source/endpoint fits"})
    # Only folds verified by the complete source/cache/count audit may be reused.
    verified = {(r["repeat"], r["fold"]): r for r in audit["datasets"]["abraham"]["folds"] if r["status"] == "verified"}
    groups = np.array([str(i).split("-")[0] for i in ids])
    reference = np.full((3, len(ids)), np.nan)
    evidence = []
    for repeat in range(3):
        for fold, (a, b) in enumerate(GroupKFold(5, shuffle=True, random_state=100+repeat).split(ids, groups=groups)):
            if (repeat, fold) not in verified:
                continue
            item = verified[(repeat, fold)]
            if item["feature_caches"]["quality"]["status"] != "verified":
                raise ValueError("Baseline quality cache missing; fold cannot be reused")
            path = baseline/f"abraham-repeat-{repeat}-fold-{fold}.npz"
            record = json.loads(path.with_suffix(".json").read_text())
            expected = {"train_ids": ids[a].tolist(), "held_ids": np.r_[held, ids[b]].tolist(),
                "evaluate_ids": ids[b].tolist(), "targets": y[b].tolist(), "code_sha256": baseline_plan["code_sha256"]}
            if (record["identity"] != expected or record["sha256"] != file_digest(path)
                    or record["sha256"] != item["sha256"]):
                raise ValueError("Baseline checkpoint changed after its exact source/cache/count audit")
            with np.load(path, allow_pickle=False) as data:
                reference[repeat, b] = data["current"]
            evidence.append({"path": str(path), "sha256": record["sha256"], "repeat": repeat, "fold": fold,
                "metadata_sha256": item["metadata_sha256"], "source_counts": item["source_counts"],
                "quality_cache_sha256": item["feature_caches"]["quality"]["sha256"]})
    values = {"current": reference, **predictions,
        **{"blend_"+name: (reference+p)/2 for name, p in predictions.items()}}
    whole = [repeat for repeat in range(3) if np.isfinite(reference[repeat]).all()]
    summary = {"observed_at_utc": utc_now(), "baseline_verified_folds": len(evidence), "required_baseline_folds": 15,
        "status": "comparison_complete" if len(whole) == 3 else "waiting_for_baseline",
        "complete_repeats": whole, "gate_evaluated": len(whole) == 3,
        "scores_for_complete_repeats": {str(repeat): {name: score(y, p[repeat]) for name, p in values.items()} for repeat in whole},
        "baseline_checkpoint_evidence": evidence, "main_validation_test_targets_scored": False,
        "reserved_targets_fitted_or_scored": False}
    if len(whole) == 3:
        scores = {name: [score(y, p) for p in matrix] for name, matrix in values.items()}
        passing = []
        for name, rows in scores.items():
            gain = np.array([a["pearson"]-b["pearson"] for a, b in zip(rows, scores["current"])])
            if (gain.mean() >= .01 and (gain > 0).sum() >= 2
                    and np.mean([r["mae"] for r in rows]) <= np.mean([r["mae"] for r in scores["current"]])):
                passing.append(name)
        selected = max(passing, key=lambda name: np.mean([r["pearson"] for r in scores[name]])) if passing else "current"
        atomic_npz(out/"abraham-inner-oof.npz", ids=ids, y=y, **values)
        summary.update({"scores": scores, "passing": passing, "selected": selected})
        write_json(out/"results.json", {"host": platform.node(), "results": {"abraham": summary},
            "main_validation_test_targets_scored": False, "reserved_targets_fitted_or_scored": False})
    elif len(evidence) < 15:
        # This is an observation, not an assumption that an unfinished run died.
        import subprocess
        probe = subprocess.run(["powershell", "-NoProfile", "-Command",
            "Get-Process -Id 22016 -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,CPU | ConvertTo-Json -Compress"],
            capture_output=True, text=True, timeout=15)
        summary["baseline_pid22016_observed_at_utc"] = utc_now()
        summary["baseline_pid22016_process_probe"] = probe.stdout.strip() or "PID not present at probe time"
    write_json(out/"comparison-status.json", summary)
    print(json.dumps({"status": summary["status"], "baseline_verified_folds": len(evidence),
        "complete_repeats": whole, "passing": summary.get("passing"), "selected": summary.get("selected"),
        "scores_for_complete_repeats": summary["scores_for_complete_repeats"]}, indent=2), flush=True)


def main(args):
    if platform.node().lower() != os.environ.get("CALNEW_COMPUTE_HOST", "").lower():
        raise ValueError("Run this modeling study on SSH host compute-host only")
    torch.set_num_threads(2)
    out, baseline = Path(args.out), Path(args.baseline)
    if (out/"results.json").exists() or out.exists() and not args.resume:
        raise ValueError("Choose a fresh run or explicitly resume the incomplete experiment")
    out.mkdir(parents=True, exist_ok=True)
    baseline_plan, hashes = common_sources(baseline)
    plan = {"host": platform.node(), "scope": "Original split42 Abraham training111 only",
        "outer_cv": "Connectivity GroupKFold5, repeat seeds100/101/102", "threads": 2,
        "source_boundary": "load_corpus reserved exclusions PLUS all186 eligible primary Abraham molecule connectivities",
        "source_vs_previous_protocol": "Stricter global primary-connectivity exclusion permits one fixed representation per source head for every endpoint fold; no inner source crossfit needed, no primary source self-exposure",
        "source_endpoint_labels": "No main primary odor-label or threshold-label fitting by new source models; augmented independent source descriptor associations only",
        "representations": {"idf_average": "Allowed-source IDF weighted L1 descriptor average projected to128",
            "idf_unit": "Same source-local IDF target projected to128 then unit Euclidean normalization"},
        "idf": "log((1+allowed source rows)/(1+allowed source document frequency))+1 after global primary exclusion",
        "source_model": {"kind": "ExtraTrees", "n_estimators": 100, "min_samples_leaf": 4,
            "max_features": .3, "random_state": 173, "threads": 2, "total_fits": 2,
            "source_features": ["rdkit", "fingerprint"], "target_width": 128},
        "endpoint_models": {"trees": {"kind": "ExtraTrees", "n_estimators": 500, "min_samples_leaf": 2,
            "max_features": .3, "random_state": 42, "threads": 2, "features": list(SEMANTIC_BASE)+["source128"]},
            "ridge100": {"kind": "standardized Ridge", "alpha": 100., "features": list(EXPLICIT_BLOCKS)+["source128"]}},
        "endpoint_preprocessing": "Outer-training-only median imputation; Ridge standardized on outer training only",
        "candidates": list(CANDIDATES), "blend": "Four standalone endpoints and their four fixed50percent CURRENT-v2 blends",
        "selection": "MeanPearson gain>=.01, positive>=2of3 repeats, NOmeanMAEincrease; highest passing meanPearson",
        "baseline": str(baseline), "baseline_selection_plan_sha256": file_digest(baseline/"selection-plan.json"),
        "baseline_gate": "Deferred until all15 exact source/cache/count/checksum/ID/target audited baseline folds exist",
        "code_sha256": hashes, "test_based_selection": False, "main_validation_test_targets_scored": False,
        "reserved_targets_fitted_or_scored": False, "target_or_family_tuning": False,
        "snapshot_bytes_parsed_then_reserved_rows_filtered": True}
    if args.resume and json.loads((out/"selection-plan.json").read_text()) != plan:
        raise ValueError("Semantic registration changed on resume")
    write_json(out/"selection-plan.json", plan)
    for relative, expected in hashes.items():
        dest = out/"source-code"/relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        if args.resume and dest.exists() and file_digest(dest) != expected:
            raise ValueError("Semantic source archive changed")
        shutil.copy2(relative, dest)
    ctx = read_only_context(Path(json.loads(Path("data/current.json").read_text())["snapshot"]))
    all_ids, ids, held, y, tr, task_source, base = cohort(ctx)
    molecules, transfer, words, word_manifest = load_source(ctx, out)
    targets, checks = source_checks(molecules, transfer, words, all_ids)
    identity = resource_identity(ctx, hashes, transfer, words, word_manifest, all_ids, ids, held, y,
        task_source, base, targets)
    resource_sha = digest(identity)
    if args.resume and json.loads((out/"resource-manifest.json").read_text())["identity"] != identity:
        raise ValueError("Semantic resources changed on resume")
    if not args.resume:
        write_json(out/"resource-manifest.json", {"recorded_at_utc": utc_now(),
            "timing": "BEFORE both source model fits and all endpoint fits", "identity": identity, "resource_sha256": resource_sha})
        for name, (keep, target, idf, audit) in targets.items():
            path = out/f"prefit-targets-{name}.npz"
            atomic_npz(path, source_ids=transfer.ids[keep], targets=target, idf=idf)
            write_json(path.with_suffix(".json"), {"recorded_at_utc": utc_now(), "timing": "BEFORE source/endpoint fits",
                "resource_sha256": resource_sha, "sha256": file_digest(path), "source_target_audit": audit})
        write_json(out/"normalization-checks.json", checks)
    else:
        for name, (keep, target, idf, audit) in targets.items():
            path = out/f"prefit-targets-{name}.npz"
            record = json.loads(path.with_suffix(".json").read_text())
            if record["resource_sha256"] != resource_sha or record["sha256"] != file_digest(path) or record["source_target_audit"] != audit:
                raise ValueError("Prefit target artifact identity/checksum changed")
            with np.load(path, allow_pickle=False) as data:
                if not (np.array_equal(data["source_ids"], transfer.ids[keep])
                        and np.array_equal(data["targets"], target) and np.array_equal(data["idf"], idf)):
                    raise ValueError("Saved prefit source IDs/targets/IDF differ from reconstructed data")
    print(f"Prefit registration complete: primary186 excluded, source={int(targets['idf_average'][0].sum())}, training111", flush=True)
    source = source_features(transfer, targets, all_ids, task_source, out, resource_sha, args.resume)
    predictions = endpoint_checkpoints(out, ids, held, y, tr, base, source, resource_sha, args.resume)
    compare(ctx, baseline, baseline_plan, out, ids, held, y, predictions)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="runs/nose-threshold-disjoint-semantic-inner-v1")
    parser.add_argument("--baseline", default="runs/nose-parity-threshold-water-inner-v2")
    parser.add_argument("--resume", action="store_true")
    with threadpool_limits(limits=2):
        main(parser.parse_args())
