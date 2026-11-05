"""Evaluate the pleasantness recipe selected inside training, then save a serving bundle.

The recipe is fixed at equal v2 + structure/text descriptor-transfer predictions.
It passed the registered >=0.01 mean gain and two-positive-repeat rule before
these development test scores were computed. Reserved final partitions stay excluded.
"""
import argparse
import json
import shutil
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch
from scipy.stats import pearsonr
from threadpoolctl import threadpool_limits

from calnew.io import file_digest, write_json
from calnew.pipeline.blocks import BlockCache
from calnew.pipeline.paper_benchmark import Context, FRACTIONS, benchmark_split
from calnew.pipeline.semantic import DescriptorTransfer, SemanticHead, SEMANTIC_BASE, predict_pleasantness
from calnew.pipeline.stages import HEDONIC_MEMBERS, QualityStage, TabularEnsemble
from nose_semantic_experiment import SOURCE, SHA256, RESERVED, load_corpus


def run(args):
    out = Path(args.out)
    if args.fit_only and not (out / "results.json").exists():
        raise ValueError("--fit-only requires a completed evaluation in this directory")
    if (out / "results.json").exists() and not args.fit_only:
        raise ValueError("Choose a fresh output directory")
    out.mkdir(parents=True, exist_ok=True)
    code = [Path(__file__), Path("scripts/nose_semantic_experiment.py")] + sorted(Path("src/calnew").rglob("*.py"))
    hashes = {}
    for path in code:
        path = path.resolve()
        relative = path.relative_to(Path.cwd())
        saved = out / ("final-fit-source-code" if args.fit_only else "source-code") / relative
        saved.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, saved)
        hashes[str(relative)] = file_digest(saved)
    write_json(out / ("final-fit-protocol.json" if args.fit_only else "protocol.json"), {"recipe": "Equal v2 + structure/text descriptor-transfer predictions",
        "selection": "runs/nose-semantic-text-inner-v2/aligned-comparison.json; registered training-only rule passed",
        "split_seeds": list(range(42, 52)), "primary_model_seeds": [42,43,44],
        "robustness_model_seed": 42, "semantic_crossfit_seed": 300,
        "validation_refit": args.refit_validation, "reserved_holdouts_opened": False,
        "test_based_model_selection": False, "code_sha256": hashes})
    started = time.time()
    torch.set_num_threads(args.threads)
    snapshot = Path(json.loads(Path("data/current.json").read_text())["snapshot"])
    ctx = Context(snapshot, RESERVED)
    molecules, labels = load_corpus(ctx, out)
    word_path = Path(args.word_vectors)
    word_manifest = json.loads(word_path.with_suffix(".json").read_text())
    if word_manifest["sha256"] != file_digest(word_path) or word_manifest["corpus_sha256"] != SHA256:
        raise ValueError("Word vector artifact checksum/source mismatch")
    terms = sorted(pd.read_csv(SOURCE, usecols=["TARGET_Descriptor"]).TARGET_Descriptor.unique())
    with np.load(word_path, allow_pickle=False) as data:
        if data["terms"].tolist() != terms:
            raise ValueError("Descriptor vocabulary mismatch")
        vectors = data["vectors"].copy()
    source_blocks = BlockCache(Path("data/features")).blocks(("rdkit","fingerprint"), molecules.smiles.tolist())
    source_x = np.column_stack([source_blocks["rdkit"],source_blocks["fingerprint"]])
    transfer = DescriptorTransfer(molecules, labels, source_x, encoder="extra_trees", threads=args.threads, term_vectors=vectors)
    ids = ctx.keller.molecule_id.to_numpy()
    rows = ctx.rows(ids)
    y, x = ctx.keller.pleasantness.to_numpy(), ctx.keller.x.to_numpy()[:,None]
    base = np.column_stack([ctx.B[n][rows] for n in SEMANTIC_BASE] + [x])
    task_source = np.column_stack([ctx.B["rdkit"][rows],ctx.B["fingerprint"][rows]])
    results = {}
    for split in (() if args.fit_only else range(42, 52)):
        tr, va, te = benchmark_split(len(ids), FRACTIONS["keller"], split, args.refit_validation)
        held = np.r_[va,te]
        semantic = SemanticHead().fit(transfer, ids[tr], ids[held], task_source[tr], task_source[held],
            base[tr], y[tr], seed=300, threads=args.threads)
        sem_pred = semantic.predict(task_source[te],base[te])
        records, predictions = [], {}
        for seed in ([42,43,44] if split == 42 else [42]):
            q, d, _ = ctx.stage_a_features(ids[tr], ids[held], seed)
            enriched = {**ctx.B, "quality": q, "direction": d}
            pick = lambda rr: {n: enriched[n][rr] for _, names in HEDONIC_MEMBERS for n in names}
            hedonic = TabularEnsemble(HEDONIC_MEMBERS, seed=seed, threads=args.threads).fit(
                pick(rows[tr]), y[tr], ctx.connectivity[rows[tr]], columns=x[tr])
            v2 = hedonic.predict(pick(rows[te]), columns=x[te])
            blend = (v2 + sem_pred)/2
            if not np.isfinite(blend).all():
                raise ValueError("Non-finite pleasantness predictions")
            records.append({"seed": seed, **{name: float(pearsonr(y[te],p).statistic)
                for name,p in (("v2",v2),("semantic",sem_pred),("v3",blend))}})
            predictions[f"v2_seed_{seed}"], predictions[f"v3_seed_{seed}"] = v2, blend
            print(f"split {split}, model seed {seed}: {records[-1]}", flush=True)
        results[str(split)] = {"scores": records, "train_n": len(tr), "test_n": len(te), "source_rows": semantic.source_rows}
        np.savez_compressed(out / f"split-{split}.npz", ids=np.asarray(ids[te],dtype=str), y=y[te], semantic=sem_pred, **predictions)
        write_json(out / "partial.json", results)
    if args.fit_only:
        summary = json.loads((out / "results.json").read_text())["robustness"]
    else:
        robustness = {name: [results[str(s)]["scores"][0][name] for s in range(42,52)] for name in ("v2","semantic","v3")}
        summary = {name: {"mean": float(np.mean(scores)), "sd": float(np.std(scores))} for name,scores in robustness.items()}
        write_json(out / "results.json", {"per_split": results, "robustness": summary, "word_vectors": word_manifest,
            "corpus_sha256": SHA256, "seconds": round(time.time()-started), "reserved_holdouts_opened": False,
            "validation_refit": args.refit_validation, "comparison": "Reduced CALNEW targets; not exact NOSE reproduction"})
    if args.fit_final or args.fit_only:
        print("Final serving fit on usable development molecules", flush=True)
        semantic = SemanticHead().fit(transfer, ids, [], task_source, task_source[:0], base, y, seed=300, threads=args.threads)
        q,d,_ = ctx.stage_a_features(ids, [], 42)
        enriched = {**ctx.B, "quality": q, "direction": d}
        pick = {n: enriched[n][rows] for _, names in HEDONIC_MEMBERS for n in names}
        hedonic = TabularEnsemble(HEDONIC_MEMBERS, seed=42, threads=args.threads).fit(pick,y,ctx.connectivity[rows],columns=x)
        qb = {n:ctx.B[n][ctx.a_rows] for n in ctx.cfg["quality_blocks"]}
        quality = QualityStage(ctx.cfg["quality_blocks"],"fingerprint",seeds=(42,),epochs=ctx.cfg["quality"]["epochs"]).fit(
            qb,ctx.labels[ctx.a_rows],ctx.direction[ctx.a_rows])
        bundle = {"semantic": semantic, "hedonic": hedonic, "quality": quality,
            "quality_blocks": ctx.cfg["quality_blocks"], "training_ids": np.asarray(ids,dtype=str), "word_vectors": word_manifest}
        joblib.dump(bundle,out / "semantic-pleasantness.joblib",compress=3)
        write_json(out / "serving.json", {"artifact_sha256": file_digest(out / "semantic-pleasantness.joblib"),
            "training_molecules": len(ids), "snapshot": str(snapshot), "reserved_holdouts_opened": False,
            "validated_endpoint": "Keller pleasantness at each molecule's higher-concentration stimulus"})
    print(summary,flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out")
    parser.add_argument("--word-vectors", default="data/features/nose-descriptor-minilm.npz")
    parser.add_argument("--refit-validation",action="store_true")
    parser.add_argument("--fit-final",action="store_true")
    parser.add_argument("--fit-only",action="store_true",help="Save a serving bundle after an existing completed evaluation")
    parser.add_argument("--threads",type=int,default=4)
    parser.add_argument("--predict-run",type=Path)
    parser.add_argument("--smiles",nargs="+")
    parser.add_argument("--dilution",type=float,default=1e-3)
    args = parser.parse_args()
    with threadpool_limits(limits=args.threads):
        if args.predict_run:
            if not args.smiles:
                parser.error("--predict-run requires --smiles")
            print(json.dumps(predict_pleasantness(args.predict_run,args.smiles,args.dilution),indent=2))
        else:
            if not args.out:
                parser.error("--out is required for evaluation")
            run(args)
