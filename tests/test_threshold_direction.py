import json
from types import SimpleNamespace

import numpy as np
import pytest

from calnew.io import file_digest
from calnew.pipeline import threshold_direction as module


def test_threshold_serving_converts_reciprocal_ppm_to_ppbv(tmp_path,monkeypatch):
    artifact=tmp_path/"threshold-transfer.joblib"
    artifact.write_bytes(b"test-only-artifact")
    (tmp_path/"serving.json").write_text(json.dumps({"artifact_sha256":file_digest(artifact)}))
    monkeypatch.setattr(module.joblib,"load",lambda _: {"feature_blocks":[]})
    monkeypatch.setattr(module,"BlockCache",lambda _: SimpleNamespace(blocks=lambda names,smiles:{}))
    # A reciprocal-ppm prediction of 2 means 0.01 ppm = 10 ppbv.
    monkeypatch.setattr(module,"predict_bundle",lambda bundle,blocks:(np.array([1.]),np.array([3.]),np.array([2.])))
    result=module.predict_threshold(tmp_path,["CCO"])["molecules"][0]
    assert result["log10_ppbv"]==1.
    assert result["ppbv"]==10.
    assert result["baseline_log10_ppbv"]==2.
    assert result["branch_log10_ppbv"]==0.


def test_threshold_artifact_checksum_checked_before_deserialization(tmp_path,monkeypatch):
    (tmp_path/"threshold-transfer.joblib").write_bytes(b"changed")
    (tmp_path/"serving.json").write_text(json.dumps({"artifact_sha256":"incorrect"}))
    def refuse(*args):
        pytest.fail("A modified artifact must never be deserialized")
    monkeypatch.setattr(module.joblib,"load",refuse)
    with pytest.raises(ValueError,match="checksum"):
        module.predict_threshold(tmp_path,["CCO"])
