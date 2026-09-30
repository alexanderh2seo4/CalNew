"""Explicit, named structure blocks for the modular pipeline.

Each block is a deterministic function of structure. Blocks encode hypotheses from the
odour literature (transport, hydrogen bonding, osmophores, chain length/branching) so that
their marginal value can be measured by ablation instead of assumed.
"""
from __future__ import annotations

from collections import deque
from pathlib import Path

import numpy as np
from rdkit import Chem
from rdkit.Chem import Crippen, Descriptors, Lipinski, MACCSkeys, rdMolDescriptors

from ..chemistry import chemistry_version, fingerprints, identify
from ..io import digest, write_json

TRANSPORT = ["MolWt", "HeavyAtomCount", "MolLogP", "TPSA", "NumRotatableBonds", "RingCount", "NumAromaticRings",
             "LabuteASA", "MolMR", "FractionCSP3", "NumHeteroatoms"]
HBOND_COUNTS = ["NumHDonors", "NumHAcceptors", "NHOHCount", "NOCount"] + [f"PEOE_VSA{i}" for i in range(1, 15)]

# Hydrogen-bond sites split by chemistry: a thiol S-H is a much weaker donor than O-H.
HBOND_SMARTS = {
    "donor_OH": "[OX2H]", "donor_NH": "[NX3;H1,H2;!$(NC=O)]", "donor_amide_NH": "[NX3;H1,H2]C=O", "donor_SH": "[SX2H]",
    "acceptor_carbonyl_O": "[CX3]=[OX1]", "acceptor_ether_O": "[OX2;H0;!$(OC=O)]([#6])[#6]", "acceptor_ester_O": "[OX2;H0]C=O",
    "acceptor_aromatic_N": "[n;X2]", "acceptor_amine_N": "[NX3;H0,H1,H2;!$(NC=O);!$(N-a)]", "acceptor_nitrile_N": "[NX1]#C",
}

# Osmophore vocabulary: Abraham's mercaptan/aldehyde/acid/unsaturated-ester indicators
# plus the functional classes with documented threshold effects.
OSMOPHORES = {
    "thiol": "[SX2H][#6]", "sulfide": "[#6][SX2;H0][#6]", "disulfide": "[#6]SS[#6]", "thioester": "[#6]C(=O)S[#6]",
    "isothiocyanate": "N=C=S", "aldehyde": "[CX3H1](=O)[#6]", "ketone": "[#6][CX3](=O)[#6]", "carboxylic_acid": "[CX3](=O)[OX2H1]",
    "ester": "[#6][CX3](=O)[OX2H0][#6]", "lactone": "[#6;R][CX3;R](=O)[OX2;R]", "unsaturated_ester": "C=C[CX3](=O)[OX2H0][#6]",
    "enal_enone": "C=C[CX3]=O", "pyrazine": "c1cnccn1", "alkoxypyrazine": "[OX2]([CH3,CH2])c1cnccn1", "furan": "c1ccoc1",
    "thiophene": "c1ccsc1", "thiazole": "c1cscn1", "pyrrole": "c1cc[nH]c1", "pyridine": "c1ccncc1", "phenol": "c[OX2H]",
    "alcohol_primary": "[CH2][OX2H]", "alcohol_secondary": "[CH1]([#6])([#6])[OX2H]", "alcohol_tertiary": "[CX4H0]([#6])([#6])([#6])[OX2H]",
    "amine_primary": "[NX3H2][CX4]", "amine_secondary": "[NX3H1]([CX4])[CX4]", "amine_tertiary": "[NX3H0]([CX4])([CX4])[CX4]",
    "nitrile": "C#N", "nitro": "[N+](=O)[O-]", "halide": "[F,Cl,Br,I]", "ether": "[OD2]([#6])[#6]", "acetal": "[CX4]([OX2][#6])[OX2][#6]",
    "alkene": "[CX3]=[CX3]", "terminal_alkene": "[CH2]=[CX3]", "alkyne": "C#C", "aromatic_ring": "a1aaaaa1",
}

_PATTERNS = {name: Chem.MolFromSmarts(s) for name, s in {**HBOND_SMARTS, **OSMOPHORES}.items()}
for _name, _pattern in _PATTERNS.items():
    if _pattern is None:
        raise ValueError(f"Invalid SMARTS for {_name}")

# Saturating chain-length basis 1 - exp(-k n^1.4) (Zarzo's form); several k values let a
# linear head fit class-specific curvature without imposing monotonicity on the output.
CHAIN_K = (0.02, 0.05, 0.1, 0.2)


def _count(mol, name):
    return len(mol.GetSubstructMatches(_PATTERNS[name]))


