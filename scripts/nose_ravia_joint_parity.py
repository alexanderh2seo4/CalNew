"""Verify the serving class reproduces the frozen training experiment."""
import json
import platform
from pathlib import Path

import numpy as np
from sklearn.model_selection import GroupKFold
from threadpoolctl import threadpool_limits

from calnew.io import write_json
from calnew.pipeline.joint_intensity import JointStudyTrees
from calnew.pipeline.paper_benchmark import Context, FRACTIONS, random_split
from nose_semantic_experiment import RESERVED

with threadpool_limits(limits=2):
    ctx = Context(Path(json.loads(Path("data/current.json").read_text())["snapshot"]), RESERVED)
    tr, va, te = random_split(len(ctx.ravia), FRACTIONS["ravia"], 42)
    all_ids = ctx.ravia.molecule_id.to_numpy()
    ids, fixed = all_ids[tr], all_ids[np.r_[va, te]]
    groups = np.array([i.split("-")[0] for i in ids])
    a, b = next(GroupKFold(5, shuffle=True, random_state=100).split(ids, groups=groups))
    excluded = {i.split("-")[0] for i in np.r_[fixed, ids[b]]}
    ktr, _, _ = random_split(len(ctx.keller), FRACTIONS["keller"], 42)
    source_ids = [i for i in ctx.keller.molecule_id.to_numpy()[ktr] if i.split("-")[0] not in excluded]
    mask = np.isin(ctx.data.panel["molecule_ids"], source_ids)
    sr, ra, rb = ctx.p_rows[mask], ctx.rows(ids[a]), ctx.rows(ids[b])
    model = JointStudyTrees(threads=2).fit({n: v[sr] for n, v in ctx.B.items()}, ctx.data.panel["x"][mask],
        ctx.data.panel["intensity"][mask], {n: v[ra] for n, v in ctx.B.items()}, ctx.ravia.y.to_numpy()[tr][a], .25)
    actual = model.predict({n: v[rb] for n, v in ctx.B.items()})
    with (np.load("runs/nose-intensity-ravia-joint-inner-v2/ravia-inner-oof.npz", allow_pickle=False) as selected,
            np.load("runs/nose-intensity-ravia-dose-transfer-inner-v1/ssh-baseline-verification.npz", allow_pickle=False) as old):
        expected = 2*selected["joint_0.25_current"][0, b]-old["selected"][0, b]
    np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-4)
    report = {"host": platform.node(), "module_matches_frozen_experiment": True,
        "max_absolute_difference": float(np.max(np.abs(actual-expected))), "scope": "First original-training CV fold only"}
    write_json(Path("runs/nose-intensity-ravia-joint-inner-v2/module-parity.json"), report)
    print(json.dumps(report, indent=2), flush=True)
