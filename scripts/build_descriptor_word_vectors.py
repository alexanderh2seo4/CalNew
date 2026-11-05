"""Encode only descriptor words with a pinned generic text encoder.

No molecular structure, panel response or odor threshold is sent to or used by
the encoder. This is a small CPU-compatible alternative to NOSE's 8B text side.
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from transformers import AutoModel, AutoTokenizer

from calnew.io import file_digest, write_json

MODEL = "sentence-transformers/all-MiniLM-L6-v2"
REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
CORPUS = Path("data/raw/nose/v1.0.0/nose-smiles-descriptor-v1.0.0.csv.gz")
CORPUS_SHA256 = "858e482f407a3577870a87a61f8f16b488412ed06922dd35dd8d4fe4cf5e6ff2"


def run(out):
    if file_digest(CORPUS) != CORPUS_SHA256:
        raise ValueError("NOSE corpus checksum differs from the pinned release")
    terms = sorted(pd.read_csv(CORPUS, usecols=["TARGET_Descriptor"]).TARGET_Descriptor.unique())
    cache = str(Path("data/checkpoints").resolve())
    torch.set_num_threads(4)
    tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=REVISION, cache_dir=cache)
    model = AutoModel.from_pretrained(MODEL, revision=REVISION, cache_dir=cache).eval()
    vectors = []
    for start in range(0, len(terms), 64):
        texts = [f"This odor smells {term}." for term in terms[start:start + 64]]
        tokens = tokenizer(texts, padding=True, truncation=False, return_tensors="pt")
        with torch.inference_mode():
            hidden = model(**tokens).last_hidden_state
            mask = tokens["attention_mask"].unsqueeze(-1)
            pooled = (hidden * mask).sum(1) / mask.sum(1).clamp_min(1)
            vectors.append(torch.nn.functional.normalize(pooled, dim=1).cpu().numpy())
    vectors = np.vstack(vectors).astype(np.float32)
    if vectors.shape != (1086, 384) or not np.isfinite(vectors).all():
        raise ValueError(f"Invalid text vectors: {vectors.shape}")
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out, terms=np.asarray(terms), vectors=vectors)
    write_json(out.with_suffix(".json"), {"model": MODEL, "revision": REVISION, "corpus_sha256": CORPUS_SHA256,
        "sha256": file_digest(out), "shape": list(vectors.shape), "pooling": "attention-masked mean, L2 normalization",
        "prompt": "This odor smells {term}.", "molecular_or_endpoint_labels_used": False})
    print(f"Saved {vectors.shape} word vectors to {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="data/features/nose-descriptor-minilm.npz")
    run(parser.parse_args().out)
