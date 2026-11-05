"""Audit parity evidence and protocol boundaries on SSH, without fitting models."""
import json
import platform
from pathlib import Path

import numpy as np
from scipy.stats import pearsonr
from sklearn.metrics import r2_score

from calnew.io import file_digest, write_json
from calnew.pipeline.paper_benchmark import Context, FRACTIONS, random_split
from nose_semantic_experiment import RESERVED

# Full precision in NOSE v2 Appendix A.9, Tables 24/25/27/29/31.
REFERENCES = {
    "threshold_abraham": {"pearson": .836, "mae": .711, "r2": .652, "mse": .778},
    "pleasantness_keller": {"pearson": .715, "mae": 6.911, "r2": .488, "mse": 89.280},
    "intensity_keller": {"pearson": .418, "mae": 12.932, "r2": .156, "mse": 269.902},
    "intensity_ravia": {"pearson": .485, "mae": 11.078, "r2": .220, "mse": 216.326},
    "descriptor_strength_keller": {"pearson": .348, "mae": 5.862, "r2": .075, "mse": 67.161},
}


def score(y, p):
    if y.shape != p.shape or not np.isfinite(y).all() or not np.isfinite(p).all():
        raise ValueError("Non-finite/misaligned saved predictions")
    return {"pearson": float(pearsonr(y, p).statistic), "mae": float(np.abs(y-p).mean()),
        "r2": float(r2_score(y, p)), "mse": float(np.square(y-p).mean())}


def saved_predictions(run, key, frame, endpoint, fractions):
    root = Path("runs")/run
    records = []
    for split in range(42, 52):
        path = root/f"split-{split}.npz"
        with np.load(path, allow_pickle=False) as data:
            _, _, te = random_split(len(frame), fractions, split)
            expected_ids = frame.molecule_id.to_numpy()[te]
            expected_y = frame[endpoint].to_numpy()[te]
            if not np.array_equal(data["ids"], expected_ids) or not np.array_equal(data["y"], expected_y):
                raise ValueError("Saved benchmark test IDs or targets changed")
            records.append({"split": split, "n": len(data["y"]), "sha256": file_digest(path),
                "scores": score(data["y"], data[key])})
    return {"source": str(root), "predictions_verified": True, "original_test_ids_and_targets_verified": True,
        "metrics": {name: {"mean": float(np.mean([r["scores"][name] for r in records])),
            "sd": float(np.std([r["scores"][name] for r in records]))} for name in REFERENCES["threshold_abraham"]},
        "per_split": records}


