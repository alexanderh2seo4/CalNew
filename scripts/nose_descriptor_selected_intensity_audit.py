"""Paired frozen-intensity descriptor benchmark; SSH only, no new recipe selection.

Refit the original teacher-forced profile C recipe once per unchanged development
partition. Compare its profiles from the saved old and selected Keller intensity
vectors. Stage-A features must already exist with verified cache provenance.
"""
from __future__ import annotations

import os
import argparse
import ast
import importlib.metadata
import json
import platform
import shutil
import tempfile
import time
from pathlib import Path

import joblib
import numpy as np
import torch
from scipy.stats import pearsonr
from sklearn.metrics import r2_score
from threadpoolctl import threadpool_limits

from calnew.io import digest, file_digest, write_json
from calnew.pipeline.paper_benchmark import Context, FRACTIONS, benchmark_split
from calnew.pipeline.stages import CombinerStage
from nose_intensity_experiment import CACHE, cache_identity
from nose_semantic_experiment import RESERVED

RUNS = {"original": Path("runs/nose-intensity-keller-v3"),
        "validation_refit": Path("runs/nose-intensity-keller-refit-v3")}


def array_sha(value):
    import hashlib
    a = np.ascontiguousarray(value)
    # Object arrays store process-local pointers; hash their values instead.
    content = json.dumps(a.tolist(), ensure_ascii=True, separators=(",", ":")).encode() if a.dtype.hasobject else a.tobytes()
    return hashlib.sha256(str(a.dtype).encode()+str(a.shape).encode()+content).hexdigest()


def ast_named(path, names):
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    found = {n.name: ast.dump(n, include_attributes=False) for n in tree.body
             if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in names}
    if set(found) != set(names):
        raise ValueError("Missing original recipe definition")
    return found


def profile_metrics(y, p):
    y, p = np.asarray(y, float), np.asarray(p, float)
    if y.shape != p.shape or y.ndim != 2 or not np.isfinite(y).all() or not np.isfinite(p).all():
        raise ValueError("Invalid descriptor prediction/target alignment")
    correlations = [float(pearsonr(y[:, j], p[:, j]).statistic)
                    if np.std(y[:, j]) > 0 and np.std(p[:, j]) > 0 else None
                    for j in range(y.shape[1])]
    defined = [v for v in correlations if v is not None]
    if not defined:
        raise ValueError("No defined descriptor Pearson correlations")
    error = np.mean((y-p)**2, axis=0)
    mae = np.mean(np.abs(y-p), axis=0)
    r2 = r2_score(y, p, multioutput="raw_values", force_finite=True)
    return {"pearson_macro": float(np.mean(defined)), "mae": float(mae.mean()),
            "r2_macro": float(r2.mean()), "mse": float(error.mean()),
            "pearson_flattened": float(pearsonr(y.ravel(), p.ravel()).statistic),
            "defined_pearson_dimensions": len(defined),
            "per_descriptor": {"pearson": correlations, "mae": mae.tolist(),
                               "r2": r2.tolist(), "mse": error.tolist()}}


def normalized_identity(identity):
    value = json.loads(json.dumps(identity))
    value["snapshot"] = value["snapshot"].replace("\\", "/")
    return value


def stage_training_ast(path):
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    tree.body = [n for n in tree.body if not isinstance(n, ast.FunctionDef) or n.name != "combine_mixture"]
    return ast.dump(tree, include_attributes=False)


