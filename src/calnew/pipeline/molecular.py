"""Serve the pinned, frozen original Uni-Mol molecular representation."""
from pathlib import Path

import numpy as np

from ..chemistry import identify
from ..io import digest, file_digest, read_json


def unimol1_vectors(smiles, artifact=Path("data/features/unimol1-research/vectors.npz"), threads=2):
    """Reuse verified vectors and encode new molecules with the identical recipe.

    Geometry failures are NaN plus availability=0, matching training. Checkpoint
    and dictionary bytes are verified before encoding; no model download occurs.
    """
    artifact = Path(artifact)
    manifest = read_json(artifact.with_suffix(".json"))
    if manifest["sha256"] != file_digest(artifact) or manifest["training"] != "unlabeled molecular pretraining; frozen":
        raise ValueError("Molecular vector checksum or training provenance mismatch")
    canonical = [identify(s).smiles for s in smiles]
    with np.load(artifact, allow_pickle=False) as data:
        keys, values = data["smiles"].tolist(), data["vectors"].copy()
    if len(set(keys)) != len(keys) or values.shape != (len(keys), 513):
        raise ValueError("Invalid molecular vector keys/shape")
    if not np.isin(values[:, -1], (0, 1)).all() or not np.isfinite(values[values[:, -1] == 1]).all():
        raise ValueError("Invalid available molecular vectors")
    lookup = dict(zip(keys, values))
    missing = list(dict.fromkeys(s for s in canonical if s not in lookup))
    if missing:
        import torch
        from unimol_tools import UniMolRepr
        from ..conformers import conformer_arrays
        weights = artifact.resolve().parents[2]/"checkpoints"/"unimol1"/manifest["revision"]
        checkpoint, dictionary = weights/"mol_pre_no_h_220816.pt", weights/"mol.dict.txt"
        if not checkpoint.exists() or not dictionary.exists():
            raise ValueError("Pinned Uni-Mol1 checkpoint and dictionary are required for new molecules")
        if file_digest(checkpoint) != manifest["checkpoint_sha256"] or file_digest(dictionary) != manifest["dictionary_sha256"]:
            raise ValueError("Pinned Uni-Mol1 weights checksum mismatch")
        identity = {key: manifest[key] for key in ("repository", "revision", "checkpoint_sha256", "dictionary_sha256",
            "rdkit", "conformer_seed", "generated_conformers", "retained_conformers", "remove_hydrogens", "training")}
        rows = artifact.parent/"rows"
        rows.mkdir(parents=True, exist_ok=True)
        encoder = None
        for s in missing:
            path = rows/f"{digest({**identity, 'smiles': s})}.npy"
            if path.exists():
                vector = np.load(path, allow_pickle=False)
            else:
                try:
                    atoms, coords, _ = conformer_arrays(s, root=weights.parents[2]/"conformers-unimol1",
                        seed=manifest["conformer_seed"], generated=1, retained=1)
                except (ValueError, RuntimeError):
                    vector = np.r_[np.full(512, np.nan), 0].astype(np.float32)
                else:
                    if encoder is None:
                        torch.set_num_threads(threads)
                        encoder = UniMolRepr(data_type="molecule", model_name="unimolv1", remove_hs=True,
                            use_cuda=False, batch_size=1, pretrained_model_path=str(checkpoint), pretrained_dict_path=str(dictionary))
                    with torch.inference_mode():
                        encoded = encoder.get_repr({"atoms": [atoms], "coordinates": [coords[0]]})
                    latent = np.asarray(encoded["cls_repr"] if isinstance(encoded, dict) else encoded, dtype=np.float32)
                    if latent.shape != (1, 512) or not np.isfinite(latent).all():
                        raise ValueError("Invalid Uni-Mol1 output")
                    vector = np.r_[latent[0], 1].astype(np.float32)
                np.save(path, vector, allow_pickle=False)
            if vector.shape != (513,) or vector[-1] not in (0, 1) or (vector[-1] == 1 and not np.isfinite(vector).all()):
                raise ValueError("Invalid cached molecular vector")
            lookup[s] = vector
    return np.stack([lookup[s] for s in canonical])
