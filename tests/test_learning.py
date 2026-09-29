import numpy as np
import pytest
import torch
from scipy.stats import norm
from calnew.calibration import GroupConformal,ProbabilityCalibrator
from calnew.losses import censored_normal_nll,forced_choice_probability
from calnew.splits import structural_groups,partition_groups,assert_disjoint,source_holdout
from calnew.ensemble import Organiser
from calnew.models import make_model
from calnew.models.classical import tanimoto


def test_splits_keep_molecules_together(toy_data):
    groups=structural_groups(toy_data)
    parts=partition_groups(groups)
    assert_disjoint(toy_data,*parts)
    assert sum(map(len,parts))==len(toy_data.ids)
    assert all(not set(groups[a])&set(groups[b]) for i,a in enumerate(parts) for b in parts[i+1:])
    with pytest.raises(ValueError): assert_disjoint(toy_data,[0],[0])
    toy_data.source_ids[:5]='held'
    train,test=source_holdout(toy_data,'held');assert len(test)==5 and not set(train)&set(test)


def test_censored_likelihood_matches_distribution_and_backpropagates():
    mean=torch.zeros(4,dtype=torch.float64,requires_grad=True);logs=torch.zeros(4,dtype=torch.float64,requires_grad=True)
    value=torch.tensor([0.,float('nan'),float('nan'),float('nan')],dtype=torch.float64)
    lower=torch.tensor([float('nan'),float('nan'),2.,8.],dtype=torch.float64)
    upper=torch.tensor([float('nan'),-2.,float('nan'),9.],dtype=torch.float64)
    loss=censored_normal_nll(mean,logs,value,lower,upper,torch.arange(4))
    expected=(-norm.logpdf(0)-norm.logcdf(-2)-norm.logsf(2)-np.log(norm.sf(8)-norm.sf(9)))/4
    assert loss.item()==pytest.approx(expected,rel=1e-6)
    loss.backward();assert torch.isfinite(mean.grad).all() and torch.isfinite(logs.grad).all()
    assert forced_choice_probability(torch.tensor(0.),0,1).item()==pytest.approx(2/3)


def test_group_conformal_not_participant_pseudoreplication():
    y=np.arange(10.)[:,None];p=np.zeros_like(y);groups=np.array([str(i) for i in range(10)])
    a=GroupConformal().fit(y,p,groups)
    b=GroupConformal().fit(np.repeat(y,5,axis=0),np.repeat(p,5,axis=0),np.repeat(groups,5))
    assert a.quantiles==b.quantiles and a.counts==[10]
    assert np.isinf(GroupConformal().fit(y[:2],p[:2],groups[:2]).quantiles).all()


def test_organiser_rejects_in_sample_lineage():
    p=np.ones((3,2,1));y=np.ones((3,1))
    with pytest.raises(ValueError): Organiser().fit(p,y,row_ids=['a','b','c'],training_ids_by_prediction=[['a'],[],[]])
    for method in ['mean','stacking','gating']:
        model=Organiser(method).fit(p,y,row_ids=['a','b','c'])
        assert np.isfinite(model.predict(p)).all()
        assert np.isnan(model.predict(np.full_like(p,np.nan))).all()


@pytest.mark.parametrize('config',[{'family':'classical','estimator':'linear','features':'descriptors'},
    {'family':'classical','estimator':'rf','n_estimators':10},
    {'family':'classical','estimator':'gp'},
    {'family':'graph','width':32,'depth':3,'epochs':2}])
def test_model_predicts_unseen_molecules_and_roundtrips(config,toy_data,tmp_path):
    import joblib
    model=make_model(config,'regression',tmp_path).fit(toy_data.subset(range(25)))
    prediction=model.predict(toy_data.smiles[25:]);assert prediction.shape==(11,1) and np.isfinite(prediction).all()
    assert set(model.training_groups).isdisjoint(toy_data.groups[25:])
    model.save(tmp_path/'model.joblib')
    np.testing.assert_allclose(joblib.load(tmp_path/'model.joblib').predict(toy_data.smiles[25:]),prediction,rtol=1e-5)


def test_classical_censoring_never_silently_dropped(toy_data,tmp_path):
    toy_data.censoring[0]='left';toy_data.upper[0]=toy_data.y[0];toy_data.y[0]=np.nan
    with pytest.raises(ValueError): make_model({'family':'classical'},'regression',tmp_path).fit(toy_data)


def test_tanimoto_matches_non_blas_oracle():
    rng=np.random.default_rng(42);x=rng.integers(0,2,(20,64)).astype(float)
    expected=np.array([[np.logical_and(a,b).sum()/np.logical_or(a,b).sum() for b in x] for a in x])
    np.testing.assert_allclose(tanimoto(x,x),expected,rtol=1e-7)