def load_existing_meta(ctx, train_ids, held_ids, out):
    identity = cache_identity(ctx, train_ids, held_ids, 42, "quality")
    path = CACHE/(digest(identity)+".npz")
    metadata = path.with_suffix(".json")
    own = out/"stage-A-fixed-refits"/(digest(identity)+".npz")
    migration = None
    if not path.exists() or not metadata.exists():
        candidates = []
        for candidate in CACHE.glob("*.json"):
            if candidate.name.startswith("."):
                continue
            prior = json.loads(candidate.read_text()).get("identity", {})
            if prior.get("kind") == "quality" and prior.get("train_ids") == identity["train_ids"] and prior.get("held_ids") == identity["held_ids"]:
                candidates.append(candidate)
        # Only documented path formatting or the proven unrelated mixture function
        # change can be normalized. Unknown producer hashes are never reused.
        for candidate in candidates:
            record = json.loads(candidate.read_text())
            prior = normalized_identity(record["identity"])
            expected = normalized_identity(identity)
            old_sha = prior["code_sha256"]["src/calnew/pipeline/stages.py"]
            archived = RUNS["original"]/"source-code/src/calnew/pipeline/stages.py"
            if old_sha != expected["code_sha256"]["src/calnew/pipeline/stages.py"]:
                if file_digest(archived) != old_sha or stage_training_ast(archived) != stage_training_ast("src/calnew/pipeline/stages.py"):
                    continue
                prior["code_sha256"]["src/calnew/pipeline/stages.py"] = expected["code_sha256"]["src/calnew/pipeline/stages.py"]
            if prior != expected:
                continue
            path, metadata = candidate.with_suffix(".npz"), candidate
            migration = {"original_manifest": str(candidate), "old_stage_sha256": old_sha,
                "path_format_normalization": True,
                "stage_training_AST_identical_except_combine_mixture": True,
                "all_other_identity_fields_identical": True}
            break
        else:
            path, metadata = own, own.with_suffix(".json")
            if not path.exists() or not metadata.exists():
                print(f"Stage A: fixed seed42 refit required for {len(train_ids)} training molecules; unmatched old producer not reused", flush=True)
                q, d, _ = ctx.stage_a_features(train_ids, held_ids, 42)
                path.parent.mkdir(parents=True, exist_ok=True)
                np.savez_compressed(path, quality=q, direction=d)
                write_json(metadata, {"identity": identity, "sha256": file_digest(path),
                    "fixed_Stage_A_refit": True, "reason": "No existing producer identity can be proved equivalent",
                    "unreused_candidate_manifests": [str(p) for p in candidates]})
    record = json.loads(metadata.read_text())
    if (migration is None and record["identity"] != json.loads(json.dumps(identity))) or record["sha256"] != file_digest(path):
        raise ValueError("Original Stage-A cache identity/checksum mismatch")
    with np.load(path, allow_pickle=False) as saved:
        q, d = saved["quality"].copy(), saved["direction"].copy()
    if q.shape != ctx.labels.shape or d.shape != ctx.direction.shape or not np.isfinite(q).all() or not np.isfinite(d).all():
        raise ValueError("Invalid cached Stage-A profile features")
    return q, d, {"path": str(path), "manifest": str(metadata),
                  "sha256": record["sha256"], "manifest_sha256": file_digest(metadata),
                  "identity": identity, "q_sha256": array_sha(q), "d_sha256": array_sha(d),
                  "serving_change_migration": record.get("serving_change_migration"),
                  "verified_read_only_cache_migration": migration,
                  "fixed_Stage_A_refit": record.get("fixed_Stage_A_refit", False)}


