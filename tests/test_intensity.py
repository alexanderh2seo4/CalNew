"""Dose-response invariants and saved-model behavior."""
import joblib
import numpy as np
import pytest

from calnew.pipeline.intensity import MonotoneDoseTrees


def test_dose_trees_preserve_monotonicity_missing_geometry_and_serialization(tmp_path):
    rng = np.random.default_rng(31)
    structure = rng.normal(size=(45, 3))
    geometry = rng.normal(size=(45, 4))
    geometry[::4] = np.nan
    rows = np.repeat(np.arange(45), 3)
    dose = np.tile([-7., -4., -1.], 45)
    y = 100/(1+np.exp(-(dose+4+structure[rows, 0])))
    blocks = {"structure": structure[rows], "geometry": geometry[rows]}
    model = MonotoneDoseTrees((("structure",), ("geometry",)), threads=1).fit(blocks, dose, y)
    grid = np.linspace(-10, 0, 101)
    features = {"structure": np.repeat(structure[:1], len(grid), axis=0),
        "geometry": np.full((len(grid), 4), np.nan)}
    members = model.predict_members(features, grid)
    assert np.isfinite(members).all()
    assert np.min(members) >= 0 and np.max(members) <= 100
    assert np.all(np.diff(members, axis=0) >= -1e-6)
    assert members[-1, 0] > members[0, 0]+30
    path = tmp_path/"dose.joblib"
    joblib.dump(model, path)
    np.testing.assert_array_equal(joblib.load(path).predict(features, grid), model.predict(features, grid))


@pytest.mark.parametrize("dose", [[float("nan")], [.1], [[-3]]])
def test_dose_trees_reject_invalid_dilutions(dose):
    with pytest.raises(ValueError, match="Log10 dilution"):
        MonotoneDoseTrees((("s",),), threads=1).fit({"s": np.ones((1, 2))}, dose, np.array([40.]))


def test_recipe_serving_roundtrip_and_endpoint_specific_dilution(tmp_path, monkeypatch):
    from calnew.io import file_digest, write_json
    from calnew.pipeline.intensity import IntensityRecipe, predict_intensity
    from calnew.pipeline import blocks as feature_module
    rng = np.random.default_rng(21)
    x = rng.normal(size=(40, 513)).astype(np.float32)
    x[:, -1] = 1
    model = IntensityRecipe("ravia", "molecular", threads=1).fit({"unimol1": x}, 50+10*x[:, 0], np.arange(40))
    artifact = tmp_path/"intensity-ravia.joblib"
    joblib.dump({"model": model, "quality": None, "quality_blocks": [], "molecular_artifact": "synthetic.npz"}, artifact)
    write_json(tmp_path/"serving-ravia.json", {"artifact_sha256": file_digest(artifact), "validated_endpoint": "Ravia highest presentation"})
    monkeypatch.setattr(feature_module.BlockCache, "blocks", lambda self, names, smiles: {})
    from calnew.pipeline import molecular
    monkeypatch.setattr(molecular, "unimol1_vectors", lambda smiles, path: x[:len(smiles)])
    actual = predict_intensity(tmp_path, ["CCO", "CC"], "ravia", cache_root=tmp_path)
    np.testing.assert_array_equal([r["intensity_0_100"] for r in actual["molecules"]], model.predict({"unimol1": x[:2]}))
    assert "dilution" not in actual["molecules"][0]
    with pytest.raises(ValueError, match="no validated dilution"):
        predict_intensity(tmp_path, ["CCO"], "ravia", .01)
    with artifact.open("ab") as f:
        f.write(b"tampered")
    with pytest.raises(ValueError, match="checksum"):
        predict_intensity(tmp_path, ["CCO"], "ravia")


def test_molecular_loader_alignment_and_checksum(tmp_path):
    from calnew.io import file_digest, write_json
    from calnew.pipeline.molecular import unimol1_vectors
    path = tmp_path/"vectors.npz"
    values = np.ones((2, 513), np.float32)
    values[1, :-1] = np.nan
    values[1, -1] = 0
    np.savez(path, smiles=np.asarray(["CCO", "CC"]), vectors=values)
    write_json(path.with_suffix(".json"), {"sha256": file_digest(path), "training": "unlabeled molecular pretraining; frozen"})
    actual = unimol1_vectors(["CC", "OCC"], path)
    np.testing.assert_array_equal(actual, values[[1, 0]])
    with path.open("ab") as f:
        f.write(b"tampered")
    with pytest.raises(ValueError, match="checksum"):
        unimol1_vectors(["CC"], path)


