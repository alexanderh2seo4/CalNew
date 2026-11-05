import joblib
import numpy as np
import pytest
from scipy import sparse

from calnew.pipeline.cooccurrence import CooccurrenceTransfer, direction_features


def test_direction_zero_and_row_independence():
    x=np.array([[0.,0.,0.],[3.,4.,0.],[-1.,2.,3.]])
    before=direction_features(x)
    assert np.array_equal(before[0],np.zeros(4))
    assert np.allclose(before[1], [.6,.8,0.,5.])
    x[2]=1e5
    assert np.array_equal(direction_features(x)[:2],before[:2])
    with pytest.raises(ValueError):
        direction_features(np.array([[np.nan]]))


def test_transfer_roundtrip_and_prediction_preserves_source_state(tmp_path):
    rng=np.random.default_rng(4)
    x=rng.normal(size=(80,12)).astype(np.float32)
    labels=sparse.csr_matrix(rng.random((80,70))>.7,dtype=np.float32)
    fitted=CooccurrenceTransfer().fit(x,labels)
    expected=fitted.predict(x[:4])
    original_idf=fitted.tfidf.idf_.copy()
    original_axes=fitted.svd.components_.copy()
    fitted.predict(x[:4]*1000)
    assert np.array_equal(fitted.tfidf.idf_,original_idf)
    assert np.array_equal(fitted.svd.components_,original_axes)
    # Parallel tree sums can differ in their final floating point bits.
    assert np.allclose(fitted.predict(x[:4]),expected,rtol=1e-12,atol=1e-12)
    path=tmp_path/'transfer.joblib'
    joblib.dump(fitted,path)
    assert np.allclose(joblib.load(path).predict(x[:4]),expected,rtol=1e-12,atol=1e-12)
    with pytest.raises(ValueError):
        CooccurrenceTransfer().fit(x[:3],labels)
