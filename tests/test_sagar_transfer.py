import importlib.util
from pathlib import Path
import numpy as np
from sklearn.model_selection import GroupKFold


def source_module(monkeypatch):
    path=Path(__file__).resolve().parents[1]/"scripts/nose_sagar_refine.py"
    monkeypatch.syspath_prepend(str(path.parent))
    spec=importlib.util.spec_from_file_location("sagar_transfer_test",path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_forbidden_connectivity_targets_cannot_affect_source_fit(monkeypatch):
    module=source_module(monkeypatch)
    rng=np.random.default_rng(7)
    ids=np.array(["A-X","A-Y"]+[f"B{i}-X" for i in range(28)])
    x=rng.normal(size=(30,5))
    y=rng.normal(size=(30,len(module.TERMS)))
    first,audit=module.fit_source(x,y,ids,["A-Z"])
    modified=y.copy()
    modified[:2]=1e9
    second,audit2=module.fit_source(x,modified,ids,["A-Z"])
    assert audit==audit2
    assert audit["source_molecules"]==28
    assert np.array_equal(first[2],second[2])
    assert np.array_equal(first[3],second[3])
    assert np.allclose(module.source_predict(first,x),module.source_predict(second,x),rtol=1e-12,atol=1e-12)


def test_source_feature_crossfit_excludes_own_group_and_outer_held(monkeypatch):
    module=source_module(monkeypatch)
    rng=np.random.default_rng(9)
    train_ids=np.array([f"Q{i}-X" for i in range(30)])
    held_ids=np.array(["HELD-X","HELD-Y"])
    source_ids=np.r_[train_ids,held_ids,[f"S{i}-X" for i in range(40)]]
    sx=rng.normal(size=(len(source_ids),5))
    sy=rng.normal(size=(len(source_ids),len(module.TERMS)))
    tx=(rng.normal(size=(30,5)),rng.normal(size=(2,5)))
    train,held,records=module.crossfit_source(sx,sy,source_ids,tx,train_ids,held_ids,held_ids)
    groups=np.array([m.split("-")[0] for m in train_ids])
    for index,(_,b) in enumerate(GroupKFold(3,shuffle=True,random_state=173).split(train_ids,groups=groups)):
        assert set(groups[b])|{"HELD"}==set(records[index]["excluded_connectivities"])
        assert records[index]["held_connectivity_overlap"]==[]
    assert records[-1]["excluded_connectivities"]==["HELD"]
    assert train.shape==(30,len(module.TERMS)) and held.shape==(2,len(module.TERMS))
    assert np.isfinite(train).all() and np.isfinite(held).all()
