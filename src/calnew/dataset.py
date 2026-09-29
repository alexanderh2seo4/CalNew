"""Task matrices retain missing labels and participant/context identifiers."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .io import digest, read_json


@dataclass
class TaskDataset:
    ids: np.ndarray
    smiles: list[str]
    groups: np.ndarray
    y: np.ndarray
    labels: list[str]
    task: str
    endpoint: str
    source_ids: np.ndarray
    lower: np.ndarray
    upper: np.ndarray
    censoring: np.ndarray
    metadata: dict

    def subset(self, indices) -> "TaskDataset":
        ix = np.asarray(indices, dtype=int)
        return TaskDataset(self.ids[ix], [self.smiles[i] for i in ix], self.groups[ix], self.y[ix], self.labels,
                           self.task, self.endpoint, self.source_ids[ix], self.lower[ix], self.upper[ix], self.censoring[ix], self.metadata)

    def signature(self) -> str:
        return digest({"snapshot": self.metadata.get("snapshot_id"), "ids": self.ids.tolist(), "endpoint": self.endpoint,
                       "labels": self.labels, "y": self.y, "bounds": [self.lower, self.upper], "censoring": self.censoring})


def load_task(snapshot: Path, endpoint: str, source: str | None = None) -> TaskDataset:
    snapshot = Path(snapshot)
    manifest = read_json(snapshot / "manifest.json")
    obs = pd.read_parquet(snapshot / "observations.parquet")
    molecules = pd.read_parquet(snapshot / "molecules.parquet").set_index("molecule_id")
    obs = obs[obs.endpoint == endpoint]
    if source:
        obs = obs[obs.source_id == source]
    obs = obs[~obs.value_origin.isin(["predicted", "calculated"])]
    if obs.empty:
        raise ValueError(f"No measured observations for {endpoint} / {source}")
    if endpoint in ("intensity", "panel_descriptor", "pleasantness", "detection_response", "receptor_activation", "receptor_ec50"):
        raise ValueError("Use contextual / receptor training for this endpoint; a molecule-only pivot would discard required context")
    task = "classification" if endpoint == "catalogue_descriptor" else "regression"
    if task == "classification":
        if obs.source_id.nunique() != 1:
            raise ValueError("Catalogue annotations require a single source head; select --source")
        # Only schema-defined catalogue zeros exist. Unassessed entries stay NaN.
        selected = obs[obs.label_state != "not_assessed"]
        rows, ys, lows, highs, censoring = [], [], [], [], []
        labels = sorted(selected.descriptor.unique())
        grouped = selected.groupby(["molecule_id", "descriptor"]).value.agg(["min", "max"])
        conflicting = grouped[grouped["min"] != grouped["max"]]
        if not conflicting.empty:
            raise ValueError("Conflicting catalogue records require review before matrix construction")
        matrix = selected.pivot_table(index="molecule_id", columns="descriptor", values="value", aggfunc="first").reindex(columns=labels)
        ids = matrix.index.to_numpy()
        y = matrix.to_numpy(dtype=float)
        sources = np.repeat(selected.source_id.iloc[0], len(ids))
        lower = upper = np.full_like(y, np.nan)
        cens = np.full(y.shape, "exact", dtype=object)
    else:
        # Keep independent observations distinct; molecule groups govern all splits.
        selected = obs[obs.censoring != "missing"].sort_values("observation_id")
        ids = selected.observation_id.to_numpy()
        y = selected.value.to_numpy(dtype=float)[:, None]
        lower = selected.lower.to_numpy(dtype=float)[:, None]
        upper = selected.upper.to_numpy(dtype=float)[:, None]
        cens = selected.censoring.to_numpy()[:, None]
        labels = [endpoint]
        sources = selected.source_id.to_numpy()
    mids = ids if task == "classification" else selected.molecule_id.to_numpy()
    mols = molecules.loc[mids]
    return TaskDataset(ids, mols.smiles.tolist(), mols.connectivity_id.to_numpy(), y, labels, task, endpoint,
                       sources, lower, upper, cens, {"snapshot_id": manifest["snapshot_id"], "source": source,
                                                   "permitted_use": "research", "target_semantics": "source_annotation" if task == "classification" else endpoint,
                                                   "unit": "annotation" if task == "classification" else selected.unit.iloc[0],
                                                   "aggregate_observations": int((obs.value_origin == "upstream_aggregate").sum())})

