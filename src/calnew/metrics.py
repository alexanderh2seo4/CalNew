"""Metrics report support explicitly; undefined estimates are not zeros."""
from __future__ import annotations

import warnings

import numpy as np
from scipy.stats import spearmanr
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, mean_absolute_error, roc_auc_score


def evaluate(y, prediction, task: str, labels: list[str] | None = None) -> dict:
    y, prediction = np.asarray(y), np.asarray(prediction)
    if y.shape != prediction.shape:
        raise ValueError("Prediction shape must match labels")
    per_label = {}
    for j in range(y.shape[1]):
        mask = np.isfinite(y[:, j]) & np.isfinite(prediction[:, j])
        truth, pred = y[mask, j], prediction[mask, j]
        name = labels[j] if labels else str(j)
        result = {"n": len(truth)}
        if not len(truth):
            result["status"] = "unavailable"
        elif task == "classification":
            p = np.clip(pred, 1e-7, 1-1e-7)
            result.update(positives=int(truth.sum()), negatives=int((1-truth).sum()),
                          brier=float(brier_score_loss(truth, p)), log_loss=float(log_loss(truth, p, labels=[0, 1])))
            if len(np.unique(truth)) == 2:
                result.update(average_precision=float(average_precision_score(truth, p)), auroc=float(roc_auc_score(truth, p)))
            else:
                result.update(average_precision=None, auroc=None, ranking_status="undefined_single_class")
        else:
            result.update(mae=float(mean_absolute_error(truth, pred)), rmse=float(np.sqrt(np.mean((truth-pred)**2))))
            result["spearman"] = float(spearmanr(truth, pred).statistic) if len(truth)>2 and np.std(truth)>0 and np.std(pred)>0 else None
        per_label[name] = result
    metric = "average_precision" if task == "classification" else "mae"
    values = [v[metric] for v in per_label.values() if v.get(metric) is not None]
    result = {"task": task, "primary_metric": "macro_"+metric, "primary": float(np.mean(values)) if values else None,
              "supported_labels": len(values), "total_labels": y.shape[1], "per_label": per_label}
    if task == "classification":
        mask = np.isfinite(y) & np.isfinite(prediction)
        if len(np.unique(y[mask])) == 2:
            result["micro_average_precision"] = float(average_precision_score(y[mask], prediction[mask]))
        result["brier"] = float(np.mean((y[mask]-prediction[mask])**2)) if mask.any() else None
    return result


def paired_group_bootstrap(y, a, b, groups, task: str, repeats=1000, seed=42) -> dict:
    """Positive differences mean A improves on B; sample molecular groups."""
    rng = np.random.default_rng(seed)
    unique = np.unique(groups)
    indices = [np.flatnonzero(groups == g) for g in unique]
    delta = []
    for _ in range(repeats):
        ix = np.concatenate([indices[j] for j in rng.integers(len(indices), size=len(indices))])
        ea, eb = evaluate(y[ix], a[ix], task)["primary"], evaluate(y[ix], b[ix], task)["primary"]
        if ea is not None and eb is not None:
            delta.append((ea-eb) if task == "classification" else (eb-ea))
    if not delta:
        return {"status": "unavailable", "reason": "No evaluable bootstrap samples"}
    return {"mean_improvement": float(np.mean(delta)), "ci95": np.quantile(delta,[.025,.975]).tolist(),
            "resampling_unit": "molecule_connectivity", "repeats": len(delta)}


def interval_metrics(y, lower, upper) -> dict:
    mask = np.isfinite(y) & np.isfinite(lower) & np.isfinite(upper)
    if not mask.any():
        return {"status": "unavailable"}
    return {"n": int(mask.sum()), "coverage": float(np.mean((y[mask]>=lower[mask]) & (y[mask]<=upper[mask]))),
            "mean_width": float(np.mean(upper[mask]-lower[mask]))}


def selective_error(y, prediction, uncertainty, task, coverages=(1.0,.75,.5,.25)):
    scores = np.nanmean(uncertainty, axis=1)
    ordering = np.argsort(scores)
    return [{"retained_fraction": f, **evaluate(y[ordering[:max(1,int(len(y)*f))]], prediction[ordering[:max(1,int(len(y)*f))]], task)} for f in coverages]

