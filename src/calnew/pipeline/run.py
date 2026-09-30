"""Train, evaluate and serve the modular pipeline.

Leakage control: stage-A (quality) meta-features for a molecule always come from a stage-A
model that never saw that molecule's structural group. For outer fold k, test rows use
A trained without fold k; training rows in fold j use A trained without folds {k, j}.
Downstream stages (B1, B2, C) are trained on fold != k only and scored on fold k.
"""
from __future__ import annotations

import importlib.metadata
import time
from pathlib import Path

import joblib
import numpy as np
import torch
from scipy.stats import pearsonr, spearmanr
from sklearn.metrics import average_precision_score, roc_auc_score

from ..chemistry import identify, nearest_similarity
from ..io import digest, read_json, write_json
from .blocks import EXPLICIT_BLOCKS, STRUCTURE_BLOCKS, BlockCache
from .data import load_stages
from .stages import (THRESHOLD_VARIANTS, CombinerStage, FlatBaseline, IntensityStage, QualityBaseline, QualityStage,
                     ThresholdStage, combine_mixture, quality_features, stack)

LOG3 = float(np.log10(3))


def _settings(anchor, fast):
    quality_blocks = list(STRUCTURE_BLOCKS) + (["unimol2"] if anchor == "unimol2" else [])
    potency_blocks = list(EXPLICIT_BLOCKS) + ["fingerprint", "quality"] + (["unimol2"] if anchor == "unimol2" else [])
    return {"anchor": anchor, "quality_blocks": quality_blocks, "potency_blocks": potency_blocks,
            "quality": {"seeds": (0,) if fast else (0, 1), "epochs": 20 if fast else 40},
            "threshold": {"seeds": (0, 1) if fast else (0, 1, 2, 3, 4), "epochs": 60 if fast else 120},
            "intensity": {"seeds": (0,) if fast else (0, 1, 2), "epochs": 80 if fast else 150},
            "combiner": {"epochs": 200 if fast else 400}}


# ------------------------------------------------------------------ metrics
def _regression(y, p):
    y, p = np.asarray(y, float), np.asarray(p, float)
    err = p - y
    out = {"n": len(y), "mae": float(np.mean(np.abs(err))), "rmse": float(np.sqrt(np.mean(err ** 2)))}
    if len(y) > 2 and np.std(y) > 0 and np.std(p) > 0:
        out["pearson"] = float(pearsonr(y, p).statistic)
        out["spearman"] = float(spearmanr(y, p).statistic)
    return out


def _threshold_metrics(y, p, fold):
    out = _regression(y, p)
    err = np.abs(np.asarray(p) - y)
    out["within_3x"], out["within_10x"] = float(np.mean(err <= LOG3)), float(np.mean(err <= 1.0))
    per_fold = [float(np.mean(err[fold == f])) for f in np.unique(fold)]
    out["fold_mae_mean"], out["fold_mae_se"] = float(np.mean(per_fold)), float(np.std(per_fold, ddof=1) / np.sqrt(len(per_fold)))
    return out


def _quality_metrics(y, p):
    ap, auc = [], []
    for j in range(y.shape[1]):
        mask = np.isfinite(y[:, j]) & np.isfinite(p[:, j])
        truth = y[mask, j]
        if len(np.unique(truth)) == 2:
            ap.append(average_precision_score(truth, p[mask, j]))
            auc.append(roc_auc_score(truth, p[mask, j]))
    return {"labels_scored": len(ap), "macro_average_precision": float(np.mean(ap)), "macro_auroc": float(np.mean(auc))}


def _profile_metrics(y, p, names):
    per = {}
    for j, name in enumerate(names):
        if np.std(y[:, j]) > 0 and np.std(p[:, j]) > 0:
            per[name] = float(pearsonr(y[:, j], p[:, j]).statistic)
    cos = np.sum(y * p, 1) / (np.linalg.norm(y, axis=1) * np.linalg.norm(p, axis=1) + 1e-9)
    return {"mean_descriptor_pearson": float(np.mean(list(per.values()))), "rmse": float(np.sqrt(np.mean((y - p) ** 2))),
            "mean_profile_cosine": float(np.mean(cos)), "per_descriptor_pearson": per}