def longest_aliphatic_chain(mol) -> int:
    """Longest path (in atoms) through acyclic, non-aromatic carbons: a tree diameter."""
    nodes = {a.GetIdx() for a in mol.GetAtoms() if a.GetAtomicNum() == 6 and not a.IsInRing() and not a.GetIsAromatic()}
    if not nodes:
        return 0
    adjacency = {i: [n.GetIdx() for n in mol.GetAtomWithIdx(i).GetNeighbors() if n.GetIdx() in nodes] for i in nodes}

    def farthest(start):
        seen, queue, last = {start: 1}, deque([start]), (start, 1)
        while queue:
            node = queue.popleft()
            for nxt in adjacency[node]:
                if nxt not in seen:
                    seen[nxt] = seen[node] + 1
                    queue.append(nxt)
                    if seen[nxt] > last[1]:
                        last = (nxt, seen[nxt])
        return last, seen

    best, remaining = 0, set(nodes)
    while remaining:  # the acyclic carbon subgraph may be a forest
        start = next(iter(remaining))
        (end, _), component = farthest(start)
        remaining -= set(component)
        (_, length), _ = farthest(end)
        best = max(best, length)
    return best


def _transport(mol):
    return [getattr(Descriptors, n)(mol) for n in TRANSPORT]


def _hbond(mol):
    values = [getattr(Descriptors, n)(mol) for n in HBOND_COUNTS]
    values += [_count(mol, n) for n in HBOND_SMARTS]
    area = Descriptors.LabuteASA(mol)
    values.append(Descriptors.TPSA(mol) / area if area else 0.0)  # polar surface fraction
    return values


def _osmophore(mol):
    return [_count(mol, n) for n in OSMOPHORES]


def _chain(mol):
    n = longest_aliphatic_chain(mol)
    heavy = mol.GetNumHeavyAtoms()
    carbons = [a for a in mol.GetAtoms() if a.GetAtomicNum() == 6]
    degree = [sum(1 for nb in a.GetNeighbors() if nb.GetAtomicNum() == 6) for a in carbons]
    acyclic = sum(1 for a in carbons if not a.IsInRing())
    values = [n, n * n, acyclic, heavy, sum(d == 3 for d in degree), sum(d == 4 for d in degree), sum(d >= 3 for d in degree)]
    values += [1 - np.exp(-k * n ** 1.4) for k in CHAIN_K] + [1 - np.exp(-k * heavy ** 1.4) for k in CHAIN_K]
    values += [Descriptors.Kappa1(mol), Descriptors.Kappa2(mol), Descriptors.Kappa3(mol), Descriptors.Chi0v(mol),
               Descriptors.Chi1v(mol), Descriptors.Chi2v(mol), Descriptors.Chi3v(mol), Descriptors.BalabanJ(mol),
               np.log1p(Descriptors.BertzCT(mol)), rdMolDescriptors.CalcNumAtomStereoCenters(mol), Lipinski.NumAliphaticRings(mol)]
    return values


def _fingerprint(smiles):
    mol = Chem.MolFromSmiles(smiles)
    maccs = np.zeros(167, dtype=np.float32)
    maccs[list(MACCSkeys.GenMACCSKeys(mol).GetOnBits())] = 1
    return np.concatenate([fingerprints([smiles], radius=2, size=1024)[0], maccs])


BLOCK_FUNCTIONS = {"transport": _transport, "hbond": _hbond, "osmophore": _osmophore, "chain": _chain}
EXPLICIT_BLOCKS = ("transport", "hbond", "osmophore", "chain")
STRUCTURE_BLOCKS = EXPLICIT_BLOCKS + ("pharmacophore", "fingerprint")


def block_names(block: str) -> list[str]:
    if block == "rdkit":
        return [name for name, _ in Descriptors.descList]
    if block == "transport":
        return list(TRANSPORT)
    if block == "hbond":
        return HBOND_COUNTS + list(HBOND_SMARTS) + ["polar_surface_fraction"]
    if block == "osmophore":
        return list(OSMOPHORES)
    if block == "chain":
        return (["longest_aliphatic_chain", "longest_chain_squared", "acyclic_carbons", "heavy_atoms", "tertiary_carbons",
                 "quaternary_carbons", "branch_points"] + [f"chain_saturation_k{k}" for k in CHAIN_K]
                + [f"size_saturation_k{k}" for k in CHAIN_K]
                + ["Kappa1", "Kappa2", "Kappa3", "Chi0v", "Chi1v", "Chi2v", "Chi3v", "BalabanJ", "log1p_BertzCT",
                   "atom_stereocentres", "aliphatic_rings"])
    raise ValueError(f"Block {block} has no named columns")


