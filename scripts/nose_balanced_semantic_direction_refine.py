"""Fixed pleasantness direction/confidence heads; reuse completed SSH source fits.

No source model is refitted. All fifteen parent balanced folds must exist and
verify before any endpoint fit. Source vectors are normalized independently,
with their original norm retained, then scored inside original training only.
"""
from __future__ import annotations

import os
import argparse
import importlib.metadata
import json
from pathlib import Path
import platform
import shutil
import time

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from calnew.io import digest, file_digest, write_json
from calnew.pipeline.blocks import BlockCache, EXPLICIT_BLOCKS
from calnew.pipeline.paper_benchmark import FRACTIONS, random_split
from calnew.pipeline.semantic import SEMANTIC_BASE
from calnew.pipeline.semantic_balanced import BalancedDescriptorTransfer, array_sha256
from calnew.pipeline.stages import stack
from nose_balanced_semantic_refine import atomic_npz, baseline_fold, common_baseline_modules
from nose_intensity_experiment import metrics
from nose_parity_progress import dependency_versions, inspect_run, read_only_context
from nose_semantic_experiment import SHA256, SOURCE, load_corpus


EPSILON = 1e-12
CANDIDATES = {representation+"_"+head: (representation, head)
    for representation in BalancedDescriptorTransfer.REPRESENTATIONS for head in ("trees", "ridge100")}


def direction_confidence(values):
    values = np.asarray(values, np.float64)
    if values.ndim != 2 or values.shape[1] != 128 or not np.isfinite(values).all():
        raise ValueError("Invalid pinned source vectors")
    norms = np.linalg.norm(values, axis=1)
    direction = values/np.maximum(norms[:, None], EPSILON)
    result = np.column_stack([direction, norms])
    if (not np.isfinite(result).all() or not np.array_equal(result[:, -1], norms)
            or not np.allclose(np.linalg.norm(direction[norms > EPSILON], axis=1), 1, rtol=0, atol=1e-12)):
        raise ValueError("Invalid direction/confidence transformation")
    return result


def parent_identity(parent, ctx):
    paths = [parent/name for name in ("results.json", "selection-plan.json", "resource-manifest.json",
        "normalization-checks.json", "keller-inner-oof.npz", "keller-folds.json")]
    if not all(path.exists() for path in paths):
        raise ValueError("Wait for all fifteen completed balanced parent folds/results")
    plan = json.loads((parent/"selection-plan.json").read_text())
    resource = json.loads((parent/"resource-manifest.json").read_text())
    result = json.loads((parent/"results.json").read_text())
    resource_sha = digest(resource)
    if result["resource_sha256"] != resource_sha or result["results"]["keller"]["training_molecules"] != 260:
        raise ValueError("Parent data identity/cohort differs")
    for relative, expected in plan["code_sha256"].items():
        path = Path(relative.replace("\\", "/"))
        if file_digest(path) != expected or file_digest(parent/"source-code"/path) != expected:
            raise ValueError("Parent frozen executable source differs")
    for name, expected in resource["snapshot_sha256"].items():
        if file_digest(ctx.snapshot/name) != expected:
            raise ValueError("Parent snapshot changed")
    for relative, expected in resource["reserved_partitions_sha256"].items():
        if file_digest(Path(relative)) != expected:
            raise ValueError("Reserved partition changed")
    if resource["task_universe_sha256"] != digest(ctx.universe):
        raise ValueError("Parent universe changed")
    for name, expected in resource["task_blocks_sha256"].items():
        if array_sha256(ctx.B[name]) != expected:
            raise ValueError("Actual parent task feature array changed")
    for name, expected in resource["dependencies"].items():
        if importlib.metadata.version(name) != expected:
            raise ValueError("Parent dependencies changed")
    if resource["python"] != platform.python_version():
        raise ValueError("Parent Python version changed")
    if (file_digest(Path("data/raw/nose/v1.0.0/nose-smiles-descriptor-v1.0.0.csv.gz")) != resource["source_archive_sha256"]
            or file_digest(Path("data/features/nose-descriptor-minilm.npz")) != resource["word_vectors_sha256"]
            or json.loads(Path("data/features/nose-descriptor-minilm.json").read_text()) != resource["word_manifest"]):
        raise ValueError("Parent generic source assets changed")
    checks = json.loads((parent/"normalization-checks.json").read_text())
    if not all(checks.values()):
        raise ValueError("Parent source exclusion/normalization checks did not pass")
    return plan, resource, resource_sha, {"path": str(parent), "resource_sha256": resource_sha,
        "artifact_sha256": {path.name: file_digest(path) for path in paths},
        "parent_code_and_data_verified": True, "completed_parent_fold_count": 15,
        "source_refits_in_this_study": 0}


