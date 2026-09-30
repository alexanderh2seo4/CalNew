import numpy as np
import pytest
import torch
from rdkit import Chem

from calnew.pipeline.blocks import OSMOPHORES, block_names, compute_block, longest_aliphatic_chain
from calnew.pipeline.fusion import BlockFusion, BlockScaler, gram_schmidt, train_fusion
from calnew.pipeline.stages import HEDONIC_MEMBERS, CombinerStage, GroupedRidge, TabularEnsemble, combine_mixture, hill


@pytest.mark.parametrize("smiles,length", [("CCCCCCCC=O", 8), ("CC(C)CCCC(C)C", 7), ("c1ccccc1CCCC", 4), ("c1ccccc1", 0),
                                           ("CC(C)(C)S", 3), ("CCCCC1CCCCC1CCC", 4)])
def test_longest_aliphatic_chain_ignores_rings(smiles, length):
    assert longest_aliphatic_chain(Chem.MolFromSmiles(smiles)) == length


def test_osmophore_block_flags_expected_groups():
    names = list(OSMOPHORES)
    thiol, aldehyde, pyrazine = compute_block("osmophore", ["CCCCS", "CCCCCC=O", "COc1nccnc1C(C)C"])
    assert thiol[names.index("thiol")] == 1 and thiol[names.index("aldehyde")] == 0
    assert aldehyde[names.index("aldehyde")] == 1
    assert pyrazine[names.index("alkoxypyrazine")] == 1


def test_hbond_block_separates_donor_types():
    x = compute_block("hbond", ["CCO", "CCS", "CC(=O)C"])
    assert x.shape[0] == 3 and np.isfinite(x).all()
    assert not np.allclose(x[0], x[1])  # O-H and S-H donors are not the same feature


def test_gram_schmidt_removes_anchor_component():
    a, anchor = torch.randn(16, 8), torch.randn(16, 8)
    projected = gram_schmidt(a, anchor)
    assert torch.allclose((projected * anchor).sum(-1), torch.zeros(16), atol=1e-4)


def test_fusion_gates_sum_to_one_and_train():
    rng = np.random.default_rng(0)
    blocks = {"anchor": rng.normal(size=(40, 6)).astype(np.float32), "extra": rng.normal(size=(40, 4)).astype(np.float32)}
    y = torch.as_tensor(blocks["extra"][:, 0], dtype=torch.float32)
    net = train_fusion(blocks, lambda raw, ix: torch.nn.functional.mse_loss(raw[:, 0], y[ix]), 1, "anchor", epochs=5, width=8)
    assert sum(net.fusion.gates().values()) == pytest.approx(1)
    with pytest.raises(ValueError):
        BlockFusion({"a": 3}, "missing")


def test_block_scaler_is_train_only_and_keeps_binary_bits():
    train = {"d": np.array([[1.0, np.nan], [3.0, 2.0]], np.float32), "fp": np.array([[0, 1], [1, 0]], np.float32)}
    scaler = BlockScaler().fit(train)
    out = scaler.transform({"d": np.array([[np.nan, 100.0]], np.float32), "fp": np.array([[1, 1]], np.float32)})
    assert np.isfinite(out["d"]).all() and out["d"].max() <= 8
    assert np.array_equal(out["fp"], np.array([[1, 1]], np.float32))


def test_hill_is_monotone_and_bounded():
    x = np.linspace(-8, 0, 50)
    curve = hill(x, np.array([80.0, -4.0, 1.2]))
    assert np.all(np.diff(curve) > 0) and curve.max() < 80 and curve.min() > 0


def test_grouped_ridge_selects_alpha():
    rng = np.random.default_rng(1)
    x = rng.normal(size=(60, 5))
    y = x[:, 0] * 2 + rng.normal(scale=0.1, size=60)
    model = GroupedRidge().fit(x, y, np.repeat(np.arange(20), 3))
    assert np.corrcoef(model.predict(x), y)[0, 1] > 0.95


