"""Registered restricted additive threshold physics study; SSH execution only.

Fit candidate physics heads first, then compare with audited current-v2 grouped
checkpoints when available. Never refit the baseline or score its main held rows.
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
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import SplineTransformer, StandardScaler
import torch
from threadpoolctl import threadpool_limits

from calnew.io import digest, file_digest, write_json
from calnew.pipeline.blocks import block_names
from calnew.pipeline.paper_benchmark import FRACTIONS, random_split
from nose_parity_progress import array_identity, dependency_versions, file_identity, inspect_run, read_only_context
from nose_semantic_experiment import RESERVED, SOURCE


CONTINUOUS = (("transport", "MolWt"), ("transport", "MolLogP"), ("transport", "TPSA"),
    ("transport", "LabuteASA"), ("chain", "longest_aliphatic_chain"), ("hbond", "polar_surface_fraction"))
CANDIDATES = {"additive_ridge10": (False, 10.), "additive_ridge100": (False, 100.),
    "class_interactions_ridge10": (True, 10.), "class_interactions_ridge100": (True, 100.)}


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


class AdditivePhysics:
    """Univariate restricted splines plus fixed linear structural-class terms."""

    def __init__(self, interactions=False):
        self.interactions = interactions

    def fit(self, x):
        if x.ndim != 2 or x.shape[1] != 6+len(block_names("osmophore")):
            raise ValueError("Unexpected restricted physics feature schema")
        self.imputer = SimpleImputer(strategy="median", keep_empty_features=True).fit(x)
        values = self.imputer.transform(x)
        if not np.isfinite(values).all():
            raise ValueError("Non-finite training physics inputs")
        self.spline = SplineTransformer(n_knots=4, degree=2, knots="uniform",
            include_bias=False, extrapolation="linear").fit(values[:, :6])
        self.interaction_axes = StandardScaler().fit(values[:, [4, 1]])
        self.scaler = StandardScaler().fit(self._basis(values))
        return self

    def _basis(self, values):
        terms = [self.spline.transform(values[:, :6]), values[:, 6:]]
        if self.interactions:
            axes = self.interaction_axes.transform(values[:, [4, 1]])
            # Only class × chain and class × logP, with no other pairwise terms.
            terms.extend((values[:, 6:]*axes[:, [0]], values[:, 6:]*axes[:, [1]]))
        return np.column_stack(terms)

    def transform(self, x):
        values = self.scaler.transform(self._basis(self.imputer.transform(x)))
        if not np.isfinite(values).all():
            raise ValueError("Non-finite transformed physics features")
        return values

    def state(self):
        return {"imputer_statistics": self.imputer.statistics_.tolist(),
            "spline_knots": [s.t.tolist() for s in self.spline.bsplines_],
            "interaction_axis_mean": self.interaction_axes.mean_.tolist(),
            "interaction_axis_scale": self.interaction_axes.scale_.tolist(),
            "output_mean": self.scaler.mean_.tolist(), "output_scale": self.scaler.scale_.tolist(),
            "output_features": len(self.scaler.mean_), "interactions": self.interactions}


def verify_transform(training, evaluation, interactions):
    first = AdditivePhysics(interactions).fit(training)
    first_state = first.state()
    actual = first.transform(evaluation)
    second = AdditivePhysics(interactions).fit(training.copy())
    if first_state != second.state() or not np.array_equal(actual, second.transform(evaluation.copy())):
        raise ValueError("Identical training transform fits are not deterministic")
    # Perturb held inputs far outside the training range, without changing the
    # training argument. Transformation cannot mutate fitted medians or knots.
    changed = evaluation.copy()
    changed[:, :6] = np.nan_to_num(changed[:, :6], nan=0.)*7.+101.
    changed[:, 6:] = np.nan_to_num(changed[:, 6:], nan=0.)+3.
    first.transform(changed)
    if first.state() != first_state or not np.array_equal(first.transform(evaluation), actual):
        raise ValueError("Held transformations changed training medians, knots, scales or predictions")
    changed[0, :6] = np.nan
    first.transform(changed)
    if first.state() != first_state:
        raise ValueError("Missing held features changed fitted state")
    return first, {"identical_training_fit_exact": True, "held_perturbation_does_not_change_fit": True,
        "missing_held_inputs_supported": True, "output_finite": True,
        "fitted_state_sha256": digest(first_state), "fitted_state": first_state}


def score(y, p):
    from scipy.stats import pearsonr
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
    for path in (Path(__file__), Path("scripts/nose_parity_progress.py")):
        relative = path.resolve().relative_to(Path.cwd().resolve())
        hashes[relative.as_posix()] = file_digest(path)
    return plan, hashes


def resources(ctx, hashes, ids, y, raw):
    return {"snapshot": str(ctx.snapshot), "snapshot_sha256": {name: file_digest(ctx.snapshot/name)
            for name in ("molecules.parquet", "observations.parquet", "stimuli.parquet")},
        "reserved_partition_sha256": {str(run/name): file_digest(run/name)
            for run in RESERVED for name in ("run.json", "split.json")},
        "source_files": {str(path): file_identity(path) for path in (
            SOURCE, Path("data/raw/li_2025/zenodo-17559514-v1/threshold_data_med.csv"),
            Path("data/features/nose-descriptor-minilm.npz"), Path("data/features/nose-descriptor-minilm.json"))},
        "task_universe_sha256": digest(ctx.universe), "settings_sha256": digest(ctx.cfg),
        "task_blocks": {name: array_identity(ctx.B[name]) for name in ("transport", "hbond", "chain", "osmophore")},
        "restricted_training_features": array_identity(raw), "training_ids_sha256": digest(ids.tolist()),
        "training_targets": array_identity(y), "dependencies": dependency_versions(), "code_sha256": hashes,
        "feature_schema": [list(item) for item in CONTINUOUS]+[["osmophore", name] for name in block_names("osmophore")]}


def cohort(ctx):
    tr, va, te = random_split(len(ctx.thr), FRACTIONS["abraham"], 42)
    all_ids = ctx.thr.molecule_id.to_numpy()
    ids, held = all_ids[tr], all_ids[np.r_[va, te]]
    y = ctx.thr.y.to_numpy()[tr]
    rows = ctx.rows(ids)
    columns = [ctx.B[block][rows, block_names(block).index(name)] for block, name in CONTINUOUS]
    raw = np.column_stack(columns+[ctx.B["osmophore"][rows]])
    if len(ids) != 111 or len(set(ids)) != 111 or not np.isfinite(y).all():
        raise ValueError("Original threshold split-42 training cohort changed")
    return ids, held, y, raw


def physics_checkpoints(ctx, out, ids, held, y, raw, resource_sha, resume):
    groups = np.array([str(i).split("-")[0] for i in ids])
    predictions = {name: np.full((3, len(ids)), np.nan) for name in CANDIDATES}
    fold_records = []
    for repeat in range(3):
        coverage = np.zeros(len(ids), dtype=int)
        for fold, (a, b) in enumerate(GroupKFold(5, shuffle=True, random_state=100+repeat).split(ids, groups=groups)):
            if set(groups[a]) & set(groups[b]):
                raise ValueError("Physics outer folds share connectivity")
            identity = {"resource_sha256": resource_sha, "train_ids": ids[a].tolist(),
                "held_ids": np.r_[held, ids[b]].tolist(), "evaluate_ids": ids[b].tolist(),
                "train_targets": y[a].tolist(), "targets": y[b].tolist()}
            path = out/f"abraham-repeat-{repeat}-fold-{fold}.npz"
            if path.exists() and path.with_suffix(".json").exists():
                if not resume:
                    raise ValueError("Existing physics checkpoints require --resume")
                record = json.loads(path.with_suffix(".json").read_text())
                if record["identity"] != identity or record["sha256"] != file_digest(path):
                    raise ValueError("Physics checkpoint identity/checksum differs")
                with np.load(path, allow_pickle=False) as data:
                    values = {name: data[name].copy() for name in data.files}
            else:
                values, checks = {}, {}
                for interactions in (False, True):
                    transform, checks[str(interactions)] = verify_transform(raw[a], raw[b], interactions)
                    train, evaluate = transform.transform(raw[a]), transform.transform(raw[b])
                    for name, (wanted, alpha) in CANDIDATES.items():
                        if wanted != interactions:
                            continue
                        model = Ridge(alpha=alpha).fit(train, y[a])
                        values[name] = model.predict(evaluate)
                atomic_npz(path, **values)
                record = {"identity": identity, "sha256": file_digest(path), "transform_checks": checks,
                    "outer_connectivity_disjoint_verified": True, "fitted_at_utc": utc_now()}
                write_json(path.with_suffix(".json"), record)
            if set(values) != set(CANDIDATES):
                raise ValueError("Physics candidate names differ")
            for name, p in values.items():
                if p.shape != (len(b),) or not np.isfinite(p).all():
                    raise ValueError("Non-finite physics fold predictions")
                predictions[name][repeat, b] = p
            coverage[b] += 1
            fold_records.append(record)
            print(f"Physics repeat{repeat+1}/3 fold{fold+1}/5 complete", flush=True)
        if not np.all(coverage == 1):
            raise ValueError("Physics repeat training-only coverage differs")
        print(json.dumps({"repeat": repeat, "standalone_physics": {
            name: score(y, p[repeat]) for name, p in predictions.items()}}), flush=True)
    atomic_npz(out/"abraham-physics-oof.npz", ids=ids.astype(str), y=y, **predictions)
    write_json(out/"physics-folds.json", fold_records)
    write_json(out/"physics-results.json", {"status": "physics_complete_baseline_gate_pending",
        "resource_sha256": resource_sha, "original_training_rows": len(ids),
        "scores": {name: [score(y, p) for p in values] for name, values in predictions.items()},
        "main_validation_test_targets_scored": False, "reserved_targets_fitted_or_scored": False})
    return predictions


def compare(ctx, baseline, baseline_plan, out, ids, held, y, predictions):
    audit = inspect_run(ctx, baseline)
    if not audit["source_archive"]["current_executable_code_matches_archive"]:
        raise ValueError("Current executable baseline code differs from archived source")
    write_json(out/"baseline-audit.json", {"observed_at_utc": utc_now(), "baseline": audit,
        "timing": "Baseline resource evidence audited after baseline fitting; physics resources pinned before physics fitting"})
    groups = np.array([str(i).split("-")[0] for i in ids])
    reference = np.full((3, len(ids)), np.nan)
    evidence = []
    for repeat in range(3):
        for fold, (a, b) in enumerate(GroupKFold(5, shuffle=True, random_state=100+repeat).split(ids, groups=groups)):
            path = baseline/f"abraham-repeat-{repeat}-fold-{fold}.npz"
            meta = path.with_suffix(".json")
            if not (path.exists() and meta.exists()):
                continue
            record = json.loads(meta.read_text())
            expected = {"train_ids": ids[a].tolist(), "held_ids": np.r_[held, ids[b]].tolist(),
                "evaluate_ids": ids[b].tolist(), "targets": y[b].tolist(), "code_sha256": baseline_plan["code_sha256"]}
            if record["identity"] != expected or record["sha256"] != file_digest(path):
                raise ValueError("Baseline changed after its cache/source/fold audit")
            with np.load(path, allow_pickle=False) as data:
                reference[repeat, b] = data["current"]
            evidence.append({"path": str(path), "sha256": record["sha256"], "repeat": repeat, "fold": fold})
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
            if gain.mean() >= .01 and (gain > 0).sum() >= 2 and np.mean([p["mae"] for p in rows]) <= np.mean([p["mae"] for p in scores["current"]]):
                passing.append(name)
        selected = max(passing, key=lambda name: np.mean([s["pearson"] for s in scores[name]])) if passing else "current"
        atomic_npz(out/"abraham-inner-oof.npz", ids=ids.astype(str), y=y, **values)
        summary.update({"scores": scores, "passing": passing, "selected": selected})
        write_json(out/"results.json", {"host": platform.node(), "results": {"abraham": summary},
            "main_validation_test_targets_scored": False, "reserved_targets_fitted_or_scored": False})
    write_json(out/"comparison-status.json", summary)
    print(json.dumps({"status": summary["status"], "baseline_verified_folds": len(evidence),
        "complete_repeats": whole, "passing": summary.get("passing"), "selected": summary.get("selected"),
        "scores_for_complete_repeats": summary["scores_for_complete_repeats"]}, indent=2), flush=True)


def main(args):
    if platform.node().lower() != os.environ.get("CALNEW_COMPUTE_HOST", "").lower():
        raise ValueError("Run this model study on SSH host compute-host only")
    torch.set_num_threads(2)
    out, baseline = Path(args.out), Path(args.baseline)
    if (out/"results.json").exists() or out.exists() and not args.resume:
        raise ValueError("Choose a fresh run or explicitly resume the incomplete experiment")
    out.mkdir(parents=True, exist_ok=True)
    baseline_plan, hashes = common_sources(baseline)
    plan = {"host": platform.node(), "scope": "Original split42 Abraham training111 only",
        "outer_cv": "Connectivity GroupKFold5, repeat seeds100/101/102", "threads": 2,
        "continuous_terms": [list(term) for term in CONTINUOUS], "osmophore_terms": block_names("osmophore"),
        "splines": {"degree": 2, "n_knots": 4, "knots": "uniform over outer-training extrema",
            "extrapolation": "linear", "include_bias": False},
        "candidates": {name: {"class_chain_logP_interactions": pair[0], "ridge_alpha": pair[1]} for name, pair in CANDIDATES.items()},
        "preprocessing": "Training-only median imputation, fitted spline knots, interaction axis scaling and final standardization",
        "blend": "Each candidate standalone and fixed50percent current-v2 blend",
        "selection": "MeanPearson gain>=.01, positive>=2of3 repeats, NOmeanMAEincrease; highest passing meanPearson",
        "baseline": str(baseline), "baseline_selection_plan_sha256": file_digest(baseline/"selection-plan.json"),
        "baseline_gate": "Deferred until all15 source/cache/checksum/ID/target audited baseline folds exist",
        "code_sha256": hashes, "main_validation_test_targets_scored": False,
        "reserved_targets_fitted_or_scored": False, "target_or_class_based_feature_tuning": False}
    if args.resume and json.loads((out/"selection-plan.json").read_text()) != plan:
        raise ValueError("Physics registration changed on resume")
    write_json(out/"selection-plan.json", plan)
    for relative, expected in hashes.items():
        dest = out/"source-code"/relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        if args.resume and dest.exists() and file_digest(dest) != expected:
            raise ValueError("Physics source archive changed")
        shutil.copy2(relative, dest)
    ctx = read_only_context(Path(json.loads(Path("data/current.json").read_text())["snapshot"]))
    ids, held, y, raw = cohort(ctx)
    identity = resources(ctx, hashes, ids, y, raw)
    if args.resume and json.loads((out/"resource-manifest.json").read_text())["identity"] != identity:
        raise ValueError("Physics resources changed on resume")
    if not args.resume:
        write_json(out/"resource-manifest.json", {"recorded_at_utc": utc_now(), "timing": "BEFORE physics fitting",
            "identity": identity, "resource_sha256": digest(identity)})
    predictions = physics_checkpoints(ctx, out, ids, held, y, raw, digest(identity), args.resume)
    compare(ctx, baseline, baseline_plan, out, ids, held, y, predictions)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="runs/nose-threshold-spline-grouped-inner-v1")
    parser.add_argument("--baseline", default="runs/nose-parity-threshold-water-inner-v2")
    parser.add_argument("--resume", action="store_true")
    with threadpool_limits(limits=2):
        main(parser.parse_args())
