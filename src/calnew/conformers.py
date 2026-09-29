"""Reproducible conformers; a failure is an unavailable branch, never a flat substitute."""
from pathlib import Path

import numpy as np
from rdkit import Chem, rdBase
from rdkit.Chem import AllChem, rdMolAlign

from .chemistry import identify
from .io import digest, read_json, write_json


def generate(smiles, root=Path('data/conformers'), seed=42, generated=32, retained=16, rms_cutoff=.5):
    identity=identify(smiles)
    config=dict(smiles=identity.smiles,seed=seed,generated=generated,retained=retained,rms_cutoff=rms_cutoff,rdkit=rdBase.rdkitVersion)
    path=Path(root)/digest(config)
    if (path/'manifest.json').exists():
        return read_json(path/'manifest.json')
    path.mkdir(parents=True,exist_ok=True)
    mol=Chem.AddHs(Chem.MolFromSmiles(identity.smiles))
    params=AllChem.ETKDGv3(); params.randomSeed=seed; params.numThreads=1; params.enforceChirality=True
    ids=list(AllChem.EmbedMultipleConfs(mol,numConfs=generated,params=params))
    if not ids:
        result=dict(config=config,status='unavailable',reason='ETKDG embedding failed',molecule_id=identity.molecule_id)
    else:
        method='MMFF94' if AllChem.MMFFHasAllMoleculeParams(mol) else 'UFF'
        optimized=AllChem.MMFFOptimizeMoleculeConfs(mol,numThreads=1,maxIters=500) if method=='MMFF94' else AllChem.UFFOptimizeMoleculeConfs(mol,numThreads=1,maxIters=500)
        valid=[i for i in ids if optimized[i][0]==0 and np.isfinite(optimized[i][1])]
        keep=[]
        for i in sorted(valid,key=lambda j:optimized[j][1]):
            if all(rdMolAlign.GetBestRMS(mol,mol,prbId=i,refId=j)>=rms_cutoff for j in keep): keep.append(i)
            if len(keep)>=retained: break
        if not keep:
            result=dict(config=config,status='unavailable',reason='No force-field optimisation converged',molecule_id=identity.molecule_id)
        else:
            coordinates=np.array([mol.GetConformer(i).GetPositions() for i in keep])
            np.savez_compressed(path/'conformers.npz',coordinates=coordinates,atoms=np.array([a.GetSymbol() for a in mol.GetAtoms()]),energies=np.array([optimized[i][1] for i in keep]))
            writer=Chem.SDWriter(str(path/'conformers.sdf'))
            for i in keep: writer.write(mol,confId=i)
            writer.close()
            result=dict(config=config,status='available',molecule_id=identity.molecule_id,retained=len(keep),force_field=method,
                        failed_optimisations=len(ids)-len(valid),path=str((path/'conformers.npz').resolve()))
    write_json(path/'manifest.json',result)
    return result


def conformer_arrays(smiles,root=Path('data/conformers'),**config):
    result=generate(smiles,root,**config)
    if result['status']!='available': raise ValueError(result['reason'])
    with np.load(result['path'],allow_pickle=False) as f:
        return f['atoms'].tolist(),f['coordinates'].copy(),result