def _rdkit(mol):
    values = []
    for _, function in Descriptors.descList:
        try:
            values.append(float(function(mol)))
        except (ValueError, ZeroDivisionError, RuntimeError):
            values.append(np.nan)
    return np.clip(values, -1e6, 1e6)  # Ipc and a few others overflow float32; trees only need the order


def compute_block(block: str, smiles: list[str]) -> np.ndarray:
    if block == "rdkit":
        # Full RDKit 2D descriptor set (volatility/size/polarity proxies); column set follows the RDKit version.
        return np.asarray([_rdkit(Chem.MolFromSmiles(s)) for s in smiles], dtype=np.float32)
    if block in BLOCK_FUNCTIONS:
        rows = []
        for s in smiles:
            mol = Chem.MolFromSmiles(s)
            rows.append([float(v) if np.isfinite(v) else np.nan for v in BLOCK_FUNCTIONS[block](mol)])
        return np.asarray(rows, dtype=np.float32)
    if block == "pharmacophore":
        # Gobbi 2D pharmacophore bits (~40k sparse) folded to 1024 counts to stay dense-friendly.
        from rdkit.Chem.Pharm2D import Generate, Gobbi_Pharm2D
        x = np.zeros((len(smiles), 1024), dtype=np.float32)
        for i, s in enumerate(smiles):
            for bit in Generate.Gen2DFingerprint(Chem.MolFromSmiles(s), Gobbi_Pharm2D.factory).GetOnBits():
                x[i, bit % 1024] += 1
        return x
    if block == "fingerprint":
        return np.stack([_fingerprint(s) for s in smiles]).astype(np.float32)
    if block == "unimol2":
        return unimol2_rows(smiles)
    if block == "molformer":
        return pretrained_rows("molformer", smiles)
    raise ValueError(f"Unknown block: {block}")


# Frozen MoLFormer-XL checkpoint already pinned by the earlier CALNEW baseline runs.
MOLFORMER = {"family": "molformer", "checkpoint": "ibm-research/MoLFormer-XL-both-10pct",
             "revision": "361063d0ad524ef77cf39b08469f6be770dc550f"}


def pretrained_rows(family: str, smiles: list[str], threads: int = 8, failures: list | None = None, chunk: int = 64) -> np.ndarray:
    """Frozen pretrained embeddings plus a final availability column.

    A molecule the encoder cannot embed (no conformers for Uni-Mol2, unsupported tokens for
    MoLFormer) is an unavailable branch: its row is NaN (imputed later from training folds only)
    and the availability column is 0, so the model can tell a missing view from a real one.
    """
    from ..models.pretrained import PretrainedModel
    config = {**(MOLFORMER if family == "molformer" else {"family": family}), "threads": threads}
    model = PretrainedModel(config, "regression", "data/features")
    rows = []
    for start in range(0, len(smiles), chunk):
        batch = smiles[start:start + chunk]
        try:
            rows.extend(model.embed(batch).astype(np.float32))
            continue
        except ValueError:
            pass  # at least one molecule failed; resolve this chunk individually (successful ones are cached)
        for s in batch:
            try:
                rows.append(model.embed([s])[0].astype(np.float32))
            except ValueError as exc:
                rows.append(None)
                if failures is not None:
                    failures.append({"smiles": s, "reason": str(exc)})
    width = next((len(r) for r in rows if r is not None), None)
    if width is None:
        raise ValueError(f"{family} embedding failed for every molecule")
    return np.stack([np.append(r, 1.0) if r is not None else np.append(np.full(width, np.nan), 0.0) for r in rows]).astype(np.float32)


def unimol2_rows(smiles: list[str], threads: int = 8, failures: list | None = None) -> np.ndarray:
    return pretrained_rows("unimol2", smiles, threads, failures)


class BlockCache:
    """Per-block, content-addressed cache keyed by canonical SMILES and code version."""
    VERSION = "pipeline-blocks-v2"  # v2: unimol2 carries an availability column

    def __init__(self, root: Path):
        self.root = Path(root) / "pipeline-blocks"
        self.root.mkdir(parents=True, exist_ok=True)

    def get(self, block: str, smiles: list[str]) -> np.ndarray:
        canonical = [identify(s).smiles for s in smiles]
        meta = {"block": block, "version": self.VERSION, "chemistry": chemistry_version(), "smiles": canonical}
        path = self.root / f"{block}-{digest(meta)[:24]}.npz"
        if path.exists():
            with np.load(path, allow_pickle=False) as data:
                return data["x"]
        x = compute_block(block, canonical)
        np.savez_compressed(path, x=x)
        write_json(path.with_suffix(".json"), {**meta, "shape": list(x.shape), "training": "none; deterministic structure features"})
        return x

    def blocks(self, names, smiles) -> dict[str, np.ndarray]:
        return {name: self.get(name, smiles) for name in names}
