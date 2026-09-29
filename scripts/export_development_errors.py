"""Create a reviewable error catalogue from development predictions only."""
import argparse
from pathlib import Path
import numpy as np
from calnew.dataset import load_task
from calnew.chemistry import identify,nearest_similarity
from calnew.io import read_json,write_json

p=argparse.ArgumentParser();p.add_argument('run',type=Path);a=p.parse_args()
report=read_json(a.run/'report.json');identity=read_json(a.run/'run.json')['identity'];split=read_json(a.run/'split.json')
dataset=load_task(Path(identity['snapshot']),identity['endpoint'],identity['source'])
dataset=dataset.subset(split['partitions']['development'])
with np.load(a.run/'development-predictions.npz',allow_pickle=False) as arrays:
    y=arrays['y'];pred=arrays[report['selected']]
errors=np.nanmean((y-pred)**2,axis=1) if dataset.task=='classification' else np.nanmean(np.abs(y-pred),axis=1)
indices=np.argsort(-errors)[:30]
rows=[]
for i in indices:
    mol=identify(dataset.smiles[i])
    rows.append({'id':str(dataset.ids[i]),'smiles':dataset.smiles[i],'connectivity_id':mol.connectivity_id,'stereochemistry':mol.stereo_status,
                 'error':float(errors[i]),'metric':'descriptor_brier' if dataset.task=='classification' else 'log_threshold_absolute_error',
                 'observed':dict(zip(report['labels'],y[i].tolist())),'predicted':dict(zip(report['labels'],pred[i].tolist()))})
write_json(a.run/'development-errors.json',{'partition':'development_outer_validation','selected':report['selected'],'largest_errors':rows,
                                         'note':'Review aid; not a final-test error catalogue.'})
print(a.run/'development-errors.json')
