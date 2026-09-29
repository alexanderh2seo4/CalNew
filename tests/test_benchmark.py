from pathlib import Path
import numpy as np
import pytest
from calnew import benchmark
from calnew.io import read_json
from calnew.predict import predict_records


def test_complete_nested_run_preserves_final_holdout(toy_data,tmp_path,monkeypatch):
    monkeypatch.setattr(benchmark,'load_task',lambda *args:toy_data)
    toy_data.metadata['target_semantics']='synthetic_test'
    config={'profile':'pilot','strategy':'grouped_random','outer_folds':2,'inner_folds':2,'trials':1,'seeds':[42],
            'bootstrap_repeats':10,'organisers':['mean','stacking'],
            'models':[{'name':'ridge','family':'classical','features':'descriptors','estimator':'linear'},
                      {'name':'rf','family':'classical','estimator':'rf','n_estimators':10}]}
    run=tmp_path/'run'
    result=benchmark.run_benchmark(tmp_path,'air_detection_threshold','synthetic',config,run,tmp_path/'features')
    assert result['failures']=={} and not read_json(run/'run.json')['test_accessed']
    assert (run/'source-code'/'benchmark.py').exists()
    with pytest.raises(ValueError): benchmark.audit_holdout(run)
    predictions=predict_records(run,['CCO','invalid-smiles'])
    assert predictions[0]['status']=='available' and predictions[1]['status']=='unavailable'
    assert predict_records(run,['CCO'],'intensity')[0]['status']=='unavailable'
    artifacts=np.load(run/'development-predictions.npz')
    assert np.isfinite(artifacts['ridge']).all()
    assert not (run/'holdout.json').exists()
