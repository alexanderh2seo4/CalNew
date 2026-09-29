"""Grouped label-shuffle check of a fixed basic expert on development folds only."""
import argparse
from pathlib import Path
import numpy as np
from calnew.dataset import load_task
from calnew.models import make_model
from calnew.metrics import evaluate
from calnew.splits import folds,assert_disjoint
from calnew.io import read_json,write_json

p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('--expert',default='descriptor_linear');a=p.parse_args()
manifest=read_json(a.run/'run.json');identity=manifest['identity'];split=read_json(a.run/'split.json')
data=load_task(Path(identity['snapshot']),identity['endpoint'],identity['source'])
ix=split['partitions']['development'];data=data.subset(ix)
labels=read_json(a.run/'report.json')['labels'];keep=[data.labels.index(l) for l in labels]
data.y=data.y[:,keep];data.lower=data.lower[:,keep];data.upper=data.upper[:,keep];data.censoring=data.censoring[:,keep];data.labels=labels
configuration=read_json(a.run/f'final-{a.expert}.json')['configuration']
groups=np.asarray(split['groups'])[ix];evaluation_folds=folds(groups,identity['configuration']['outer_folds'],42)
blocks={g:np.flatnonzero(data.groups==g) for g in np.unique(data.groups)}
results=[]
for seed in (42,137,271):
    rng=np.random.default_rng(seed);shuffled=data.y.copy()
    for size in sorted({len(v) for v in blocks.values()}):
        same=[v for v in blocks.values() if len(v)==size]
        for destination,source in zip(same,rng.permutation(len(same))): shuffled[destination]=data.y[same[source]]
    control=data.subset(np.arange(len(data.ids)));control.y=shuffled
    predictions=np.full_like(shuffled,np.nan)
    for train,val in evaluation_folds:
        assert_disjoint(data,train,val)
        model=make_model(configuration,data.task,Path('data/features')).fit(control.subset(train))
        predictions[val]=model.predict(control.subset(val).smiles)
    results.append({'seed':seed,'evaluation':evaluate(shuffled,predictions,data.task,labels)})
write_json(a.run/f'shuffle-control-{a.expert}.json',{'partition':'development_only','expert':a.expert,'results':results,
    'interpretation':'A leakage diagnostic, not a formal architecture-selection comparison. Configuration was fixed from the real-label development run.'})
print(a.run/f'shuffle-control-{a.expert}.json')
