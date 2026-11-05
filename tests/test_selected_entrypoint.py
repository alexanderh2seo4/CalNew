import importlib.util
from pathlib import Path
import pytest


def load_entrypoint():
    path=Path(__file__).resolve().parents[1]/"scripts/predict_olfaction_selected.py"
    spec=importlib.util.spec_from_file_location("selected_entrypoint_test",path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_selected_threshold_drops_old_interval_and_preserves_profile(monkeypatch):
    module=load_entrypoint()
    monkeypatch.setattr(module,"predict",lambda *a,**k:{"molecules":[{"molecule_id":"M-X",
        "threshold":{"approx_90pct_log_interval":[0,5]},"at_dilution":{"profile":{"floral":4.}}}]})
    monkeypatch.setattr(module,"predict_threshold",lambda *a,**k:{"run":"new","model":"blend","endpoint":"air_detection_threshold",
        "molecules":[{"molecule_id":"M-X","log10_ppbv":2.,"ppbv":100.,"baseline_log10_ppbv":1.,"branch_log10_ppbv":3.}]})
    result=module.predict_selected(["CCO"])
    assert result["molecules"][0]["at_dilution"]["profile"]=={"floral":4.}
    assert result["molecules"][0]["threshold"]["ppbv"]==100.
    assert "approx_90pct_log_interval" not in result["molecules"][0]["threshold"]


def test_selected_heads_must_align_by_molecular_identity(monkeypatch):
    module=load_entrypoint()
    monkeypatch.setattr(module,"predict",lambda *a,**k:{"molecules":[{"molecule_id":"A-X"}]})
    monkeypatch.setattr(module,"predict_threshold",lambda *a,**k:{"molecules":[{"molecule_id":"B-X"}]})
    with pytest.raises(ValueError,match="identities"):
        module.predict_selected(["CCO"])
