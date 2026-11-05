"""Read current training-only trial progress on the compute host."""
import collections
import json
import platform
from pathlib import Path

import numpy as np
from calnew.io import write_json

report = {"host": platform.node(), "trials": {}}
for name in ("nose-intensity-keller-quality-inner-v2", "nose-intensity-ravia-robust-inner-v2",
        "nose-intensity-ravia-transport-inner-v2", "nose-intensity-ravia-joint-inner-v2"):
    root = Path("runs")/name
    if (root/"results.json").exists():
        result = json.loads((root/"results.json").read_text())
        inner = next(iter(result["results"].values()))
        report["trials"][name] = {"selected": inner["selected"], "passing": inner["passing"],
            "means": {n: {k: float(np.mean([v[k] for v in values])) for k in ("pearson", "mae", "rmse")}
                for n, values in inner["scores"].items()}}
    elif (root/"partial.json").exists():
        report["trials"][name] = {"completed_repeats": json.loads((root/"partial.json").read_text())}
    else:
        report["trials"][name] = {"complete": False}
hashes = collections.Counter()
for path in Path("runs/nose-intensity-feature-cache-v1").glob("*.json"):
    if path.name.startswith("."):
        continue
    value = json.loads(path.read_text())
    identity = value.get("identity", {})
    hashes[(identity.get("kind"), identity.get("code_sha256", {}).get("src/calnew/pipeline/stages.py"))] += 1
report["cache_stage_versions"] = [{"kind": k, "sha256": s, "count": n} for (k, s), n in hashes.items()]
print(json.dumps(report, indent=2), flush=True)
write_json(Path("runs/intensity-refinement-summary.json"), report)
