"""Frozen paired threshold direction/confidence benchmark on SSH only.

The recipe is chosen solely by the completed original111 grouped training check.
Benchmark the identical fixed blend against a fresh current-v2 comparator on
ten unchanged primary splits, and separately on validation-refit partitions.
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
from scipy.stats import pearsonr
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.metrics import r2_score
from sklearn.model_selection import GroupKFold
import torch
from threadpoolctl import threadpool_limits

from calnew.io import digest, file_digest, write_json
from calnew.pipeline.auxiliary import exclude_touching
from calnew.pipeline.paper_benchmark import FRACTIONS, benchmark_split
from calnew.pipeline.semantic import SEMANTIC_BASE
from calnew.pipeline.semantic_balanced import array_sha256
from nose_intensity_experiment import CACHE, cache_identity
from nose_parity_progress import array_identity, dependency_versions, inspect_run, read_only_context, verify_source_archive
from nose_parity_refine import current_threshold
from nose_threshold_semantic_refine import CANDIDATES, atomic_npz, cohort, endpoint_transform, score, utc_now
from nose_threshold_semantic_direction_refine import direction_confidence, load_pinned_source


SELECTED = "blend_idf_unit_trees"
SELECTION = Path("runs/nose-threshold-disjoint-semantic-direction-inner-v1")
SOURCE_RUN = Path("runs/nose-threshold-disjoint-semantic-inner-v1")
BASELINE = Path("runs/nose-parity-threshold-water-inner-v2")
OUTPUTS = {"original": Path("runs/nose-threshold-direction-original-v1"),
    "validation_refit": Path("runs/nose-threshold-direction-refit-v1")}


def metrics(y, p):
    if y.shape != p.shape or not np.isfinite(y).all() or not np.isfinite(p).all():
        raise ValueError("Invalid paired benchmark targets/predictions")
    return {"pearson": float(pearsonr(y, p).statistic), "mae": float(np.abs(y-p).mean()),
        "r2": float(r2_score(y, p)), "mse": float(np.square(y-p).mean())}


def verify_selection(ctx, all_ids, ids, held, y, tr, base, original, source_evidence):
    plan = json.loads((SELECTION/"selection-plan.json").read_text())
    archive = verify_source_archive(SELECTION, plan)
    if (not archive["current_executable_code_matches_archive"] or plan["test_based_selection"]
            or plan["reserved_targets_fitted_or_scored"] or plan["source_fits_in_this_study"] != 0
            or plan["tree_model"] != {"n_estimators": 500, "min_samples_leaf": 2,
                "max_features": .3, "random_state": 42, "threads": 2}
            or plan["source_feature_transform"]["epsilon"] != 1e-12):
        raise ValueError("Frozen direction/confidence selection recipe differs")
    resource = json.loads((SELECTION/"resource-manifest.json").read_text())
    identity, resource_sha = resource["identity"], resource["resource_sha256"]
    if (digest(identity) != resource_sha or identity["source_reuse_evidence"] != source_evidence
            or identity["original_training111_ids"] != ids.tolist()
            or identity["original_training111_targets"] != array_identity(y)
            or identity["all186_ids"] != all_ids.tolist()
            or identity["dependencies"] != dependency_versions()):
        raise ValueError("Parent selection resource identity differs")
    transformed = {name: direction_confidence(values) for name, values in original.items()}
    for name, values in transformed.items():
        path = SELECTION/f"prefit-direction-confidence-{name}.npz"
        record = json.loads(path.with_suffix(".json").read_text())
        if (record["resource_sha256"] != resource_sha or record["sha256"] != file_digest(path)
                or record["array"] != array_identity(values)
                or identity["transformed_source129"][name] != array_identity(values)):
            raise ValueError("Parent direction/confidence actual feature identity differs")
        with np.load(path, allow_pickle=False) as data:
            if not np.array_equal(data["ids"], all_ids) or not np.array_equal(data["features"], values):
                raise ValueError("Parent transformed source IDs/values differ")
    baseline_plan = json.loads((BASELINE/"selection-plan.json").read_text())
    audit = inspect_run(ctx, BASELINE)
    verified = audit["datasets"]["abraham"]["folds"]
    if (audit["status"] != "complete" or not audit["source_archive"]["current_executable_code_matches_archive"]
            or len(verified) != 15 or any(f["status"] != "verified"
                or f["feature_caches"]["quality"]["status"] != "verified" for f in verified)):
        raise ValueError("Original15 baseline fold/source/cache/count audit failed")
    features = {name: np.column_stack([base[head][tr], transformed[representation][tr]])
        for name, (representation, head) in CANDIDATES.items()}
    predictions = {name: np.full((3, len(ids)), np.nan) for name in ("current", *CANDIDATES)}
    groups = np.array([str(i).split("-")[0] for i in ids])
    checkpoints = []
    for repeat in range(3):
        coverage = np.zeros(len(ids), int)
        for fold, (a, b) in enumerate(GroupKFold(5, shuffle=True, random_state=100+repeat).split(ids, groups=groups)):
            if set(groups[a]) & set(groups[b]):
                raise ValueError("Parent training-only grouped folds overlap")
            path = SELECTION/f"abraham-repeat-{repeat}-fold-{fold}.npz"
            record = json.loads(path.with_suffix(".json").read_text())
            expected = {"resource_sha256": resource_sha, "train_ids": ids[a].tolist(),
                "held_ids": np.r_[held, ids[b]].tolist(), "evaluate_ids": ids[b].tolist(),
                "train_targets": y[a].tolist(), "targets": y[b].tolist(),
                "features_sha256": {name: array_sha256(x) for name, x in features.items()}}
            if record["identity"] != expected or record["sha256"] != file_digest(path):
                raise ValueError("Parent selection fold IDs/targets/actual features/checksum differ")
            with np.load(path, allow_pickle=False) as data:
                if set(data.files) != set(CANDIDATES):
                    raise ValueError("Parent candidate set differs")
                for name in CANDIDATES:
                    predictions[name][repeat, b] = data[name]
            baseline_path = BASELINE/path.name
            baseline_record = json.loads(baseline_path.with_suffix(".json").read_text())
            expected_baseline = {"train_ids": ids[a].tolist(), "held_ids": np.r_[held, ids[b]].tolist(),
                "evaluate_ids": ids[b].tolist(), "targets": y[b].tolist(), "code_sha256": baseline_plan["code_sha256"]}
            if baseline_record["identity"] != expected_baseline or baseline_record["sha256"] != file_digest(baseline_path):
                raise ValueError("Original baseline changed after its exact audit")
            with np.load(baseline_path, allow_pickle=False) as data:
                predictions["current"][repeat, b] = data["current"]
            coverage[b] += 1
            checkpoints.append({"repeat": repeat, "fold": fold, "selection_path": str(path),
                "selection_sha256": record["sha256"], "baseline_path": str(baseline_path),
                "baseline_sha256": baseline_record["sha256"]})
        if not np.all(coverage == 1):
            raise ValueError("Parent original training111 unique coverage differs")
    predictions.update({"blend_"+name: (predictions["current"]+predictions[name])/2 for name in CANDIDATES})
    saved = json.loads((SELECTION/"results.json").read_text())["results"]["abraham"]
    scores = {name: [score(y, p) for p in values] for name, values in predictions.items()}
    if set(scores) != set(saved["scores"]):
        raise ValueError("Saved parent score candidates differ")
    passing = []
    for name, rows in scores.items():
        for actual, expected in zip(rows, saved["scores"][name]):
            if any(not np.isclose(actual[k], expected[k], rtol=0, atol=1e-12) for k in actual):
                raise ValueError("Saved parent scores differ from raw checkpoint reconstruction")
        gains = np.array([a["pearson"]-b["pearson"] for a, b in zip(rows, scores["current"])])
        if (gains.mean() >= .01 and (gains > 0).sum() >= 2
                and np.mean([s["mae"] for s in rows]) <= np.mean([s["mae"] for s in scores["current"]])):
            passing.append(name)
    selected = max(passing, key=lambda n: np.mean([s["pearson"] for s in scores[n]])) if passing else "current"
    if sorted(passing) != sorted(saved["passing"]) or saved["selected"] != selected or selected != SELECTED:
        raise ValueError("Frozen parent .01 gate/selected recipe does not reconstruct")
    oof_path = SELECTION/"abraham-inner-oof.npz"
    with np.load(oof_path, allow_pickle=False) as data:
        if not np.array_equal(data["ids"], ids) or not np.array_equal(data["y"], y):
            raise ValueError("Parent OOF original IDs/targets differ")
        if any(not np.array_equal(data[name], values) for name, values in predictions.items()):
            raise ValueError("Parent OOF arrays differ from raw fold reconstruction")
    return transformed["idf_unit"], {"selected": SELECTED, "gate": {
        "mean_pearson_gain_minimum": .01, "positive_repeats_minimum": 2, "no_mean_mae_increase": True},
        "selected_scores": scores[SELECTED], "baseline_scores": scores["current"],
        "passing": passing, "source_reuse_evidence": source_evidence, "baseline_audit": audit,
        "selection_code_archive_verified": True, "selection_results_sha256": file_digest(SELECTION/"results.json"),
        "selection_plan_sha256": file_digest(SELECTION/"selection-plan.json"),
        "selection_resource_manifest_sha256": file_digest(SELECTION/"resource-manifest.json"),
        "selection_oof_sha256": file_digest(oof_path), "selection_fold_checkpoints": checkpoints,
        "no_source_refits_in_benchmark": True, "development_test_score_used_for_selection": False}


def stage_a_source_audit(ctx, train_ids, held_ids):
    forbidden = {str(i).split("-")[0] for i in held_ids}
    train_rows = ctx.rows(train_ids)
    fold = np.random.default_rng(42).permutation(len(train_rows)) % 5
    records = []
    for j in range(-1, 5):
        excluded = forbidden if j < 0 else forbidden | set(ctx.connectivity[train_rows[fold == j]])
        keep = ctx.a_rows[~np.isin(ctx.connectivity[ctx.a_rows], sorted(excluded))]
        if set(ctx.connectivity[keep]) & excluded:
            raise ValueError("Held connectivity entered Stage-A source rows")
        records.append({"fold": j, "source_rows": len(keep),
            "source_ids_sha256": digest([ctx.universe[r] for r in keep]),
            "excluded_connectivities": sorted(excluded), "held_connectivity_overlap": []})
    return records


def stage_a_features(ctx, train_ids, held_ids, out, resume):
    identity = cache_identity(ctx, train_ids, held_ids, 42, "quality")
    exact = CACHE/(digest(identity)+".npz")
    exact_meta = exact.with_suffix(".json")
    own = out/"stage-A-fixed-refits"/(digest(identity)+".npz")
    path = exact if exact.exists() and exact_meta.exists() else own
    metadata = path.with_suffix(".json")
    if path.exists() != metadata.exists():
        raise ValueError("Orphan Stage-A artifact preserved; do not overwrite partial evidence")
    if path.exists():
        record = json.loads(metadata.read_text())
        if record["identity"] != json.loads(json.dumps(identity)) or record["sha256"] != file_digest(path):
            raise ValueError("Same-producer Stage-A cache identity/checksum differs")
        with np.load(path, allow_pickle=False) as data:
            q, d = data["quality"].copy(), data["direction"].copy()
    else:
        print(f"Stage-A fixed seed42 refit: training={len(train_ids)}, held={len(held_ids)}; unknown old producers remain untouched", flush=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        write_json(path.with_suffix(".prefit.json"), {"recorded_at_utc": utc_now(),
            "identity": identity, "source_exclusion_audit": stage_a_source_audit(ctx, train_ids, held_ids),
            "timing": "BEFORE fixed Stage-A fit", "reserved_targets_fitted_or_scored": False})
        q, d, _ = ctx.stage_a_features(train_ids, held_ids, 42)
        atomic_npz(path, quality=q, direction=d)
        record = {"identity": identity, "sha256": file_digest(path), "fixed_Stage_A_refit": True,
            "fitted_at_utc": utc_now(), "reason": "No exact same-producer cache available; unknown caches not reused"}
        write_json(metadata, record)
    if q.shape != ctx.labels.shape or d.shape != ctx.direction.shape or not np.isfinite(q).all() or not np.isfinite(d).all():
        raise ValueError("Invalid paired Stage-A feature shape/finiteness")
    return {**ctx.B, "quality": q, "direction": d}, {"path": str(path), "sha256": record["sha256"],
        "metadata_sha256": file_digest(metadata), "identity": identity,
        "fixed_Stage_A_refit": record.get("fixed_Stage_A_refit", False),
        "quality": array_identity(q), "direction": array_identity(d),
        "source_exclusion_audit": stage_a_source_audit(ctx, train_ids, held_ids)}


def benchmark_resources(ctx, hashes, all_ids, all_y, features, source_evidence, selection):
    return {"snapshot": str(ctx.snapshot), "snapshot_sha256": {name: file_digest(ctx.snapshot/name)
            for name in ("molecules.parquet", "observations.parquet", "stimuli.parquet")},
        "all186_ids": all_ids.tolist(), "all186_threshold_targets": array_identity(all_y),
        "all186_selected_branch_features": array_identity(features),
        "context_blocks": {name: array_identity(value) for name, value in ctx.B.items()},
        "auxiliary_blocks": {name: array_identity(value) for name, value in ctx.aux_blocks.items()},
        "auxiliary_ids": ctx.aux.molecule_id.tolist(), "auxiliary_targets": array_identity(ctx.aux.y.to_numpy()),
        "stage_A_labels": array_identity(ctx.labels), "stage_A_direction_targets": array_identity(ctx.direction),
        "settings_sha256": digest(ctx.cfg), "dependencies": dependency_versions(), "code_sha256": hashes,
        "source_reuse_evidence": source_evidence, "frozen_selection_sha256": digest(selection)}


def split_resource(ctx, all_ids, all_y, features, split, refit, resource_sha):
    tr, va, te = benchmark_split(len(all_ids), FRACTIONS["abraham"], split, refit)
    train_ids, held_ids = all_ids[tr], all_ids[np.r_[va, te]]
    expected_sizes = (148, 0, 38) if refit else (111, 37, 38)
    if (len(tr), len(va), len(te)) != expected_sizes:
        raise ValueError("Original split sizes changed")
    keep = exclude_touching(ctx.aux, held_ids)
    forbidden = {str(i).split("-")[0] for i in held_ids}
    if set(ctx.aux.connectivity.to_numpy()[keep]) & forbidden:
        raise ValueError("Held connectivity entered threshold auxiliary source")
    identity = {"global_resource_sha256": resource_sha, "split_seed": split, "validation_refit": refit,
        "train_ids": train_ids.tolist(), "validation_ids": all_ids[va].tolist(), "test_ids": all_ids[te].tolist(),
        "held_ids": held_ids.tolist(), "train_targets": all_y[tr].tolist(),
        "validation_targets": all_y[va].tolist(), "test_targets": all_y[te].tolist(),
        "training_branch_features": array_identity(features[tr]), "test_branch_features": array_identity(features[te]),
        "primary_training_held_connectivity_overlaps": sorted({str(i).split("-")[0] for i in train_ids} & forbidden),
        "water_source_ids_sha256": digest(ctx.aux.molecule_id.to_numpy()[keep].tolist()),
        "water_source_targets": array_identity(ctx.aux.y.to_numpy()[keep]), "water_source_rows": int(keep.sum()),
        "water_held_connectivity_overlap": [], "stage_A_expected_identity": cache_identity(ctx, train_ids, held_ids, 42, "quality"),
        "stage_A_source_exclusion_audit": stage_a_source_audit(ctx, train_ids, held_ids)}
    return tr, va, te, identity


def run(args):
    if platform.node().lower() != os.environ.get("CALNEW_COMPUTE_HOST", "").lower():
        raise ValueError("All benchmark compute must remain on SSH host compute-host")
    torch.set_num_threads(2)
    for out in OUTPUTS.values():
        if out.exists() and not args.resume:
            raise ValueError("Existing completed/partial benchmark prevents duplicate fitting")
    ctx = read_only_context(Path(json.loads(Path("data/current.json").read_text())["snapshot"]))
    all_ids, selection_ids, selection_held, selection_y, selection_tr, task_source, base = cohort(ctx)
    original, source_evidence = load_pinned_source(SOURCE_RUN, ctx, all_ids, selection_ids,
        selection_held, selection_y, task_source, base)
    transformed, selection = verify_selection(ctx, all_ids, selection_ids, selection_held, selection_y,
        selection_tr, base, original, source_evidence)
    features = np.column_stack([base["trees"], transformed])
    all_y = ctx.thr.y.to_numpy()
    hashes = dict(json.loads((SELECTION/"selection-plan.json").read_text())["code_sha256"])
    for path in (Path(__file__), Path("scripts/nose_parity_refine.py")):
        relative = path.resolve().relative_to(Path.cwd().resolve())
        hashes[relative.as_posix()] = file_digest(path)
    resources = benchmark_resources(ctx, hashes, all_ids, all_y, features, source_evidence, selection)
    resource_sha = digest(resources)
    # Freeze both protocols and every split assignment before ANY benchmark
    # fitting or development test score, including fixed Stage-A refits.
    for protocol, out in OUTPUTS.items():
        out.mkdir(parents=True, exist_ok=True)
        refit = protocol == "validation_refit"
        plan = {"host": platform.node(), "task": "threshold_abraham", "protocol": protocol,
            "split_seeds": list(range(42, 52)), "split_sizes": [148, 0, 38] if refit else [111, 37, 38],
            "selected_recipe": SELECTED, "selection_run": str(SELECTION), "frozen_selection_sha256": digest(selection),
            "selection_gate": selection["gate"], "source_fits": 0,
            "candidate_branch": {"kind": "ExtraTrees", "n_estimators": 500, "min_samples_leaf": 2,
                "max_features": .3, "random_state": 42, "threads": 2,
                "features": list(SEMANTIC_BASE)+["idf_unit_predicted_direction128", "original_predicted_norm"]},
            "selected_prediction": "0.5*fresh_current_v2 + 0.5*fixed_direction_confidence_ET",
            "baseline_recipe": "Exact frozen nose_parity_refine.current_threshold: ThresholdStage seeds420..424 plus THRESHOLD_MEMBERS seed42, equal mean of fusion-ensemble and four member predictions",
            "Stage_A": "Exact same-producer quality cache with seed42, or explicit fixed original seed42 refit within this new directory",
            "stage_A_unknown_old_caches": "Preserved and never reused without exact producer identity",
            "source_boundary": "Descriptor arrays globally exclude ALL186 primary connectivities and reserved exclusions; no source refits",
            "auxiliary_boundary": "Water and Stage-A source fitting excludes every split held connectivity; reserved sources filtered before Context",
            "primary_assignments": "Unchanged original random splits; existing primary connectivity overlaps preserved and recorded",
            "test_based_selection": False, "reserved_targets_fitted_or_scored": False,
            "development_test_scoring_authorized_for_frozen_benchmark": True, "production_changed": False,
            "historical_pearson_context": .824471 if refit else .785935,
            "historical_comparison": "Fresh paired comparator reported separately; no requirement to reproduce historical floats",
            "code_sha256": hashes, "resource_sha256": resource_sha, "threads": 2}
        if args.resume and json.loads((out/"protocol.json").read_text()) != plan:
            raise ValueError("Frozen benchmark protocol changed on resume")
        if args.resume and json.loads((out/"resource-manifest.json").read_text())["identity"] != resources:
            raise ValueError("Frozen benchmark resources changed on resume")
        write_json(out/"protocol.json", plan)
        write_json(out/"frozen-selection.json", selection)
        if not args.resume:
            write_json(out/"resource-manifest.json", {"recorded_at_utc": utc_now(),
                "timing": "BEFORE any new benchmark/Stage-A fit or development test score", "identity": resources,
                "resource_sha256": resource_sha})
        for relative, expected in hashes.items():
            destination = out/"source-code"/relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if args.resume and destination.exists() and file_digest(destination) != expected:
                raise ValueError("Archived benchmark source differs")
            shutil.copy2(relative, destination)
        for split in range(42, 52):
            _, _, _, identity = split_resource(ctx, all_ids, all_y, features, split, refit, resource_sha)
            path = out/f"split-{split}-prefit-resource.json"
            if args.resume and json.loads(path.read_text())["identity"] != json.loads(json.dumps(identity)):
                raise ValueError("Frozen split IDs/targets/branch arrays/source exclusion changed")
            if not args.resume:
                write_json(path, {"recorded_at_utc": utc_now(), "timing": "BEFORE any benchmark/Stage-A fit or test score",
                    "identity": identity, "identity_sha256": digest(identity)})
    print("Both benchmark plans frozen: parent gate/raw arrays/15folds verified, two protocols, zero source refits", flush=True)
    started = time.time()
    for protocol, out in OUTPUTS.items():
        refit = protocol == "validation_refit"
        completed = (out/"results.json").exists()
        results = {}
        for split in range(42, 52):
            tr, va, te, identity = split_resource(ctx, all_ids, all_y, features, split, refit, resource_sha)
            path, metadata = out/f"split-{split}.npz", out/f"split-{split}.json"
            if path.exists() != metadata.exists():
                raise ValueError("Orphan paired checkpoint preserved; do not overwrite partial evidence")
            if path.exists():
                if not args.resume:
                    raise ValueError("Existing split requires explicit resume")
                record = json.loads(metadata.read_text())
                if record["identity"] != json.loads(json.dumps(identity)) or record["sha256"] != file_digest(path):
                    raise ValueError("Paired benchmark checkpoint identity/checksum differs")
                with np.load(path, allow_pickle=False) as data:
                    ids, targets = data["ids"].copy(), data["y"].copy()
                    predictions = {name: data[name].copy() for name in ("baseline", "branch", "selected")}
            else:
                print(f"{protocol} split{split}: preparing exact Stage-A producer", flush=True)
                train_ids, held_ids = all_ids[tr], all_ids[np.r_[va, te]]
                enriched, stage_a = stage_a_features(ctx, train_ids, held_ids, out, args.resume)
                write_json(out/f"split-{split}-stage-A-resource.json", {"recorded_at_utc": utc_now(),
                    "timing": "BEFORE threshold endpoint fits and development test score", "stage_A": stage_a})
                print(f"{protocol} split{split}: fresh current-v2 and fixed selected branch", flush=True)
                baseline = current_threshold(ctx, train_ids, held_ids, all_ids[te], enriched, all_y[tr])
                training, evaluation, transform_check = endpoint_transform(features[tr], features[te], False)
                model = ExtraTreesRegressor(n_estimators=500, min_samples_leaf=2, max_features=.3,
                    random_state=42, n_jobs=2).fit(training, all_y[tr])
                branch = model.predict(evaluation)
                selected = (baseline+branch)/2
                predictions = {"baseline": baseline, "branch": branch, "selected": selected}
                ids, targets = all_ids[te], all_y[te]
                if any(p.shape != (38,) or not np.isfinite(p).all() for p in predictions.values()):
                    raise ValueError("Invalid fresh paired predictions")
                # Save exact paired arrays and provenance before scoring them.
                atomic_npz(path, ids=ids, y=targets, train_ids=train_ids, train_y=all_y[tr],
                    validation_ids=all_ids[va], validation_y=all_y[va], **predictions)
                record = {"identity": identity, "sha256": file_digest(path), "Stage_A": stage_a,
                    "branch_transform_checks": transform_check, "fitted_at_utc": utc_now(),
                    "selected_recipe": SELECTED, "source_refits": 0,
                    "source128_array": source_evidence["source_features"]["idf_unit"]["actual_source128_array"],
                    "direction_confidence129": array_identity(transformed),
                    "prediction_arrays": {name: array_identity(p) for name, p in predictions.items()}}
                write_json(metadata, record)
            if not np.array_equal(ids, all_ids[te]) or not np.array_equal(targets, all_y[te]):
                raise ValueError("Original benchmark test IDs/targets differ")
            if not np.array_equal(predictions["selected"], (predictions["baseline"]+predictions["branch"])/2):
                raise ValueError("Frozen half blend reconstruction differs")
            scores = {name: metrics(targets, p) for name, p in predictions.items()}
            results[str(split)] = {"split": split, "train_n": len(tr), "validation_n": len(va), "test_n": len(te),
                "scores": scores, "checkpoint_sha256": record["sha256"],
                "primary_connectivity_overlap": identity["primary_training_held_connectivity_overlaps"],
                "water_source_rows": identity["water_source_rows"], "fixed_Stage_A_refit": record["Stage_A"]["fixed_Stage_A_refit"]}
            if not completed:
                write_json(out/"partial.json", {"status": "running", "frozen_recipe": SELECTED, "per_split": results})
            print(json.dumps({"protocol": protocol, "split": split, "scores": scores}), flush=True)
        summary = {name: {metric: {"mean": float(np.mean([row["scores"][name][metric] for row in results.values()])),
            "sd": float(np.std([row["scores"][name][metric] for row in results.values()]))}
            for metric in ("pearson", "mae", "r2", "mse")} for name in ("baseline", "branch", "selected")}
        paired = {"pearson_wins": sum(row["scores"]["selected"]["pearson"] > row["scores"]["baseline"]["pearson"] for row in results.values()),
            "mae_wins": sum(row["scores"]["selected"]["mae"] < row["scores"]["baseline"]["mae"] for row in results.values()),
            "mean_pearson_gain": summary["selected"]["pearson"]["mean"]-summary["baseline"]["pearson"]["mean"],
            "mean_mae_change": summary["selected"]["mae"]["mean"]-summary["baseline"]["mae"]["mean"]}
        result = {"status": "complete", "host": platform.node(), "protocol": protocol, "selected_recipe": SELECTED,
            "per_split": results, "metrics": summary, "paired": paired, "frozen_selection_sha256": digest(selection),
            "protocol_sha256": file_digest(out/"protocol.json"), "resource_sha256": resource_sha,
            "historical_pearson_context": .824471 if refit else .785935,
            "historical_numbers_not_required_to_match_fresh_baseline": True,
            "source_model_refits": 0, "reserved_targets_fitted_or_scored": False,
            "test_based_selection": False, "production_changed": False,
            "seconds_since_both_protocols_started": round(time.time()-started)}
        if completed:
            prior = json.loads((out/"results.json").read_text())
            if any(prior[key] != result[key] for key in ("per_split", "metrics", "paired", "selected_recipe",
                    "frozen_selection_sha256", "protocol_sha256", "resource_sha256")):
                raise ValueError("Completed benchmark summary differs from raw paired checkpoint reconstruction")
        else:
            write_json(out/"results.json", result)
        print(json.dumps({"protocol": protocol, "metrics": summary, "paired": paired}, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resume", action="store_true")
    with threadpool_limits(limits=2):
        run(parser.parse_args())