@pytest.mark.parametrize("mode", ["regularized", "all_trees"])
def test_regularized_ravia_recipe_reloads_with_its_feature_schema(tmp_path, mode):
    from calnew.pipeline.intensity import IntensityRecipe
    from calnew.pipeline.stages import RAVIA_MEMBERS
    rng = np.random.default_rng(44)
    names = {n for _, member in RAVIA_MEMBERS for n in member}
    blocks = {n: rng.normal(size=(45, 3)).astype(np.float32) for n in names}
    blocks["unimol2"][::3, 0] = np.nan
    y = 50+10*blocks["rdkit"][:, 0]
    model = IntensityRecipe("ravia", mode, threads=1).fit(blocks, y, np.arange(45))
    assert set(model.feature_names) == names
    path = tmp_path/"ravia.joblib"
    joblib.dump(model, path)
    np.testing.assert_array_equal(joblib.load(path).predict(blocks), model.predict(blocks))


def test_ravia_transfer_blends_reference_doses_and_reloads_without_a_dilution_input(tmp_path):
    from calnew.pipeline.dose_transfer import RaviaDoseTransfer, REFERENCE_DOSES
    from calnew.pipeline.semantic import SEMANTIC_BASE
    from calnew.pipeline.stages import TabularEnsemble
    from sklearn.linear_model import Ridge
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    rng = np.random.default_rng(55)
    blocks = {n: rng.normal(size=(30, 2)) for n in SEMANTIC_BASE}
    source = MonotoneDoseTrees((("rdkit",),), threads=1).fit(blocks, np.linspace(-7, 0, 30),
        np.linspace(10, 90, 30))
    proxies = np.column_stack([source.predict(blocks, np.full(30, dose)) for dose in REFERENCE_DOSES])
    y = 40+5*blocks["rdkit"][:, 0]
    ridge = make_pipeline(StandardScaler(), Ridge(alpha=10)).fit(proxies, y)
    baseline = TabularEnsemble((("extra_trees", ("rdkit",)),), threads=1).fit(blocks, y, np.arange(30))
    model = RaviaDoseTransfer(baseline, source, ridge)
    actual = model.predict_parts(blocks)
    np.testing.assert_allclose(actual["selected"], (baseline.predict(blocks)+np.clip(ridge.predict(proxies), 0, 100))/2)
    assert set(model.feature_names) == set(SEMANTIC_BASE)
    artifact = tmp_path/"transfer.joblib"
    joblib.dump(model, artifact)
    np.testing.assert_array_equal(joblib.load(artifact).predict(blocks), actual["selected"])
    with pytest.raises(ValueError, match="single endpoint"):
        model.predict(blocks, np.full(30, -3.))


def test_shared_study_head_handles_missing_features_and_serializes_the_selected_blend(tmp_path):
    from calnew.pipeline.joint_intensity import JointStudyTrees, RaviaJointIntensity
    from calnew.pipeline.intensity import IntensityRecipe
    from calnew.pipeline.semantic import SEMANTIC_BASE
    from calnew.pipeline.stages import RAVIA_MEMBERS
    rng = np.random.default_rng(79)
    names = set(SEMANTIC_BASE) | {n for _, member in RAVIA_MEMBERS for n in member}
    blocks = {n: rng.normal(size=(60, 3)) for n in names}
    blocks["rdkit"][::5, 1] = np.nan
    source = {n: v[:40] for n, v in blocks.items()}
    target = {n: v[40:] for n, v in blocks.items()}
    y = np.clip(50+10*blocks["rdkit"][:, 0], 0, 100)
    joint = JointStudyTrees(threads=1).fit(source, np.linspace(-7, -1, 40), y[:40], target, y[40:])
    current = IntensityRecipe("ravia", "baseline", threads=1).fit(target, y[40:], np.arange(20))
    model = RaviaJointIntensity(current, joint)
    parts = model.predict_parts(target)
    np.testing.assert_allclose(parts["selected"], (current.predict(target)+joint.predict(target))/2)
    assert np.isfinite(parts["selected"]).all() and np.all((parts["selected"] >= 0)&(parts["selected"] <= 100))
    artifact = tmp_path/"joint.joblib"
    joblib.dump(model, artifact)
    np.testing.assert_array_equal(joblib.load(artifact).predict(target), parts["selected"])
    with pytest.raises(ValueError, match="single endpoint"):
        model.predict(target, np.zeros(20))


