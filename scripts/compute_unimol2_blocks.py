"""Compute frozen Uni-Mol2 embeddings for the pipeline in resumable chunks.

The pretrained adapter caches one file per molecule only after a whole call finishes, so a
single call over thousands of molecules loses everything on interruption. Chunking makes
the (CPU-bound, conformer-dominated) job resumable. Molecules whose conformers fail are
logged to logs/unimol2-unavailable.json and marked unavailable in the block. Finally the pipeline block cache entry
is assembled from the per-molecule files.
"""
import argparse
import time
from pathlib import Path

from calnew.io import read_json, write_json
from calnew.pipeline.blocks import BlockCache, unimol2_rows
from calnew.pipeline.data import load_stages

p = argparse.ArgumentParser()
p.add_argument("--snapshot", type=Path)
p.add_argument("--reserved-run", type=Path, nargs="*", default=[Path("runs/basic-threshold-models"), Path("runs/basic-descriptor-models")])
p.add_argument("--chunk", type=int, default=50)
p.add_argument("--threads", type=int, default=8)
a = p.parse_args()
snapshot = a.snapshot or Path(read_json(Path("data/current.json"))["snapshot"])
smiles = load_stages(snapshot, a.reserved_run).molecules.smiles.tolist()
started, failures = time.time(), []
for start in range(0, len(smiles), a.chunk):
    unimol2_rows(smiles[start:start + a.chunk], a.threads, failures)
    done = min(start + a.chunk, len(smiles))
    rate = (time.time() - started) / done
    print(f"{done}/{len(smiles)} molecules, {rate:.1f}s/molecule average, ~{rate * (len(smiles) - done) / 3600:.1f}h left", flush=True)
write_json(Path("logs/unimol2-unavailable.json"), failures)
x = BlockCache(Path("data/features")).get("unimol2", smiles)
print("DONE", x.shape, f"unavailable={len(failures)}", f"{time.time() - started:.0f}s", flush=True)
