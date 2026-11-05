"""Read-only numerical/provenance inventory, executed on the SSH host."""
import importlib.util
import json
import platform
from pathlib import Path

import numpy as np

from calnew.io import file_digest, write_json
from calnew.pipeline.paper_benchmark import Context, FRACTIONS, random_split
from nose_semantic_experiment import RESERVED


def main():
    ctx = Context(Path(json.loads(Path("data/current.json").read_text())["snapshot"]), RESERVED)
    report = {"host": platform.node(), "packages": {n: importlib.util.find_spec(n) is not None
        for n in ("catboost", "lightgbm", "xgboost", "sklearn", "torch")}, "tasks": {}, "frozen_oof": {}}
    for name, frame in (("abraham", ctx.thr), ("keller", ctx.keller), ("ravia", ctx.ravia)):
        tr, va, te = random_split(len(frame), FRACTIONS[name], 42)
        ids = frame.molecule_id.to_numpy()
        conns = np.array([i.split("-")[0] for i in ids])
        report["tasks"][name] = {"eligible": len(ids), "train": len(tr), "validation": len(va), "test": len(te),
            "unique_training_connectivities": len(set(conns[tr])),
            "train_held_connectivity_overlaps": sorted(set(conns[tr]) & set(conns[np.r_[va, te]]))}
        for root in ("nose-semantic-trees-inner-v2", "nose-semantic-text-inner-v2"):
            path = Path("runs")/root/f"{name}-inner-oof.npz"
            if path.exists():
                with np.load(path, allow_pickle=False) as data:
                    report["frozen_oof"][str(path)] = {"sha256": file_digest(path),
                        "shapes": {k: list(data[k].shape) for k in data.files},
                        "ids_match_original_training": bool(np.array_equal(data["ids"], ids[tr]))}
    report["feature_dimensions"] = {n: list(x.shape) for n, x in ctx.B.items()}
    report["auxiliary_water_rows"] = len(ctx.aux)
    write_json(Path("runs/parity-probe-20261002.json"), report)
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