def test_keller_proxy_excludes_held_connectivity_variants_and_each_training_feature_group(monkeypatch):
    import importlib
    from pathlib import Path
    from types import SimpleNamespace
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]/"scripts"))
    transfer = importlib.import_module("nose_ravia_dose_transfer")
    ids = np.asarray(["a-one", "a-two", "b-one", "c-one", "d-one", "e-one", "f-one"])
    held = np.asarray(["held-variant"])
    calls = []

    def source(ctx, source_ids, excluded, threads):
        calls.append(set(excluded))
        return set(excluded), 0

    def proxy(excluded, ctx, target_ids):
        assert "held" in excluded
        if len(calls) <= 3:
            assert all(i.split("-")[0] in excluded for i in target_ids)
        return np.zeros((len(target_ids), 3))

    monkeypatch.setattr(transfer, "source_model", source)
    monkeypatch.setattr(transfer, "proxy", proxy)
    transfer.crossfit(None, ids, ids, held, held, 1)
    assert len(calls) == 4 and calls[-1] == {"held"}

    # Exercise the real source filtering with a held molecule's alternate variant.
    monkeypatch.undo()
    data = SimpleNamespace(panel={"molecule_ids": np.asarray(["held-other", "safe-one"]),
        "x": np.asarray([-3., -3.]), "intensity": np.asarray([20., 30.])})
    ctx = SimpleNamespace(data=data, p_rows=np.array([0, 1]), connectivity=np.asarray(["held", "safe"]),
        B={n: np.asarray([[1.], [2.]]) for n in transfer.SEMANTIC_BASE})
    def fit(self, blocks, dose, target):
        assert target.tolist() == [30.] and dose.tolist() == [-3.]
        assert all(v[:, 0].tolist() == [2.] for v in blocks.values())
        return self
    monkeypatch.setattr(transfer.MonotoneDoseTrees, "fit", fit)
    _, count = transfer.source_model(ctx, data.panel["molecule_ids"], {"held"}, 1)
    assert count == 1


@pytest.mark.parametrize("mixture", [False, True])
def test_pipeline_uses_selected_intensity_before_combiner_and_at_mixture_primacy(monkeypatch, mixture):
    from types import SimpleNamespace
    from calnew.pipeline import intensity as intensity_module, run
    received, doses = [], []
    quality = SimpleNamespace(predict=lambda b: (np.array([[.2, .8]]), np.ones((1, 2)), np.array([[1., 0.]])))
    hill = SimpleNamespace(params=lambda b: np.array([[[80., -5., 1.]]]),
        predict=lambda b, x: (np.array([15.]), np.array([3.])))

    def combine(q, i, x, d):
        received.append(i.copy())
        return np.column_stack([i, i/2]), np.array([50.])

    bundle = {"settings": {"quality_blocks": ["fingerprint"], "potency_blocks": ["fingerprint"]},
        "quality": quality, "intensity": hill,
        "threshold": SimpleNamespace(predict=lambda b: {"ensemble": np.array([2.]), "fusion_sd": np.array([.1])}),
        "combiner": SimpleNamespace(predict=combine, direction=lambda q, d: d), "dilution_range": [-7, -1],
        "training_smiles": {}, "labels": ["a", "b"], "descriptors": ["d1", "d2"],
        "threshold_abs_error_q90": 1., "anchor": "fingerprint"}
    monkeypatch.setattr(run.joblib, "load", lambda p: bundle)
    monkeypatch.setattr(run, "BlockCache", lambda root: SimpleNamespace(blocks=lambda names, smiles: {n: np.ones((1, 2)) for n in names}))

    def selected(path, smiles, dataset, dilution, cache_root, return_curve=False):
        doses.append(dilution)
        assert dataset == "keller"
        return {"recipe": "blend_dose_semantic", "validated_endpoint": "Keller",
            "molecules": [{"intensity_0_100": 88. if return_curve else 40.,
                "dose_response": {"representation": "blend_dose_semantic", "curve": []}}]}

    monkeypatch.setattr(intensity_module, "predict_intensity", selected)
    base = run.predict("base", ["CCO"])
    actual = run.predict("base", ["CCO"], mixture=mixture, intensity_run="selected")
    assert received[0][0] == 15 and received[1][0] == 88
    assert actual["molecules"][0]["at_dilution"]["intensity_0_100"] == 88
    assert actual["molecules"][0]["at_dilution"]["intensity_seed_sd"] is None
    assert actual["molecules"][0]["threshold"] == base["molecules"][0]["threshold"]
    assert actual["molecules"][0]["dose_response"]["representation"] == "blend_dose_semantic"
    if mixture:
        assert doses == [.001, .0002] and actual["mixture"]["intensity"] == 40
    else:
        assert doses == [.001]