def test_combiner_defaults_to_mean_profile_under_strong_penalty():
    rng = np.random.default_rng(2)
    q = rng.normal(size=(30, 4)).astype(np.float32)
    profile = np.abs(rng.normal(size=(30, 3))) + np.array([5.0, 1.0, 0.5])
    model = CombinerStage(epochs=50, penalty=1e6).fit(q, np.full(30, 50.0), np.full(30, -3.0), profile, np.full(30, 40.0))
    pred, pleasant = model.predict(q, np.full(30, 50.0), np.full(30, -3.0))
    cos = pred @ profile.mean(0) / (np.linalg.norm(pred, axis=1) * np.linalg.norm(profile.mean(0)))
    assert cos.min() > 0.99 and abs(pleasant.mean() - 40) < 5
    with pytest.raises(ValueError):
        CombinerStage(epochs=5).fit(q, np.full(30, 50.0), np.full(30, -3.0), profile, np.full(30, 40.0))


def test_mixture_rule_is_labelled_unvalidated_and_normalised():
    a = {"hill": [80, -5, 1], "x": -3, "direction": [1, 0], "pleasantness": 70}
    b = {"hill": [40, -2, 1], "x": -3, "direction": [0, 1], "pleasantness": 20}
    mixed = combine_mixture([a, b])
    assert np.linalg.norm(mixed["direction"]) == pytest.approx(1)
    assert min(mixed["component_intensities_at_primacy"]) <= mixed["intensity"] <= max(mixed["component_intensities_at_primacy"])
    assert mixed["pleasantness"] > 45  # the stronger component dominates hedonics
    assert mixed["validation"].startswith("unvalidated")
    with pytest.raises(ValueError):
        combine_mixture([])


def test_quality_stage_learns_second_vocabulary_with_masked_rows():
    from calnew.pipeline.stages import QualityStage
    rng = np.random.default_rng(3)
    blocks = {"fingerprint": (rng.random((40, 16)) > 0.5).astype(np.float32), "transport": rng.normal(size=(40, 3)).astype(np.float32)}
    labels = (blocks["fingerprint"][:, :2] > 0).astype(float)
    labels[:10] = np.nan  # not assessed by the catalogue
    direction = np.abs(rng.normal(size=(40, 4)))
    direction /= np.linalg.norm(direction, axis=1, keepdims=True)
    direction[20:] = np.nan  # not panel-rated
    model = QualityStage(["fingerprint", "transport"], "fingerprint", seeds=(0,), epochs=3).fit(blocks, labels, direction)
    probabilities, embedding, predicted = model.predict(blocks)
    assert probabilities.shape == (40, 2) and embedding.shape[0] == 40
    assert np.allclose(np.linalg.norm(predicted, axis=1), 1, atol=1e-5)


def test_combiner_refuses_mismatched_prior_setting():
    rng = np.random.default_rng(4)
    q = rng.normal(size=(20, 3)).astype(np.float32)
    prior = np.full((20, 2), 1 / np.sqrt(2), np.float32)
    model = CombinerStage(epochs=5, penalty=1.0).fit(q, np.full(20, 50.0), np.full(20, -3.0), np.ones((20, 2)), np.full(20, 40.0), prior=prior)
    assert 0 < model.prior_weight < 1
    model.predict(q, np.full(20, 50.0), np.full(20, -3.0), prior)
    with pytest.raises(ValueError):
        model.predict(q, np.full(20, 50.0), np.full(20, -3.0))


def test_paper_split_is_deterministic_and_uses_paper_ratios():
    from calnew.pipeline.paper_benchmark import random_split
    tr, va, te = random_split(268, (0.6, 0.2, 0.2), 42)
    assert (len(tr), len(va), len(te)) == (160, 54, 54)  # paper Table 10
    assert tuple(map(len, random_split(474, (0.8, 0.1, 0.1)))) == (379, 47, 48)
    assert tuple(map(len, random_split(248, (0.8, 0.1, 0.1)))) == (198, 25, 25)
    assert len(set(tr) | set(va) | set(te)) == 268
    assert np.array_equal(te, random_split(268, (0.6, 0.2, 0.2), 42)[2])


def test_ravia_dilution_labels_parse_without_guessing():
    from calnew.ingest import _ravia_fraction
    assert _ravia_fraction("100.00%") == (1.0, "reported_dilution_percent")
    assert _ravia_fraction("10.00%")[0] == pytest.approx(0.1)
    assert _ravia_fraction("Solid") == (None, "solid_undiluted")
    assert _ravia_fraction("-") == (None, "unreported") and _ravia_fraction(float("nan")) == (None, "unreported")


