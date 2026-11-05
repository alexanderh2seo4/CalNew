"""Estimate the fixed v2 threshold model with training counts close to NOSE's 160.

Ten-fold connectivity CV uses 165-168 training rows and scores all 186 development
molecules out of fold. This is a separate protocol, not the paper's fixed test split.
No model selection uses these scores; reserved final partitions remain excluded.
"""
import argparse
import json
import shutil
import time
from pathlib import Path

import numpy as np
import torch
from scipy.stats import pearsonr
from sklearn.model_selection import GroupKFold
from threadpoolctl import threadpool_limits

from calnew.io import file_digest, write_json
from calnew.pipeline.auxiliary import exclude_touching
from calnew.pipeline.paper_benchmark import Context
from calnew.pipeline.stages import THRESHOLD_MEMBERS, TabularEnsemble, ThresholdStage
from nose_semantic_experiment import RESERVED


def run(args):
    out=Path(args.out)
    if (out/"results.json").exists():
        raise ValueError("Choose a new output directory")
    out.mkdir(parents=True,exist_ok=True)
    files=[Path(__file__)]+sorted(Path("src/calnew").rglob("*.py"))
    hashes={}
    for path in files:
        relative=path.resolve().relative_to(Path.cwd())
        saved=out/"source-code"/relative
        saved.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,saved)
        hashes[str(relative)]=file_digest(saved)
    write_json(out/"protocol.json",{"protocol":"10-fold development connectivity CV, pooled out-of-fold Pearson",
        "fold_seed":42,"model_seeds":args.seeds,"model_recipe":"unchanged v2",
        "warm_start":str(args.warm_start) if args.warm_start else None,
        "purpose":"Estimate performance with training count close to published NOSE 160, keeping all reserved exclusions",
        "model_selection":False,"reserved_holdouts_opened":False,"code_sha256":hashes})
    torch.set_num_threads(args.threads)
    start=time.time()
    snapshot=Path(json.loads(Path("data/current.json").read_text())["snapshot"])
    ctx=Context(snapshot,RESERVED)
    ids=ctx.thr.molecule_id.to_numpy()
    groups=np.asarray([i.split("-")[0] for i in ids])
    y=ctx.thr.y.to_numpy()
    rows=ctx.rows(ids)
    predictions=np.full((len(args.seeds),len(ids)),np.nan)
    splits=list(GroupKFold(10,shuffle=True,random_state=42).split(ids,groups=groups))
    folds=np.full(len(ids),-1,int)
    for fold,(_,te) in enumerate(splits):
        folds[te]=fold
    if args.warm_start:
        with np.load(args.warm_start,allow_pickle=False) as saved:
            if not np.array_equal(saved["ids"],ids) or not np.array_equal(saved["y"],y):
                raise ValueError("Warm-start IDs/targets differ")
            previous=saved["predictions"]
            previous_seeds=saved["model_seeds"].tolist()
            assigned=np.isfinite(previous).any(0)
            if not np.array_equal(saved["folds"][assigned],folds[assigned]):
                raise ValueError("Warm-start folds differ")
            for j,seed in enumerate(args.seeds):
                if seed in previous_seeds:
                    predictions[j]=previous[previous_seeds.index(seed)]
    training_counts=[]
    for fold,(tr,te) in enumerate(splits):
        if set(groups[tr]) & set(groups[te]):
            raise ValueError("Connectivity group crosses a CV boundary")
        folds[te]=fold
        training_counts.append(len(tr))
        for j,seed in enumerate(args.seeds):
            if np.isfinite(predictions[j,te]).all():
                print(f"Reused fold {fold+1}/10, model seed {seed}",flush=True)
                continue
            q,d,_=ctx.stage_a_features(ids[tr],ids[te],seed)
            enriched={**ctx.B,"quality":q,"direction":d}
            pick=lambda rr:{n:enriched[n][rr] for _,names in THRESHOLD_MEMBERS for n in names}
            keep=exclude_touching(ctx.aux,ids[te])
            auxiliary=({n:v[keep] for n,v in ctx.aux_blocks.items()},ctx.aux.y.to_numpy()[keep],1.)
            members=TabularEnsemble(THRESHOLD_MEMBERS,seed=seed,threads=args.threads).fit(
                pick(rows[tr]),y[tr],ctx.connectivity[rows[tr]],auxiliary=auxiliary)
            potency=lambda rr:{n:enriched[n][rr] for n in ctx.cfg["potency_blocks"]}
            fusion=ThresholdStage(ctx.cfg["potency_blocks"],"fingerprint",seeds=tuple(seed*10+k for k in range(5)),
                epochs=ctx.cfg["threshold"]["epochs"]).fit(potency(rows[tr]),y[tr],ctx.connectivity[rows[tr]])
            predictions[j,te]=np.column_stack([fusion.predict(potency(rows[te]))["ensemble"],
                members.predict_members(pick(rows[te]))]).mean(1)
            if not np.isfinite(predictions[j,te]).all():
                raise ValueError("Non-finite threshold CV predictions")
            np.savez_compressed(out/"partial.npz",ids=np.asarray(ids,dtype=str),y=y,folds=folds,predictions=predictions,model_seeds=args.seeds)
            print(f"fold {fold+1}/10, model seed {seed}, train {len(tr)}, test {len(te)}",flush=True)
    scores=[float(pearsonr(y,p).statistic) for p in predictions]
    np.savez_compressed(out/"oof.npz",ids=np.asarray(ids,dtype=str),y=y,folds=folds,predictions=predictions,model_seeds=args.seeds)
    write_json(out/"results.json",{"pooled_pearson_per_model_seed":scores,"mean":float(np.mean(scores)),
        "model_seed_sd":float(np.std(scores)),"model_seeds":args.seeds,"training_counts":training_counts,"molecules_scored":len(ids),
        "seconds":round(time.time()-start),"reserved_holdouts_opened":False,
        "difference_from_paper":"Ten-fold CV instead of its fixed 54-molecule test; reduced cohort and water auxiliary targets"})
    print(scores,flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",required=True)
    parser.add_argument("--threads",type=int,default=2)
    parser.add_argument("--seeds",type=int,nargs="+",default=[42,43,44])
    parser.add_argument("--warm-start",type=Path)
    args=parser.parse_args()
    with threadpool_limits(limits=args.threads):
        run(args)
