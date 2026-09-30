"""Evaluate the modular pipeline with the NOSE downstream protocol (arXiv:2604.10452, Tables 3, 4, 10).

Protocol reproduced: random molecule-level splits fixed with seed 42, the paper's train/val/test
ratios (thresholds 160/54/54 = 60/20/20; Keller and Ravia 80/10/10), three model seeds (42-44),
test-set Pearson (and MAE for descriptor strength), reported as mean (sd).

Deliberate differences, all recorded in the output:
- CALNEW's reserved final tests and the pipeline test partition stay closed, so every dataset
  is smaller than in the paper (e.g. Abraham 186 vs 268).
- Keller molecule targets use each molecule's higher-concentration stimulus; descriptor
  strength covers the 20 semantic descriptors (the paper's 21-dim target is not specified).
- Ravia uses published group means at each molecule's most concentrated dilution
  (178 molecules in the public files vs 248 in the paper).
- Models train on the train split only; the validation split is not used (no early stopping).
- Threshold tree members also train on Li et al. 2025 water thresholds (CC BY 4.0) as flagged
  auxiliary rows; rows of the split's validation/test molecules and of reserved molecules are dropped.
Random splits are easier than CALNEW's structural splits; these numbers are not comparable
with the structural cross-validation results in docs/PIPELINE.md.
"""
from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from scipy.stats import pearsonr

from ..chemistry import identify, scaffold
from ..io import digest, write_json
from ..models.classical import tanimoto
from .blocks import EXPLICIT_BLOCKS, BlockCache
from .auxiliary import exclude_touching, load_li_2025
from .data import exclude_reserved as _exclude_reserved, load_stages
from .run import _settings
from .stages import (HEDONIC_MEMBERS, RAVIA_MEMBERS, THRESHOLD_MEMBERS, CombinerStage, FlatBaseline, GroupedRidge, IntensityStage,
                     QualityStage, TabularEnsemble, ThresholdStage, quality_features, stack)

# Published NOSE Table 3 / Table 4 test-set values, mean (sd) over seeds 42-44.
PAPER = {
    "threshold_abraham": {"NOSE": (0.84, 0.03), "ChemBERTa": (0.81, 0.02), "POM": (0.79, 0.02), "Uni-Mol": (0.78, 0.05),
                          "GIN": (0.72, 0.02), "Morgan": (0.60, 0.18), "AttentiveFP": (0.59, 0.35), "GCN": (0.22, 0.09)},
    "pleasantness_keller": {"NOSE": (0.71, 0.05), "Uni-Mol": (0.68, 0.02), "POM": (0.68, 0.03), "ChemBERTa": (0.65, 0.04),
                            "AttentiveFP": (0.52, 0.05), "Morgan": (0.51, 0.03), "GCN": (0.43, 0.01), "GIN": (0.30, 0.04)},
    "intensity_keller": {"NOSE": (0.42, 0.01), "ChemBERTa": (0.39, 0.07), "AttentiveFP": (0.33, 0.01), "POM": (0.32, 0.07),
                         "Uni-Mol": (0.27, 0.03), "GCN": (0.11, 0.05), "GIN": (0.06, 0.14), "Morgan": (0.05, 0.02)},
    "intensity_ravia": {"NOSE": (0.49, 0.03), "ChemBERTa": (0.47, 0.06), "AttentiveFP": (0.47, 0.00), "POM": (0.32, 0.06),
                        "Uni-Mol": (0.31, 0.02), "GIN": (0.19, 0.11), "GCN": (0.19, 0.01), "Morgan": (0.10, 0.19)},
    "descriptor_strength_keller": {"NOSE": (0.348, 0.060), "Uni-Mol": (0.330, 0.050), "ChemBERTa": (0.330, 0.089),
                                   "AttentiveFP": (0.327, 0.065), "POM": (0.314, 0.039), "Morgan": (0.244, 0.023),
                                   "GCN": (0.171, 0.006), "GIN": (0.128, 0.007)},
}
PAPER_MAE = {"descriptor_strength_keller": {"NOSE": 5.862, "ChemBERTa": 6.110, "AttentiveFP": 6.232, "GCN": 6.247, "POM": 6.304,
                                            "Morgan": 6.483, "GIN": 6.528, "Uni-Mol": 6.741}}
