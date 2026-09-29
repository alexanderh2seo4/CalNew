"""Score structure-resolved examples with saved models; never ingest predictions as evidence."""
from pathlib import Path
import json
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote
import numpy as np
import pandas as pd
import requests
import joblib
from rdkit import Chem
from rdkit.Chem import Descriptors,rdMolDescriptors
from calnew.chemistry import identify,nearest_similarity
from calnew.io import read_json,write_json,digest

ROOT=Path('results/canvas-candidates-2026-09-24')
ROOT.mkdir(parents=True,exist_ok=True)
REFERENCES=[('Calone','28940-11-6'),('Helional','1205-17-0'),('Floralozone','67634-15-5'),('Melonal','106-72-9'),
 ('Cyclamen aldehyde','103-95-7'),('Dihydromyrcenol','18479-58-8'),('Phenylacetaldehyde','122-78-1'),('2-Phenylethanol','60-12-8'),
 ('Benzyl acetate','140-11-4'),('Phenethyl acetate','103-45-7'),('cis-3-Hexen-1-ol','928-96-1'),('cis-3-Hexenyl acetate','3681-71-8'),
 ('gamma-Decalactone','706-14-9'),('delta-Decalactone','705-86-2'),('beta-Ionone','14901-07-6'),('alpha-Ionone','127-41-3'),
 ('Methyl dihydrojasmonate','24851-98-7'),('Ambroxide','6790-58-5')]

def acquire(item):
    name,cas=item
    path=ROOT/'identities'/f'{cas}.json';path.parent.mkdir(exist_ok=True)
    url=f'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{quote(cas)}/property/SMILES,ConnectivitySMILES,InChIKey,IUPACName,MolecularFormula/JSON'
    if path.exists(): body=read_json(path)
    else:
        response=requests.get(url,timeout=45);response.raise_for_status();body=response.json();write_json(path,body)
    properties=body['PropertyTable']['Properties']
    if len(properties)!=1: raise ValueError(f'Ambiguous chemical resolution: {name}')
    prop=properties[0];molecule=identify(prop['SMILES'])
    if molecule.inchikey!=prop['InChIKey']: raise ValueError(f'Identity mismatch: {name}')
    return {'name':name,'cas':cas,'cid':prop['CID'],'smiles':prop['SMILES'],'identity_url':url,
            'pubchem_url':f"https://pubchem.ncbi.nlm.nih.gov/compound/{prop['CID']}",
            'iupac':prop['IUPACName'],'candidate_type':'known_reference_structure',
            'novelty':'Known compound; no novelty claim','material_note':'A resolved structure is not verification of an obtainable batch or isomer composition.'}

def protected_partition(bundle,run,molecule_ids):
    snapshot=Path('data/snapshots/955c3ab05ff9fb7d')
    molecules=pd.read_parquet(snapshot/'molecules.parquet',columns=['molecule_id','connectivity_id']).set_index('molecule_id')
    split=read_json(run/'split.json')
    if bundle['task']=='classification': row_to_molecule={mid:mid for mid in split['row_ids']}
    else:
        obs=pd.read_parquet(snapshot/'observations.parquet',columns=['observation_id','molecule_id'])
        row_to_molecule=dict(zip(obs.observation_id,obs.molecule_id))
    test_ids={row_to_molecule[split['row_ids'][i]] for i in split['partitions']['test']}
    test_groups=set(molecules.loc[list(test_ids)].connectivity_id)
    result=[]
    for s in molecule_ids:
        mol=identify(s);g=mol.connectivity_id
        result.append('development_group' if g in bundle['training_groups'] else 'calibration_group' if g in bundle['calibration_groups'] else 'reserved_test_group' if g in test_groups else 'outside_endpoint_dataset')
    return result

