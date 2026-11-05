"""Audit saved training-only parity checkpoints on SSH, without model fitting.

The supplemental resource identities are observed AFTER some fits. They must not
be described as pre-fit provenance, and this script never rewrites run evidence.
"""
from __future__ import annotations

import os
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path
import sys

import numpy as np
from scipy.stats import pearsonr
from sklearn.model_selection import GroupKFold
import torch
from threadpoolctl import threadpool_limits

from calnew.io import digest, file_digest, write_json
from calnew.pipeline import blocks as block_module
from calnew.pipeline.auxiliary import LI_2025, LI_2025_SHA256, exclude_touching
from calnew.pipeline.paper_benchmark import Context, FRACTIONS, random_split
from nose_intensity_experiment import CACHE, cache_identity
from nose_semantic_experiment import RESERVED, SHA256, SOURCE


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def array_identity(values):
    array = np.ascontiguousarray(values)
    header = {"dtype": str(array.dtype), "shape": list(array.shape)}
    h = hashlib.sha256(json.dumps(header, sort_keys=True).encode())
    h.update(array.tobytes(order="C"))
    return {**header, "sha256_header_and_c_order_bytes": h.hexdigest()}


def file_identity(path, expected=None):
    path = Path(path)
    if not path.exists():
        return {"path": str(path), "exists": False}
    value = {"path": str(path), "exists": True, "bytes": path.stat().st_size,
        "sha256": file_digest(path)}
    if expected is not None:
        value["matches_pinned_sha256"] = value["sha256"] == expected
    return value