def test_rdkit_block_is_finite_or_nan_and_named():
    x = compute_block("rdkit", ["CCO", "c1ccccc1O", "CC(C)(C)CCCCCCCCCCCCCCCCCCCC"])
    assert x.shape == (3, len(block_names("rdkit")))
    assert np.all(np.isnan(x) | (np.abs(x) <= 1e6))
    assert x[0, block_names("rdkit").index("MolWt")] == pytest.approx(46.07, abs=0.01)


def test_tabular_ensemble_averages_members_and_imputes():
    rng = np.random.default_rng(0)
    n = 80
    blocks = {name: rng.normal(size=(n, 4)).astype(np.float32) for name in ("rdkit", "transport", "hbond", "osmophore", "chain", "quality", "direction", "fingerprint")}
    blocks["rdkit"][::7, 1] = np.nan
    y = blocks["rdkit"][:, 0] * 2 + blocks["quality"][:, 0]
    y = np.nan_to_num(y)
    model = TabularEnsemble(HEDONIC_MEMBERS, seed=1, threads=1).fit(blocks, y, np.arange(n), columns=np.ones((n, 1)))
    members = model.predict_members(blocks, columns=np.ones((n, 1)))
    assert members.shape == (n, len(HEDONIC_MEMBERS))
    assert np.allclose(model.predict(blocks, columns=np.ones((n, 1))), members.mean(1))
    assert np.corrcoef(model.predict(blocks, columns=np.ones((n, 1))), y)[0, 1] > 0.8
    with pytest.raises(ValueError):
        TabularEnsemble((("svm", ("rdkit",)),)).fit(blocks, y, np.arange(n))


def test_aux_members_use_flagged_rows_and_predict_as_task_rows():
    rng = np.random.default_rng(0)
    names = ("rdkit", "transport", "hbond", "osmophore", "chain", "fingerprint")
    make = lambda n: {k: rng.normal(size=(n, 3)).astype(np.float32) for k in names}
    task, aux = make(40), make(200)
    y = task["rdkit"][:, 0].astype(float)
    y_aux = aux["rdkit"][:, 0] + 5.0  # same structure signal, different medium offset
    members = (("extra_trees+aux", names), ("ridge", ("fingerprint",)))
    with_aux = TabularEnsemble(members, seed=0, threads=1).fit(task, y, np.arange(40), auxiliary=(aux, y_aux, 1.0))
    assert with_aux.auxiliary_rows == 200
    pred = with_aux.predict_members(task)[:, 0]
    assert abs(pred.mean() - y.mean()) < 1.0  # flag 0 at prediction: no medium offset leaks in
    plain = TabularEnsemble(members, seed=0, threads=1).fit(task, y, np.arange(40))
    assert plain.auxiliary_rows == 0 and plain.predict(task).shape == (40,)
    with pytest.raises(ValueError):
        TabularEnsemble(members).fit(task, y, np.arange(40), columns=np.ones((40, 1)), auxiliary=(aux, y_aux, 1.0))


def test_exclude_touching_drops_same_molecule_and_scaffold_analogues():
    import pandas as pd
    from calnew.pipeline.auxiliary import exclude_touching
    from calnew.chemistry import identify, scaffold
    smiles = ["CCCCCCCC=O", "c1ccccc1CC=O", "c1ccccc1O", "CCCCCCCCC=O", "CC(C)(C)S"]
    aux = pd.DataFrame({"molecule_id": [identify(s).molecule_id for s in smiles], "smiles": smiles})
    aux["connectivity"] = [m.split("-")[0] for m in aux.molecule_id]
    aux["scaffold"] = [scaffold(s) for s in aux.smiles]
    held = [identify("CCCCCCCC=O").molecule_id]
    assert exclude_touching(aux, held).tolist() == [False, True, True, True, True]
    keep = exclude_touching(aux, held + [identify("c1ccccc1C").molecule_id], ["CCCCCCCC=O", "c1ccccc1C"], by_scaffold=True)
    assert keep.tolist() == [False, False, False, False, True]  # benzene scaffold and the nonanal analogue go
