"""Leakage-resistant split manifests shared by every representation."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from rdkit import DataStructs
from rdkit.ML.Cluster import Butina
from sklearn.model_selection import GroupKFold

from .chemistry import fingerprint, scaffold
from .dataset import TaskDataset
from .io import digest, write_json


def structural_groups(data: TaskDataset, strategy: str = "structural", cutoff: float = 0.4) -> np.ndarray:
    if strategy == "grouped_random":
        return data.groups.copy()
    if strategy not in ("structural", "cluster"):
        raise ValueError(f"Unsupported grouping strategy: {strategy}")
    representative = {}
    for group, smi in zip(data.groups, data.smiles):
        representative.setdefault(group, smi)
    keys = sorted(representative)
    assignment = {}
    cluster_keys = []
    for key in keys:
        ring = scaffold(representative[key])
        if strategy == "structural" and ring:
            assignment[key] = "scaffold:" + ring
        else:
            cluster_keys.append(key)
    fps = [fingerprint(representative[key], chirality=False) for key in cluster_keys]
    distances = []
    for i in range(1, len(fps)):
        distances.extend(1.0 - np.array(DataStructs.BulkTanimotoSimilarity(fps[i], fps[:i])))
    if fps:
        for members in Butina.ClusterData(distances, len(fps), cutoff, isDistData=True, reordering=True):
            name = "cluster:" + digest(sorted(cluster_keys[i] for i in members))[:16]
            for i in members:
                assignment[cluster_keys[i]] = name
    return np.array([assignment[g] for g in data.groups])


def partition_groups(groups: np.ndarray, fractions=(0.7, 0.15, 0.15), seed: int = 42) -> list[np.ndarray]:
    if len(fractions) < 2 or not np.isclose(sum(fractions), 1) or min(fractions) <= 0:
        raise ValueError("Split fractions must be positive and sum to one")
    unique, sizes = np.unique(groups, return_counts=True)
    if len(unique) < len(fractions):
        raise ValueError("Not enough independent groups for the requested partition")
    rng = np.random.default_rng(seed)
    # Largest groups first; shuffled stable tie order. No outcome information is used.
    order = rng.permutation(len(unique))
    order = order[np.argsort(-sizes[order], kind="stable")]
    totals = np.zeros(len(fractions))
    targets = np.array(fractions) * len(groups)
    assigned = {}
    for position, j in enumerate(order):
        # Ensure nonempty partitions even with a few large groups.
        remaining, empty = len(order) - position, np.flatnonzero(totals == 0)
        if remaining == len(empty):
            choice = int(empty[0])
        else:
            choice = int(np.argmax(targets - totals))
        assigned[unique[j]] = choice
        totals[choice] += sizes[j]
    return [np.array([i for i, g in enumerate(groups) if assigned[g] == part], dtype=int) for part in range(len(fractions))]


def folds(groups: np.ndarray, n_splits: int, seed: int = 42):
    if len(np.unique(groups)) < n_splits:
        raise ValueError("Insufficient independent groups for cross-validation")
    return list(GroupKFold(n_splits=n_splits, shuffle=True, random_state=seed).split(np.arange(len(groups)), groups=groups))


def assert_disjoint(data: TaskDataset, *partitions):
    seen = set()
    for ix in partitions:
        groups = set(data.groups[np.asarray(ix, dtype=int)])
        if seen.intersection(groups):
            raise ValueError("Connectivity leakage between partitions")
        seen.update(groups)


def source_holdout(data: TaskDataset, source_id: str) -> tuple[np.ndarray, np.ndarray]:
    test = np.flatnonzero(data.source_ids == source_id)
    if not len(test):
        raise ValueError("Held-out source is absent")
    held_groups = set(data.groups[test])
    train = np.array([i for i, g in enumerate(data.groups) if g not in held_groups and data.source_ids[i] != source_id], dtype=int)
    if not len(train):
        raise ValueError("Source holdout leaves no independent training molecules")
    assert_disjoint(data, train, test)
    return train, test


def freeze_split(data: TaskDataset, destination: Path, strategy="structural", seed=42, cutoff=0.4) -> dict:
    groups = structural_groups(data, strategy, cutoff)
    dev, cal, test = partition_groups(groups, seed=seed)
    assert_disjoint(data, dev, cal, test)
    parts = {"development": dev.tolist(), "calibration": cal.tolist(), "test": test.tolist()}
    payload = {"schema": 1, "dataset_signature": data.signature(), "strategy": strategy, "seed": seed,
               "butina_distance_cutoff": cutoff, "row_ids": data.ids.tolist(), "groups": groups.tolist(),
               "partitions": parts, "actual_fractions": {k: len(v) / len(data.ids) for k, v in parts.items()},
               "unique_groups": len(np.unique(groups)), "largest_group": int(max(np.unique(groups, return_counts=True)[1]))}
    payload["split_id"] = digest(payload)
    path = Path(destination)
    if path.exists():
        from .io import read_json
        if read_json(path) != payload:
            raise ValueError("Frozen split differs; use a new destination")
    else:
        write_json(path, payload)
    return payload

