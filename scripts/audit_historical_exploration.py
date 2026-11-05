"""Audit saved historical exploration predictions on SSH without fitting models.

The input archive contains trusted research scratch artifacts selected by the
human-authorized audit. No archived experiment is executed. Historical classes
are restored as state bags, and metrics use original split-42 TRAIN rows only.
Missing predictions, fold provenance and identifiers stay explicitly unverified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pickle
import platform
import shutil
import tarfile
from pathlib import Path, PurePosixPath

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import numpy as np
from scipy.stats import pearsonr
from sklearn.model_selection import KFold


class ArchivedState:
    """Restore data attributes without importing or invoking historical models."""


class ResearchUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if module.startswith("calnew."):
            return ArchivedState
        if module == "pathlib" and name == "PosixPath":
            return PurePosixPath
        return super().find_class(module, name)


def restore(path):
    with path.open("rb") as f:
        return ResearchUnpickler(f).load()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def metric(y, p):
    y, p = np.asarray(y, float), np.asarray(p, float)
    if y.shape != p.shape or y.ndim != 1 or not np.isfinite(y).all() or not np.isfinite(p).all():
        raise ValueError("Prediction/target vectors must be aligned and finite")
    return {"pearson": float(pearsonr(y, p).statistic),
            "mae": float(np.mean(np.abs(y-p))), "rmse": float(np.sqrt(np.mean((y-p)**2)))}


def repeated(y, p):
    p = np.asarray(p, float)
    if p.ndim != 2 or p.shape[1] != len(y):
        raise ValueError("Saved repeated predictions have invalid shape")
    scores = [metric(y, row) for row in p]
    return {"per_repeat": scores, "mean": {k: float(np.mean([s[k] for s in scores])) for k in scores[0]}}


def combo(y, oof, names):
    if any(n not in oof for n in names):
        return {"verified": False, "missing_members": [n for n in names if n not in oof]}
    return {"members": names, "scores": repeated(y, np.mean([oof[n] for n in names], axis=0))}


def main(args):
    out = args.out
    if (out / "summary.json").exists():
        raise ValueError("This audit already exists; use a new output directory")
    inputs = out / "source-archives"
    inputs.mkdir(parents=True, exist_ok=True)
    with tarfile.open(args.archive) as tar:
        for member in tar.getmembers():
            p = PurePosixPath(member.name)
            if p.is_absolute() or ".." in p.parts or not (member.isfile() or member.isdir()):
                raise ValueError("Unsafe archive entry")
        tar.extractall(inputs, filter="data")
    shutil.copy2(Path(__file__), out / "audit_historical_exploration.py")
    manifest = {str(p.relative_to(inputs)).replace("\\", "/"):
                {"sha256": sha(p), "bytes": p.stat().st_size}
                for p in sorted(inputs.rglob("*")) if p.is_file()}
    result = {"host": platform.node(), "python": platform.python_version(),
              "input_archive_sha256": sha(args.archive), "source_files": manifest,
              "compute_scope": "Saved predictions and training labels only; no fit, no experiment replay, no reserved final scoring",
              "historical_protocol": {"primary_split": 42, "repeats": 3, "folds": 5,
                  "fold_seeds": [100, 101, 102], "fold_kind": "ordinary KFold (not connectivity-grouped)",
                  "stage_A": "Precomputed before downstream inner folds; not fully nested",
                  "provenance_limit": "OOF pickles store y and named prediction arrays, without molecule IDs, fold IDs, or source hashes; context/source infer alignment but do not prove executed folds"},
              "artifacts": {}, "missing_numerical_evidence": []}
    states = {n: restore(inputs / n / "ctx_42.pkl") for n in ("S1", "S3")}
    state = states["S1"]
    ctx = state["ctx"]
    frames = {"abraham": ctx.thr, "pleasantness": ctx.keller, "ravia": ctx.ravia}
    tables = {}
    for task, frame in frames.items():
        ds = "keller" if task == "pleasantness" else task
        tr, va, te = [np.asarray(i, int) for i in state["splits"][ds]]
        if len(set(np.r_[tr, va, te])) != len(frame) or len(np.r_[tr, va, te]) != len(frame):
            raise ValueError("Historical primary split is not exhaustive/disjoint")
        target = (frame.pleasantness if task == "pleasantness" else frame.y).to_numpy(float)[tr]
        ids = frame.molecule_id.to_numpy()[tr].astype(str)
        other = states["S3"]["ctx"].keller if ds == "keller" else getattr(states["S3"]["ctx"], "thr" if ds == "abraham" else "ravia")
        other_tr = np.asarray(states["S3"]["splits"][ds][0], int)
        other_y = (other.pleasantness if task == "pleasantness" else other.y).to_numpy(float)[other_tr]
        if not np.array_equal(ids, other.molecule_id.to_numpy()[other_tr].astype(str)) or not np.array_equal(target, other_y):
            raise ValueError("Historical contexts disagree on training identities/targets")
        groups = np.array([s.split("-")[0] for s in ids])
        folds = []
        for seed in (100, 101, 102):
            per = []
            for a, b in KFold(5, shuffle=True, random_state=seed).split(ids):
                per.append({"train_rows": len(a), "validation_rows": len(b),
                            "connectivity_overlap": sorted(set(groups[a]) & set(groups[b]))})
            folds.append({"seed": seed, "folds": per})
        tables[task] = {"y": target, "ids": ids, "folds": folds,
                       "primary": {"train": len(tr), "val": len(va), "test": len(te), "total": len(frame)}}
    result["training_identity_checks"] = {t: {"context_S1_S3_identical": True,
          "primary_sizes": v["primary"], "training_ids": v["ids"].tolist(),
          "expected_folds_from_source": v["folds"]} for t, v in tables.items()}
    current = {"abraham": ["pipeline_B1", "xgb_rd_ex_fp", "et_rd_ex_fp", "ridge_fp"],
               "pleasantness": ["et_rd_ex_q_d", "et_rd_ex_fp"],
               "ravia": ["xgb_rd_ex_q_d", "xgb_rd_ex_q", "xgb_rd_ex_fp"]}
    for path in sorted((inputs / "S2").rglob("oof_*.pkl")):
        task = "pleasantness" if "pleasantness" in path.name else "ravia" if "ravia" in path.name else "abraham"
        artifact = restore(path)
        y = np.asarray(artifact["y"], float)
        if not np.array_equal(y, tables[task]["y"]):
            raise ValueError("Saved OOF labels differ from trusted historical training context: " + path.name)
        oof = artifact["oof"]
        row = {"task": task, "n": len(y), "target_values_equal_context_train": True,
               "numerical_values_recovered": True, "complete_fold_alignment_verified": False,
               "members": {name: repeated(y, p) for name, p in oof.items()},
               "fixed_equal_baseline": combo(y, oof, current[task])}
        row["candidate_additions"] = {name: combo(y, oof, current[task]+[name])
            for name in oof if "molformer" in name or "unimol2" in name}
        if task == "abraham" and "ridge_unimol2" in oof:
            base = current[task]+["ridge_unimol2"]
            row["current_with_unimol2"] = combo(y, oof, base)
            for weight in (1.0, .5, .25):
                names = [f"xgb_joint_w{weight}", f"et_joint_w{weight}"]
                if all(n in oof for n in names):
                    row.setdefault("water_joint_variants", {})[str(weight)] = {
                        "swap_trees": combo(y, oof, ["pipeline_B1"]+names+["ridge_fp", "ridge_unimol2"]),
                        "add_trees": combo(y, oof, base+names)}
        if task == "ravia" and "et_unimol2" in oof:
            row["current_with_unimol2"] = combo(y, oof, current[task]+["et_unimol2"])
        result["artifacts"][str(path.relative_to(inputs)).replace("\\", "/")] = row
    # Stored Li transfer values establish a training proxy correlation, not a head's CV score.
    aux = np.load(inputs / "S2" / "li_aux_train_oof.npy", allow_pickle=False)
    result["water_transfer_proxy"] = {"artifact": "S2/li_aux_train_oof.npy",
        "scores_against_abraham_training_target": metric(tables["abraham"]["y"], aux),
        "interpretation": "Correlation of cross-fitted water proxy with air target; not downstream predictive benchmark",
        "fold_alignment_verified": False}
    full = np.load(inputs / "S2" / "stray" / "li_aux_split42.npy", allow_pickle=False)
    rows = np.array([ctx.row[s] for s in tables["abraham"]["ids"]], int)
    result["water_transfer_proxy_full_array"] = {"shape": list(full.shape),
        "scores_training_rows_only": metric(tables["abraham"]["y"], full[rows]),
        "artifact": "S2/stray/li_aux_split42.npy", "fold_alignment_verified": False}
    seeds = restore(inputs / "S2" / "stageA_keller_seeds.pkl")
    first = state["feats"]["keller", 42]
    result["stage_A_seeds"] = {"stored_seed_count": len(seeds),
        "shapes": [[list(np.shape(a)) for a in item] for item in seeds],
        "first_features_exactly_match_context": all(np.array_equal(a, b) for a,b in zip(seeds[0],first)),
        "final_predictions_available": False,
        "reported_seed_averaging_and_measured_profile_ceiling_scores_verified": False}
    for technique, reason in {
        "Stage-A seed averaging and measured-profile pleasantness ceiling": "Archive stores feature arrays; no saved final OOF predictions. Verification would require model fitting, excluded from this audit.",
        "Validation-fitted and half-shrunk ensemble weights": "Source computes NNLS weights and prints scores but saves neither weights nor results. This audit does not replay or fit NNLS.",
        "Water proxy-augmented heads": "Source saves proxy arrays only; modified head OOF arrays are not persisted.",
        "S3 random tree search, Keller/Ravia-to-threshold transfer, pooled water variants": "Scripts present; no corresponding durable OOF result arrays identified.",
        "Original scratch fold/source provenance": "Prediction artifacts omit row/fold IDs and source checksums; inferred alignment is weaker than verified executed folds."}.items():
        result["missing_numerical_evidence"].append({"technique": technique, "reason": reason})
    (out / "summary.json").write_text(json.dumps(result, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    small = {"host": result["host"], "artifacts": {k: {"n": v["n"],
        "members": list(v["members"]), "baseline": v["fixed_equal_baseline"]} for k,v in result["artifacts"].items()},
        "water_proxy": result["water_transfer_proxy"], "unverified": result["missing_numerical_evidence"]}
    print(json.dumps(small, indent=2, allow_nan=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("runs/nose-historical-exploration-audit"))
    main(parser.parse_args())