def run(args):
    if platform.node().lower() != os.environ.get("CALNEW_COMPUTE_HOST", "").lower():
        raise ValueError("All descriptor audit compute must run on the authorized SSH server")
    out = Path(args.out)
    if (out/"results.json").exists():
        raise ValueError("Completed result already exists; use a new output directory")
    if out.exists() and not args.resume:
        raise ValueError("Existing partial audit requires --resume")
    out.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(2)
    sources = [Path(__file__), Path("scripts/nose_intensity_experiment.py"),
               Path("scripts/nose_semantic_experiment.py")]+sorted(Path("src/calnew").rglob("*.py"))
    hashes = {p.resolve().relative_to(Path.cwd().resolve()).as_posix(): file_digest(p) for p in sources}
    current = ast_named("src/calnew/pipeline/stages.py", ["ProfileCombiner", "CombinerStage", "_inverse_softplus"])
    original = ast_named(RUNS["original"]/"source-code/src/calnew/pipeline/stages.py", list(current))
    if current != original:
        raise ValueError("Current C recipe differs from the archived original recipe")
    plan = {"host": platform.node(), "scope": "Paired descriptor profiles from frozen Keller old/selected intensity inputs",
        "protocols": list(RUNS), "split_seeds": list(range(42, 52)), "model_seed": 42,
        "profile_model": "Unchanged original CombinerStage, measured-intensity teacher forcing; same fitted C for both predictions",
        "fixed_training_recipe": "400 epochs; original fixed penalties .01/.1/1/10/100 chosen by original grouped3 training-only routine",
        "new_head_or_hyperparameter_selection": False, "test_based_selection": False,
        "Stage_A": "Prefer verified existing caches and documented AST/path migration; fixed original seed42 refit if producer identity cannot be verified",
        "reserved_targets_fitted_or_scored": False, "primary_test_assignments_unchanged": True,
        "code_sha256": hashes, "threads": 2,
        "original_C_AST_identical": True,
        "comparison_limit": "Fresh fixed C fits at model seed42; frozen historical intensity arrays may originate from Mac or SSH. Not reconstruction of all original benchmark model seeds."}
    if args.resume and json.loads((out/"protocol.json").read_text()) != plan:
        raise ValueError("Resume audit source/protocol changed")
    write_json(out/"protocol.json", plan)
    for relative, sha in hashes.items():
        dest = out/"source-code"/relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        if args.resume and dest.exists() and file_digest(dest) != sha:
            raise ValueError("Archived audit source changed")
        shutil.copy2(relative, dest)
    ctx = Context(Path(json.loads(Path("data/current.json").read_text())["snapshot"]), RESERVED)
    frame = ctx.keller
    ids = frame.molecule_id.to_numpy()
    cohorts, cache_records, frozen_records = {}, {}, {}
    # Entire preflight completes before any profile fitting begins.
    for protocol, folder in RUNS.items():
        prior = json.loads((folder/"protocol.json").read_text())
        refit = protocol == "validation_refit"
        if prior["dataset"] != "keller" or prior["recipe"] != "blend_dose_semantic" or prior["validation_refit"] != refit:
            raise ValueError("Frozen intensity run has a different recipe/protocol")
        if file_digest(folder/"frozen-selection.json") != prior["selection_sha256"]:
            raise ValueError("Frozen intensity selection checksum differs")
        for split in range(42, 52):
            key = f"{protocol}-{split}"
            tr, va, te = benchmark_split(len(ids), FRACTIONS["keller"], split, refit)
            train_ids, held_ids = ids[tr], ids[np.r_[va, te]]
            train_conn = {s.split("-")[0] for s in train_ids}
            held_conn = {s.split("-")[0] for s in held_ids}
            if train_conn & held_conn:
                raise ValueError("Keller primary training/held connectivity overlap")
            q, d, meta = load_existing_meta(ctx, train_ids, held_ids, out)
            path = folder/f"split-{split}.npz"
            with np.load(path, allow_pickle=False) as saved:
                expected_y = frame.intensity.to_numpy()[te]
                if not np.array_equal(saved["ids"], ids[te]) or not np.array_equal(saved["y"], expected_y):
                    raise ValueError("Frozen intensity IDs/targets differ from original assignment")
                old, selected = saved["baseline"].copy(), saved["selected"].copy()
            if any(p.shape != (len(te),) or not np.isfinite(p).all() or np.any((p < 0)|(p > 100)) for p in (old, selected)):
                raise ValueError("Invalid frozen intensity predictions")
            cohorts[key] = (tr, va, te, q, d, old, selected)
            cache_records[key] = meta
            frozen_records[key] = {"path": str(path), "sha256": file_digest(path),
                "protocol_sha256": file_digest(folder/"protocol.json"),
                "selection_sha256": file_digest(folder/"frozen-selection.json"),
                "train_ids": train_ids.tolist(), "validation_ids": ids[va].tolist(), "test_ids": ids[te].tolist(),
                "intensity_y_sha256": array_sha(expected_y)}
    resources = {"snapshot": str(ctx.snapshot), "snapshot_sha256": {
        n: file_digest(ctx.snapshot/n) for n in ("molecules.parquet", "observations.parquet", "stimuli.parquet")},
        "reserved_partition_sha256": {str(p/n): file_digest(p/n) for p in RESERVED for n in ("run.json", "split.json")},
        "panel_profile_sha256": array_sha(ctx.prof), "panel_intensity_sha256": array_sha(ctx.data.panel["intensity"]),
        "panel_pleasantness_sha256": array_sha(ctx.data.panel["pleasantness"]),
        "panel_dose_sha256": array_sha(ctx.data.panel["x"]), "panel_ids_sha256": array_sha(ctx.data.panel["molecule_ids"]),
        "task_profile_sha256": array_sha(ctx.keller_profile), "descriptor_names": ctx.data.panel["descriptors"],
        "stage_A_caches": cache_records, "frozen_intensity_inputs": frozen_records,
        "dependencies": {n: importlib.metadata.version(n) for n in ("numpy", "scipy", "torch", "pandas", "scikit-learn", "rdkit")},
        "python": platform.python_version(), "code_sha256": hashes}
    if args.resume and (out/"resource-manifest.json").exists() and json.loads((out/"resource-manifest.json").read_text()) != resources:
        raise ValueError("Resume data/features/frozen inputs/resources changed")
    write_json(out/"resource-manifest.json", resources)
    resource_sha = digest(resources)
    write_json(out/"preflight.json", {"host": platform.node(), "verified_protocols": len(RUNS),
        "verified_splits": len(cohorts), "all_Stage_A_features_present": True,
        "fixed_Stage_A_refits": sum(m["fixed_Stage_A_refit"] for m in cache_records.values()),
        "all_frozen_intensity_IDs_targets_and_selection_hashes_verified": True,
        "resource_sha256": resource_sha, "C_profile_fit_has_started": False})
    print(f"Preflight verified {len(cohorts)} frozen splits and existing Stage-A caches", flush=True)
    if args.preflight_only:
        return
    results = {}
    started = time.time()
    for key, (tr, va, te, q, d, old_i, selected_i) in cohorts.items():
        protocol, split = key.rsplit("-", 1)
        split = int(split)
        path = out/f"{key}.npz"
        metadata = path.with_suffix(".json")
        identity = {"resource_sha256": resource_sha, "frozen_intensity_input": frozen_records[key],
                    "stage_A_sha256": cache_records[key]["sha256"], "descriptor_targets_sha256": array_sha(ctx.keller_profile[te])}
        if args.resume and path.exists() and metadata.exists():
            record = json.loads(metadata.read_text())
            if record["identity"] != identity or record["sha256"] != file_digest(path) or record["model_sha256"] != file_digest(path.with_suffix(".joblib")):
                raise ValueError("Existing profile checkpoint provenance changed")
            with np.load(path, allow_pickle=False) as saved:
                if not np.array_equal(saved["ids"], ids[te]) or not np.array_equal(saved["y"], ctx.keller_profile[te]):
                    raise ValueError("Saved profile IDs/targets changed")
                old_p, selected_p = saved["old_intensity_profile"].copy(), saved["selected_intensity_profile"].copy()
            scores = {"old_intensity": profile_metrics(ctx.keller_profile[te], old_p),
                      "selected_intensity": profile_metrics(ctx.keller_profile[te], selected_p)}
            if scores != record["scores"]:
                raise ValueError("Saved profile metrics differ")
            results[key] = record
            print(f"{key}: verified saved profile checkpoint", flush=True)
            continue
        sel = np.isin(ctx.data.panel["molecule_ids"], ids[tr])
        rows = ctx.p_rows[sel]
        if set(ctx.connectivity[rows]) & {m.split("-")[0] for m in ids[np.r_[va, te]]}:
            raise ValueError("Held connectivity entered profile C training")
        print(f"{key}: fit unchanged C recipe on {len(tr)} molecules/{len(rows)} training stimuli", flush=True)
        model = CombinerStage(epochs=ctx.cfg["combiner"]["epochs"], seed=42).fit(q[rows],
            ctx.data.panel["intensity"][sel], ctx.data.panel["x"][sel], ctx.prof[sel],
            ctx.data.panel["pleasantness"][sel], ctx.connectivity[rows], prior=d[rows])
        test_rows = ctx.rows(ids[te])
        dose = frame.x.to_numpy()[te]
        old_p = model.predict(q[test_rows], old_i, dose, d[test_rows])[0]
        selected_p = model.predict(q[test_rows], selected_i, dose, d[test_rows])[0]
        scores = {"old_intensity": profile_metrics(ctx.keller_profile[te], old_p),
                  "selected_intensity": profile_metrics(ctx.keller_profile[te], selected_p)}
        np.savez_compressed(path, ids=ids[te].astype(str), y=ctx.keller_profile[te],
            old_intensity_profile=old_p, selected_intensity_profile=selected_p,
            old_intensity=old_i, selected_intensity=selected_i, dose=dose,
            quality=q[test_rows], direction=d[test_rows], train_ids=ids[tr].astype(str),
            validation_ids=ids[va].astype(str), descriptor_names=np.asarray(ctx.data.panel["descriptors"], str))
        joblib.dump(model, path.with_suffix(".joblib"), compress=3)
        record = {"identity": identity, "sha256": file_digest(path),
            "model_sha256": file_digest(path.with_suffix(".joblib")), "protocol": protocol, "split_seed": split,
            "training_molecules": len(tr), "training_stimuli": len(rows), "validation_molecules": len(va), "test_molecules": len(te),
            "C_selected_penalty": model.selected_penalty, "C_fixed_recipe_inner_scores": model.inner_scores,
            "C_direction_prior_weight": model.prior_weight, "training_held_connectivity_overlap": [], "scores": scores}
        write_json(metadata, record)
        results[key] = record
        write_json(out/"partial.json", results)
        write_json(out/"progress.json", {"completed": len(results), "total": len(cohorts), "latest": key})
        print(f"{key}: " + json.dumps({n: {k: v[k] for k in ("pearson_macro", "mae", "r2_macro", "mse")} for n,v in scores.items()}), flush=True)
    summary = {}
    for protocol in RUNS:
        rows = [r for r in results.values() if r["protocol"] == protocol]
        summary[protocol] = {name: {metric: {"mean": float(np.mean([r["scores"][name][metric] for r in rows])),
            "sd": float(np.std([r["scores"][name][metric] for r in rows]))}
            for metric in ("pearson_macro", "mae", "r2_macro", "mse", "pearson_flattened")}
            for name in ("old_intensity", "selected_intensity")}
        summary[protocol]["positive_splits"] = {
            "pearson": sum(r["scores"]["selected_intensity"]["pearson_macro"] > r["scores"]["old_intensity"]["pearson_macro"] for r in rows),
            "mae": sum(r["scores"]["selected_intensity"]["mae"] < r["scores"]["old_intensity"]["mae"] for r in rows)}
    result = {"host": platform.node(), "seconds": round(time.time()-started), "resource_sha256": resource_sha,
        "model_seed": 42, "descriptor_names": ctx.data.panel["descriptors"], "summary": summary,
        "per_split": results, "new_recipe_selection": False, "reserved_targets_fitted_or_scored": False,
        "comparison_limit": plan["comparison_limit"]}
    write_json(out/"results.json", result)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="runs/nose-descriptor-selected-intensity-audit-v1")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--preflight-only", action="store_true")
    with threadpool_limits(limits=2):
        run(parser.parse_args())
