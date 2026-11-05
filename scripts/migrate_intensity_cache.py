"""Re-key verified feature caches after an unrelated mixture-serving change.

Only the combine_mixture definition may differ from the archived stage module.
Every other AST node, other pinned source hash, snapshot table and array checksum
must agree. This never relaxes training/held IDs or structural exclusions.
"""
import ast
import copy
import json
import platform
import shutil
from pathlib import Path

from calnew.io import digest, file_digest, write_json

CACHE = Path("runs/nose-intensity-feature-cache-v1")
STAGES = "src/calnew/pipeline/stages.py"


def training_ast(path):
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    tree.body = [node for node in tree.body if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        or node.name != "combine_mixture"]
    return ast.dump(tree, include_attributes=False)


def migrate():
    original = Path("runs/nose-intensity-keller-v3/source-code")/STAGES
    if training_ast(original) != training_ast(STAGES):
        raise ValueError("Archived and current training code differ beyond mixture serving")
    old_sha, new_sha = file_digest(original), file_digest(STAGES)
    current_hashes = {n: file_digest(n) for n in (STAGES, "src/calnew/pipeline/paper_benchmark.py",
        "src/calnew/pipeline/fusion.py", "src/calnew/pipeline/semantic.py", "scripts/nose_intensity_experiment.py")}
    migrated, skipped, retained_replicas = [], 0, 0
    for path in list(CACHE.glob("*.json")):
        if path.name.startswith("."):
            continue
        record = json.loads(path.read_text())
        identity = record.get("identity", {})
        hashes = identity.get("code_sha256", {})
        if hashes.get(STAGES) != old_sha or old_sha == new_sha:
            continue
        if any(hashes.get(n) != sha for n, sha in current_hashes.items() if n != STAGES):
            skipped += 1
            continue
        snapshot = Path(identity["snapshot"])
        if any(file_digest(snapshot/name) != sha for name, sha in identity["snapshot_sha256"].items()):
            raise ValueError("Transferred cache snapshot changed")
        source = path.with_suffix(".npz")
        if file_digest(source) != record["sha256"]:
            raise ValueError("Transferred cache checksum changed")
        identity = copy.deepcopy(identity)
        identity["snapshot"] = str(snapshot)
        identity["code_sha256"][STAGES] = new_sha
        target = CACHE/(digest(identity)+".npz")
        if target.exists():
            existing = json.loads(target.with_suffix(".json").read_text())
            actual_sha = file_digest(target)
            if existing["identity"] != identity or existing["sha256"] != actual_sha:
                raise ValueError("Existing cache identity/checksum differs")
            if actual_sha != record["sha256"]:
                retained_replicas += 1  # Keep the already-pinned numerical replica; never overwrite it.
            continue
        shutil.copy2(source, target)
        write_json(target.with_suffix(".json"), {**record, "identity": identity,
            "serving_change_migration": {"host": platform.node(), "source_manifest": str(path),
                "old_stage_sha256": old_sha, "new_stage_sha256": new_sha,
                "proof": "Entire stage AST identical after removing only combine_mixture; all other pinned code/data and array hashes unchanged"}})
        migrated.append(str(target))
    report = {"host": platform.node(), "migrated": len(migrated), "skipped_other_code_changes": skipped,
        "different_valid_numerical_replicas_retained": retained_replicas,
        "old_stage_sha256": old_sha, "new_stage_sha256": new_sha, "paths": migrated}
    write_json(Path("runs/intensity-cache-serving-migration.json"), report)
    print(json.dumps({k: v for k, v in report.items() if k != "paths"}, indent=2), flush=True)


if __name__ == "__main__":
    migrate()
