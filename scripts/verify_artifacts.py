"""Audit saved basic-model runs without opening their final test partitions."""
from pathlib import Path
import json
import numpy as np
from calnew.io import read_json,write_json
from calnew.benchmark import code_identity

results=[]
for name in ['basic-threshold-models','basic-descriptor-models']:
    root=Path('runs')/name
    manifest=read_json(root/'run.json');report=read_json(root/'report.json');split=read_json(root/'split.json')
    assert manifest['status']=='complete' and report['failures']=={}
    assert not manifest['test_accessed'] and not (root/'holdout.json').exists()
    groups=np.array(split['groups'])
    parts=list(split['partitions'].values())
    assert all(not set(groups[a])&set(groups[b]) for i,a in enumerate(parts) for b in parts[i+1:])
    with np.load(root/'development-predictions.npz',allow_pickle=False) as arrays:
        assert np.isfinite(arrays[report['selected']]).all()
    assert (root/'model.joblib').exists() and (root/'source-code'/'benchmark.py').exists()
    assert manifest['identity']['code_identity']==code_identity()
    results.append({'run':name,'selected':report['selected'],'failures':report['failures'],
                    'group_separation':'verified','final_holdout':'unopened','source_identity':'matches_current_source',
                    'saved_model':'present','development_predictions':'finite'})
for name in ['threshold','descriptor']:
    records=read_json(Path(f'data/example-{name}-predictions.json'))
    assert all(r['status']=='available' for r in records if r['smiles']!='invalid')
    assert all(r['status']=='unavailable' for r in records if r['smiles']=='invalid')
write_json(Path('docs/verification.json'),{'basic_runs':results,'example_predictions':'verified',
                                        'prospective_validation':'not_performed','test_command':'.venv/bin/python -m pytest -q'})
print(json.dumps(results,indent=2))
