"""Train-only test of the released NOSE augmented descriptor corpus.

This experiment never scores reserved or paper-benchmark test molecules. Each
inner validation molecule is removed from descriptor transfer training, including
its connectivity-equivalent structures. Downstream training features are themselves
cross-fitted. The vocabulary projection is fixed independently of any labels.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from scipy import sparse
from scipy.stats import pearsonr
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold
from threadpoolctl import threadpool_limits

from calnew.chemistry import identify
from calnew.io import file_digest, write_json
from calnew.pipeline.blocks import BlockCache
from calnew.pipeline.auxiliary import exclude_touching
from calnew.pipeline.data import exclude_reserved
from calnew.pipeline.fusion import BlockScaler
from calnew.pipeline.paper_benchmark import Context, FRACTIONS, random_split
from calnew.pipeline.semantic import DescriptorTransfer
from calnew.pipeline.stages import HEDONIC_MEMBERS, THRESHOLD_MEMBERS, TabularEnsemble, ThresholdStage

URL = "https://github.com/Xianyusyy/NOSE/releases/download/v1.0.0/nose-smiles-descriptor-v1.0.0.csv.gz"
SHA256 = "858e482f407a3577870a87a61f8f16b488412ed06922dd35dd8d4fe4cf5e6ff2"
SOURCE = Path("data/raw/nose/v1.0.0/nose-smiles-descriptor-v1.0.0.csv.gz")
RESERVED = [Path("runs/basic-threshold-models"), Path("runs/basic-descriptor-models")]


def load_corpus(ctx, out):
    if file_digest(SOURCE) != SHA256:
        raise ValueError("NOSE corpus checksum differs from the pinned release")
    raw = pd.read_csv(SOURCE).drop_duplicates()
    identities = {}
    for smiles in raw.SMILES.unique():
        try:
            identities[smiles] = identify(smiles)
        except ValueError:
            pass
    molecules = pd.DataFrame([
        {"molecule_id": i.molecule_id, "smiles": i.smiles}
        for i in identities.values()
    ]).drop_duplicates("molecule_id")
    molecules = exclude_reserved(molecules, ctx.data, RESERVED, ctx.all_molecules).reset_index(drop=True)
    rows = {m: i for i, m in enumerate(molecules.molecule_id)}
    terms = sorted(raw.TARGET_Descriptor.unique())
    vocab = {term: i for i, term in enumerate(terms)}
    ii, jj = [], []
    for smiles, group in raw.groupby("SMILES"):
        identity = identities.get(smiles)
        if identity is None or identity.molecule_id not in rows:
            continue
        ii.extend([rows[identity.molecule_id]] * len(group))
        jj.extend(vocab[t] for t in group.TARGET_Descriptor)
    labels = sparse.coo_matrix((np.ones(len(ii), np.float32), (ii, jj)), shape=(len(molecules), len(terms))).tocsr()
    labels.data[:] = 1  # duplicates and equivalent molecular strings do not gain weight
    write_json(out / "source.json", {"url": URL, "sha256": SHA256, "terms": len(terms),
        "unique_valid_molecules": len({i.molecule_id for i in identities.values()}),
        "molecules_after_reserved_exclusion": len(molecules), "pairs_after_exclusion": int(labels.nnz),
        "contains_positive_strength_or_source_labels": False,
        "use": "research experiment; augmented associations, not measured panel targets",
        "rights": "NOSE MIT code licence does not replace underlying third-party dataset terms"})
    return molecules, labels


def frozen_molecular_vectors(path, smiles):
    """Align a checksummed, label-free geometry artifact without fitting any axes."""
    path = Path(path)
    manifest = json.loads(path.with_suffix(".json").read_text())
    if manifest["sha256"] != file_digest(path) or manifest["training"] != "unlabeled molecular pretraining; frozen":
        raise ValueError("Molecular vector checksum or training provenance mismatch")
    with np.load(path, allow_pickle=False) as data:
        keys, values = data["smiles"].tolist(), data["vectors"].copy()
    if len(set(keys)) != len(keys) or values.shape != (len(keys), 513):
        raise ValueError("Invalid molecular vector keys/shape")
    available = values[:, -1] == 1
    if not np.isin(values[:, -1], (0, 1)).all() or not np.isfinite(values[available]).all():
        raise ValueError("Invalid available molecular vectors")
    rows = {s: i for i, s in enumerate(keys)}
    if any(s not in rows for s in smiles):
        raise ValueError("Missing molecular vector; build artifact for these molecules first")
    return values[[rows[s] for s in smiles]], manifest



def run(args):
    out = Path(args.out)
    if (out / "results.json").exists():
        raise ValueError("Choose a new output directory")
    out.mkdir(parents=True, exist_ok=True)
    for path in (Path(__file__), Path("src/calnew/pipeline/semantic.py")):
        saved = out / "source-code" / path.name
        saved.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path,saved)
    started = time.time()
    torch.set_num_threads(args.threads)
    ctx = Context(Path(json.loads(Path("data/current.json").read_text())["snapshot"]), RESERVED)
    molecules, labels = load_corpus(ctx, out)
    print(f"Corpus: {len(molecules)} molecules after holdout exclusion, {labels.shape[1]} terms", flush=True)
    cache = BlockCache(Path("data/features"))
    blocks = cache.blocks(("rdkit", "fingerprint"), molecules.smiles.tolist())
    source_features = np.column_stack([blocks["rdkit"], blocks["fingerprint"]])
    task_features = np.column_stack([ctx.B["rdkit"], ctx.B["fingerprint"]])
    molecular_manifest, task_molecular = None, None
    if args.molecular_vectors:
        source_molecular, molecular_manifest = frozen_molecular_vectors(args.molecular_vectors, molecules.smiles.tolist())
        task_molecular, _ = frozen_molecular_vectors(args.molecular_vectors, ctx.smiles)
        source_features = np.column_stack([source_features, source_molecular])
        task_features = np.column_stack([task_features, task_molecular])
    vectors, vector_manifest = None, None
    if args.word_vectors:
        vector_path = Path(args.word_vectors)
        vector_manifest = json.loads(vector_path.with_suffix(".json").read_text())
        if vector_manifest["sha256"] != file_digest(vector_path) or vector_manifest["corpus_sha256"] != SHA256:
            raise ValueError("Word vector artifact checksum/source mismatch")
        terms = sorted(pd.read_csv(SOURCE, usecols=["TARGET_Descriptor"]).TARGET_Descriptor.unique())
        with np.load(vector_path, allow_pickle=False) as word_data:
            if word_data["terms"].tolist() != terms:
                raise ValueError("Word vector vocabulary order mismatch")
            vectors = word_data["vectors"].copy()
    transfer = DescriptorTransfer(molecules, labels, source_features, args.alpha, args.encoder, args.threads, vectors)
    results = {}
    for dataset, frame, target in (("abraham", ctx.thr, "y"), ("keller", ctx.keller, "pleasantness")):
        if dataset not in args.datasets:
            continue
        tr, va, te = random_split(len(frame), FRACTIONS[dataset], 42)
        ids = frame.molecule_id.to_numpy()
        fixed_held = ids[np.r_[va, te]]
        ids, y = ids[tr], frame[target].to_numpy()[tr]
        rows = ctx.rows(ids)
        base = np.column_stack([ctx.B[n][rows] for n in ("rdkit", "transport", "hbond", "osmophore", "chain", "fingerprint")])
        if dataset == "keller":
            base = np.column_stack([base, frame.x.to_numpy()[tr]])
        names = ["structure", "structure_semantic", "semantic"]
        if task_molecular is not None:
            names += ["structure_molecular"]
        if args.include_v2:
            names += ["v2", "v2_plus_semantic"]
        predictions = {name: np.zeros((args.repeats, len(y))) for name in names}
        counts = []
        for rep in range(args.repeats):
            for fold, (a, b) in enumerate(KFold(5, shuffle=True, random_state=100 + rep).split(ids)):
                sem_tr, sem_va, count = transfer.crossfit(ids[a], list(fixed_held) + list(ids[b]),
                    task_features[rows[a]], task_features[rows[b]], 300 + rep * 5 + fold)
                counts.append(count)
                for name, xtr, xva in (("structure", base[a], base[b]),
                        ("structure_semantic", np.column_stack([base[a], sem_tr]), np.column_stack([base[b], sem_va])),
                        ("semantic", sem_tr, sem_va)):
                    model = ExtraTreesRegressor(n_estimators=500, max_features=0.3, min_samples_leaf=2,
                        n_jobs=args.threads, random_state=42)
                    predictions[name][rep, b] = model.fit(xtr, y[a]).predict(xva)
                if task_molecular is not None:
                    # Imputation is fitted inside the endpoint-training fold only.
                    scaler = BlockScaler().fit({"m": task_molecular[rows[a]]})
                    molecular = scaler.transform({"m": task_molecular[rows]})["m"]
                    model = ExtraTreesRegressor(n_estimators=500, max_features=0.3, min_samples_leaf=2,
                        n_jobs=args.threads, random_state=42)
                    predictions["structure_molecular"][rep, b] = model.fit(
                        np.column_stack([base[a], molecular[a]]), y[a]).predict(np.column_stack([base[b], molecular[b]]))
                if args.include_v2:
                    held_ids = list(fixed_held) + list(ids[b])
                    q, d, _ = ctx.stage_a_features(ids[a], held_ids, 42)
                    bq = {**ctx.B, "quality": q, "direction": d}
                    train_rows, test_rows = rows[a], rows[b]
                    members = THRESHOLD_MEMBERS if dataset == "abraham" else HEDONIC_MEMBERS
                    pick = lambda rr: {n: bq[n][rr] for _, blocks in members for n in blocks}
                    if dataset == "abraham":
                        auxiliary_keep = exclude_touching(ctx.aux, held_ids)
                        auxiliary = ({n: v[auxiliary_keep] for n, v in ctx.aux_blocks.items()},
                            ctx.aux.y.to_numpy()[auxiliary_keep], 1.0)
                        member_model = TabularEnsemble(members, seed=42, threads=args.threads).fit(
                            pick(train_rows), y[a], ctx.connectivity[train_rows], auxiliary=auxiliary)
                        potency = lambda rr: {n: bq[n][rr] for n in ctx.cfg["potency_blocks"]}
                        fusion = ThresholdStage(ctx.cfg["potency_blocks"], "fingerprint", seeds=tuple(420 + i for i in range(5)),
                            epochs=ctx.cfg["threshold"]["epochs"]).fit(potency(train_rows), y[a], ctx.connectivity[train_rows])
                        current = np.column_stack([fusion.predict(potency(test_rows))["ensemble"],
                            member_model.predict_members(pick(test_rows))]).mean(1)
                    else:
                        concentrations = frame.x.to_numpy()[tr, None]
                        member_model = TabularEnsemble(members, seed=42, threads=args.threads).fit(
                            pick(train_rows), y[a], ctx.connectivity[train_rows], columns=concentrations[a])
                        current = member_model.predict(pick(test_rows), columns=concentrations[b])
                    predictions["v2"][rep, b] = current
                    predictions["v2_plus_semantic"][rep, b] = 0.5 * (current + predictions["structure_semantic"][rep, b])
                print(f"{dataset} repeat {rep + 1}/{args.repeats} fold {fold + 1}/5; {count} corpus molecules", flush=True)
            print({name: round(float(pearsonr(y, p[rep]).statistic), 4) for name, p in predictions.items()}, flush=True)
        results[dataset] = {"n_training_molecules": len(y), "corpus_molecules_per_fit": [min(counts), max(counts)],
            "inner_cv_pearson": {name: [float(pearsonr(y, p).statistic) for p in values] for name, values in predictions.items()},
            "selection": "5-fold CV inside split-42 training only; main validation/test and reserved labels never scored"}
        np.savez_compressed(out / f"{dataset}-inner-oof.npz", y=y, ids=np.asarray(ids, dtype=str), **predictions)
        write_json(out / "partial.json", results)
    write_json(out / "results.json", {"results": results, "seconds": round(time.time() - started),
        "alpha": args.alpha, "encoder": args.encoder, "include_v2": args.include_v2,
        "projection_width": 128, "source_sha256": SHA256, "word_vectors": vector_manifest,
        "molecular_vectors": molecular_manifest,
        "datasets": args.datasets,
        "script_sha256": file_digest(out / "source-code" / Path(__file__).name),
        "semantic_module_sha256": file_digest(out / "source-code" / "semantic.py"),
        "reserved_holdouts_opened": False})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--alpha", type=float, default=100.0)
    parser.add_argument("--encoder", choices=("ridge", "extra_trees", "mlp"), default="ridge")
    parser.add_argument("--include-v2", action="store_true", help="Evaluate v2 and a fixed equal blend with fully nested stage-A features")
    parser.add_argument("--word-vectors", type=Path, help="Pinned generic-text word vectors, built by build_descriptor_word_vectors.py")
    parser.add_argument("--molecular-vectors", type=Path, help="Checksummed original-Uni-Mol vectors from build_unimol1_vectors.py")
    parser.add_argument("--datasets",nargs="+",choices=("abraham","keller"),default=["abraham","keller"])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--threads", type=int, default=8)
    arguments = parser.parse_args()
    with threadpool_limits(limits=arguments.threads):
        run(arguments)
