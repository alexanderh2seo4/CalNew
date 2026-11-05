"""Check actual intensity bundles and the CLI on the SSH compute host."""
import argparse
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

import numpy as np
import torch
from threadpoolctl import threadpool_limits

from calnew.chemistry import chemistry_version, identify
from calnew.io import digest, file_digest, write_json
from calnew.pipeline.blocks import BlockCache
from calnew.pipeline.intensity import predict_intensity
from calnew.pipeline.paper_benchmark import Context
from calnew.pipeline.run import predict
from nose_semantic_experiment import RESERVED


def prepare_frozen_subset(ctx, smiles):
    """Slice existing frozen embeddings, retaining a checksum of their source."""
    rows = [ctx.smiles.index(s) for s in smiles]
    block = "unimol2"
    full_meta = {"block": block, "version": BlockCache.VERSION, "chemistry": chemistry_version(), "smiles": ctx.smiles}
    source = Path("data/features/pipeline-blocks")/f"{block}-{digest(full_meta)[:24]}.npz"
    with np.load(source, allow_pickle=False) as data:
        values = data["x"][rows]
    np.testing.assert_array_equal(values, ctx.B[block][rows])
    meta = {**full_meta, "smiles": smiles}
    target = source.parent/f"{block}-{digest(meta)[:24]}.npz"
    np.savez_compressed(target, x=values)
    write_json(target.with_suffix(".json"), {**meta, "shape": list(values.shape),
        "training": "Existing frozen molecular embeddings; exact row subset, no new label fitting",
        "source": str(source), "source_sha256": file_digest(source), "source_rows": rows})


def main(args):
    torch.set_num_threads(2)
    root = Path.cwd()
    ctx = Context(Path(json.loads(Path("data/current.json").read_text())["snapshot"]), RESERVED)
    smiles = list(dict.fromkeys([ctx.keller.smiles.iloc[0], ctx.ravia.smiles.iloc[0]]))
    smiles = [identify(s).smiles for s in smiles]
    prepare_frozen_subset(ctx, smiles)
    keller = "runs/nose-intensity-keller-refit-v3"
    ravia = str(args.ravia_run)
    standalone_k = predict_intensity(keller, smiles, dilution=.001, return_curve=True)
    values = np.array([[p["intensity_0_100"] for p in m["dose_response"]["curve"]] for m in standalone_k["molecules"]]).T
    assert np.isfinite(values).all() and values.min() >= 0 and values.max() <= 100
    assert np.min(np.diff(values, axis=0)) >= -1e-5
    standalone_r = predict_intensity(ravia, smiles, dataset="ravia")
    baseline = predict("runs/modular-pipeline-fingerprint-v5", smiles)
    combined = predict("runs/modular-pipeline-fingerprint-v5", smiles, intensity_run=keller, mixture=True)
    for old, new, head in zip(baseline["molecules"], combined["molecules"], standalone_k["molecules"]):
        assert old["threshold"] == new["threshold"]
        assert new["at_dilution"]["intensity_0_100"] == head["intensity_0_100"]
        assert new["at_dilution"]["intensity_seed_sd"] is None
    primary = predict_intensity(keller, smiles, dilution=.0002)
    np.testing.assert_allclose(combined["mixture"]["component_intensities_at_primacy"],
        [m["intensity_0_100"] for m in primary["molecules"]])
    cli_checks = {}
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root/"src")
    for dataset, run in (("keller", keller), ("ravia", ravia)):
        out = Path("runs")/f"ssh-smoke-cli-{dataset}.json"
        result = subprocess.run([sys.executable, "-m", "calnew", "pipeline", "intensity-predict", "--run", run,
            "--dataset", dataset, "--smiles"]+smiles+["--out", str(out)], check=True, capture_output=True, text=True, env=env)
        actual = json.loads(result.stdout)
        assert json.loads(out.read_text()) == actual
        cli_checks[dataset] = actual
    rejected = subprocess.run([sys.executable, "-m", "calnew", "pipeline", "intensity-predict", "--run", ravia,
        "--dataset", "ravia", "--smiles", smiles[0], "--dilution", ".01"], capture_output=True, text=True, env=env)
    assert rejected.returncode == 2 and "no validated dilution" in rejected.stderr
    report = {"host": platform.node(), "smiles": smiles, "dose_grid_points": len(values),
        "monotonicity_violations": 0, "thresholds_unchanged": True, "mixture_uses_selected_primacy_intensities": True,
        "ravia_dilution_guard": True, "cli_out_roundtrips": True, "standalone_keller": standalone_k,
        "standalone_ravia": standalone_r, "combined": combined, "cli": cli_checks}
    write_json(args.out, report)
    print(json.dumps({k: v for k, v in report.items() if k not in ("standalone_keller", "standalone_ravia", "combined", "cli")}, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ravia-run", type=Path, default=Path("runs/nose-intensity-ravia-dose-transfer-refit-v1"))
    parser.add_argument("--out", type=Path, default=Path("runs/intensity-ssh-smoke.json"))
    args = parser.parse_args()
    with threadpool_limits(limits=2):
        main(args)
