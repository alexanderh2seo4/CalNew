"""Stage datasets, reserved-holdout exclusion and one global molecular grouping.

Every stage uses the same connectivity/structural groups over the union of molecules, so
out-of-fold meta-features and evaluation folds agree across stages. Molecules reserved as
final tests by earlier CALNEW runs are removed from every stage, and a new pipeline test
partition is reserved without being read.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

from ..chemistry import scaffold
from ..io import digest, read_json
from ..splits import partition_groups, structural_groups

KELLER_ATTRIBUTES = ("intensity", "pleasantness")
PROFILE_SEMANTICS = ("DREAM convention: per stimulus, sum of descriptor ratings divided by the number of participants who "
                     "rated intensity; a descriptor a participant did not select counts as zero applicability for that participant")


@dataclass
class StageData:
    quality: dict        # molecule-level catalogue labels
    threshold: dict      # observation-level air thresholds
    panel: dict          # stimulus-level Keller aggregates
    molecules: pd.DataFrame
    groups: dict         # molecule_id -> global group
    folds: dict          # molecule_id -> fold index (reserved molecules absent)
    reserved: dict
    manifest: dict


def _reserved_from_runs(runs: list[Path], snapshot_molecules: pd.DataFrame) -> tuple[set, set]:
    """Connectivity IDs and ring-scaffold groups held out as final tests by earlier runs."""
    connectivity, scaffolds = set(), set()
    old_obs = {}
    for run in runs:
        split = read_json(Path(run) / "split.json")
        identity = read_json(Path(run) / "run.json").get("identity", {})
        if "snapshot" not in identity:
            raise ValueError(f"Run {run} does not record its snapshot; cannot resolve its reserved test molecules")
        snapshot = Path(identity["snapshot"])
        rows = np.asarray(split["row_ids"])
        test = np.asarray(split["partitions"]["test"], dtype=int)
        ids = rows[test]
        if identity.get("endpoint") != "catalogue_descriptor":  # observation-level rows map to molecules
            if not (snapshot / "observations.parquet").exists():
                raise ValueError(f"Snapshot {snapshot} for run {run} is missing; cannot resolve reserved observations")
            key = str(snapshot)
            if key not in old_obs:
                old_obs[key] = pd.read_parquet(snapshot / "observations.parquet", columns=["observation_id", "molecule_id"]).set_index("observation_id").molecule_id
            ids = [old_obs[key].get(i, i) for i in ids]
        connectivity.update(str(i).split("-")[0] for i in ids)
        scaffolds.update(g for g in np.asarray(split["groups"])[test] if str(g).startswith("scaffold:"))
    return connectivity, scaffolds


def load_stages(snapshot: Path, reserved_runs: list[Path], folds: int = 5, seed: int = 42, pipeline_test_fraction: float = 0.15,
                min_label_positives: int = 20) -> StageData:
    snapshot = Path(snapshot)
    obs = pd.read_parquet(snapshot / "observations.parquet")
    molecules = pd.read_parquet(snapshot / "molecules.parquet").set_index("molecule_id")
    stimuli = pd.read_parquet(snapshot / "stimuli.parquet").set_index("stimulus_id")
    obs = obs[~obs.value_origin.isin(["predicted", "calculated"])]

    # Stage A: catalogue descriptors (single source head).
    cat = obs[(obs.endpoint == "catalogue_descriptor") & (obs.source_id == "leffingwell") & (obs.label_state != "not_assessed")]
    qmatrix = cat.pivot_table(index="molecule_id", columns="descriptor", values="value", aggfunc="first")

    # Stage B1: air thresholds, exact observations only (the imported table has no censoring).
    thr = obs[(obs.endpoint == "air_detection_threshold") & (obs.censoring == "exact")].sort_values("observation_id")

    # Stage B2/C: Keller stimulus aggregates.
    k = obs[obs.source_id == "keller_2016"]
    raters = k[k.endpoint == "intensity"].groupby("stimulus_id").subject_id.nunique()
    means = {a: k[k.endpoint == a].groupby("stimulus_id").value.mean() for a in KELLER_ATTRIBUTES}
    desc = k[(k.endpoint == "panel_descriptor") & ~k.descriptor.isin(["how familiar is the smell?", "the odor is:"])]
    descriptor_names = sorted(desc.descriptor.unique())
    sums = desc.groupby(["stimulus_id", "descriptor"]).value.sum().unstack().reindex(columns=descriptor_names).fillna(0.0)
    panel = pd.DataFrame(means).join(sums.div(raters.reindex(sums.index), axis=0))
    panel = panel[raters.reindex(panel.index) >= 10]
    panel["molecule_id"] = stimuli.loc[panel.index, "molecule_id"]
    panel["log10_dilution"] = np.log10(stimuli.loc[panel.index, "nominal_concentration"].astype(float))
    panel["raters"] = raters.reindex(panel.index)

    # Exclusions: earlier final tests (connectivity and ring scaffold).
    all_ids = sorted(set(qmatrix.index) | set(thr.molecule_id) | set(panel.molecule_id))
    reserved_conn, reserved_scaffolds = _reserved_from_runs(reserved_runs, molecules)
    mol = molecules.loc[all_ids]
    ring = {m: ("scaffold:" + scaffold(s)) if scaffold(s) else None for m, s in zip(mol.index, mol.smiles)}
    excluded = {m for m in all_ids if mol.at[m, "connectivity_id"] in reserved_conn or ring[m] in reserved_scaffolds}
    kept = [m for m in all_ids if m not in excluded]

    # One global structural grouping over the union of retained molecules.
    view = SimpleNamespace(groups=mol.loc[kept, "connectivity_id"].to_numpy(), smiles=mol.loc[kept, "smiles"].tolist())
    group_of = dict(zip(kept, structural_groups(view, "structural")))

    # Reserve a new pipeline test partition from groups containing panel molecules; never read here.
    panel_ids = [m for m in panel.molecule_id.unique() if m in group_of]
    panel_groups = np.array([group_of[m] for m in panel_ids])
    _, _, test_ix = partition_groups(panel_groups, (1 - 2 * pipeline_test_fraction, pipeline_test_fraction, pipeline_test_fraction), seed)
    pipeline_test_groups = set(panel_groups[test_ix])
    usable = [m for m in kept if group_of[m] not in pipeline_test_groups]

    # Greedy size balancing; scarce threshold/panel molecules weigh more so every fold can score them.
    scarce = set(thr.molecule_id) | set(panel.molecule_id)
    weight = {}
    for m in usable:
        weight[group_of[m]] = weight.get(group_of[m], 0) + (1 + 8 * (m in scarce))
    rng = np.random.default_rng(seed)
    unique = np.array(sorted(weight))
    order = rng.permutation(len(unique))
    order = order[np.argsort([-weight[unique[i]] for i in order], kind="stable")]
    load, fold_of_group = np.zeros(folds), {}
    for i in order:
        f = int(np.argmin(load))
        fold_of_group[unique[i]] = f
        load[f] += weight[unique[i]]
    fold_of = {m: int(fold_of_group[group_of[m]]) for m in usable}

    q = qmatrix.loc[[m for m in qmatrix.index if m in fold_of]]
    positives = (q == 1).sum()
    labels = sorted(positives[positives >= min_label_positives].index)
    q = q[labels]
    thr = thr[thr.molecule_id.isin(fold_of)]
    panel = panel[panel.molecule_id.isin(fold_of)]

    reserved = {"earlier_run_test_connectivity": len(reserved_conn), "earlier_run_test_scaffolds": len(reserved_scaffolds),
                "molecules_excluded_for_earlier_holdouts": len(excluded), "pipeline_test_groups": sorted(pipeline_test_groups),
                "pipeline_test_molecules": sorted(m for m in kept if group_of[m] in pipeline_test_groups)}
    manifest = {"snapshot": str(snapshot), "snapshot_id": read_json(snapshot / "manifest.json")["snapshot_id"],
                "reserved_runs": [str(r) for r in reserved_runs], "folds": folds, "seed": seed,
                "counts": {"quality_molecules": len(q), "quality_labels": len(labels), "threshold_observations": len(thr),
                           "threshold_molecules": int(thr.molecule_id.nunique()), "panel_stimuli": len(panel),
                           "panel_molecules": int(panel.molecule_id.nunique()), "usable_molecules": len(usable)},
                "panel_descriptors": descriptor_names, "profile_semantics": PROFILE_SEMANTICS,
                "concentration_axis": "log10 solution dilution in paraffin oil (not gas-phase concentration)"}
    manifest["pipeline_split_id"] = digest({"folds": fold_of, "reserved": reserved["pipeline_test_groups"]})
    return StageData(
        quality={"ids": q.index.to_numpy(), "y": q.to_numpy(float), "labels": labels},
        threshold={"ids": thr.observation_id.to_numpy(), "molecule_ids": thr.molecule_id.to_numpy(), "y": thr.value.to_numpy(float),
                   "unit": "log10(ppbv)"},
        panel={"ids": panel.index.to_numpy(), "molecule_ids": panel.molecule_id.to_numpy(), "x": panel.log10_dilution.to_numpy(float),
               "intensity": panel.intensity.to_numpy(float), "pleasantness": panel.pleasantness.to_numpy(float),
               "profile": panel[descriptor_names].to_numpy(float), "descriptors": descriptor_names, "raters": panel.raters.to_numpy()},
        molecules=molecules.loc[usable, ["smiles", "connectivity_id"]], groups={m: group_of[m] for m in usable}, folds=fold_of,
        reserved=reserved, manifest=manifest)