def main():
    records=[];failures=[]
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures=[pool.submit(acquire,item) for item in REFERENCES]
        for item,future in zip(REFERENCES,futures):
            try: records.append(future.result())
            except Exception as exc: failures.append({'name':item[0],'reason':str(exc)})
    for name,smiles in [('7-Ethyl Calone scaffold','CCC1=CC2=C(C=C1)OCC(=O)CO2'),
        ('7-n-Propyl Calone scaffold','CCCC1=CC2=C(C=C1)OCC(=O)CO2'),
        ('7-Isopropyl Calone scaffold','CC(C)C1=CC2=C(C=C1)OCC(=O)CO2')]:
        records.append({'name':name,'smiles':smiles,'candidate_type':'structure_defined_analogue',
                        'novelty':'Related substitutions appear in prior art; no novelty claim',
                        'identity_url':'https://patents.google.com/patent/EP0902024B1/en',
                        'material_note':'Computational structure only; no batch, procurement or synthesis verification.'})
    write_json(ROOT/'candidate-inputs.json',{'candidates':records,'identity_failures':failures})
    smiles=[r['smiles'] for r in records]
    for r in records:
        mol=identify(r['smiles']);graph=Chem.MolFromSmiles(mol.smiles)
        r.update(molecule_id=mol.molecule_id,stereochemistry=mol.stereo_status,
                 structure={'heavy_atoms':graph.GetNumHeavyAtoms(),'rings':rdMolDescriptors.CalcNumRings(graph),
                            'rotatable_bonds':rdMolDescriptors.CalcNumRotatableBonds(graph),'bertz_complexity':Descriptors.BertzCT(graph),
                            'molecular_weight':mol.molecular_weight,'rdkit_logp':Descriptors.MolLogP(graph)})
    for task,run in [('threshold',Path('runs/basic-threshold-models')),('descriptor',Path('runs/basic-descriptor-models'))]:
        bundle=joblib.load(run/'model.joblib');all_predictions=[];expert_names=[];errors={}
        for name in bundle['expert_layout']:
            print(task,name,flush=True)
            try: value=np.mean([m.predict(smiles) for m in bundle['models'][name]],axis=0)
            except Exception as exc:
                errors[name]=str(exc);value=np.full((len(smiles),len(bundle['labels'])),np.nan)
                for i,s in enumerate(smiles):
                    try: value[i]=np.mean([m.predict([s])[0] for m in bundle['models'][name]],axis=0)
                    except Exception as inner: errors[f'{name}:{i}']=str(inner)
            all_predictions.append(value);expert_names.append(name)
        experts=np.stack(all_predictions,axis=1)
        pred=bundle['organiser'].predict(experts) if bundle['organiser'] else experts[:,expert_names.index(bundle['selected'])]
        if task=='descriptor': pred=bundle['calibrator'].transform(pred)
        else: lower,upper=bundle['calibrator'].interval(pred)
        similarities=nearest_similarity(smiles,bundle['training_smiles'])
        partitions=protected_partition(bundle,run,smiles)
        for i,r in enumerate(records):
            result={'selected':bundle['selected'],'model_version':bundle['run_id'],'training_similarity':float(similarities[i]),
                    'partition':partitions[i],'expert_predictions':{name:dict(zip(bundle['labels'],experts[i,j].tolist())) for j,name in enumerate(expert_names)},
                    'expert_disagreement':float(np.nanmean(np.nanstd(experts[i],axis=0))),
                    'estimates':dict(zip(bundle['labels'],pred[i].tolist())),'unavailable_experts':[name for j,name in enumerate(expert_names) if not np.isfinite(experts[i,j]).all()]}
            if task=='threshold':
                result.update(log10_ppbv=float(pred[i,0]),ppbv=float(10**pred[i,0]),interval90_ppbv=[float(10**lower[i,0]),float(10**upper[i,0])])
            else:
                result['top_descriptors']=sorted(zip(bundle['labels'],pred[i].tolist()),key=lambda x:x[1],reverse=True)[:6]
                result['missing_requested_labels']=[l for l in ['marine','watery','ozonic','pleasantness','refractory_time'] if l not in bundle['labels']]
            r[task]=result
        write_json(ROOT/f'{task}-inference.json',{'candidates':records,'branch_errors':errors})
    write_json(ROOT/'screening.json',{'candidates':records,'identity_failures':failures,
        'scope':'Research hypotheses and reference selection. No new sensory observations, synthesis feasibility, novelty or adaptation-time predictions.',
        'benchmark_policy':'No sensory labels or outcomes were opened for reserved test molecules. Such structures are marked and excluded from the recommended new-measurement shortlist.',
        'candidate_input_hash':digest(read_json(ROOT/'candidate-inputs.json'))})
    for r in sorted(records,key=lambda x:x['threshold']['ppbv']):
        print(r['name'],round(r['threshold']['ppbv'],3),round(r['threshold']['training_similarity'],2),r['threshold']['partition'],r['descriptor']['partition'],r['descriptor']['top_descriptors'][:3],flush=True)

if __name__=='__main__': main()