PAPER_N = {"threshold_abraham": 268, "pleasantness_keller": 474, "intensity_keller": 474, "descriptor_strength_keller": 474,
           "intensity_ravia": 248}
FRACTIONS = {"abraham": (0.6, 0.2, 0.2), "keller": (0.8, 0.1, 0.1), "ravia": (0.8, 0.1, 0.1)}


def random_split(n, fractions, seed=42):
    order = np.random.default_rng(seed).permutation(n)
    # floor(train), round(val), rest = test reproduces the paper's Table 10 sizes (160/54/54, 379/47/48, 198/25/25).
    a = int(np.floor(fractions[0] * n))
    b = a + int(round(fractions[1] * n))
    return order[:a], order[a:b], order[b:]


def _pearson(y, p):
    return float(pearsonr(y, p).statistic) if np.std(y) > 0 and np.std(p) > 0 else float("nan")


def _descriptor_scores(y, p):
    per = [_pearson(y[:, j], p[:, j]) for j in range(y.shape[1])]
    return {"pearson_mean_per_descriptor": float(np.nanmean(per)), "pearson_flattened": _pearson(y.ravel(), p.ravel()),
            "mae": float(np.mean(np.abs(y - p)))}


def _ravia_table(snapshot: Path, molecules: pd.DataFrame) -> pd.DataFrame:
    obs = pd.read_parquet(snapshot / "observations.parquet")
    stim = pd.read_parquet(snapshot / "stimuli.parquet").set_index("stimulus_id")
    r = obs[(obs.source_id == "ravia_2020") & (obs.endpoint == "intensity")].copy()
    if r.empty:
        raise ValueError("Ravia 2020 is not in this snapshot; run `calnew fetch/ingest ravia_2020` and `calnew snapshot`")
    conc = stim.loc[r.stimulus_id]
    # Undiluted and solid presentations rank as the most concentrated.
    r["fraction"] = np.where(conc.concentration_basis.to_numpy() == "solid_undiluted", 1.0, conc.nominal_concentration.to_numpy(float))
    r = r[np.isfinite(r.fraction) & (r.fraction > 0)]
    top = r.groupby("molecule_id").fraction.transform("max")
    target = r[r.fraction == top].groupby("molecule_id").value.mean()
    return pd.DataFrame({"molecule_id": target.index, "y": target.to_numpy(),
                         "smiles": molecules.loc[target.index, "smiles"].to_numpy()})


