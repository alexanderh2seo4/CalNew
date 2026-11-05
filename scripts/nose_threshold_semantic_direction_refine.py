"""Registered threshold direction/confidence refinement; SSH execution only.

Reuse two fully pinned, globally primary-disjoint source representations without
source refitting. Normalize each predicted vector independently and retain its
original length as one confidence coordinate before fixed endpoint heads.
"""
from __future__ import annotations

import os
import argparse
import json
from pathlib import Path
import platform
import shutil

import numpy as np
from sklearn.model_selection import GroupKFold
import torch
from threadpoolctl import threadpool_limits

from calnew.io import digest, file_digest, write_json
from calnew.pipeline.semantic import SEMANTIC_BASE
from calnew.pipeline.semantic_balanced import BalancedDescriptorTransfer
from nose_parity_progress import array_identity, dependency_versions, inspect_run, read_only_context, verify_source_archive
from nose_threshold_semantic_refine import (CANDIDATES, atomic_npz, cohort, common_sources,
    compare, endpoint_checkpoints, utc_now)


EPSILON = 1e-12


def direction_confidence(values):
    if values.ndim != 2 or values.shape[1] != 128 or not np.isfinite(values).all():
        raise ValueError("Invalid original source prediction array")
    values = values.astype(np.float64)
    original_norm = np.linalg.norm(values, axis=1)
    direction = values/np.maximum(original_norm[:, None], EPSILON)
    transformed = np.column_stack([direction, original_norm])
    nonzero = original_norm > EPSILON
    if (not np.isfinite(transformed).all() or not np.allclose(
            np.linalg.norm(direction[nonzero], axis=1), 1, rtol=0, atol=1e-12)
            or not np.array_equal(transformed[:, -1], original_norm)):
        raise ValueError("Direction/confidence normalization failed")
    return transformed


def normalization_checks(original, transformed, all_ids, ids, tr):
    if not np.array_equal(direction_confidence(original[tr]), transformed[tr]):
        raise ValueError("Normalization depends on other rows")
    if not np.array_equal(direction_confidence(np.zeros((2, 128))), np.zeros((2, 129))):
        raise ValueError("Fixed-epsilon zero vector handling failed")
    primary_changed = original.copy()
    keep = np.zeros(len(original), bool)
    keep[tr] = True
    primary_changed[~keep] = primary_changed[~keep]*7.+101.
    if not np.array_equal(direction_confidence(primary_changed)[tr], transformed[tr]):
        raise ValueError("Main-held feature rows influenced normalized original training rows")
    groups = np.array([str(i).split("-")[0] for i in ids])
    folds = []
    for repeat in range(3):
        for fold, (a, b) in enumerate(GroupKFold(5, shuffle=True, random_state=100+repeat).split(ids, groups=groups)):
            changed = original.copy()
            changed[tr[b]] = changed[tr[b]]*7.+101.
            if not np.array_equal(direction_confidence(changed)[tr[a]], transformed[tr[a]]):
                raise ValueError("Outer held features influenced training normalization")
            folds.append({"repeat": repeat, "fold": fold,
                "held_perturbation_changes_no_training_normalized_values": True})
    norms = transformed[:, -1]
    return {"epsilon": EPSILON, "per_row_normalization_has_no_fitted_parameters": True,
        "original_norm_retained_exactly": True, "nonzero_direction_unit_length_verified": True,
        "zero_vectors_finite_and_all_zero": True, "main_held_perturbation_training_values_identical": True,
        "eligible186_ids_sha256": digest(all_ids.tolist()), "fold_checks": folds,
        "original_norm_range": [float(norms.min()), float(norms.max())],
        "original_norm_mean": float(norms.mean()), "zero_or_below_epsilon_rows": int((norms <= EPSILON).sum())}


