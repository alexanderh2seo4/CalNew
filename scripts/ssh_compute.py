"""Run a project command with the isolated SSH checkout taking import priority."""
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
environment = dict(os.environ)
environment["PYTHONPATH"] = str(root/"src")
environment["PATH"] = str(Path(sys.executable).parent)+os.pathsep+environment.get("PATH", "")
sys.exit(subprocess.call([sys.executable]+sys.argv[1:], cwd=root, env=environment))