class Context:
    """Task tables, feature blocks and stage-A training material shared by every evaluation."""

    def __init__(self, snapshot: Path, reserved_runs, cache_root=Path("data/features")):
        self.snapshot = snapshot = Path(snapshot)
        self.cfg = cfg = _settings("fingerprint", fast=False)
        self.data = data = load_stages(snapshot, reserved_runs)
        self.all_molecules = all_molecules = pd.read_parquet(snapshot / "molecules.parquet").set_index("molecule_id")

        # Task tables (non-reserved molecules only).
        thr = pd.DataFrame({"molecule_id": data.threshold["molecule_ids"], "y": 3 - data.threshold["y"]})  # log(1/ODT[ppm])
        thr["smiles"] = all_molecules.loc[thr.molecule_id, "smiles"].to_numpy()
        panel = pd.DataFrame({"molecule_id": data.panel["molecule_ids"], "x": data.panel["x"], "intensity": data.panel["intensity"],
                              "pleasantness": data.panel["pleasantness"]})
        self.prof = prof = data.panel["profile"]
        high = panel.groupby("molecule_id").x.transform("max").to_numpy() == panel.x.to_numpy()
        keller = panel[high].drop_duplicates("molecule_id").copy()
        self.keller_profile = prof[np.flatnonzero(high)][~panel[high].duplicated("molecule_id").to_numpy()]
        keller["smiles"] = all_molecules.loc[keller.molecule_id, "smiles"].to_numpy()
        ravia = _exclude_reserved(_ravia_table(snapshot, all_molecules), data, reserved_runs, all_molecules)
        self.thr, self.keller, self.ravia = thr, keller, ravia

        # Features for every molecule involved (quality-model training set + all task molecules).
        self.universe = universe = list(dict.fromkeys(list(data.molecules.index) + list(ravia.molecule_id)))
        self.row = row = {m: i for i, m in enumerate(universe)}
        self.smiles = all_molecules.loc[universe, "smiles"].tolist()
        names = sorted(set(cfg["quality_blocks"]) | set(cfg["potency_blocks"]) - {"quality"} | {"rdkit", "unimol2"})
        self.B = BlockCache(cache_root).blocks(names, self.smiles)
        self.connectivity = np.array([m.split("-")[0] for m in universe])

        # Stage-A training material: catalogue labels + Keller panel directions (as in run_pipeline).
        self.labels = labels = np.full((len(universe), data.quality["y"].shape[1]), np.nan)
        labels[[row[m] for m in data.quality["ids"]]] = data.quality["y"]
        self.direction = direction = np.full((len(universe), prof.shape[1]), np.nan)
        self.p_rows = p_rows = np.array([row[m] for m in data.panel["molecule_ids"]])
        for r in np.unique(p_rows):
            v = prof[p_rows == r].mean(0)
            direction[r] = v / (np.linalg.norm(v) or 1.0)
        self.a_rows = np.flatnonzero(np.isfinite(labels).any(1) | np.isfinite(direction).all(1))

        # Training-only auxiliary rows for "+aux" members (water thresholds; never evaluated).
        self.aux = load_li_2025(data, reserved_runs, all_molecules)
        aux_names = sorted({n for kind, names in THRESHOLD_MEMBERS if kind.endswith("+aux") for n in names})
        self.aux_blocks = BlockCache(cache_root).blocks(aux_names, self.aux.smiles.tolist())

    def rows(self, ids):
        return np.array([self.row[m] for m in ids])

    def stage_a_features(self, train_ids, heldout_ids, seed):
        """OOF quality features for train molecules; held-out ones from A trained without any held-out molecule.
        Returns (catalogue logits, panel direction, fused embedding)."""
        cfg, conn, n = self.cfg, self.connectivity, len(self.universe)
        qb = lambda rows: {k: self.B[k][rows] for k in cfg["quality_blocks"]}
        held_conn = {i.split("-")[0] for i in heldout_ids}
        base = self.a_rows[~np.isin(conn[self.a_rows], list(held_conn))]
        q = np.zeros((n, self.labels.shape[1]), np.float32)
        d = np.zeros((n, self.direction.shape[1]), np.float32)
        e = None
        train_rows = self.rows(train_ids)
        fold = np.random.default_rng(seed).permutation(len(train_rows)) % 5
        settings = {**cfg["quality"], "seeds": (seed,)}
        for j in range(-1, 5):
            excluded = held_conn if j < 0 else held_conn | set(conn[train_rows[fold == j]])
            keep = base if j < 0 else base[~np.isin(conn[base], list(excluded))]
            model = QualityStage(cfg["quality_blocks"], "fingerprint", **settings).fit(qb(keep), self.labels[keep], self.direction[keep])
            probabilities, emb, dirs = model.predict(qb(np.arange(n)))
            e = np.zeros((n, emb.shape[1]), np.float32) if e is None else e
            target = self.rows(heldout_ids) if j < 0 else train_rows[fold == j]
            q[target], d[target], e[target] = quality_features(probabilities)[target], dirs[target], emb[target]
        return q, d, e