def load_pinned_source(source_run, ctx, all_ids, ids, held, y, task_source, base):
    plan_path, resource_path = source_run/"selection-plan.json", source_run/"resource-manifest.json"
    source_plan = json.loads(plan_path.read_text())
    archive = verify_source_archive(source_run, source_plan)
    if not archive["current_executable_code_matches_archive"]:
        raise ValueError("Pinned source run live code differs from its archive")
    manifest = json.loads(resource_path.read_text())
    identity = manifest["identity"]
    source_sha = manifest["resource_sha256"]
    if digest(identity) != source_sha or manifest["timing"] != "BEFORE both source model fits and all endpoint fits":
        raise ValueError("Original source resource identity or prefit timing differs")
    if (identity["all186_ids"] != all_ids.tolist() or identity["training111_ids"] != ids.tolist()
            or identity["main_held_ids"] != held.tolist() or identity["training111_targets"] != array_identity(y)
            or identity["task_universe_sha256"] != digest(ctx.universe)
            or identity["settings_sha256"] != digest(ctx.cfg)
            or identity["task_source_inputs"] != array_identity(task_source)
            or identity["endpoint_base_inputs"] != {name: array_identity(value) for name, value in base.items()}
            or identity["dependencies"] != dependency_versions()):
        raise ValueError("Original source cohort/features/targets/dependencies differ")
    for name, expected in identity["snapshot_sha256"].items():
        if file_digest(ctx.snapshot/name) != expected:
            raise ValueError("Original source snapshot differs")
    for relative, expected in identity["reserved_partition_sha256"].items():
        if file_digest(Path(relative)) != expected:
            raise ValueError("Reserved partition identity differs")
    for relative, item in identity["source_files"].items():
        path = Path(relative)
        if item["exists"] != path.exists() or item["exists"] and file_digest(path) != item["sha256"]:
            raise ValueError("Pinned source resource file differs")
    for name, expected in identity["task_blocks"].items():
        if array_identity(ctx.B[name]) != expected:
            raise ValueError("Original source Context feature array differs")
    forbidden = {str(i).split("-")[0] for i in all_ids}
    if {str(i).split("-")[0] for i in identity["filtered_source_ids"]} & forbidden:
        raise ValueError("Original source included primary threshold connectivity")
    fits = json.loads((source_run/"source-fits.json").read_text())
    if fits["total_registered_source_model_fits"] != 2 or fits["primary_source_connectivity_overlap"] != []:
        raise ValueError("Original globally disjoint source-fit evidence differs")
    values, evidence = {}, {}
    for name in BalancedDescriptorTransfer.REPRESENTATIONS:
        path = source_run/f"source-{name}.npz"
        record = json.loads(path.with_suffix(".json").read_text())
        audit = identity["source_targets"][name]["audit"]
        if (record != fits["representations"][name] or record["identity"] != {
                "resource_sha256": source_sha, "representation": name,
                "evaluate_ids": all_ids.tolist(), "source_target_audit": audit}
                or record["sha256"] != file_digest(path)
                or audit["excluded_connectivities"] != sorted(forbidden)
                or audit["held_connectivity_overlap"] != []
                or record["source_fits_in_this_cache"] != 1):
            raise ValueError("Pinned source feature manifest/exclusion identity differs")
        with np.load(path, allow_pickle=False) as data:
            if not np.array_equal(data["ids"], all_ids):
                raise ValueError("Pinned source feature order differs from eligible186 cohort")
            original = data["features"].copy()
        if original.shape != (186, 128) or array_identity(original) != record["feature_array"]:
            raise ValueError("Actual pinned source128 array differs")
        target_path = source_run/f"prefit-targets-{name}.npz"
        target_record = json.loads(target_path.with_suffix(".json").read_text())
        if (target_record["resource_sha256"] != source_sha or target_record["source_target_audit"] != audit
                or target_record["sha256"] != file_digest(target_path)):
            raise ValueError("Original prefit source target artifact differs")
        with np.load(target_path, allow_pickle=False) as data:
            if (data["source_ids"].tolist() != identity["filtered_source_ids"]
                    or array_identity(data["targets"]) != identity["source_targets"][name]["target"]
                    or array_identity(data["idf"]) != identity["source_targets"][name]["idf"]):
                raise ValueError("Actual original source IDs/targets/IDF arrays differ")
        values[name] = original
        evidence[name] = {"path": str(path), "sha256": record["sha256"],
            "metadata_sha256": file_digest(path.with_suffix(".json")), "actual_source128_array": array_identity(original),
            "prefit_targets_sha256": target_record["sha256"], "source_target_audit": audit,
            "source_fitted_at_utc": record["fitted_at_utc"]}
    return values, {"source_run": str(source_run), "selection_plan_sha256": file_digest(plan_path),
        "resource_manifest_sha256": file_digest(resource_path), "original_source_resource_sha256": source_sha,
        "original_prefit_resource_timestamp_utc": manifest["recorded_at_utc"],
        "common_and_original_source_code_archive_verified": True, "source_features": evidence,
        "new_source_model_fits": 0}