# ------------------------------------------------------------------ training
def run_pipeline(snapshot: Path, reserved_runs: list[Path], out: Path, anchor="fingerprint", folds=5, fast=False,
                 cache_root=Path("data/features"), threads=8, log=print) -> dict:
    out = Path(out)
    if (out / "metrics.json").exists():
        raise ValueError(f"{out} already contains a completed run; use a new output directory")
    out.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(threads)
    started = time.time()
    cfg = _settings(anchor, fast)
    data = load_stages(snapshot, reserved_runs, folds=folds)
    ids = data.molecules.index.to_numpy()
    row = {m: i for i, m in enumerate(ids)}
    cache = BlockCache(cache_root)
    names = sorted(set(cfg["quality_blocks"]) | set(cfg["potency_blocks"]) - {"quality"})
    log(f"features: {names} for {len(ids)} molecules")
    B = cache.blocks(names, data.molecules.smiles.tolist())
    fold = np.array([data.folds[m] for m in ids])
    group = np.array([data.groups[m] for m in ids])

    q_rows = np.array([row[m] for m in data.quality["ids"]])
    q_y = data.quality["y"]
    t_rows = np.array([row[m] for m in data.threshold["molecule_ids"]])
    t_y = data.threshold["y"]
    p_rows = np.array([row[m] for m in data.panel["molecule_ids"]])
    p_x, p_int, p_pl, p_prof = data.panel["x"], data.panel["intensity"], data.panel["pleasantness"], data.panel["profile"]

    # Stage A learns two vocabularies: catalogue labels (Leffingwell) and the unit panel-descriptor
    # direction (Keller, averaged over dilutions). Unassessed entries stay NaN and are masked.
    labels_all = np.full((len(ids), q_y.shape[1]), np.nan)
    labels_all[q_rows] = q_y
    direction_all = np.full((len(ids), p_prof.shape[1]), np.nan)
    for r in np.unique(p_rows):
        v = p_prof[p_rows == r].mean(0)
        direction_all[r] = v / (np.linalg.norm(v) or 1.0)
    a_rows = np.flatnonzero(np.isfinite(labels_all).any(1) | np.isfinite(direction_all).all(1))
    qb = lambda rows: {n: B[n][rows] for n in cfg["quality_blocks"]}
    memo, quality_models = {}, {}

    def stage_a(excluded: frozenset):
        if excluded not in memo:
            keep = a_rows[~np.isin(fold[a_rows], list(excluded))]
            t = time.time()
            model = QualityStage(cfg["quality_blocks"], anchor, **cfg["quality"]).fit(qb(keep), labels_all[keep], direction_all[keep])
            probabilities, _, direction = model.predict(qb(np.arange(len(ids))))
            memo[excluded] = (probabilities, direction)
            quality_models[excluded] = model
            log(f"  stage A without folds {sorted(excluded)}: {time.time() - t:.0f}s")
        return memo[excluded]

    def meta(k):
        q = np.empty((len(ids), q_y.shape[1]), np.float32)
        d = np.empty((len(ids), p_prof.shape[1]), np.float32)
        for j in range(folds):
            rows = fold == j
            excluded = frozenset({j}) if k is None or j == k else frozenset({k, j})
            probabilities, direction = stage_a(excluded)
            q[rows], d[rows] = probabilities[rows], direction[rows]
        return q, d
    flat_targets = np.column_stack([p_int, p_pl, p_prof])
    flat_x = lambda rows, x: np.column_stack([stack({n: B[n][rows] for n in EXPLICIT_BLOCKS + ("fingerprint",)},
                                                    EXPLICIT_BLOCKS + ("fingerprint",)), x])

    oof = {"quality": np.full(q_y.shape, np.nan), "quality_baseline": np.full(q_y.shape, np.nan),
           "threshold": {}, "intensity": np.full(len(p_rows), np.nan), "intensity_sd": np.full(len(p_rows), np.nan),
           "hill": np.full((len(p_rows), 3), np.nan), "profile_oracle": np.full(p_prof.shape, np.nan),
           "profile_predicted": np.full(p_prof.shape, np.nan), "pleasant_oracle": np.full(len(p_rows), np.nan),
           "pleasant_predicted": np.full(len(p_rows), np.nan), "panel_direction": np.full(p_prof.shape, np.nan), "flat_ridge": np.full(flat_targets.shape, np.nan),
           "flat_trees": np.full(flat_targets.shape, np.nan)}
    gates = {}
    for k in range(folds):
        log(f"outer fold {k}")
        probabilities, D = meta(k)
        Q = quality_features(probabilities)
        Bk = {**B, "quality": Q}
        # A: quality on held-out fold
        te = fold[q_rows] == k
        oof["quality"][te] = stage_a(frozenset({k}))[0][q_rows[te]]
        base_x = lambda rows: stack({n: B[n][rows] for n in EXPLICIT_BLOCKS + ("fingerprint",)}, EXPLICIT_BLOCKS + ("fingerprint",))
        oof["quality_baseline"][te] = QualityBaseline().fit(base_x(q_rows[~te]), q_y[~te]).predict(base_x(q_rows[te]))
        gates[f"fold{k}_quality"] = quality_models[frozenset({k})].gates()
        # B1: threshold
        tr, te = fold[t_rows] != k, fold[t_rows] == k
        pick = lambda rows: {n: Bk[n][rows] for n in cfg["potency_blocks"]}
        threshold = ThresholdStage(cfg["potency_blocks"], anchor, **cfg["threshold"]).fit(pick(t_rows[tr]), t_y[tr], group[t_rows[tr]])
        for name, value in threshold.predict(pick(t_rows[te])).items():
            oof["threshold"].setdefault(name, np.full(len(t_y), np.nan))[te] = value
        oof["threshold"].setdefault("null_mean", np.full(len(t_y), np.nan))[te] = t_y[tr].mean()
        gates[f"fold{k}_threshold"] = [n.fusion.gates() for n in threshold.nets]
        # B2: intensity dose-response
        tr, te = fold[p_rows] != k, fold[p_rows] == k
        intensity = IntensityStage(cfg["potency_blocks"], anchor, **cfg["intensity"]).fit(pick(p_rows[tr]), p_x[tr], p_int[tr])
        mean, sd = intensity.predict(pick(p_rows[te]), p_x[te])
        oof["intensity"][te], oof["intensity_sd"][te] = mean, sd
        oof["hill"][te] = intensity.params(pick(p_rows[te])).mean(0)
        # C: combiner, teacher-forced on measured intensity
        oof["panel_direction"][te] = D[p_rows[te]]
        combiner = CombinerStage(**cfg["combiner"]).fit(Q[p_rows[tr]], p_int[tr], p_x[tr], p_prof[tr], p_pl[tr], group[p_rows[tr]],
                                                         prior=D[p_rows[tr]])
        gates[f"fold{k}_combiner"] = {"penalty": combiner.selected_penalty, "prior_weight": combiner.prior_weight}
        oof["profile_oracle"][te], oof["pleasant_oracle"][te] = combiner.predict(Q[p_rows[te]], p_int[te], p_x[te], D[p_rows[te]])
        oof["profile_predicted"][te], oof["pleasant_predicted"][te] = combiner.predict(Q[p_rows[te]], mean, p_x[te], D[p_rows[te]])
        # End-to-end baselines
        fx_tr, fx_te = flat_x(p_rows[tr], p_x[tr]), flat_x(p_rows[te], p_x[te])
        oof["flat_ridge"][te] = FlatBaseline("ridge").fit(fx_tr, flat_targets[tr], group[p_rows[tr]]).predict(fx_te)
        oof["flat_trees"][te] = FlatBaseline("extra_trees").fit(fx_tr, flat_targets[tr], group[p_rows[tr]]).predict(fx_te)

    # ------------------------------------------------------------ metrics
    descriptors = data.panel["descriptors"]
    t_fold = fold[t_rows]
    metrics = {
        "quality": {"pipeline_stage_A": _quality_metrics(q_y, oof["quality"]),
                    "logistic_explicit_fingerprint": _quality_metrics(q_y, oof["quality_baseline"]),
                    "panel_direction_cosine": float(np.mean(np.sum(oof["panel_direction"] * p_prof, 1) / np.linalg.norm(p_prof, axis=1))),
                    "mean_direction_cosine_baseline": float(np.mean(p_prof @ (p_prof.mean(0) / np.linalg.norm(p_prof.mean(0)))
                                                                    / np.linalg.norm(p_prof, axis=1)))},
        "threshold": {name: _threshold_metrics(t_y, p, t_fold) for name, p in oof["threshold"].items() if not name.endswith("_sd")},
        "intensity": {"pipeline_stage_B2_hill": _regression(p_int, oof["intensity"]),
                      "flat_ridge": _regression(p_int, oof["flat_ridge"][:, 0]),
                      "flat_extra_trees": _regression(p_int, oof["flat_trees"][:, 0])},
        "pleasantness": {"pipeline_oracle_intensity": _regression(p_pl, oof["pleasant_oracle"]),
                         "pipeline_predicted_intensity": _regression(p_pl, oof["pleasant_predicted"]),
                         "flat_ridge": _regression(p_pl, oof["flat_ridge"][:, 1]),
                         "flat_extra_trees": _regression(p_pl, oof["flat_trees"][:, 1])},
        "profile": {"pipeline_oracle_intensity": _profile_metrics(p_prof, oof["profile_oracle"], descriptors),
                    "pipeline_predicted_intensity": _profile_metrics(p_prof, oof["profile_predicted"], descriptors),
                    "flat_ridge": _profile_metrics(p_prof, oof["flat_ridge"][:, 2:], descriptors),
                    "flat_extra_trees": _profile_metrics(p_prof, oof["flat_trees"][:, 2:], descriptors)},
    }
    sd = oof["threshold"]["fusion_sd"]
    metrics["threshold"]["fusion"]["mean_predicted_sd"] = float(np.mean(sd))
    metrics["threshold"]["fusion"]["coverage_of_1.645sd"] = float(np.mean(np.abs(oof["threshold"]["fusion"] - t_y) <= 1.645 * sd))
    # Dose-response sanity: does the predicted curve rise between the two dilutions of the same molecule?
    mols = data.panel["molecule_ids"]
    rises = [(oof["intensity"][ix[np.argmax(p_x[ix])]] >= oof["intensity"][ix[np.argmin(p_x[ix])]])
             for m in np.unique(mols) for ix in [np.flatnonzero(mols == m)] if len(ix) > 1 and np.ptp(p_x[ix]) > 0]
    metrics["intensity"]["pipeline_stage_B2_hill"]["monotone_pairs_fraction"] = float(np.mean(rises)) if rises else None
    log("final fit on all usable development molecules")

    # ------------------------------------------------------------ final fit
    probabilities_f, Df = meta(None)
    Qf = quality_features(probabilities_f)
    Bf = {**B, "quality": Qf}
    pick = lambda rows: {n: Bf[n][rows] for n in cfg["potency_blocks"]}
    final_quality = QualityStage(cfg["quality_blocks"], anchor, **cfg["quality"]).fit(qb(a_rows), labels_all[a_rows], direction_all[a_rows])
    final = {
        "settings": cfg, "anchor": anchor, "labels": data.quality["labels"], "descriptors": descriptors,
        "quality": final_quality,
        "threshold": ThresholdStage(cfg["potency_blocks"], anchor, **cfg["threshold"]).fit(pick(t_rows), t_y, group[t_rows]),
        "intensity": IntensityStage(cfg["potency_blocks"], anchor, **cfg["intensity"]).fit(pick(p_rows), p_x, p_int),
        "combiner": CombinerStage(**cfg["combiner"]).fit(Qf[p_rows], p_int, p_x, p_prof, p_pl, group[p_rows], prior=Df[p_rows]),
        "training_smiles": {"quality": data.molecules.smiles.to_numpy()[q_rows].tolist(),
                            "threshold": data.molecules.smiles.to_numpy()[t_rows].tolist(),
                            "panel": data.molecules.smiles.to_numpy()[np.unique(p_rows)].tolist()},
        "threshold_abs_error_q90": float(np.quantile(np.abs(oof["threshold"]["ensemble"] - t_y), 0.9)),
        "intensity_abs_error_q90": float(np.quantile(np.abs(oof["intensity"] - p_int), 0.9)),
        "dilution_range": [float(p_x.min()), float(p_x.max())],
    }
    joblib.dump(final, out / "pipeline.joblib")
    np.savez_compressed(out / "oof-predictions.npz", quality=oof["quality"], quality_baseline=oof["quality_baseline"],
                        intensity=oof["intensity"], hill=oof["hill"], profile_predicted=oof["profile_predicted"],
                        profile_oracle=oof["profile_oracle"], flat_trees=oof["flat_trees"], flat_ridge=oof["flat_ridge"],
                        **{f"threshold_{k}": v for k, v in oof["threshold"].items()}, threshold_y=t_y, panel_x=p_x,
                        panel_intensity=p_int, panel_profile=p_prof, panel_ids=data.panel["ids"].astype(str))
    packages = {p: importlib.metadata.version(p) for p in ("calnew", "numpy", "torch", "rdkit", "scikit-learn")}
    manifest = {**data.manifest, "reserved": {k: (len(v) if isinstance(v, list) else v) for k, v in data.reserved.items()},
                "pipeline_test_accessed": False, "settings": {k: (list(v) if isinstance(v, tuple) else v) for k, v in cfg.items()},
                "packages": packages, "seconds": round(time.time() - started),
                "code_identity": digest({p.name: p.read_text() for p in sorted(Path(__file__).parent.glob("*.py"))})}
    write_json(out / "reserved-pipeline-test.json", {"note": "Reserved; not read by training or evaluation.",
                                                    "molecules": data.reserved["pipeline_test_molecules"],
                                                    "groups": data.reserved["pipeline_test_groups"]})
    write_json(out / "run.json", manifest)
    write_json(out / "gates.json", gates)
    write_json(out / "metrics.json", metrics)
    (out / "REPORT.md").write_text(render(metrics, manifest))
    log(f"done in {manifest['seconds']}s")
    return metrics


