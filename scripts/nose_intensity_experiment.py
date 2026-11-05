"""Select intensity recipes strictly inside the original split-42 training rows.

The outer CV and every quality/descriptor meta-feature fit exclude validation
connectivities. Main development validation/test and reserved final labels are
never scored here. Caches pin training IDs, held IDs, source code and snapshot.
"""
from __future__ import annotations

import argparse
import json
import shutil
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from scipy.stats import pearsonr
from sklearn.decomposition import PCA
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.impute import SimpleImputer
from sklearn.model_selection import GridSearchCV, GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR
from threadpoolctl import threadpool_limits

from calnew.io import digest, file_digest, write_json
from calnew.pipeline.blocks import BlockCache
from calnew.pipeline.intensity import INTENSITY_STRUCTURE, KELLER_DOSE_MEMBERS, MonotoneDoseTrees
from calnew.pipeline.paper_benchmark import Context, FRACTIONS, random_split
from calnew.pipeline.semantic import DescriptorTransfer, SEMANTIC_BASE
from calnew.pipeline.stages import IntensityStage, RAVIA_MEMBERS, TabularEnsemble
from nose_semantic_experiment import RESERVED, SHA256, SOURCE, frozen_molecular_vectors, load_corpus

CACHE = Path("runs/nose-intensity-feature-cache-v1")


def load_transfer(ctx, out, threads):
    molecules, labels = load_corpus(ctx, out)
    path = Path("data/features/nose-descriptor-minilm.npz")
    manifest = json.loads(path.with_suffix(".json").read_text())
    if manifest["sha256"] != file_digest(path) or manifest["corpus_sha256"] != SHA256:
        raise ValueError("Word vector artifact/source mismatch")
    terms = sorted(pd.read_csv(SOURCE, usecols=["TARGET_Descriptor"]).TARGET_Descriptor.unique())
    with np.load(path, allow_pickle=False) as data:
        if data["terms"].tolist() != terms:
            raise ValueError("Descriptor vocabulary mismatch")
        vectors = data["vectors"].copy()
    blocks = BlockCache(Path("data/features")).blocks(("rdkit", "fingerprint"), molecules.smiles.tolist())
    source = np.column_stack([blocks["rdkit"], blocks["fingerprint"]])
    return DescriptorTransfer(molecules, labels, source, encoder="extra_trees", threads=threads,
        term_vectors=vectors), manifest


def cache_identity(ctx, train_ids, held_ids, seed, kind):
    files = ["src/calnew/pipeline/paper_benchmark.py", "src/calnew/pipeline/stages.py",
        "src/calnew/pipeline/fusion.py", "src/calnew/pipeline/semantic.py", "scripts/nose_intensity_experiment.py"]
    return {"kind": kind, "snapshot": str(ctx.snapshot),
        "snapshot_sha256": {n: file_digest(ctx.snapshot/n) for n in ("molecules.parquet", "observations.parquet", "stimuli.parquet")},
        "train_ids": list(map(str, train_ids)), "held_ids": list(map(str, held_ids)),
        "universe": ctx.universe, "seed": int(seed), "cfg": ctx.cfg,
        "code_sha256": {n: file_digest(Path(n)) for n in files},
        "descriptor_source_sha256": SHA256,
        "word_vectors_sha256": file_digest(Path("data/features/nose-descriptor-minilm.npz"))}


def cached_meta(ctx, train_ids, held_ids, seed=42):
    identity = cache_identity(ctx, train_ids, held_ids, seed, "quality")
    path = CACHE / (digest(identity) + ".npz")
    manifest = path.with_suffix(".json")
    if path.exists() and manifest.exists():
        provenance = json.loads(manifest.read_text())
        if provenance["identity"] != json.loads(json.dumps(identity)) or provenance["sha256"] != file_digest(path):
            raise ValueError("Quality cache provenance/checksum mismatch")
        with np.load(path, allow_pickle=False) as data:
            q, d = data["quality"].copy(), data["direction"].copy()
    else:
        q, d, _ = ctx.stage_a_features(train_ids, held_ids, seed)
        CACHE.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(path, quality=q, direction=d)
        write_json(manifest, {"identity": identity, "sha256": file_digest(path)})
    if q.shape != ctx.labels.shape or d.shape != ctx.direction.shape or not np.isfinite(q).all() or not np.isfinite(d).all():
        raise ValueError("Quality cache shape/finiteness mismatch")
    return {**ctx.B, "quality": q, "direction": d}


