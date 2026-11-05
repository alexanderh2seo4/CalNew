"""Resume the two unfinished Keller runs on the Windows SSH compute host."""
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

root = Path(__file__).resolve().parents[1]
os.chdir(root)
environment = dict(os.environ)
environment["PYTHONPATH"] = str(root/"src")
environment["PATH"] = str(Path(sys.executable).parent)+os.pathsep+environment.get("PATH", "")
commands = {
    "keller": ["scripts/nose_intensity_benchmark.py", "--selection", "runs/nose-intensity-keller-v3/frozen-selection.json", "--dataset", "keller",
        "--out", "runs/nose-intensity-keller-v3", "--threads", "2", "--resume"],
    "keller_refit": ["scripts/nose_intensity_benchmark.py", "--selection", "runs/nose-intensity-keller-refit-v3/frozen-selection.json", "--dataset", "keller",
        "--out", "runs/nose-intensity-keller-refit-v3", "--threads", "2", "--resume", "--refit-validation", "--fit-final"],
}
processes, handles = {}, []
metadata = {"host": platform.node(), "python": sys.version, "platform": platform.platform(), "jobs": {}}
for name, arguments in commands.items():
    stdout = (root/"runs"/f"ssh-{name}.log").open("a", encoding="utf-8")
    stderr = (root/"runs"/f"ssh-{name}-stderr.log").open("a", encoding="utf-8")
    handles.extend([stdout, stderr])
    process = subprocess.Popen([sys.executable]+arguments, cwd=root, env=environment, stdout=stdout, stderr=stderr)
    processes[name] = process
    metadata["jobs"][name] = {"pid": process.pid, "command": arguments}
    print(f"Started {name} on {platform.node()}, PID {process.pid}", flush=True)
(root/"runs/ssh-intensity-jobs.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
finished = set()
while len(finished) != len(processes):
    for name, process in processes.items():
        if name not in finished and process.poll() is not None:
            finished.add(name)
            metadata["jobs"][name]["exit_code"] = process.returncode
            print(f"Finished {name}: exit {process.returncode}", flush=True)
            (root/"runs/ssh-intensity-jobs.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    if len(finished) != len(processes):
        time.sleep(5)
for handle in handles:
    handle.close()
sys.exit(0 if all(p.returncode == 0 for p in processes.values()) else 1)