# ------------------------------------------------------------------ report
def _row(name, m, keys):
    return "| " + name + " | " + " | ".join("" if m.get(k) is None else f"{m[k]:.3f}" for k in keys) + " |"


def render(metrics, manifest) -> str:
    c = manifest["counts"]
    lines = [f"# Modular pipeline run ({manifest['settings']['anchor']} anchor)", "",
             f"Snapshot `{manifest['snapshot_id'][:16]}`; {manifest['folds']}-fold grouped CV over one global structural grouping. "
             f"Quality: {c['quality_molecules']} molecules x {c['quality_labels']} labels. Threshold: {c['threshold_observations']} air "
             f"observations. Panel: {c['panel_stimuli']} Keller stimuli from {c['panel_molecules']} molecules. "
             f"{manifest['reserved']['molecules_excluded_for_earlier_holdouts']} molecules excluded for earlier final tests; "
             f"{manifest['reserved']['pipeline_test_molecules']} reserved as the unopened pipeline test.", "",
             "## Stage A: quality (catalogue descriptors)", "", "| Model | macro AP | macro AUROC |", "|---|---:|---:|"]
    for name, m in metrics["quality"].items():
        if isinstance(m, dict):
            lines.append(_row(name, m, ["macro_average_precision", "macro_auroc"]))
    lines += ["", f"Panel-descriptor direction head (second vocabulary): held-out cosine {metrics['quality']['panel_direction_cosine']:.3f} "
              f"vs {metrics['quality']['mean_direction_cosine_baseline']:.3f} for the mean training direction.",
              "", "## Stage B1: air detection threshold, log10(ppbv)", "",
              "| Model | MAE | RMSE | Spearman | within 3x | within 10x | fold MAE (SE) |", "|---|---:|---:|---:|---:|---:|---:|"]
    for name, m in sorted(metrics["threshold"].items(), key=lambda kv: kv[1]["mae"]):
        lines.append(_row(name, m, ["mae", "rmse", "spearman", "within_3x", "within_10x"])[:-1] + f"| {m['fold_mae_mean']:.3f} ({m['fold_mae_se']:.3f}) |")
    lines += ["", "Ridge variants isolate the feature blocks: " + "; ".join(f"`{k}` = {'+'.join(v)}" for k, v in THRESHOLD_VARIANTS.items()) + ".",
              "", "## Stage B2: perceived intensity (Keller, 0-100)", "", "| Model | Pearson | RMSE |", "|---|---:|---:|"]
    for name, m in metrics["intensity"].items():
        lines.append(_row(name, m, ["pearson", "rmse"]))
    lines += ["", "## Stage C: combined descriptor profile and pleasantness", "",
              "| Model | mean descriptor r | profile cosine | profile RMSE | pleasantness r |", "|---|---:|---:|---:|---:|"]
    for name in metrics["profile"]:
        p, q = metrics["profile"][name], metrics["pleasantness"][name]
        lines.append(f"| {name} | {p['mean_descriptor_pearson']:.3f} | {p['mean_profile_cosine']:.3f} | {p['rmse']:.3f} | {q.get('pearson', float('nan')):.3f} |")
    lines += ["", "`oracle` feeds measured intensity into the combiner; `predicted` feeds stage-B2 output. The gap is the error "
              "propagated from the potency stage.", "", "## Limits", "",
              f"- Concentration axis: {manifest['concentration_axis']}.", f"- Profile targets: {manifest['profile_semantics']}.",
              "- Mixture combination (`combine_mixture`) is an analytic literature rule and is not validated by this run.",
              "- Out-of-fold metrics on development molecules only; the pipeline test partition was not read."]
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------ prediction
def predict(run: Path, smiles: list[str], dilution: float = 1e-3, mixture: bool = False, cache_root=Path("data/features")) -> dict:
    bundle = joblib.load(Path(run) / "pipeline.joblib")  # trusted local artifact (pickle)
    cfg = bundle["settings"]
    canonical = [identify(s).smiles for s in smiles]
    names = sorted(set(cfg["quality_blocks"]) | set(cfg["potency_blocks"]) - {"quality"})
    B = BlockCache(cache_root).blocks(names, canonical)
    probabilities, _, panel_direction = bundle["quality"].predict({n: B[n] for n in cfg["quality_blocks"]})
    Q = quality_features(probabilities)
    pb = {**{n: B[n] for n in names}, "quality": Q}
    potency = {n: pb[n] for n in cfg["potency_blocks"]}
    threshold = bundle["threshold"].predict(potency)
    x = np.full(len(canonical), np.log10(dilution))
    hill_params = bundle["intensity"].params(potency).mean(0)
    intensity, intensity_sd = bundle["intensity"].predict(potency, x)
    profile, pleasant = bundle["combiner"].predict(Q, intensity, x, panel_direction)
    directions = bundle["combiner"].direction(Q, panel_direction)
    lo, hi = bundle["dilution_range"]
    similarity = {k: nearest_similarity(canonical, v) for k, v in bundle["training_smiles"].items()}
    records = []
    for i, s in enumerate(canonical):
        top = np.argsort(-probabilities[i])[:6]
        records.append({
            "smiles": s, "molecule_id": identify(s).molecule_id,
            "quality": {"top_catalogue_labels": {bundle["labels"][j]: round(float(probabilities[i, j]), 3) for j in top},
                        "semantics": "ranking of catalogue (Leffingwell) descriptor records; positive-weighted, not calibrated"},
            "threshold": {"log10_ppbv": float(threshold["ensemble"][i]), "ppbv": float(10 ** threshold["ensemble"][i]),
                          "approx_90pct_log_interval": [float(threshold["ensemble"][i] - bundle["threshold_abs_error_q90"]),
                                                        float(threshold["ensemble"][i] + bundle["threshold_abs_error_q90"])],
                          "fusion_sd_log10": float(threshold["fusion_sd"][i])},
            "dose_response": {"I_max": float(hill_params[i, 0]), "x50_log10_dilution": float(hill_params[i, 1]), "slope": float(hill_params[i, 2])},
            "at_dilution": {"dilution": dilution, "in_trained_range": bool(lo <= x[i] <= hi), "intensity_0_100": float(intensity[i]),
                            "intensity_seed_sd": float(intensity_sd[i]), "pleasantness_0_100": float(pleasant[i]),
                            "profile": {d: round(float(v), 2) for d, v in zip(bundle["descriptors"], profile[i])}},
            "applicability": {f"nearest_tanimoto_{k}": float(v[i]) for k, v in similarity.items()},
            "_direction": directions[i].tolist(),
        })
    result = {"run": str(run), "anchor": bundle["anchor"], "molecules": records,
              "concentration_axis": "log10 solution dilution in paraffin oil (Keller protocol)"}
    if mixture:
        result["mixture"] = combine_mixture([{"hill": [r["dose_response"]["I_max"], r["dose_response"]["x50_log10_dilution"],
                                                       r["dose_response"]["slope"]], "x": np.log10(dilution),
                                              "direction": r["_direction"], "pleasantness": r["at_dilution"]["pleasantness_0_100"]}
                                             for r in records])
        result["mixture"]["profile_direction"] = dict(zip(bundle["descriptors"], np.round(result["mixture"]["direction"], 3).tolist()))
    for r in records:
        r.pop("_direction")
    return result