def cached_semantic(ctx, transfer, train_ids, held_ids, seed=300):
    identity = cache_identity(ctx, train_ids, held_ids, seed, "semantic")
    path = CACHE / (digest(identity) + ".npz")
    manifest = path.with_suffix(".json")
    if path.exists() and manifest.exists():
        provenance = json.loads(manifest.read_text())
        if provenance["identity"] != json.loads(json.dumps(identity)) or provenance["sha256"] != file_digest(path):
            raise ValueError("Semantic cache provenance/checksum mismatch")
        with np.load(path, allow_pickle=False) as data:
            semantic = data["semantic"].copy()
        count = provenance["source_rows"]
    else:
        features = np.column_stack([ctx.B["rdkit"], ctx.B["fingerprint"]])
        tr, held = ctx.rows(train_ids), ctx.rows(held_ids)
        a, b, count = transfer.crossfit(np.asarray(train_ids), held_ids, features[tr], features[held], seed)
        semantic = np.zeros((len(ctx.universe), 128), np.float32)
        semantic[tr], semantic[held] = a, b
        CACHE.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(path, semantic=semantic)
        write_json(manifest, {"identity": identity, "sha256": file_digest(path), "source_rows": count})
    if semantic.shape != (len(ctx.universe), 128) or not np.isfinite(semantic).all():
        raise ValueError("Semantic cache shape/finiteness mismatch")
    return semantic, count


def metrics(y, p):
    if not np.isfinite(p).all():
        raise ValueError("Non-finite intensity predictions")
    return {"pearson": float(pearsonr(y, p).statistic), "mae": float(np.abs(y-p).mean()),
        "rmse": float(np.sqrt(np.mean((y-p)**2)))}


def fit_candidates(ctx, dataset, train_ids, held_ids, test_ids, enriched, semantic, molecular, threads, seed=42):
    frame = ctx.keller if dataset == "keller" else ctx.ravia
    frame = frame.set_index("molecule_id")
    tr, te = ctx.rows(train_ids), ctx.rows(test_ids)
    groups = ctx.connectivity[tr]
    if set(groups) & {str(i).split("-")[0] for i in held_ids}:
        raise ValueError("Training and held molecular connectivities overlap")
    blocks = {**enriched, "semantic": semantic, "unimol1": molecular}
    pick = lambda names, rows: {n: blocks[n][rows] for n in names}
    predictions, models = {}, {}
    if dataset == "keller":
        sel = np.isin(ctx.data.panel["molecule_ids"], train_ids)
        rows, x, y = ctx.p_rows[sel], ctx.data.panel["x"][sel], ctx.data.panel["intensity"][sel]
        dose = frame.loc[test_ids, "x"].to_numpy()
        names = ctx.cfg["potency_blocks"]
        baseline = IntensityStage(names, "fingerprint", seeds=(seed,), epochs=ctx.cfg["intensity"]["epochs"]).fit(pick(names, rows), x, y)
        models["baseline"] = baseline
        predictions["baseline"] = baseline.predict(pick(names, te), dose)[0]
        for name, members in (("dose_trees", KELLER_DOSE_MEMBERS),
                ("dose_semantic", (SEMANTIC_BASE + ("semantic",),)),
                ("dose_molecular", (INTENSITY_STRUCTURE + ("fingerprint", "unimol1"),))):
            names = set(n for member in members for n in member)
            model = MonotoneDoseTrees(members, seed, threads).fit(pick(names, rows), x, y)
            predictions[name] = model.predict(pick(names, te), dose)
            models[name] = model
    else:
        y = frame.loc[train_ids, "y"].to_numpy()
        candidates = {"baseline": RAVIA_MEMBERS,
            "molecular": (("extra_trees", ("unimol1",)),),
            "structure_molecular": (("extra_trees", SEMANTIC_BASE + ("unimol1",)),),
            "molecular_boost": (("xgboost", INTENSITY_STRUCTURE + ("unimol1",)),),
            "semantic": (("extra_trees", SEMANTIC_BASE + ("semantic",)),)}
        for name, members in candidates.items():
            names = set(n for _, member in members for n in member)
            model = TabularEnsemble(members, seed, threads).fit(pick(names, tr), y, groups)
            predictions[name] = model.predict(pick(names, te))
            models[name] = model
        svr = GridSearchCV(Pipeline([("impute", SimpleImputer(keep_empty_features=True)),
            ("scale", StandardScaler()), ("pca", PCA(n_components=25, svd_solver="full")), ("svr", SVR(epsilon=1.0))]),
            {"svr__C": [10., 100., 1000.], "svr__gamma": [v/25 for v in (.1, 1., 10.)]},
            cv=GroupKFold(3, shuffle=True, random_state=173), scoring="neg_mean_squared_error", n_jobs=1)
        svr.fit(molecular[tr], y, groups=groups)
        models["molecular_svr"] = svr
        predictions["molecular_svr"] = np.clip(svr.predict(molecular[te]), 0, 100)
    for name in list(predictions):
        if name != "baseline":
            predictions["blend_" + name] = (predictions["baseline"] + predictions[name])/2
    return predictions, models