def run_paper_benchmark(snapshot: Path, reserved_runs, out: Path, model_seeds=(42, 43, 44), split_seed=42, robustness_splits=(43, 44, 45, 46),
                        cache_root=Path("data/features"), threads=8, log=print) -> dict:
    out = Path(out)
    if (out / "results.json").exists():
        raise ValueError(f"{out} already contains results; use a new output directory")
    out.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(threads)
    started = time.time()
    ctx = Context(snapshot, reserved_runs, cache_root)
    snapshot, cfg, data, B, row, connectivity = ctx.snapshot, ctx.cfg, ctx.data, ctx.B, ctx.row, ctx.connectivity
    thr, keller, ravia, keller_profile, prof, p_rows = ctx.thr, ctx.keller, ctx.ravia, ctx.keller_profile, ctx.prof, ctx.p_rows

    aux_used = []  # auxiliary rows each threshold fit actually used

    def stage_a_features(train_ids, heldout_ids, seed):
        return ctx.stage_a_features(train_ids, heldout_ids, seed)[:2]

    def tabular(members, seed, blocks, train_rows, y, test_rows, columns_train=None, columns_test=None, heldout_ids=None):
        pick = lambda rows: {n: blocks[n][rows] for _, names in members for n in names}
        auxiliary = None
        if heldout_ids is not None and any(kind.endswith("+aux") for kind, _ in members):
            keep = exclude_touching(ctx.aux, heldout_ids)  # no water row of a validation/test molecule
            auxiliary = ({n: v[keep] for n, v in ctx.aux_blocks.items()}, ctx.aux.y.to_numpy()[keep], 1.0)
        model = TabularEnsemble(members, seed=seed, threads=threads).fit(pick(train_rows), y, connectivity[train_rows], columns_train, auxiliary)
        if auxiliary is not None:
            aux_used.append(model.auxiliary_rows)
        return model.predict_members(pick(test_rows), columns_test)

    def evaluate(split_seed, model_seeds):
        results, splits = {}, {}
        task_frames = {"abraham": thr, "keller": keller, "ravia": ravia}
        for dataset, frame in task_frames.items():
            tr, va, te = random_split(len(frame), FRACTIONS[dataset], split_seed)
            splits[dataset] = {"n": len(frame), "train": len(tr), "val": len(va), "test": len(te),
                               "test_molecules": frame.molecule_id.to_numpy()[te].tolist()}
            train_ids, held_ids = frame.molecule_id.to_numpy()[tr], frame.molecule_id.to_numpy()[np.concatenate([va, te])]
            test_rows = np.array([row[m] for m in frame.molecule_id.to_numpy()[te]])
            train_rows = np.array([row[m] for m in train_ids])
            y_te = frame.y.to_numpy()[te] if "y" in frame else None
            for seed in model_seeds:
                t0 = time.time()
                torch.manual_seed(seed)
                q, d = stage_a_features(train_ids, held_ids, seed)
                Bq = {**B, "quality": q, "direction": d}
                pick = lambda rows: {n: Bq[n][rows] for n in cfg["potency_blocks"]}
                fp = lambda rows: B["fingerprint"][rows]
                ex = lambda rows: stack({n: B[n][rows] for n in EXPLICIT_BLOCKS + ("fingerprint",)}, EXPLICIT_BLOCKS + ("fingerprint",))
                groups_tr = connectivity[train_rows]
                seeds5 = tuple(seed * 10 + k for k in range(5))
                if dataset == "abraham":
                    y_tr = frame.y.to_numpy()[tr]
                    stage = ThresholdStage(cfg["potency_blocks"], "fingerprint", seeds=seeds5, epochs=cfg["threshold"]["epochs"]).fit(pick(train_rows), y_tr, groups_tr)
                    pred = stage.predict(pick(test_rows))
                    # v2: B1 ensemble averaged with descriptor-tree and fingerprint-ridge members.
                    v2 = np.column_stack([pred["ensemble"], tabular(THRESHOLD_MEMBERS, seed, Bq, train_rows, y_tr, test_rows,
                                                                    heldout_ids=held_ids)]).mean(1)
                    scores = {"pipeline_B1_ensemble": _pearson(y_te, pred["ensemble"]), "pipeline_v2": _pearson(y_te, v2),
                              "pipeline_B1_fusion": _pearson(y_te, pred["fusion"]),
                              "ridge_explicit_quality": _pearson(y_te, pred["ridge_explicit_quality"]),
                              "morgan_ridge": _pearson(y_te, GroupedRidge().fit(fp(train_rows), y_tr, groups_tr).predict(fp(test_rows))),
                              "explicit_fp_extra_trees": _pearson(y_te, FlatBaseline().fit(ex(train_rows), y_tr[:, None], groups_tr).predict(ex(test_rows)).ravel())}
                    results.setdefault("threshold_abraham", []).append(scores)
                elif dataset == "ravia":
                    y_tr = frame.y.to_numpy()[tr]
                    stage = IntensityStage(cfg["potency_blocks"], "fingerprint", seeds=(seed,), epochs=cfg["intensity"]["epochs"]).fit(
                        pick(train_rows), np.zeros(len(train_rows)), y_tr)
                    v2 = tabular(RAVIA_MEMBERS, seed, Bq, train_rows, y_tr, test_rows).mean(1)
                    scores = {"pipeline_B2": _pearson(y_te, stage.predict(pick(test_rows), np.zeros(len(test_rows)))[0]), "pipeline_v2": _pearson(y_te, v2),
                              "morgan_ridge": _pearson(y_te, GroupedRidge().fit(fp(train_rows), y_tr, groups_tr).predict(fp(test_rows))),
                              "explicit_fp_extra_trees": _pearson(y_te, FlatBaseline().fit(ex(train_rows), y_tr[:, None], groups_tr).predict(ex(test_rows)).ravel())}
                    results.setdefault("intensity_ravia", []).append(scores)
                else:
                    # Stages B2 and C train on every stimulus (both dilutions) of the training molecules.
                    train_set = set(train_ids)
                    sel = np.array([m in train_set for m in data.panel["molecule_ids"]])
                    s_rows = p_rows[sel]
                    x_tr, i_tr, pl_tr, pr_tr = data.panel["x"][sel], data.panel["intensity"][sel], data.panel["pleasantness"][sel], prof[sel]
                    x_te = frame.x.to_numpy()[te]
                    b2 = IntensityStage(cfg["potency_blocks"], "fingerprint", seeds=(seed,), epochs=cfg["intensity"]["epochs"]).fit(pick(s_rows), x_tr, i_tr)
                    i_pred = b2.predict(pick(test_rows), x_te)[0]
                    comb = CombinerStage(epochs=cfg["combiner"]["epochs"], seed=seed).fit(q[s_rows], i_tr, x_tr, pr_tr, pl_tr, connectivity[s_rows], prior=d[s_rows])
                    prof_pred, pl_pred = comb.predict(q[test_rows], i_pred, x_te, d[test_rows])
                    y_int, y_pl, y_prof = frame.intensity.to_numpy()[te], frame.pleasantness.to_numpy()[te], keller_profile[te]
                    # Molecule-level baselines on the same targets the paper uses.
                    fx_tr = np.column_stack([ex(train_rows), frame.x.to_numpy()[tr]])
                    fx_te = np.column_stack([ex(test_rows), x_te])
                    targets_tr = np.column_stack([frame.intensity.to_numpy()[tr], frame.pleasantness.to_numpy()[tr], keller_profile[tr]])
                    flat = FlatBaseline().fit(fx_tr, targets_tr, groups_tr).predict(fx_te)
                    morgan = FlatBaseline("ridge").fit(fp(train_rows), targets_tr, groups_tr).predict(fp(test_rows))
                    # v2 stage-C hedonic head: molecule-level trees on descriptors + stage-A outputs + dilution.
                    hedonic = tabular(HEDONIC_MEMBERS, seed, Bq, train_rows, frame.pleasantness.to_numpy()[tr], test_rows,
                                      frame.x.to_numpy()[tr][:, None], x_te[:, None]).mean(1)
                    results.setdefault("intensity_keller", []).append({"pipeline_B2": _pearson(y_int, i_pred), "pipeline_v2": _pearson(y_int, i_pred), "morgan_ridge": _pearson(y_int, morgan[:, 0]),
                                                                       "explicit_fp_extra_trees": _pearson(y_int, flat[:, 0])})
                    results.setdefault("pleasantness_keller", []).append({"pipeline_C": _pearson(y_pl, pl_pred), "pipeline_v2": _pearson(y_pl, hedonic), "morgan_ridge": _pearson(y_pl, morgan[:, 1]),
                                                                          "explicit_fp_extra_trees": _pearson(y_pl, flat[:, 1])})
                    results.setdefault("descriptor_strength_keller", []).append({"pipeline_C": _descriptor_scores(y_prof, prof_pred), "pipeline_v2": _descriptor_scores(y_prof, prof_pred),
                                                                                 "morgan_ridge": _descriptor_scores(y_prof, morgan[:, 2:]),
                                                                                 "explicit_fp_extra_trees": _descriptor_scores(y_prof, flat[:, 2:])})
                log(f"{dataset} seed {seed}: {time.time() - t0:.0f}s")


        return results, splits

    def summarise(results):
        summary = {}
        for task, runs in results.items():
            summary[task] = {}
            for model in runs[0]:
                if isinstance(runs[0][model], dict):
                    summary[task][model] = {k: (float(np.mean([r[model][k] for r in runs])), float(np.std([r[model][k] for r in runs])))
                                            for k in runs[0][model]}
                else:
                    values = [r[model] for r in runs]
                    summary[task][model] = (float(np.mean(values)), float(np.std(values)))
        return summary

    results, splits = evaluate(split_seed, model_seeds)
    summary = summarise(results)
    write_json(out / "partial" / f"split-{split_seed}.json", {"summary": summary, "per_seed": results})  # survives a later crash
    robustness_runs = {}
    for extra in robustness_splits:
        log(f"robustness split {extra}")
        extra_results, _ = evaluate(extra, (model_seeds[0],))
        write_json(out / "partial" / f"split-{extra}.json", {"per_seed": extra_results})
        for task, runs in extra_results.items():
            robustness_runs.setdefault(task, []).extend(runs)
    for task, runs in results.items():  # include the primary split's first model seed
        robustness_runs.setdefault(task, []).insert(0, runs[0])
    robustness = summarise(robustness_runs) if robustness_splits else {}
    manifest = {"protocol": "NOSE arXiv:2604.10452 downstream: random split seed %d, model seeds %s" % (split_seed, list(model_seeds)),
                "snapshot": str(snapshot), "splits": {k: {kk: vv for kk, vv in v.items() if kk != "test_molecules"} for k, v in splits.items()},
                "paper_n": PAPER_N, "reserved_holdouts_opened": False, "seconds": round(time.time() - started),
                "differences": __doc__.split("Deliberate differences, all recorded in the output:")[1].split("Random splits")[0].strip(),
                "split_id": digest({k: v["test_molecules"] for k, v in splits.items()}),
                "auxiliary": {"source": "Li et al. 2025 water ODT, Zenodo 10.5281/zenodo.17559514 (CC BY 4.0)",
                              "rows_after_reserved_exclusion": len(ctx.aux),
                              "rows_per_threshold_fit": [int(min(aux_used)), int(max(aux_used))] if aux_used else None}}
    manifest["robustness"] = f"split seeds {[split_seed] + list(robustness_splits)} with model seed {model_seeds[0]}" if robustness_splits else None
    write_json(out / "results.json", {"summary": summary, "robustness": robustness, "robustness_per_split": robustness_runs, "per_seed": results, "paper": PAPER, "paper_mae": PAPER_MAE, "manifest": manifest})
    write_json(out / "splits.json", splits)
    (out / "REPORT.md").write_text(render_paper(summary, manifest, robustness), encoding="utf-8")
    log(f"done in {manifest['seconds']}s")
    return summary


