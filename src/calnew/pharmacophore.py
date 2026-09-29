"""Generic features and fold-local ligand templates, without sensory label invention."""
import numpy as np
from rdkit import Chem, DataStructs
from rdkit.Chem.Pharm2D import Generate, Gobbi_Pharm2D


def pharmacophore2d(smiles):
    rows=[]
    for s in smiles:
        fp=Generate.Gen2DFingerprint(Chem.MolFromSmiles(s),Gobbi_Pharm2D.factory)
        arr=np.zeros(fp.GetNumBits(),dtype=np.float32)
        arr[list(fp.GetOnBits())]=1
        rows.append(arr)
    return np.array(rows)


class LigandTemplates:
    """Fit only on experimentally supported training ligands; audit IDs are retained."""
    def fit(self,smiles,ligand_ids,training_ids,active):
        if not set(ligand_ids).issubset(set(training_ids)):
            raise ValueError('Pharmacophore templates include held-out ligands')
        from .chemistry import fingerprints
        active=np.asarray(active,dtype=bool)
        if not active.any(): raise ValueError('No measured active training ligands')
        self.training_ids=list(training_ids)
        self.templates=fingerprints([s for s,a in zip(smiles,active) if a])
        return self

    def transform(self,smiles):
        from .chemistry import fingerprints
        from .models.classical import tanimoto
        similarity=tanimoto(fingerprints(smiles),self.templates)
        return np.column_stack([similarity.max(1),similarity.mean(1)])
