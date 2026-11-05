"""Cache frozen original-Uni-Mol vectors for non-reserved research molecules.

Use the paper's no-hydrogen molecular checkpoint, but not its odor-trained
adapters. One optimized ETKDGv3 conformer per molecule keeps this CPU feasible.
Conformer failures are an unavailable branch; no flat geometry is substituted.
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch
from huggingface_hub import hf_hub_download
from rdkit import rdBase
from unimol_tools import UniMolRepr

from calnew.conformers import conformer_arrays
from calnew.io import digest, file_digest, write_json
from calnew.pipeline.paper_benchmark import Context
from nose_semantic_experiment import RESERVED, load_corpus

REPOSITORY = "dptech/Uni-Mol-Models"
REVISION = "9f19c45c718192888a1c8a1c905f69f0755ea502"


def run(args):
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    weights = Path("data/checkpoints/unimol1") / REVISION
    model_path = hf_hub_download(REPOSITORY, "mol_pre_no_h_220816.pt", revision=REVISION, local_dir=weights)
    dictionary = hf_hub_download(REPOSITORY, "mol.dict.txt", revision=REVISION, local_dir=weights)
    identity = {"repository": REPOSITORY, "revision": REVISION, "checkpoint_sha256": file_digest(model_path),
        "dictionary_sha256": file_digest(dictionary), "rdkit": rdBase.rdkitVersion,
        "conformer_seed": 42, "generated_conformers": 1, "retained_conformers": 1,
        "remove_hydrogens": True, "training": "unlabeled molecular pretraining; frozen"}
    write_json(out / "encoder.json", identity)
    if args.smoke:
        smiles = ["CCO", "CC(=O)C", "CC(C)C=O"]
    else:
        snapshot = Path(json.loads(Path("data/current.json").read_text())["snapshot"])
        ctx = Context(snapshot, RESERVED)
        molecules, _ = load_corpus(ctx, out)
        smiles = list(dict.fromkeys(molecules.smiles.tolist() + ctx.smiles))
    rows_dir = out / "rows"
    rows_dir.mkdir(exist_ok=True)
    paths = [rows_dir / f"{digest({**identity, 'smiles': s})}.npy" for s in smiles]
    missing = [i for i, path in enumerate(paths) if not path.exists()]
    torch.set_num_threads(args.threads)
    encoder = UniMolRepr(data_type="molecule", model_name="unimolv1", remove_hs=True,
        use_cuda=False, batch_size=args.batch_size, pretrained_model_path=model_path, pretrained_dict_path=dictionary)
    failures, started = [], time.time()
    for start in range(0, len(missing), args.batch_size):
        batch = missing[start:start + args.batch_size]
        valid, atoms, coordinates = [], [], []
        for i in batch:
            try:
                atom, coordinate, _ = conformer_arrays(smiles[i], root=Path("data/conformers-unimol1"),
                    seed=42, generated=1, retained=1)
                valid.append(i)
                atoms.append(atom)
                coordinates.append(coordinate[0])
            except (ValueError, RuntimeError) as exc:
                np.save(paths[i], np.r_[np.full(512, np.nan), 0].astype(np.float32), allow_pickle=False)
                failures.append({"smiles": smiles[i], "reason": str(exc)})
        if valid:
            with torch.inference_mode():
                result = encoder.get_repr({"atoms": atoms, "coordinates": coordinates})
            vectors = np.asarray(result["cls_repr"] if isinstance(result, dict) else result, dtype=np.float32)
            if vectors.shape != (len(valid), 512) or not np.isfinite(vectors).all():
                raise ValueError(f"Invalid Uni-Mol output: {vectors.shape}")
            for i, vector in zip(valid, vectors):
                np.save(paths[i], np.r_[vector, 1].astype(np.float32), allow_pickle=False)
        write_json(out / "failures.json", failures)
        print(f"Uni-Mol1 {min(start + args.batch_size, len(missing))}/{len(missing)}; {round(time.time() - started)}s", flush=True)
    vectors = np.stack([np.load(path, allow_pickle=False) for path in paths])
    if vectors[:, -1].mean() < 0.9:
        raise ValueError("Uni-Mol1 unavailable for more than 10% of research molecules")
    artifact = out / ("smoke.npz" if args.smoke else "vectors.npz")
    np.savez_compressed(artifact, smiles=np.asarray(smiles), vectors=vectors)
    write_json(artifact.with_suffix(".json"), {**identity, "sha256": file_digest(artifact),
        "shape": list(vectors.shape), "available": int(vectors[:, -1].sum()), "reserved_molecules_scored": False})
    print(f"Saved {vectors.shape} vectors to {artifact}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="data/features/unimol1-research")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=32)
    run(parser.parse_args())