def main():
    ctx = Context(Path(json.loads(Path("data/current.json").read_text())["snapshot"]), RESERVED)
    report = {"host": platform.node(), "paper": {"version": "2604.10452v2", "precision": "Appendix A.9",
        "url": "https://arxiv.org/html/2604.10452v2#A9", "references": REFERENCES},
        "original_train_only": {}, "validation_refit": {}, "separate_protocols": {}, "development_connectivity_overlaps": {}}
    for label, run in (("original_train_only", "nose-protocol-v4"), ("validation_refit", "nose-development-refit-v1")):
        path = Path("runs")/run/"results.json"
        data = json.loads(path.read_text())
        for task in REFERENCES:
            result = data["robustness"][task]["pipeline_v2"]
            metrics = {"pearson": {"mean": result[0], "sd": result[1]}} if isinstance(result, list) else {
                "pearson": {"mean": result["pearson_mean_per_descriptor"][0], "sd": result["pearson_mean_per_descriptor"][1]},
                "mae": {"mean": result["mae"][0], "sd": result["mae"][1]}}
            report[label][task] = {"source": str(path), "sha256": file_digest(path),
                "metrics": metrics, "predictions_verified": False, "retained_evidence": "Saved benchmark metric summaries; raw task prediction arrays not retained"}
    for label, refit in (("original_train_only", False), ("validation_refit", True)):
        report[label]["pleasantness_keller"] = saved_predictions(
            "nose-semantic-pleasantness-refit-v3" if refit else "nose-semantic-pleasantness-v3", "v3_seed_42",
            ctx.keller, "pleasantness", FRACTIONS["keller"])
        for task, run in (("intensity_keller", "nose-intensity-keller-refit-v3" if refit else "nose-intensity-keller-v3"),
                ("intensity_ravia", "nose-intensity-ravia-joint-refit-v2" if refit else "nose-intensity-ravia-joint-v2")):
            frame, endpoint, fractions = (ctx.keller, "intensity", FRACTIONS["keller"]) if task == "intensity_keller" else (ctx.ravia, "y", FRACTIONS["ravia"])
            report[label][task] = saved_predictions(run, "selected", frame, endpoint, fractions)
        for task, value in report[label].items():
            value["meets_exact_paper_pearson_point_estimate"] = value["metrics"]["pearson"]["mean"] >= REFERENCES[task]["pearson"]
            value["pearson_difference"] = value["metrics"]["pearson"]["mean"]-REFERENCES[task]["pearson"]
    path = Path("runs/nose-threshold-grouped-tenfold-v2/results.json")
    report["separate_protocols"]["threshold_grouped_tenfold"] = {"source": str(path), "sha256": file_digest(path), **json.loads(path.read_text())}
    for name, frame in (("abraham", ctx.thr), ("keller", ctx.keller), ("ravia", ctx.ravia)):
        ids = frame.molecule_id.to_numpy()
        conns = np.array([str(i).split("-")[0] for i in ids])
        records = {}
        for split in range(42, 52):
            tr, va, te = random_split(len(ids), FRACTIONS[name], split)
            train_test = sorted(set(conns[tr]) & set(conns[te]))
            train_validation = sorted(set(conns[tr]) & set(conns[va]))
            validation_test = sorted(set(conns[va]) & set(conns[te]))
            if train_test or train_validation or validation_test:
                records[str(split)] = {"train_test": train_test, "train_validation": train_validation,
                    "validation_test": validation_test,
                    "refit_train_test": sorted(set(conns[np.r_[tr, va]]) & set(conns[te]))}
        report["development_connectivity_overlaps"][name] = records
    report["new_training_only_trials"] = {}
    for run in ("nose-parity-pleasantness-grouped-inner-v2", "nose-parity-threshold-water-inner-v2"):
        root = Path("runs")/run
        if not (root/"results.json").exists():
            report["new_training_only_trials"][run] = {"status": "incomplete", "completed_fold_checkpoints": len(list(root.glob("*-fold-*.npz")))}
            continue
        result = json.loads((root/"results.json").read_text())
        record = {"status": "complete", "host": result["host"], "results_sha256": file_digest(root/"results.json"), "datasets": {}}
        for name, values in result["results"].items():
            record["datasets"][name] = {"selected": values["selected"], "passing": values["passing"],
                "mean_scores": {model: {metric: float(np.mean([s[metric] for s in scores])) for metric in ("pearson", "mae", "rmse")}
                    for model, scores in values["scores"].items()}}
        report["new_training_only_trials"][run] = record
    report["completion_audit"] = {"original_train_only_five_task_pearson": all(
        value["meets_exact_paper_pearson_point_estimate"] for value in report["original_train_only"].values()),
        "shared_data_reproduction": False, "all_eleven_paper_tasks_evaluated": False,
        "all_reported_metrics_verified": False, "reserved_targets_fitted_or_scored": False,
        "reason": "Original train-only threshold/pleasantness gaps remain; data/targets/splits differ; other paper tasks and some metrics are missing"}
    write_json(Path("runs/nose-parity-current-audit-20261002.json"), report)
    small = {k: {task: record["metrics"] for task, record in report[k].items()}
        for k in ("original_train_only", "validation_refit")}
    small["development_connectivity_overlaps"] = report["development_connectivity_overlaps"]
    small["completion_audit"] = report["completion_audit"]
    small["new_training_only_trials"] = report["new_training_only_trials"]
    print(json.dumps(small, indent=2), flush=True)


if __name__ == "__main__":
    main()