def reconstruct_source(ctx, out, resource):
    """Load pinned labels/features only; this never calls source model fit."""
    molecules, labels = load_corpus(ctx, out)
    word_path = Path("data/features/nose-descriptor-minilm.npz")
    terms = sorted(pd.read_csv(SOURCE, usecols=["TARGET_Descriptor"]).TARGET_Descriptor.unique())
    with np.load(word_path, allow_pickle=False) as saved:
        if saved["terms"].tolist() != terms:
            raise ValueError("Source reconstruction vocabulary order changed")
        words = saved["vectors"].copy()
    blocks = BlockCache(Path("data/features")).blocks(("rdkit", "fingerprint"), molecules.smiles.tolist())
    features = np.column_stack([blocks["rdkit"], blocks["fingerprint"]])
    transfer = BalancedDescriptorTransfer(molecules, labels, features, words, threads=2)
    label_sha = digest({"shape": labels.shape, "data": array_sha256(labels.data),
        "indices": array_sha256(labels.indices), "indptr": array_sha256(labels.indptr)})
    if (file_digest(SOURCE) != SHA256 or array_sha256(transfer.ids) != resource["source_ids_sha256"]
            or array_sha256(features) != resource["source_features_sha256"]
            or label_sha != resource["source_labels_sha256"]
            or array_sha256(transfer.projection) != resource["projection_sha256"]):
        raise ValueError("Actual reconstructed original source labels/features/projection differ")
    return transfer


