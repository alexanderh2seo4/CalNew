"""Research acquisition policies keep prospective evaluation groups untouched."""
import numpy as np
from .chemistry import fingerprints,identify
from .models.classical import tanimoto


def suggest(candidate_pool,batch_size,*,anchors=(),protected_groups=(),policy='mixed',seed=42):
    if batch_size<1: raise ValueError('Batch size must be positive')
    rng=np.random.default_rng(seed)
    candidates=[]; seen=set()
    for row in candidate_pool:
        mol=identify(row['smiles'])
        if mol.molecule_id in seen or mol.connectivity_id in set(protected_groups): continue
        if row.get('identity_verified') is not True or row.get('delivery_feasible') is not True: continue
        seen.add(mol.molecule_id); candidates.append({**row,'molecule_id':mol.molecule_id,'group':mol.connectivity_id})
    if policy not in ('mixed','random','diversity'): raise ValueError('Unknown acquisition policy')
    anchors=[r for r in candidates if r['molecule_id'] in set(anchors)]
    if policy=='mixed':
        fractions=np.array([.4,.3,.2,.1])*batch_size
        counts=np.floor(fractions).astype(int)
        for i in np.argsort(-(fractions-counts))[:batch_size-counts.sum()]: counts[i]+=1
        if len(anchors)<counts[3]: raise ValueError('Insufficient eligible repeated anchors for requested batch')
    else: counts=[0,batch_size,0,0]
    if len(candidates)<batch_size: raise ValueError('Insufficient eligible candidate molecules')
    selected=[]; used=set()
    def take(rows,n,reason):
        for r in rows:
            if r['molecule_id'] in used: continue
            selected.append({**r,'acquisition_reason':reason}); used.add(r['molecule_id'])
            n-=1
            if n==0: break
    if policy=='random':
        take([candidates[i] for i in rng.permutation(len(candidates))],batch_size,'random_control')
        return selected
    if counts[3]: take(anchors,counts[3],'repeated_anchor')
    if counts[0]: take(sorted(candidates,key=lambda r:r.get('reducible_uncertainty',0),reverse=True),counts[0],'reducible_uncertainty')
    if counts[2]: take(sorted(candidates,key=lambda r:r.get('analogue_disagreement',0),reverse=True),counts[2],'discriminating_analogue')
    fp=fingerprints([r['smiles'] for r in candidates])
    sim=tanimoto(fp,fp)
    while len(selected)<batch_size:
        chosen=[i for i,r in enumerate(candidates) if r['molecule_id'] in used]
        score=1-sim[:,chosen].max(axis=1) if chosen else np.array([1-r.get('training_similarity',0) for r in candidates])
        score[chosen]=-np.inf
        r=candidates[int(np.argmax(score))]
        take([r],1,'chemical_diversity')
    return selected
