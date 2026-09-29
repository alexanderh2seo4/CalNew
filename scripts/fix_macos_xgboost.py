"""Optional local environment repair for the macOS XGBoost wheel's libomp lookup."""
import subprocess
import sys
from pathlib import Path
from importlib.util import find_spec

if sys.platform!='darwin':
    raise SystemExit('This repair applies only to macOS.')
sklearn=Path(find_spec('sklearn').origin).parent
xgb=Path(find_spec('xgboost').origin).parent/'lib'/'libxgboost.dylib'
runtime=sklearn/'.dylibs'/'libomp.dylib'
if not runtime.exists(): raise SystemExit('No bundled sklearn OpenMP runtime; install libomp through your environment manager.')
rpath=str(runtime.parent)
existing=subprocess.check_output(['otool','-l',str(xgb)],text=True)
if rpath not in existing:
    subprocess.run(['install_name_tool','-add_rpath',rpath,str(xgb)],check=True)
print('XGBoost local wheel can locate',runtime)
