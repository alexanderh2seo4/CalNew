"""Training-only auxiliary data. Never an evaluation target.

Li et al. 2025 (Metabolites, PMC12654368; Zenodo 10.5281/zenodo.17559514, CC BY 4.0) deposit
median odour detection thresholds in water (mg/L). The air-threshold stage uses them as extra
training rows with a medium flag, so tree members can share structure-potency patterns
across media. Rows of reserved molecules are dropped on load; callers must also drop rows
whose molecules touch the evaluated molecules (`exclude_touching`).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..chemistry import identify, scaffold
from ..io import file_digest
from .data import exclude_reserved

LI_2025 = Path("data/raw/li_2025/zenodo-17559514-v1")
LI_2025_URL = "https://zenodo.org/records/17559514/files/threshold_data_med.csv?download=1"
LI_2025_SHA256 = "8800c21198ffec96f170a2b7000ab7577718e2857689984906f3e47fdb9e5eb2"


def load_li_2025(data, reserved_runs, molecules: pd.DataFrame, folder: Path = LI_2025) -> pd.DataFrame:
    """Water thresholds as -log10(mg/L) per molecule (median over duplicate structures)."""
    path = Path(folder) / "threshold_data_med.csv"
    if not path.exists():
        raise ValueError(f"Auxiliary water thresholds missing: download {LI_2025_URL} to {path} (see docs/PIPELINE.md)")
    if file_digest(path) != LI_2025_SHA256:
        raise ValueError(f"{path} does not match the pinned sha256 {LI_2025_SHA256[:12]}...; re-download it")
    raw = pd.read_csv(path)
    # Four deposited values use spaces as digit grouping ("0.000 0063" = 6.3e-6).
    value = pd.to_numeric(raw.threshold.astype("string").str.replace(" ", "", regex=False), errors="coerce").to_numpy(dtype=float, na_value=np.nan)
    rows = []
    for smiles, v in zip(raw.SMILES, value):
        if not (np.isfinite(v) and v > 0):
            continue
        try:
            ident = identify(smiles)
        except ValueError:  # salts, mixtures and unparseable structures are not single-molecule rows
            continue
        rows.append((ident.molecule_id, ident.smiles, -np.log10(v)))
    frame = (pd.DataFrame(rows, columns=["molecule_id", "smiles", "y"])
             .groupby("molecule_id").agg(smiles=("smiles", "first"), y=("y", "median")).reset_index())
    frame = exclude_reserved(frame, data, reserved_runs, molecules)
    frame["connectivity"] = [m.split("-")[0] for m in frame.molecule_id]
    frame["scaffold"] = [scaffold(s) for s in frame.smiles]
    return frame.reset_index(drop=True)


def exclude_touching(aux: pd.DataFrame, molecule_ids, smiles=(), by_scaffold: bool = False) -> np.ndarray:
    """Mask of auxiliary rows to keep: not the same molecule (connectivity key) as any given one and,
    with `by_scaffold` (structural splits), not sharing its ring scaffold either."""
    touching = np.array(aux.connectivity.isin({m.split("-")[0] for m in molecule_ids}), dtype=bool)
    if by_scaffold:
        smiles = list(smiles)
        rings = {r for r in (scaffold(s) for s in smiles) if r}
        touching |= np.array(aux.scaffold.isin(rings), dtype=bool)
        acyclic = [s for s in smiles if not scaffold(s)]
        candidates = np.flatnonzero(~touching & (aux.scaffold == "").to_numpy())
        if acyclic and len(candidates):  # acyclic groups are Butina clusters at Tanimoto distance 0.4
            from ..chemistry import fingerprints
            from ..models.classical import tanimoto
            sim = tanimoto(fingerprints(aux.smiles.to_numpy()[candidates].tolist(), chirality=False), fingerprints(acyclic, chirality=False))
            touching[candidates[sim.max(1) >= 0.6]] = True
    return ~touching
