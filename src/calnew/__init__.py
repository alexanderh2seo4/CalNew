"""CALNEW research system. Prediction is conditional on endpoint and evidence."""

__version__ = "0.1.0"

# Keep optional libraries' model/code caches within the research workspace.
import os
from pathlib import Path
for _key,_relative in {'HF_HOME':'data/checkpoints/huggingface','HF_MODULES_CACHE':'data/checkpoints/modules',
                       'TORCH_HOME':'data/checkpoints/torch','MPLCONFIGDIR':'data/cache/matplotlib'}.items():
    os.environ.setdefault(_key,str(Path(_relative).resolve()))
