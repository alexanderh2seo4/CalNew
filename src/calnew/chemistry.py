"""Molecular identity is stereo-specific; split groups are connectivity-specific."""
from __future__ import annotations

from functools import lru_cache

import numpy as np
from rdkit import Chem, DataStructs, rdBase
from rdkit.Chem import Descriptors, rdFingerprintGenerator
from rdkit.Chem.Scaffolds import MurckoScaffold

from .schema import Molecule


@lru_cache(maxsize=50000)
def identify(smiles: str) -> Molecule:
    if not isinstance(smiles, str) or not smiles.strip():
        raise ValueError("Missing SMILES")
    mol = Chem.MolFromSmiles(smiles)
    if mol is None or mol.GetNumAtoms() == 0:
        raise ValueError(f"Invalid SMILES: {smiles!r}")
    if len(Chem.GetMolFrags(mol)) != 1:
        raise ValueError("Disconnected structures require explicit mixture/material handling")
    Chem.AssignStereochemistry(mol, cleanIt=True, force=True)
    stereo = list(Chem.FindPotentialStereo(mol))
    status = "unspecified" if any(str(s.specified) == "Unspecified" for s in stereo) else ("specified" if stereo else "achiral")
    canonical = Chem.MolToSmiles(mol, isomericSmiles=True)
    key = Chem.MolToInchiKey(mol)
    if not key:
        raise ValueError("Could not construct InChIKey")
    return Molecule(molecule_id=key, original_smiles=smiles, smiles=canonical, inchikey=key,
                    connectivity_id=key.split("-")[0], molecular_weight=Descriptors.MolWt(mol), stereo_status=status)


def fingerprint(smiles: str, radius: int = 2, size: int = 2048, chirality: bool = True):
    mol = Chem.MolFromSmiles(identify(smiles).smiles)
    return rdFingerprintGenerator.GetMorganGenerator(radius=radius, fpSize=size, includeChirality=chirality).GetFingerprint(mol)


def fingerprints(smiles: list[str], radius: int = 2, size: int = 2048, chirality: bool = True) -> np.ndarray:
    result = np.zeros((len(smiles), size), dtype=np.float32)
    for i, smi in enumerate(smiles):
        DataStructs.ConvertToNumpyArray(fingerprint(smi, radius, size, chirality), result[i])
    return result


DESCRIPTORS = [(n, f) for n, f in Descriptors.descList]


def descriptors(smiles: list[str]) -> np.ndarray:
    rows = []
    for smi in smiles:
        mol = Chem.MolFromSmiles(identify(smi).smiles)
        values = []
        for _, fn in DESCRIPTORS:
            try:
                value = float(fn(mol))
                values.append(value if np.isfinite(value) else np.nan)
            except (ValueError, OverflowError, ZeroDivisionError):
                values.append(np.nan)
        rows.append(values)
    return np.array(rows, dtype=np.float32)


def scaffold(smiles: str) -> str:
    return MurckoScaffold.MurckoScaffoldSmiles(smiles=smiles, includeChirality=False)


def nearest_similarity(query: list[str], train: list[str]) -> np.ndarray:
    if not train:
        return np.zeros(len(query))
    refs = [fingerprint(s, chirality=False) for s in train]
    return np.array([max(DataStructs.BulkTanimotoSimilarity(fingerprint(s, chirality=False), refs)) for s in query])


def chemistry_version() -> str:
    return f"rdkit-{rdBase.rdkitVersion}:identity-v1"

