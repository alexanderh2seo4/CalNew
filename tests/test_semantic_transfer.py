"""Leakage checks for the optional NOSE corpus experiment."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy import sparse


def _transfer_class():
    path = Path(__file__).resolve().parents[1] / "scripts" / "nose_semantic_experiment.py"
    spec = importlib.util.spec_from_file_location("nose_semantic_experiment", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.DescriptorTransfer


@pytest.mark.parametrize("use_text", [False, True])
@pytest.mark.parametrize("encoder", ["ridge", "extra_trees", "mlp"])
def test_transfer_excludes_all_connectivity_variants_before_fitting(use_text, encoder):
    if encoder == "mlp":
        import torch
        torch.set_num_threads(2)
    cls = _transfer_class()
    rng = np.random.default_rng(10)
    molecules = pd.DataFrame({"molecule_id": ["held-a", "held-b"] + [f"train{i}-a" for i in range(12)]})
    features = rng.normal(size=(14, 3)).astype(np.float32)
    labels = sparse.csr_matrix(rng.integers(0, 2, size=(14, 6), dtype=np.int32))
    vectors = rng.normal(size=(6, 7)).astype(np.float32) if use_text else None
    original = cls(molecules, labels, features, term_vectors=vectors, encoder=encoder, threads=2)
    expected, count = original.predict(["held-c"], features[:2])
    changed = cls(molecules, labels, features.copy(), term_vectors=vectors, encoder=encoder, threads=2)
    changed.features[:2] = 1e8
    changed.targets[:2] = -1e8
    actual, changed_count = changed.predict(["held-c"], features[:2])
    assert count == changed_count == 12
    np.testing.assert_array_equal(actual, expected)


def test_transfer_crossfit_excludes_predicted_training_rows_and_fixed_holdouts():
    cls = _transfer_class()
    ids = np.array([f"train{i}-a" for i in range(9)])
    features = np.arange(9, dtype=np.float32)[:, None]
    transfer = cls(pd.DataFrame({"molecule_id": ids}), sparse.eye(9, format="csr"), features)
    calls = []

    def record_predict(excluded, x):
        excluded = set(excluded)
        calls.append(excluded)
        assert "outer-test-a" in excluded
        for row in x[:, 0].astype(int):
            if row < 9:
                assert ids[row] in excluded
        return np.repeat(x, 128, axis=1), 1

    transfer.predict = record_predict
    train, test, _ = transfer.crossfit(ids, ["outer-test-a"], features, np.array([[99]], np.float32), 42)
    assert len(calls) == 4 and calls[-1] == {"outer-test-a"}
    np.testing.assert_array_equal(train[:, 0], features[:, 0])
    assert test[0, 0] == 99


def test_physical_property_loader_never_requests_odor_targets(monkeypatch):
    path = Path(__file__).resolve().parents[1] / "scripts" / "abraham_properties_experiment.py"
    spec = importlib.util.spec_from_file_location("abraham_properties_experiment", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    requested = []

    def source_reader(path, *, usecols):
        requested.append(set(usecols))
        if Path(path).name == "behavior.csv":
            assert set(usecols) == {"Stimulus", "E", "S", "A", "B", "L", "V"}
            return pd.DataFrame({name: [1.0] for name in usecols})
        assert set(usecols) == {"CID", "IsomericSMILES"}
        return pd.DataFrame({"CID": [1], "IsomericSMILES": ["CCO"]})

    monkeypatch.setattr(module.pd, "read_csv", source_reader)
    monkeypatch.setattr(module, "file_digest", lambda _: "synthetic-source")
    properties, manifest = module.property_table()
    assert len(properties) == 1 and list(properties.columns) == list(module.PROPERTIES)
    assert len(requested) == 2 and manifest["odor_target_columns_loaded"] is False


def test_semantic_head_final_fit_and_serialization(tmp_path):
    import joblib
    from calnew.pipeline.semantic import DescriptorTransfer, SemanticHead
    rng = np.random.default_rng(43)
    ids = np.asarray([f"m{i}-a" for i in range(18)])
    source = rng.normal(size=(18,4)).astype(np.float32)
    labels = sparse.csr_matrix(rng.integers(0,2,size=(18,6)))
    transfer = DescriptorTransfer(pd.DataFrame({"molecule_id":ids}), labels, source)
    base = rng.normal(size=(9,5)).astype(np.float32)
    model = SemanticHead().fit(transfer,ids[:9],[],source[:9],source[:0],base,base[:,0],threads=1)
    expected = model.predict(source[:9],base)
    path = tmp_path / "head.joblib"
    joblib.dump(model,path)
    np.testing.assert_array_equal(joblib.load(path).predict(source[:9],base),expected)


def test_frozen_molecular_loader_rejects_mutated_artifact(tmp_path):
    from calnew.io import file_digest, write_json
    path = Path(__file__).resolve().parents[1] / "scripts" / "nose_semantic_experiment.py"
    spec = importlib.util.spec_from_file_location("nose_semantic_experiment",path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    artifact = tmp_path / "vectors.npz"
    np.savez(artifact,smiles=np.asarray(["CCO","CC"]),vectors=np.ones((2,513),np.float32))
    write_json(artifact.with_suffix(".json"),{"sha256":file_digest(artifact),"training":"unlabeled molecular pretraining; frozen"})
    actual,_ = module.frozen_molecular_vectors(artifact,["CC","CCO"])
    assert actual.shape == (2,513)
    with artifact.open("ab") as handle:
        handle.write(b"tampered")
    with pytest.raises(ValueError,match="checksum"):
        module.frozen_molecular_vectors(artifact,["CCO"])


def test_inner_comparison_rejects_changed_endpoint_targets(tmp_path):
    path = Path(__file__).resolve().parents[1] / "scripts" / "compare_semantic_inner.py"
    spec = importlib.util.spec_from_file_location("compare_semantic_inner",path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    baseline,candidate = tmp_path/"baseline.npz",tmp_path/"candidate.npz"
    ids = np.asarray(["a","b","c","d"])
    y = np.asarray([0.,1.,2.,3.])
    prediction = np.repeat(y[None,:],3,axis=0)
    np.savez(baseline,ids=ids,y=y,v2=prediction)
    np.savez(candidate,ids=ids,y=y+1,semantic=prediction)
    with pytest.raises(ValueError,match="IDs/targets differ"):
        module.compare(baseline,candidate)