def dependency_versions():
    result = {"python": sys.version, "platform": platform.platform()}
    for name in ("numpy", "pandas", "scipy", "scikit-learn", "xgboost", "torch", "rdkit", "threadpoolctl"):
        try:
            result[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            result[name] = "distribution metadata unavailable"
    return result


def read_only_context(snapshot):
    # Context normally can compute a missing feature cache. This audit prohibits
    # that path, including accidental frozen-model inference or cache mutation.
    if not Path("data/features/pipeline-blocks").is_dir():
        raise ValueError("Existing structure feature cache directory is missing")
    original = block_module.compute_block

    def refuse_missing_cache(block, smiles):
        raise ValueError(f"Missing cached {block} features; audit will not generate them")

    block_module.compute_block = refuse_missing_cache
    try:
        return Context(snapshot, RESERVED)
    finally:
        block_module.compute_block = original


def resource_identity(ctx):
    source_files = {
        "water_source_csv": file_identity(LI_2025/"threshold_data_med.csv", LI_2025_SHA256),
        "descriptor_source_csv": file_identity(SOURCE, SHA256),
        "descriptor_word_vectors": file_identity("data/features/nose-descriptor-minilm.npz"),
        "descriptor_word_manifest": file_identity("data/features/nose-descriptor-minilm.json"),
    }
    word_manifest = Path("data/features/nose-descriptor-minilm.json")
    if word_manifest.exists() and source_files["descriptor_word_vectors"]["exists"]:
        manifest = json.loads(word_manifest.read_text())
        source_files["descriptor_word_vectors"]["matches_manifest_sha256"] = (
            source_files["descriptor_word_vectors"]["sha256"] == manifest.get("sha256"))
        source_files["descriptor_word_vectors"]["manifest_corpus_matches_source"] = (
            manifest.get("corpus_sha256") == source_files["descriptor_source_csv"].get("sha256"))
    reserved = {}
    for folder in RESERVED:
        reserved[str(folder)] = {str(path.relative_to(folder)): file_identity(path)
            for path in sorted(folder.glob("*.json"))}
    return {"observed_at_utc": utc_now(), "provenance_timing": "SUPPLEMENTAL AUDIT AFTER SOME FITS; not pre-fit provenance",
        "snapshot": str(ctx.snapshot), "snapshot_parquets": {
            name: file_identity(ctx.snapshot/name) for name in ("molecules.parquet", "observations.parquet", "stimuli.parquet")},
        "source_files": source_files, "dependency_versions": dependency_versions(),
        "reserved_manifest_files": reserved,
        "universe_ids_sha256": digest(ctx.universe), "settings_sha256": digest(ctx.cfg),
        "context_arrays": {name: array_identity(values) for name, values in sorted(ctx.B.items())},
        "context_water_arrays": {name: array_identity(values) for name, values in sorted(ctx.aux_blocks.items())},
        "context_training_arrays": {"quality_labels": array_identity(ctx.labels),
            "panel_direction": array_identity(ctx.direction), "panel_profile": array_identity(ctx.prof)},
        "water_source_ids_sha256": digest(ctx.aux.molecule_id.tolist()),
        "water_source_targets": array_identity(ctx.aux.y.to_numpy()),
        "water_source_rows": len(ctx.aux)}


def verify_source_archive(run, plan):
    entries, errors = [], []
    for relative, expected in plan["code_sha256"].items():
        normalized = Path(relative.replace("\\", "/"))
        saved = run/"source-code"/normalized
        archived = file_identity(saved, expected)
        if not archived.get("exists") or not archived.get("matches_pinned_sha256"):
            errors.append(f"Archived source differs or is missing: {relative}")
        current = file_identity(normalized, expected)
        entries.append({"relative_path": str(normalized), "archive": archived, "current": current,
            "appledouble_metadata": normalized.name.startswith("._")})
    if errors:
        raise ValueError("; ".join(errors))
    return {"archive_verified": True, "files": entries,
        "current_executable_code_matches_archive": all(
            item["current"].get("matches_pinned_sha256", False) for item in entries if not item["appledouble_metadata"]),
        "note": "AppleDouble entries are archive metadata, not executable Python dependencies"}


def cache_audit(ctx, identity, repeat, fold, dataset, source_counts):
    report = {}
    for kind, seed in (("quality", 42), ("semantic", 300+repeat*5+fold)):
        if kind == "semantic" and dataset != "keller":
            continue
        expected = cache_identity(ctx, identity["train_ids"], identity["held_ids"], seed, kind)
        path = CACHE/(digest(expected)+".npz")
        manifest_path = path.with_suffix(".json")
        item = {"path": str(path), "manifest": str(manifest_path), "status": "missing"}
        if path.exists() and manifest_path.exists():
            manifest = json.loads(manifest_path.read_text())
            expected_json = json.loads(json.dumps(expected))
            if manifest.get("identity") != expected_json or manifest.get("sha256") != file_digest(path):
                raise ValueError(f"Pinned feature cache identity or checksum mismatch: {path}")
            with np.load(path, allow_pickle=False) as data:
                names = ("quality", "direction") if kind == "quality" else ("semantic",)
                shapes = {}
                for name in names:
                    values = data[name]
                    shape = ctx.labels.shape if name == "quality" else ctx.direction.shape if name == "direction" else (len(ctx.universe), 128)
                    if values.shape != shape or not np.isfinite(values).all():
                        raise ValueError(f"Invalid cached feature shape/finiteness: {path}:{name}")
                    shapes[name] = list(values.shape)
            source_verified = expected["snapshot_sha256"] == {name: file_digest(ctx.snapshot/name)
                for name in ("molecules.parquet", "observations.parquet", "stimuli.parquet")}
            if Path(SOURCE).exists():
                source_verified = source_verified and expected["descriptor_source_sha256"] == file_digest(SOURCE)
            if not source_verified:
                raise ValueError(f"Feature cache pinned source data no longer match current files: {path}")
            item.update({"status": "verified", "sha256": manifest["sha256"], "shape": shapes,
                "training_and_held_ids_exact": True, "code_data_source_identity_exact": source_verified,
                "manifest_sha256": file_digest(manifest_path), "cache_identity_sha256": digest(expected)})
            if kind == "semantic":
                if manifest.get("source_rows") != source_counts.get("descriptor_source_count"):
                    raise ValueError("Fold descriptor source count differs from semantic cache manifest")
                item["source_rows"] = manifest["source_rows"]
        report[kind] = item
    return report


def water_counts(ctx, train_ids, held_ids, seed):
    train_ids = np.asarray(train_ids)
    groups = np.array([str(i).split("-")[0] for i in train_ids])
    counts = []
    for _, b in GroupKFold(3, shuffle=True, random_state=seed).split(train_ids, groups=groups):
        counts.append(int(exclude_touching(ctx.aux, np.r_[held_ids, train_ids[b]]).sum()))
    counts.append(int(exclude_touching(ctx.aux, held_ids).sum()))
    return counts


def score(y, p):
    return {"pearson": float(pearsonr(y, p).statistic), "mae": float(np.abs(y-p).mean()),
        "rmse": float(np.sqrt(np.square(y-p).mean()))}


def inspect_run(ctx, run):
    run = Path(run)
    if not (run/"selection-plan.json").exists():
        return {"path": str(run), "status": "absent"}
    plan = json.loads((run/"selection-plan.json").read_text())
    if plan.get("original_split_seed") != 42 or plan.get("fold_seeds") != [100, 101, 102]:
        raise ValueError("Unrecognized split/repeat plan")
    if plan.get("test_based_selection") is not False or plan.get("reserved_targets_fitted_or_scored") is not False:
        raise ValueError("Run plan does not establish training-only scoring scope")
    result = {"path": str(run), "selection_plan_sha256": file_digest(run/"selection-plan.json"),
        "source_archive": verify_source_archive(run, plan), "datasets": {}}
    for dataset in plan["datasets"]:
        if dataset not in ("abraham", "keller"):
            raise ValueError("Unexpected task in training-only progress audit")
        frame = ctx.thr if dataset == "abraham" else ctx.keller
        tr, va, te = random_split(len(frame), FRACTIONS[dataset], 42)
        all_ids = frame.molecule_id.to_numpy()
        ids, main_held = all_ids[tr], all_ids[np.r_[va, te]]
        y = frame["y" if dataset == "abraham" else "pleasantness"].to_numpy()[tr]
        groups = np.array([str(i).split("-")[0] for i in ids])
        if len(set(ids)) != len(ids) or not np.isfinite(y).all():
            raise ValueError("Training-only cohort has duplicate IDs or non-finite targets")
        task = {"training_rows": len(ids), "training_ids_sha256": digest(ids.tolist()),
            "training_targets": array_identity(y), "main_held_ids_sha256": digest(main_held.tolist()),
            "primary_train_main_held_connectivity_overlaps": sorted(set(groups) & {str(i).split("-")[0] for i in main_held}),
            "repeats": [], "folds": []}
        for repeat in range(3):
            coverage = np.zeros(len(ids), dtype=int)
            predictions, completed = {}, 0
            for fold, (a, b) in enumerate(GroupKFold(5, shuffle=True, random_state=100+repeat).split(ids, groups=groups)):
                path = run/f"{dataset}-repeat-{repeat}-fold-{fold}.npz"
                meta_path = path.with_suffix(".json")
                expected = {"train_ids": ids[a].tolist(), "held_ids": np.r_[main_held, ids[b]].tolist(),
                    "evaluate_ids": ids[b].tolist(), "targets": y[b].tolist(), "code_sha256": plan["code_sha256"]}
                item = {"repeat": repeat, "fold": fold, "path": str(path), "status": "incomplete"}
                if path.exists() and meta_path.exists():
                    meta = json.loads(meta_path.read_text())
                    if meta["identity"] != expected or meta["sha256"] != file_digest(path):
                        raise ValueError(f"Checkpoint identity/checksum mismatch: {path}")
                    if not meta.get("grouped_outer_fold_verified") or set(groups[a]) & set(groups[b]):
                        raise ValueError("Checkpoint does not verify disjoint outer connectivity groups")
                    if set(expected["evaluate_ids"]) & set(main_held):
                        raise ValueError("Main held ID appears in scored checkpoint")
                    with np.load(path, allow_pickle=False) as data:
                        names = set(data.files)
                        if "current" not in names or predictions and names != set(predictions):
                            raise ValueError("Checkpoint candidate names are incomplete or inconsistent")
                        for name in data.files:
                            values = data[name]
                            if values.shape != (len(b),) or not np.isfinite(values).all():
                                raise ValueError("Saved predictions are misaligned or non-finite")
                            predictions.setdefault(name, np.full(len(ids), np.nan))[b] = values
                    counts = meta["source_counts"]
                    if dataset == "abraham" and counts.get("water_source_counts") != water_counts(
                            ctx, expected["train_ids"], expected["held_ids"], 300+repeat*5+fold):
                        raise ValueError("Fold water source counts fail held-connectivity exclusion reconstruction")
                    coverage[b] += 1
                    completed += 1
                    item.update({"status": "verified", "sha256": meta["sha256"], "metadata_sha256": file_digest(meta_path),
                        "evaluate_rows": len(b), "source_counts": counts,
                        "feature_caches": cache_audit(ctx, expected, repeat, fold, dataset, counts)})
                task["folds"].append(item)
            row = {"repeat": repeat, "fold_seed": 100+repeat, "completed_folds": completed,
                "status": "complete" if completed == 5 else "incomplete"}
            if completed == 5:
                if not np.all(coverage == 1):
                    raise ValueError("Completed repeat does not cover each original training ID exactly once")
                row["training_only_scores"] = {name: score(y, values) for name, values in predictions.items()}
                row["unique_original_training_coverage_verified"] = True
            task["repeats"].append(row)
        task["status"] = "complete" if all(row["status"] == "complete" for row in task["repeats"]) else "incomplete"
        if task["status"] == "complete" and (run/"results.json").exists():
            saved = json.loads((run/"results.json").read_text())["results"][dataset]
            if saved["training_molecules"] != len(ids):
                raise ValueError("Saved final result training count differs from reconstructed cohort")
            names = set(task["repeats"][0]["training_only_scores"])
            if set(saved["scores"]) != names:
                raise ValueError("Saved final result candidate names differ from checkpoints")
            passing = []
            for name in sorted(names):
                scores = [row["training_only_scores"][name] for row in task["repeats"]]
                for reconstructed, original in zip(scores, saved["scores"][name]):
                    if any(not np.isclose(reconstructed[key], original[key], rtol=0, atol=1e-12)
                            for key in reconstructed):
                        raise ValueError("Saved final metrics differ from checkpoint reconstruction")
                current = [row["training_only_scores"]["current"] for row in task["repeats"]]
                gain = np.array([a["pearson"]-b["pearson"] for a, b in zip(scores, current)])
                if gain.mean() >= .01 and (gain > 0).sum() >= 2 and np.mean([s["mae"] for s in scores]) <= np.mean([s["mae"] for s in current]):
                    passing.append(name)
            selected = max(passing, key=lambda name: np.mean([
                row["training_only_scores"][name]["pearson"] for row in task["repeats"]])) if passing else "current"
            if sorted(saved["passing"]) != passing or saved["selected"] != selected:
                raise ValueError("Saved promotion decision differs from reconstructed frozen gate")
            task["saved_final_results_verified"] = {"sha256": file_digest(run/"results.json"),
                "scores_and_promotion_exact": True, "passing": passing, "selected": selected}
        result["datasets"][dataset] = task
    result["status"] = "complete" if all(task["status"] == "complete" for task in result["datasets"].values()) else "incomplete"
    return result


def main(args):
    host = platform.node()
    if host.lower() != os.environ.get("CALNEW_COMPUTE_HOST", "").lower():
        raise ValueError("Run this numerical audit on SSH host compute-host only")
    torch.set_num_threads(2)
    report = {"host": host, "started_at_utc": utc_now(), "threads": 2,
        "audit_scope": "Saved original-training fold checkpoints only; no fits, main development held scores, or reserved scores",
        "resource_provenance_timing": "SUPPLEMENTAL AUDIT AFTER SOME FITS; not pre-fit provenance",
        "audit_script": file_identity(Path(__file__)), "runs": {}}
    snapshot = Path(json.loads(Path("data/current.json").read_text())["snapshot"])
    ctx = read_only_context(snapshot)
    report["supplemental_current_resource_identity"] = resource_identity(ctx)
    for run in args.runs:
        try:
            report["runs"][run] = inspect_run(ctx, run)
        except (ValueError, KeyError, OSError, json.JSONDecodeError) as exc:
            report["runs"][run] = {"path": run, "status": "audit_failed", "error": str(exc)}
    report["completed_at_utc"] = utc_now()
    write_json(Path(args.out), report)
    compact = {"host": host, "at_utc": report["completed_at_utc"], "report": args.out, "runs": {}}
    for run, item in report["runs"].items():
        compact["runs"][run] = {"status": item["status"], "error": item.get("error"),
            "datasets": {name: {"status": task["status"], "repeats": task["repeats"],
                "source_counts": [fold.get("source_counts") for fold in task["folds"] if fold["status"] == "verified"]}
                for name, task in item.get("datasets", {}).items()}}
    print(json.dumps(compact, indent=2), flush=True)
    return int(any(item["status"] == "audit_failed" for item in report["runs"].values()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", nargs="+", default=["runs/nose-parity-threshold-water-inner-v2",
        "runs/nose-parity-pleasantness-grouped-inner-v2"])
    parser.add_argument("--out", default="runs/nose-parity-progress-20261002.json")
    with threadpool_limits(limits=2):
        sys.exit(main(parser.parse_args()))
