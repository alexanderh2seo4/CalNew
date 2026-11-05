"""Read only process/checkpoint status of the two active SSH research jobs."""
import os
import json
from pathlib import Path
import platform
import subprocess

if platform.node().lower() != os.environ.get("CALNEW_COMPUTE_HOST", "").lower():
    raise ValueError("Use authorized SSH host only")
query = "Get-CimInstance Win32_Process | Where-Object { $_.Name -like 'python*' -and ($_.CommandLine -like '*nose_balanced_semantic_refine.py*' -or $_.CommandLine -like '*nose_threshold_direction_benchmark.py*') } | Select-Object ProcessId,Name,CommandLine | ConvertTo-Json -Compress"
processes = subprocess.run(["powershell", "-NoProfile", "-Command", query], capture_output=True, text=True, check=True).stdout.strip()
status = {"host": platform.node(), "live_processes": json.loads(processes) if processes else [], "runs": {}}
for name in ("nose-balanced-semantic-grouped-inner-v1", "nose-threshold-direction-original-v1"):
    root = Path("runs")/name
    status["runs"][name] = {"exists": root.exists(), "final_results_present": (root/"results.json").exists(),
        "progress": json.loads((root/"fold-progress.json").read_text()) if (root/"fold-progress.json").exists() else None,
        "source_feature_npz": len(list((root/"source-feature-cache").glob("*.npz")))}
print(json.dumps(status, indent=2), flush=True)
