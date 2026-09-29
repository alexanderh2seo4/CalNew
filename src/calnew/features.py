"""Content-addressed structure-only features; fitting imputation/scaling belongs to models."""
from __future__ import annotations

from pathlib import Path

import numpy as np

from .chemistry import DESCRIPTORS, chemistry_version, descriptors, fingerprints, identify
from .io import digest, read_json, write_json


class FeatureCache:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def get(self, smiles: list[str], kind="morgan", radius=2, size=2048) -> np.ndarray:
        canonical = [identify(s).smiles for s in smiles]
        meta = {"kind": kind, "radius": radius, "size": size, "chemistry_version": chemistry_version(),
                "smiles": canonical, "descriptor_names": [n for n,_ in DESCRIPTORS] if kind in ("descriptors","combined") else [],
                "training": "none; deterministic chemical features"}
        key = digest(meta)
        path = self.root / f"{key}.npz"
        if path.exists():
            with np.load(path, allow_pickle=False) as data:
                return data["x"]
        if kind == "morgan":
            x = fingerprints(canonical,radius,size)
        elif kind == "descriptors":
            x = descriptors(canonical)
        elif kind == "combined":
            x = np.concatenate([fingerprints(canonical,radius,size),descriptors(canonical)],axis=1)
        elif kind == "pharmacophore":
            from .pharmacophore import pharmacophore2d
            x = pharmacophore2d(canonical)
        else:
            raise ValueError(f"Unknown feature kind: {kind}")
        np.savez_compressed(path,x=x)
        write_json(path.with_suffix(".json"),meta)
        return x