def main(args):
    if platform.node().lower() != os.environ.get("CALNEW_COMPUTE_HOST", "").lower():
        raise ValueError("Run this modeling study on SSH host compute-host only")
    torch.set_num_threads(2)
    out, source_run, baseline = Path(args.out), Path(args.source_run), Path(args.baseline)
    if (out/"results.json").exists() or out.exists() and not args.resume:
        raise ValueError("Choose a fresh output or explicitly resume the incomplete run")
    out.mkdir(parents=True, exist_ok=True)
    baseline_plan, hashes = common_sources(baseline)
    own = Path(__file__).resolve().relative_to(Path.cwd().resolve())
    hashes[own.as_posix()] = file_digest(own)
    plan = {"host": platform.node(), "scope": "Original split42 Abraham training111 only",
        "rationale": "Source regressors average unit-target vectors and can shrink predicted lengths; separate predicted direction from original norm confidence before fixed endpoint heads",
        "source_run": str(source_run), "source_fits_in_this_study": 0,
        "source_boundary": "Previously fitted source arrays exclude all186 eligible primary Abraham connectivities in addition to reserved exclusions",
        "source_feature_transform": {"direction": "prediction128/max(original Euclidean norm,epsilon)",
            "confidence": "Original prediction128 Euclidean norm, one appended coordinate",
            "epsilon": EPSILON, "output_width": 129, "fitted_parameters": 0},
        "outer_cv": "Connectivity GroupKFold5, repeat seeds100/101/102", "threads": 2,
        "candidates": {name: {"source_representation": representation, "head": head,
            "features": "SEMANTIC_BASE+unit128+original_norm" if head == "trees" else "explicit_chemistry+unit128+original_norm"}
            for name, (representation, head) in CANDIDATES.items()},
        "tree_model": {"n_estimators": 500, "min_samples_leaf": 2, "max_features": .3,
            "random_state": 42, "threads": 2}, "ridge_model": {"alpha": 100., "standardized": True},
        "endpoint_preprocessing": "Outer-training-only median imputation; Ridge standardized on outer training only",
        "blend": "Four standalone endpoints and their four fixed50percent CURRENT-v2 blends",
        "selection": "Unchanged meanPearson gain>=.01, positive>=2of3 repeats, NOmeanMAEincrease; highest passing meanPearson",
        "baseline": str(baseline), "baseline_selection_plan_sha256": file_digest(baseline/"selection-plan.json"),
        "baseline_audit": "All15 exact source/cache/count/checksum/ID/target folds required before fitting endpoints",
        "code_sha256": hashes, "test_based_selection": False, "target_or_family_tuning": False,
        "main_validation_test_targets_scored": False, "reserved_targets_fitted_or_scored": False,
        "snapshot_bytes_parsed_then_reserved_rows_filtered": True}
    if args.resume and json.loads((out/"selection-plan.json").read_text()) != plan:
        raise ValueError("Direction/confidence registration changed on resume")
    write_json(out/"selection-plan.json", plan)
    for relative, expected in hashes.items():
        dest = out/"source-code"/relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        if args.resume and dest.exists() and file_digest(dest) != expected:
            raise ValueError("Direction/confidence source archive differs")
        shutil.copy2(relative, dest)
    ctx = read_only_context(Path(json.loads(Path("data/current.json").read_text())["snapshot"]))
    all_ids, ids, held, y, tr, task_source, base = cohort(ctx)
    original, source_evidence = load_pinned_source(source_run, ctx, all_ids, ids, held, y, task_source, base)
    transformed = {name: direction_confidence(value) for name, value in original.items()}
    checks = {name: normalization_checks(original[name], value, all_ids, ids, tr)
        for name, value in transformed.items()}
    audit = inspect_run(ctx, baseline)
    folds = audit["datasets"]["abraham"]["folds"]
    if (audit["status"] != "complete" or not audit["source_archive"]["current_executable_code_matches_archive"]
            or len(folds) != 15 or any(f["status"] != "verified"
                or f["feature_caches"]["quality"]["status"] != "verified" for f in folds)):
        raise ValueError("All15 exact baseline folds and quality caches must verify before new endpoint fits")
    identity = {"code_sha256": hashes, "dependencies": dependency_versions(),
        "source_reuse_evidence": source_evidence, "original_training111_ids": ids.tolist(),
        "original_training111_targets": array_identity(y), "all186_ids": all_ids.tolist(),
        "endpoint_base_inputs": {name: array_identity(value) for name, value in base.items()},
        "context_blocks": {name: array_identity(ctx.B[name]) for name in SEMANTIC_BASE},
        "transformed_source129": {name: array_identity(value) for name, value in transformed.items()},
        "normalization_checks": checks, "baseline_audit": audit}
    resource_sha = digest(identity)
    if args.resume and json.loads((out/"resource-manifest.json").read_text())["identity"] != identity:
        raise ValueError("Direction/confidence pinned resources differ on resume")
    if not args.resume:
        write_json(out/"resource-manifest.json", {"recorded_at_utc": utc_now(),
            "timing": "BEFORE new endpoint fits; original source prefit provenance explicitly referenced",
            "identity": identity, "resource_sha256": resource_sha})
        write_json(out/"normalization-checks.json", checks)
        for name, value in transformed.items():
            path = out/f"prefit-direction-confidence-{name}.npz"
            atomic_npz(path, ids=all_ids, features=value)
            write_json(path.with_suffix(".json"), {"resource_sha256": resource_sha,
                "sha256": file_digest(path), "array": array_identity(value), "source_model_refits": 0})
    else:
        for name, value in transformed.items():
            path = out/f"prefit-direction-confidence-{name}.npz"
            record = json.loads(path.with_suffix(".json").read_text())
            if record["resource_sha256"] != resource_sha or record["sha256"] != file_digest(path):
                raise ValueError("Saved deterministic transformation artifact differs")
            with np.load(path, allow_pickle=False) as data:
                if not (np.array_equal(data["ids"], all_ids) and np.array_equal(data["features"], value)):
                    raise ValueError("Saved direction/confidence values differ")
    print("Prefit direction/confidence registration complete: two source arrays reused, zero source fits, baseline15 verified", flush=True)
    predictions = endpoint_checkpoints(out, ids, held, y, tr, base, transformed, resource_sha, args.resume)
    compare(ctx, baseline, baseline_plan, out, ids, held, y, predictions)
    # The reused comparator describes the original source-fit study; keep this
    # new run's provenance timing explicit without altering any previous run.
    path = out/"baseline-audit.json"
    report = json.loads(path.read_text())
    report["timing"] = "Baseline audited after baseline fits; direction/confidence resources pinned before new endpoint fits; source arrays reused with original prefit provenance"
    report["source_model_refits_in_this_study"] = 0
    write_json(path, report)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="runs/nose-threshold-disjoint-semantic-direction-inner-v1")
    parser.add_argument("--source-run", default="runs/nose-threshold-disjoint-semantic-inner-v1")
    parser.add_argument("--baseline", default="runs/nose-parity-threshold-water-inner-v2")
    parser.add_argument("--resume", action="store_true")
    with threadpool_limits(limits=2):
        main(parser.parse_args())