def source_arrays(parent_record, name, train_ids, held_ids, eval_ids, seed, parent_resource_sha, transfer, out):
    records = parent_record["source_fits"][name]
    if len(records) != 4:
        raise ValueError("Expected three grouped source feature folds and one held fit")
    groups = np.array([str(m).split("-")[0] for m in train_ids])
    matrix = np.full((len(train_ids), 128), np.nan, np.float32)
    coverage = np.zeros(len(train_ids), int)
    evidence = []

    def load(item, requested, forbidden):
        path = Path(item["path"])
        metadata = path.with_suffix(".json")
        saved = json.loads(metadata.read_text())
        expected = {"resources_sha256": parent_resource_sha, "representation": name,
            "excluded_connectivities": sorted({str(m).split("-")[0] for m in forbidden}),
            "evaluate_ids": requested.tolist(), "source_seed": 173}
        if (saved["identity"] != expected or saved["sha256"] != item["sha256"]
                or saved["sha256"] != file_digest(path) or saved["source_fit"] != item["source_fit"]
                or saved["source_fit"]["excluded_connectivities"] != expected["excluded_connectivities"]
                or saved["source_fit"]["held_connectivity_overlap"] != []):
            raise ValueError("Parent source cache/IDF/exclusion identity differs")
        with np.load(path, allow_pickle=False) as data:
            values = data["features"].copy()
        if values.shape != (len(requested), 128) or not np.isfinite(values).all():
            raise ValueError("Invalid actual parent source feature array")
        _, actual_targets, actual_idf, actual_audit = transfer.source_targets(
            expected["excluded_connectivities"], name)
        if actual_audit != saved["source_fit"]:
            raise ValueError("Actual reconstructed original source IDF/targets/exclusions differ")
        idf_path = out/"reconstructed-parent-idf"/(digest(expected)+".npz")
        idf_metadata = idf_path.with_suffix(".json")
        if idf_path.exists() != idf_metadata.exists():
            raise ValueError("Orphan reconstructed IDF artifact; refuse reuse")
        if idf_path.exists():
            with np.load(idf_path, allow_pickle=False) as reconstructed:
                if not np.array_equal(reconstructed["idf"], actual_idf):
                    raise ValueError("Saved reconstructed IDF array changed")
        else:
            atomic_npz(idf_path, idf=actual_idf)
        reconstruction = {"path": str(idf_path), "sha256": file_digest(idf_path),
            "actual_idf_sha256": array_sha256(actual_idf),
            "actual_targets_sha256": array_sha256(actual_targets),
            "actual_target_shape": list(actual_targets.shape),
            "matches_original_source_fit_audit": True,
            "timing": "Reconstructed from pinned allowed source labels before NEW endpoint fits; original parent disk metadata was recorded after its source fit"}
        if idf_metadata.exists() and json.loads(idf_metadata.read_text()) != reconstruction:
            raise ValueError("Saved reconstructed IDF metadata changed")
        write_json(idf_metadata, reconstruction)
        return values, {"path": str(path), "sha256": saved["sha256"],
            "metadata_sha256": file_digest(metadata), "actual_source_array_sha256": array_sha256(values),
            "source_fit": saved["source_fit"], "evaluate_ids": requested.tolist(),
            "source_target_reconstruction": reconstruction}

    for inner, (a, b) in enumerate(GroupKFold(3, shuffle=True, random_state=seed).split(train_ids, groups=groups)):
        item = records[inner]
        if (item["inner_fold"] != inner or item["train_ids"] != train_ids[a].tolist()
                or item["feature_ids"] != train_ids[b].tolist() or set(groups[a]) & set(groups[b])):
            raise ValueError("Parent source feature grouped assignment changed")
        matrix[b], record = load(item, train_ids[b], np.r_[held_ids, train_ids[b]])
        coverage[b] += 1
        evidence.append(record)
    if records[3]["inner_fold"] != "held" or records[3]["feature_ids"] != eval_ids.tolist():
        raise ValueError("Parent held source fit assignment differs")
    evaluate, record = load(records[3], eval_ids, held_ids)
    evidence.append(record)
    if not np.all(coverage == 1) or not np.isfinite(matrix).all():
        raise ValueError("Parent source crossfit feature coverage is incomplete")
    train, test = direction_confidence(matrix), direction_confidence(evaluate)
    combined = np.vstack([matrix, evaluate])
    if not np.array_equal(direction_confidence(combined)[:len(matrix)], train):
        raise ValueError("Source normalization depends on other rows")
    combined[len(matrix):] = combined[len(matrix):]*7+101
    if not np.array_equal(direction_confidence(combined)[:len(matrix)], train):
        raise ValueError("Held source perturbation changed normalized training values")
    if not np.array_equal(direction_confidence(np.zeros((2, 128))), np.zeros((2, 129))):
        raise ValueError("Fixed-epsilon zero-vector handling failed")
    return train, test, {"source_caches": evidence, "train_source129_sha256": array_sha256(train),
        "evaluate_source129_sha256": array_sha256(test), "held_perturbation_changes_no_train_values": True,
        "per_row_norm_retained_exactly": True, "source_refits": 0}