def run(args):
    out = Path(args.out)
    if (out/"results.json").exists():
        raise ValueError("Choose a new output directory")
    out.mkdir(parents=True, exist_ok=True)
    paths = [Path(__file__), Path("scripts/nose_semantic_experiment.py")] + sorted(Path("src/calnew").rglob("*.py"))
    hashes = {}
    for path in paths:
        dest = out/"source-code"/path.resolve().relative_to(Path.cwd())
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        hashes[str(path)] = file_digest(dest)
    write_json(out/"selection-plan.json", {"original_split_seed": 42, "fold_seeds": [100, 101, 102],
        "selection_data": "Original split-42 training molecules only; 5-fold connectivity-grouped CV repeated three times",
        "candidates": {"keller": ["baseline Hill", "monotone trees", "semantic monotone trees", "structure/Uni-Mol1 monotone trees", "equal baseline blends"],
            "ravia": ["baseline v2", "Uni-Mol1 extra trees", "structure/Uni-Mol1 extra trees", "Uni-Mol1 boosting", "semantic trees", "nested Uni-Mol1 SVR", "equal baseline blends"]},
        "promotion": "Mean Pearson gain >= 0.01, positive gain in at least two repeats, mean MAE no more than 1% above baseline; choose best passing mean Pearson",
        "svr_tuning": "Nested 3-fold grouped CV; all preprocessing fitted inside each tuning fold",
        "test_based_model_selection": False, "reserved_holdouts_opened": False, "code_sha256": hashes})
    started = time.time()
    torch.set_num_threads(args.threads)
    ctx = Context(Path(json.loads(Path("data/current.json").read_text())["snapshot"]), RESERVED)
    transfer, manifest = load_transfer(ctx, out, args.threads)
    molecular, mol_manifest = frozen_molecular_vectors(Path("data/features/unimol1-research/vectors.npz"), ctx.smiles)
    results = {}
    for dataset in args.datasets:
        frame = ctx.keller if dataset == "keller" else ctx.ravia
        tr, va, te = random_split(len(frame), FRACTIONS[dataset], 42)
        all_ids = frame.molecule_id.to_numpy()
        ids, fixed_held = all_ids[tr], all_ids[np.r_[va, te]]
        y = frame["intensity" if dataset == "keller" else "y"].to_numpy()[tr]
        groups = np.array([i.split("-")[0] for i in ids])
        predictions = {}
        for rep in range(3):
            for fold, (a, b) in enumerate(GroupKFold(5, shuffle=True, random_state=100+rep).split(ids, groups=groups)):
                held = np.r_[fixed_held, ids[b]]
                enriched = cached_meta(ctx, ids[a], held)
                sem, count = cached_semantic(ctx, transfer, ids[a], held, 300+rep*5+fold)
                values, _ = fit_candidates(ctx, dataset, ids[a], held, ids[b], enriched, sem, molecular, args.threads)
                for name, p in values.items():
                    if name not in predictions:
                        predictions[name] = np.zeros((3, len(y)))
                    predictions[name][rep, b] = p
                print(f"{dataset} repeat {rep+1}/3 fold {fold+1}/5; source rows {count}", flush=True)
            scores = {n: metrics(y, p[rep]) for n, p in predictions.items()}
            print({n: {k: round(v, 4) for k, v in s.items()} for n, s in scores.items()}, flush=True)
            np.savez_compressed(out/f"{dataset}-inner-oof.npz", ids=ids.astype(str), y=y, **predictions)
        scores = {name: [metrics(y, p) for p in values] for name, values in predictions.items()}
        base_r = np.array([m["pearson"] for m in scores["baseline"]])
        base_mae = np.mean([m["mae"] for m in scores["baseline"]])
        passing = []
        for name, values in scores.items():
            gain = np.array([m["pearson"] for m in values]) - base_r
            if gain.mean() >= .01 and (gain > 0).sum() >= 2 and np.mean([m["mae"] for m in values]) <= base_mae*1.01:
                passing.append(name)
        selected = max(passing, key=lambda n: np.mean([m["pearson"] for m in scores[n]])) if passing else "baseline"
        results[dataset] = {"n": len(ids), "scores": scores, "passing": passing, "selected": selected}
        write_json(out/"partial.json", results)
    write_json(out/"results.json", {"results": results, "word_vectors": manifest, "molecular_vectors": mol_manifest,
        "reserved_holdouts_opened": False, "seconds": round(time.time()-started)})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--datasets", nargs="+", choices=("keller", "ravia"), default=["keller", "ravia"])
    parser.add_argument("--threads", type=int, default=4)
    args = parser.parse_args()
    with threadpool_limits(limits=args.threads):
        run(args)
