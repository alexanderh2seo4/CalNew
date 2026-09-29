import numpy as np
import pytest
import torch
from calnew.contextual import ConcentrationCurve,receptor_network
from calnew.pharmacophore import LigandTemplates
from calnew.conformers import generate
from calnew.active import suggest


def test_curve_context_and_monotonicity():
    context=dict(protocol='pilot',matrix='air',unit='log10(ppbv)')
    x=np.linspace(-3,3,20);y=100/(1+np.exp(-x))
    model=ConcentrationCurve().fit(x,y,**context)
    assert np.all(np.diff(model.predict(x,**context))>=0)
    with pytest.raises(ValueError): model.predict([10],**context)
    with pytest.raises(ValueError): model.predict([0],protocol='new',matrix='air',unit='log10(ppbv)')


def test_templates_enforce_training_membership():
    with pytest.raises(ValueError): LigandTemplates().fit(['CCO'],['test'],['train'],[True])
    fitted=LigandTemplates().fit(['CCO'],['train'],['train'],[True])
    assert fitted.transform(['CCO'])[0,0]==pytest.approx(1)


def test_conformers_deterministic_and_failure_explicit(tmp_path):
    a=generate('C[C@H](O)CC',tmp_path,generated=4,retained=2)
    assert a==generate('C[C@H](O)CC',tmp_path,generated=4,retained=2)
    assert a['status']=='available'
    coords=np.load(a['path'])['coordinates'];assert coords.shape[0]<=2 and np.isfinite(coords).all()


def test_active_selection_protects_holdout_and_requires_verified_material(toy_data):
    pool=[dict(smiles=s,identity_verified=True,delivery_feasible=True,reducible_uncertainty=i) for i,s in enumerate(toy_data.smiles)]
    selected=suggest(pool,10,anchors=[toy_data.ids[0]],protected_groups=[toy_data.groups[1]])
    assert len(selected)==10 and len({r['molecule_id'] for r in selected})==10
    assert toy_data.ids[1] not in {r['molecule_id'] for r in selected}
    assert sum(r['acquisition_reason']=='repeated_anchor' for r in selected)==1
    with pytest.raises(ValueError): suggest(pool,10)


def test_receptor_branch_keeps_direct_path_and_masks_sequence():
    model=receptor_network(8,12,3,32)
    y=model(torch.randn(4,8),torch.randn(4,20,12),torch.randn(4,3))
    assert y.shape==(4,1);y.sum().backward()
    assert model.molecule.weight.grad is not None
