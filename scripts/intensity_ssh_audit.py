"""Inspect and export intensity results on the SSH host, without local compute."""
import argparse
import json
import platform
import tarfile
from pathlib import Path

import numpy as np

from calnew.io import file_digest, write_json

RUNS = (
    "nose-intensity-keller-v3", "nose-intensity-keller-refit-v3",
    "nose-intensity-ravia-v3", "nose-intensity-ravia-refit-v3",
    "nose-intensity-ravia-dose-transfer-inner-v1", "nose-intensity-ravia-dose-transfer-v1",
    "nose-intensity-ravia-dose-transfer-refit-v1",
    "nose-intensity-keller-quality-inner-v2", "nose-intensity-ravia-robust-inner-v2",
    "nose-intensity-ravia-transport-inner-v2", "nose-intensity-ravia-joint-inner-v2",
    "nose-intensity-ravia-joint-v2", "nose-intensity-ravia-joint-refit-v2",
)


def audit():
    report = {"host": platform.node(), "runs": {}}
    for name in RUNS:
        root = Path("runs")/name
        if not (root/"results.json").exists():
            report["runs"][name] = {"completed_splits": len(list(root.glob("split-*.npz")))}
            continue
        results = json.loads((root/"results.json").read_text())
        record = {k: results[k] for k in ("recipe", "summary", "positive_pearson_splits", "reserved_holdouts_opened") if k in results}
        if "results" in results:
            inner = next(iter(results["results"].values()))
            record["selection"] = inner["selected"]
            record["training_cv"] = {n: {k: float(np.mean([v[k] for v in scores]))
                for k in ("pearson", "mae", "rmse")} for n, scores in inner["scores"].items()}
        if "per_split" in results:
            values = results["per_split"]
            record["pearson_gains"] = {s: v["selected"]["pearson"]-v["baseline"]["pearson"] for s, v in values.items()}
            record["mae_wins"] = sum(v["selected"]["mae"] < v["baseline"]["mae"] for v in values.values())
            if "all_stimuli" in next(iter(values.values())):
                record["all_stimuli"] = {n: {k: float(np.mean([v["all_stimuli"][n][k] for v in values.values()]))
                    for k in ("pearson", "mae", "rmse")} for n in ("baseline", "selected")}
                record["dose_monotonicity_violations"] = sum(v["dose_monotonicity_violations"] for v in values.values())
        for manifest in root.glob("serving-*.json"):
            data = json.loads(manifest.read_text())
            artifact = root/(manifest.stem.replace("serving-", "intensity-")+".joblib")
            if file_digest(artifact) != data["artifact_sha256"]:
                raise ValueError(f"Artifact checksum changed: {artifact}")
            record["serving"] = data
            record["artifact_bytes"] = artifact.stat().st_size
        if "dose-transfer" in name and "inner" not in name:
            old = Path("runs")/("nose-intensity-ravia-refit-v3" if "refit" in name else "nose-intensity-ravia-v3")
            differences = []
            for split in range(42, 52):
                with np.load(root/f"split-{split}.npz", allow_pickle=False) as new, np.load(old/f"split-{split}.npz", allow_pickle=False) as previous:
                    if not np.array_equal(new["ids"], previous["ids"]) or not np.array_equal(new["y"], previous["y"]):
                        raise ValueError("Ravia evaluation assignment/target changed")
                    differences.append(float(np.max(np.abs(new["baseline"]-previous["baseline"]))))
            record["original_test_ids_and_targets_verified"] = True
            record["max_paired_baseline_difference_from_macos"] = max(differences)
        if "ravia-joint" in name and "inner" not in name:
            old = Path("runs")/("nose-intensity-ravia-dose-transfer-refit-v1" if "refit" in name else "nose-intensity-ravia-dose-transfer-v1")
            differences = []
            for split in range(42, 52):
                with np.load(root/f"split-{split}.npz", allow_pickle=False) as new, np.load(old/f"split-{split}.npz", allow_pickle=False) as previous:
                    if not np.array_equal(new["ids"], previous["ids"]) or not np.array_equal(new["y"], previous["y"]):
                        raise ValueError("Shared-study test assignments/targets changed")
                    differences.append(float(np.max(np.abs(new["baseline"]-previous["selected"]))))
            if max(differences) > 1e-6:
                raise ValueError("Improved baseline changed in shared-study comparison")
            record["previous_improved_baseline_verified"] = True
            record["max_baseline_difference_from_previous_head"] = max(differences)
            record["main_target_connectivity_overlaps"] = {s: v["target_train_held_connectivity_overlaps"]
                for s, v in results["per_split"].items() if v["target_train_held_connectivity_overlaps"]}
        report["runs"][name] = record
    write_json(Path("runs/intensity-ssh-audit.json"), report)
    print(json.dumps(report, indent=2), flush=True)


def export(names, archive):
    with tarfile.open(archive, "w:gz", compresslevel=1) as target:
        for name in names:
            root = Path("runs")/name
            for path in root.rglob("*"):
                if path.is_file() and not path.name.startswith(".") and "__pycache__" not in path.parts:
                    target.add(path, arcname=str(path), recursive=False)
    print(f"Exported {archive}: {Path(archive).stat().st_size} bytes", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", nargs="*")
    parser.add_argument("--archive", default="calnew-intensity-results.tar.gz")
    args = parser.parse_args()
    audit()
    if args.export:
        export(args.export, args.archive)