def _fmt(v):
    return f"{v[0]:.2f} ({v[1]:.2f})"


def render_paper(summary, manifest, robustness=None) -> str:
    names = {"threshold_abraham": "Threshold (Abraham)", "pleasantness_keller": "Pleasantness (Keller)", "intensity_keller": "Intensity (Keller)",
             "intensity_ravia": "Intensity (Ravia)", "descriptor_strength_keller": "Descriptor strength (Keller)"}
    lines = ["# Modular pipeline under the NOSE downstream protocol", "", manifest["protocol"] + ". Test-set Pearson, mean (sd) over model seeds.", "",
             "| Task | n here / paper | test n | Pipeline v1 | Pipeline v2 | Morgan ridge (ours) | Extra-trees explicit+FP (ours) | NOSE (paper) | Morgan (paper) | best other paper baseline |",
             "|---|---|---:|---:|---:|---:|---:|---:|---:|---|"]
    for task in ["threshold_abraham", "pleasantness_keller", "intensity_keller", "intensity_ravia", "descriptor_strength_keller"]:
        if task not in summary:
            continue
        s = summary[task]
        ds = task.split("_")[-1]
        split = manifest["splits"][ds]
        key = "pearson_mean_per_descriptor"
        pipe = [k for k in s if k.startswith("pipeline") and k != "pipeline_v2"][0]
        val = (lambda m: _fmt(s[m][key]) if isinstance(s[m], dict) else _fmt(s[m]))
        paper = PAPER[task]
        others = sorted(((k, v) for k, v in paper.items() if k not in ("NOSE", "Morgan")), key=lambda kv: -kv[1][0])[0]
        lines.append(f"| {names[task]} | {split['n']} / {manifest['paper_n'][task]} | {split['test']} | {val(pipe)} | {val('pipeline_v2') if 'pipeline_v2' in s else '—'} | {val('morgan_ridge')} | "
                     f"{val('explicit_fp_extra_trees')} | {_fmt(paper['NOSE'])} | {_fmt(paper['Morgan'])} | {others[0]} {_fmt(others[1])} |")
    if robustness:
        lines += ["", f"## Split robustness ({manifest['robustness']})", "",
                  "Mean (sd) over random splits. With the reduced datasets, test sets hold 11-38 molecules, so a single split is noisy.", "",
                  "| Task | Pipeline v1 | Pipeline v2 | Morgan ridge (ours) | Extra-trees explicit+FP (ours) | NOSE (paper, split 42) |", "|---|---:|---:|---:|---:|---:|"]
        for task in ["threshold_abraham", "pleasantness_keller", "intensity_keller", "intensity_ravia", "descriptor_strength_keller"]:
            if task in robustness:
                r = robustness[task]
                pipe = [k for k in r if k.startswith("pipeline") and k != "pipeline_v2"][0]
                v = (lambda m: _fmt(r[m]["pearson_mean_per_descriptor"]) if isinstance(r[m], dict) else _fmt(r[m]))
                lines.append(f"| {names[task]} | {v(pipe)} | {v('pipeline_v2') if 'pipeline_v2' in r else '—'} | {v('morgan_ridge')} | "
                             f"{v('explicit_fp_extra_trees')} | {_fmt(PAPER[task]['NOSE'])} |")
    if "descriptor_strength_keller" in summary:
        s = summary["descriptor_strength_keller"]
        lines += ["", "Descriptor strength, other aggregations (the paper does not define how Pearson is pooled over 21 dimensions):", "",
                  "| Model | Pearson mean per descriptor | Pearson flattened | MAE |", "|---|---:|---:|---:|"]
        for m, v in s.items():
            lines.append(f"| {m} | {_fmt(v['pearson_mean_per_descriptor'])} | {_fmt(v['pearson_flattened'])} | {v['mae'][0]:.2f} |")
        lines.append(f"| NOSE (paper) | {PAPER['descriptor_strength_keller']['NOSE'][0]:.3f} | — | {PAPER_MAE['descriptor_strength_keller']['NOSE']:.2f} |")
    if "pipeline_B1_fusion" in summary.get("threshold_abraham", {}):
        t = summary["threshold_abraham"]
        lines += ["", f"Threshold components: fusion {_fmt(t['pipeline_B1_fusion'])}, ridge explicit+quality {_fmt(t['ridge_explicit_quality'])}."]
    lines += ["", "## Differences from the paper", "", manifest["differences"], "",
              "The Morgan-ridge column is our reimplementation of the paper's weakest-feature baseline on the same reduced splits: "
              "comparing it with the paper's Morgan row shows how much the smaller, different datasets shift the scale.",
              "", "Random splits leak close analogues between train and test and are easier than CALNEW's structural splits; "
              "see docs/PIPELINE.md for the structural cross-validation results."]
    return "\n".join(lines) + "\n"