def run(args):
    if platform.node().lower() != os.environ.get("CALNEW_COMPUTE_HOST", "").lower():
        raise ValueError("Run modeling only on authorized SSH host compute-host")
    out, parent, baseline = Path(args.out), Path(args.parent), Path(args.baseline)
    if (out/"results.json").exists() or (out.exists() and not args.resume):
        raise ValueError("Choose a fresh run or explicitly resume an incomplete run")
    if not (parent/"results.json").exists():
        raise ValueError("Parent balanced source run is still incomplete; no endpoint fits permitted")
    ctx = read_only_context(Path(json.loads(Path("data/current.json").read_text())["snapshot"]))
    parent_plan, parent_resource, parent_sha, parent_evidence = parent_identity(parent, ctx)
    baseline_plan, hashes = common_baseline_modules(baseline)
    for path in (Path(__file__), Path("scripts/nose_balanced_semantic_refine.py"),
            Path("scripts/nose_parity_progress.py"), Path("src/calnew/pipeline/semantic_balanced.py")):
        relative = path.resolve().relative_to(Path.cwd().resolve())
        hashes[relative.as_posix()] = file_digest(path)
    plan = {"host": platform.node(), "scope": "Original Keller split42 training260 only",
        "outer_cv": "Three connectivity GroupKFold5 repeats, seeds100/101/102", "threads": 2,
        "parent_source": str(parent), "parent_plan_sha256": file_digest(parent/"selection-plan.json"),
        "parent_resource_sha256": parent_sha, "source_refits": 0,
        "source_feature_transform": "Per-row prediction128/max(Euclidean norm,1e-12), append original norm; no fitted parameters",
        "source_output_width": 129, "required_parent_completion": "All15 exact source-fold/cache/ID/target/checksum assignments verified BEFORE endpoint fitting",
        "idf_target_verification": "Reconstruct all120 original source IDF/target hashes from pinned allowed labels before NEW endpoint fits; no source model refits",
        "candidates": {name: {"representation": representation, "head": head,
            "features": "SEMANTIC_BASE+dilution+unit128+originalnorm" if head == "trees"
                else "EXPLICIT_BLOCKS+dilution+unit128+originalnorm"} for name, (representation, head) in CANDIDATES.items()},
        "endpoint_models": {"trees": {"n_estimators": 500, "min_samples_leaf": 2,
            "max_features": .3, "random_state": 42, "threads": 2},
            "ridge100": "Training-fold median imputation, StandardScaler, Ridge(alpha=100)"},
        "endpoint_prediction_bounds": [0, 100],
        "original_norm_role": "Heuristic consensus coordinate; no calibrated uncertainty claim",
        "candidate_predictions": "Four fixed standalone heads and four fixed half-CURRENT-v3 blends",
        "gate": "Mean Pearson gain>=.01; positive>=2/3 repeats; no meanMAE increase; highest passing meanPearson",
        "baseline": str(baseline), "baseline_plan_sha256": file_digest(baseline/"selection-plan.json"),
        "code_sha256": hashes, "main_validation_test_targets_scored": False,
        "reserved_targets_fitted_or_scored": False, "post_score_eligibility_changes": False}
    out.mkdir(parents=True, exist_ok=True)
    if args.resume and json.loads((out/"selection-plan.json").read_text()) != plan:
        raise ValueError("Direction/confidence registration changed")
    write_json(out/"selection-plan.json", plan)
    for relative, expected in hashes.items():
        target = out/"source-code"/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if args.resume and target.exists() and file_digest(target) != expected:
            raise ValueError("Archived direction source changed")
        shutil.copy2(relative, target)
    audit = inspect_run(ctx, str(baseline))
    task = audit["datasets"]["keller"]
    if task["status"] != "complete" or not task["saved_final_results_verified"]["scores_and_promotion_exact"]:
        raise ValueError("Current-v3 fifteen-fold comparator is incomplete/unverified")
    write_json(out/"baseline-audit.json", audit)
    transfer = reconstruct_source(ctx, out, parent_resource)
    frame = ctx.keller
    tr, va, te = random_split(len(frame), FRACTIONS["keller"], 42)
    all_ids = frame.molecule_id.to_numpy()
    ids, fixed_held = all_ids[tr], all_ids[np.r_[va, te]]
    y, dose = frame.pleasantness.to_numpy()[tr], frame.x.to_numpy()[tr, None]
    groups = np.array([str(m).split("-")[0] for m in ids])
    if len(ids) != 260 or set(groups) & {str(m).split("-")[0] for m in fixed_held}:
        raise ValueError("Primary Keller training/main-held boundary changed")
    rows = ctx.rows(ids)
    bases = {"trees": np.column_stack([stack(ctx.B, SEMANTIC_BASE)[rows], dose]),
        "ridge100": np.column_stack([stack(ctx.B, EXPLICIT_BLOCKS)[rows], dose])}
    with np.load(parent/"keller-inner-oof.npz", allow_pickle=False) as saved:
        if not np.array_equal(saved["ids"], ids) or not np.array_equal(saved["y"], y):
            raise ValueError("Parent original-training OOF cohort differs")
        parent_current = saved["current"].copy()
    prefits, evidence = {}, {}
    for repeat in range(3):
        for fold, (a, b) in enumerate(GroupKFold(5, shuffle=True, random_state=100+repeat).split(ids, groups=groups)):
            held = np.r_[fixed_held, ids[b]]
            path = parent/f"keller-repeat-{repeat}-fold-{fold}.npz"
            record = json.loads(path.with_suffix(".json").read_text())
            current, comparator = baseline_fold(baseline, baseline_plan, repeat, fold, ids[a], held, ids[b], y[b])
            expected = {"resource_sha256": parent_sha, "train_ids": ids[a].tolist(), "held_ids": held.tolist(),
                "evaluate_ids": ids[b].tolist(), "train_targets": y[a].tolist(), "targets": y[b].tolist(),
                "baseline": comparator}
            if (record["identity"] != expected or record["sha256"] != file_digest(path)
                    or not record["outer_connectivity_disjoint_verified"]):
                raise ValueError("Parent outer fold identity/checksum changed")
            with np.load(path, allow_pickle=False) as saved:
                if not np.array_equal(saved["current"], current) or not np.array_equal(parent_current[repeat, b], current):
                    raise ValueError("Parent paired current-v3 predictions differ")
            source, sources = {}, {}
            for name in BalancedDescriptorTransfer.REPRESENTATIONS:
                train, evaluate, sources[name] = source_arrays(record, name, ids[a], held, ids[b],
                    300+repeat*5+fold, parent_sha, transfer, out)
                source[name] = (train, evaluate)
            prefits[(repeat, fold)] = (a, b, held, current, source)
            evidence[f"{repeat}-{fold}"] = {"parent_fold_path": str(path), "parent_fold_sha256": record["sha256"],
                "parent_fold_metadata_sha256": file_digest(path.with_suffix(".json")),
                "baseline": comparator, "source_arrays": sources}
    resources = {"parent": parent_evidence, "fifteen_prefit_feature_assignments": evidence,
        "training_ids": ids.tolist(), "training_targets_sha256": array_sha256(y),
        "endpoint_base_sha256": {name: array_sha256(value) for name, value in bases.items()},
        "code_sha256": hashes, "dependencies": dependency_versions()}
    resource_sha = digest(resources)
    resource_path = out/"resource-manifest.json"
    if args.resume and resource_path.exists() and json.loads(resource_path.read_text()) != resources:
        raise ValueError("Resume pinned source/base/comparator/data resources changed")
    if args.resume and not resource_path.exists() and list(out.glob("keller-repeat-*-fold-*.npz")):
        raise ValueError("Endpoint fits exist without the required prefit resource manifest")
    write_json(resource_path, resources)
    names = ("current",)+tuple(CANDIDATES)+tuple("blend_"+name for name in CANDIDATES)
    predictions = {name: np.full((3, len(ids)), np.nan) for name in names}
    started = time.time()
    print("Direction/confidence prefit registration complete:15 parent source folds verified, zero new source fits", flush=True)
    for (repeat, fold), (a, b, held, current, sources) in prefits.items():
        identity = {"resource_sha256": resource_sha, "train_ids": ids[a].tolist(), "held_ids": held.tolist(),
            "evaluate_ids": ids[b].tolist(), "train_targets": y[a].tolist(), "targets": y[b].tolist(),
            "prefit_feature_assignment": evidence[f"{repeat}-{fold}"]}
        path = out/f"keller-repeat-{repeat}-fold-{fold}.npz"
        metadata = path.with_suffix(".json")
        if path.exists() != metadata.exists():
            raise ValueError("Orphan endpoint prediction/metadata; refuse reuse")
        if args.resume and path.exists():
            record = json.loads(metadata.read_text())
            if record["identity"] != identity or record["sha256"] != file_digest(path):
                raise ValueError("Direction endpoint resume identity/checksum differs")
            with np.load(path, allow_pickle=False) as saved:
                values = {name: saved[name].copy() for name in saved.files}
            if not np.array_equal(values["current"], current):
                raise ValueError("Resume current comparator differs")
        else:
            values = {"current": current}
            for name, (representation, head) in CANDIDATES.items():
                train, evaluate = sources[representation]
                x, z = np.column_stack([bases[head][a], train]), np.column_stack([bases[head][b], evaluate])
                model = (make_pipeline(SimpleImputer(strategy="median", keep_empty_features=True),
                    ExtraTreesRegressor(n_estimators=500, min_samples_leaf=2, max_features=.3,
                        random_state=42, n_jobs=2)) if head == "trees" else
                    make_pipeline(SimpleImputer(strategy="median", keep_empty_features=True), StandardScaler(), Ridge(alpha=100)))
                values[name] = np.clip(model.fit(x, y[a]).predict(z), 0, 100)
                values["blend_"+name] = (current+values[name])/2
            atomic_npz(path, **values)
            record = {"identity": identity, "sha256": file_digest(path), "source_refits": 0,
                "all_source_arrays_prefit_pinned": True, "held_perturbation_normalization_checks_passed": True}
            write_json(metadata, record)
        if set(values) != set(predictions):
            raise ValueError("Direction checkpoint candidate schema differs")
        for name, p in values.items():
            if p.shape != (len(b),) or not np.isfinite(p).all():
                raise ValueError("Non-finite/incomplete direction endpoint prediction")
            predictions[name][repeat, b] = p
        write_json(out/"fold-progress.json", {"completed_folds": repeat*5+fold+1, "total_folds": 15})
        print(f"Direction/confidence repeat{repeat+1}/3 fold{fold+1}/5 complete", flush=True)
    scores = {name: [metrics(y, p) for p in matrix] for name, matrix in predictions.items()}
    passing = []
    for name, values in scores.items():
        gain = np.array([a["pearson"]-b["pearson"] for a, b in zip(values, scores["current"])])
        if gain.mean() >= .01 and (gain > 0).sum() >= 2 and np.mean([p["mae"] for p in values]) <= np.mean([p["mae"] for p in scores["current"]]):
            passing.append(name)
    selected = max(passing, key=lambda name: np.mean([p["pearson"] for p in scores[name]])) if passing else "current"
    atomic_npz(out/"keller-inner-oof.npz", ids=ids.astype(str), y=y, **predictions)
    result = {"host": platform.node(), "resource_sha256": resource_sha, "seconds": round(time.time()-started),
        "results": {"keller": {"training_molecules": len(ids), "scores": scores, "passing": passing, "selected": selected}},
        "source_refits": 0, "main_validation_test_targets_scored": False, "reserved_targets_fitted_or_scored": False}
    write_json(out/"results.json", result)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="runs/nose-balanced-semantic-direction-inner-v1")
    parser.add_argument("--parent", default="runs/nose-balanced-semantic-grouped-inner-v1")
    parser.add_argument("--baseline", default="runs/nose-parity-pleasantness-grouped-inner-v2")
    parser.add_argument("--resume", action="store_true")
    with threadpool_limits(limits=2):
        run(parser.parse_args())
