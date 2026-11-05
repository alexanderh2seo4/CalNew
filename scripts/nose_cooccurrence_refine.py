"""Frozen training-only trial using the new globally disjoint curated corpus."""
import os
import json
from pathlib import Path
import platform
import shutil
import time

import joblib
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from calnew.io import file_digest,write_json
from calnew.pipeline.blocks import BlockCache,EXPLICIT_BLOCKS
from calnew.pipeline.cooccurrence import CooccurrenceTransfer,direction_features
from calnew.pipeline.paper_benchmark import FRACTIONS,random_split
from calnew.pipeline.semantic import SEMANTIC_BASE
from calnew.pipeline.semantic_balanced import array_sha256
from calnew.pipeline.stages import stack
from nose_compact_heads import BASELINES
from nose_parity_progress import read_only_context,inspect_run,dependency_versions
from nose_threshold_semantic_refine import atomic_npz,score

OUT=Path("runs/nose-cooccurrence-inner-20261028-v1")
SOURCE=Path("data/curated/nose-20261028-v1")
CANDIDATES={r+"_"+h:(r,h) for r in ("raw","direction") for h in ("trees","ridge")}


def run():
    if platform.node().lower()!=os.environ.get("CALNEW_COMPUTE_HOST", "").lower():
        raise ValueError("Use authorized SSH host")
    if OUT.exists():
        raise ValueError("Existing run preserved")
    OUT.mkdir(parents=True)
    manifest=json.loads((SOURCE/"manifest.json").read_text())
    for name,sha in manifest["files"].items():
        if file_digest(SOURCE/name)!=sha:
            raise ValueError("Curated source checksum mismatch")
    plan={"host":platform.node(),"source_manifest_sha256":file_digest(SOURCE/"manifest.json"),
        "source_scope":"All reserved groups and ALL primary development connectivities excluded",
        "source_recipe":"L2 TF-IDF; SVD64 seed173 n_iter7; standardize64 target axes; ET150 leaf4 maxfeatures.3 seed173",
        "source_features":["rdkit","fingerprint"],"candidates":CANDIDATES,
        "heads":{"trees":"ET500 leaf2 maxfeatures.3 seed42 on SEMANTIC_BASE+latent",
            "ridge":"Training-fold median/scale/Ridge100 on EXPLICIT_BLOCKS+latent"},
        "candidate_blends":"Each standalone and fixed half/current",
        "training_scope":"Original split42 training111/260 only; 3 repeats GroupKFold5 seeds100..102",
        "gate":{"mean_pearson_gain_min":.01,"positive_repeats_min":2,"no_mean_mae_increase":True},
        "main_validation_test_targets_scored":False,"reserved_targets_fitted_or_scored":False,
        "dependencies":dependency_versions(),"code_sha256":{str(p):file_digest(p) for p in
            [Path(__file__),Path("src/calnew/pipeline/cooccurrence.py")]}}
    write_json(OUT/"selection-plan.json",plan)
    for p in [Path(__file__),Path("src/calnew/pipeline/cooccurrence.py")]:
        shutil.copy2(p,OUT/p.name)
    print("Plan frozen before source and endpoint fitting",flush=True)
    ctx=read_only_context(Path(json.loads(Path("data/current.json").read_text())["snapshot"]))
    molecules=pd.read_parquet(SOURCE/"molecules.parquet")
    labels=sparse.load_npz(SOURCE/"binary-associations.npz")
    forbidden={str(m).split("-")[0] for f in (ctx.thr,ctx.keller,ctx.ravia) for m in f.molecule_id}
    if set(molecules.molecule_id.str.split("-").str[0]) & forbidden:
        raise ValueError("Primary connectivity in source")
    source_blocks=BlockCache(Path("data/features")).blocks(("rdkit","fingerprint"),molecules.smiles.tolist())
    features=np.column_stack([source_blocks[n] for n in ("rdkit","fingerprint")])
    task_features=np.column_stack([ctx.B[n] for n in ("rdkit","fingerprint")])
    write_json(OUT/"source-prefit.json",{"source_ids":molecules.molecule_id.tolist(),
        "source_features_sha256":array_sha256(features),"task_features_sha256":array_sha256(task_features),
        "source_associations_sha256":file_digest(SOURCE/"binary-associations.npz"),
        "primary_connectivity_overlap":[],"timing":"BEFORE source fit"})
    print(f"Fit co-occurrence source on {len(molecules)} molecules",flush=True)
    source=CooccurrenceTransfer().fit(features,labels)
    task_raw=source.predict(task_features)
    joblib.dump(source,OUT/"source-transfer.joblib",compress=3)
    atomic_npz(OUT/"source-predictions.npz",ids=np.array(ctx.universe,dtype=str),raw=task_raw)
    write_json(OUT/"source-fit.json",{"artifact_sha256":file_digest(OUT/"source-transfer.joblib"),
        "predictions_sha256":file_digest(OUT/"source-predictions.npz"),
        "svd_explained_variance":float(source.svd.explained_variance_ratio_.sum()),
        "primary_connectivity_overlap":[],"endpoint_labels_fitted":False})
    print("Source fit saved; begin original-training folds",flush=True)
    results={}
    for dataset,baseline in BASELINES.items():
        audit=inspect_run(ctx,baseline)
        if audit["datasets"][dataset]["status"]!="complete":
            raise ValueError("Incomplete baseline")
        write_json(OUT/f"{dataset}-baseline-audit.json",audit)
        frame=ctx.thr if dataset=="abraham" else ctx.keller
        tr,va,te=random_split(len(frame),FRACTIONS[dataset],42)
        ids=frame.molecule_id.to_numpy(dtype=str)[tr]
        y=frame["y" if dataset=="abraham" else "pleasantness"].to_numpy()[tr]
        rows=ctx.rows(ids)
        groups=np.array([m.split("-")[0] for m in ids])
        bases={"trees":stack(ctx.B,SEMANTIC_BASE)[rows],"ridge":stack(ctx.B,EXPLICIT_BLOCKS)[rows]}
        if dataset=="keller":
            bases={k:np.column_stack([x,frame.x.to_numpy()[tr]]) for k,x in bases.items()}
        latent={"raw":task_raw[rows],"direction":direction_features(task_raw[rows])}
        designs={name:np.column_stack([bases[head],latent[representation]])
            for name,(representation,head) in CANDIDATES.items()}
        write_json(OUT/f"{dataset}-prefit.json",{"ids":ids.tolist(),"targets":y.tolist(),
            "features":{n:array_sha256(x) for n,x in designs.items()}})
        names=["current",*CANDIDATES,*("blend_"+n for n in CANDIDATES)]
        predictions={n:np.full((3,len(ids)),np.nan) for n in names}
        started=time.time()
        for repeat in range(3):
            for fold,(a,b) in enumerate(GroupKFold(5,shuffle=True,random_state=100+repeat).split(ids,groups=groups)):
                if set(groups[a]) & set(groups[b]):
                    raise ValueError("Outer connectivity overlap")
                old=baseline/f"{dataset}-repeat-{repeat}-fold-{fold}.npz"
                record=json.loads(old.with_suffix(".json").read_text())
                identity=record["identity"]
                if (file_digest(old)!=record["sha256"] or identity["train_ids"]!=ids[a].tolist()
                        or identity["evaluate_ids"]!=ids[b].tolist() or identity["targets"]!=y[b].tolist()):
                    raise ValueError("Baseline identity differs")
                with np.load(old,allow_pickle=False) as saved:
                    predictions["current"][repeat,b]=saved["current"]
                for name,(_,head) in CANDIDATES.items():
                    model=make_pipeline(SimpleImputer(strategy="median",keep_empty_features=True),
                        ExtraTreesRegressor(n_estimators=500,min_samples_leaf=2,max_features=.3,random_state=42,n_jobs=2)) if head=="trees" else make_pipeline(
                        SimpleImputer(strategy="median",keep_empty_features=True),StandardScaler(),Ridge(alpha=100))
                    p=model.fit(designs[name][a],y[a]).predict(designs[name][b])
                    if dataset=="keller":
                        p=np.clip(p,0,100)
                    predictions[name][repeat,b]=p
                    predictions["blend_"+name][repeat,b]=(p+predictions["current"][repeat,b])/2
                path=OUT/f"{dataset}-repeat-{repeat}-fold-{fold}.npz"
                atomic_npz(path,ids=ids[b],y=y[b],**{n:p[repeat,b] for n,p in predictions.items()})
                write_json(path.with_suffix(".json"),{"train_ids":ids[a].tolist(),"evaluate_ids":ids[b].tolist(),
                    "targets":y[b].tolist(),"baseline_sha256":file_digest(old),"sha256":file_digest(path),
                    "source_artifact_sha256":file_digest(OUT/"source-transfer.joblib"),"connectivity_disjoint":True})
                print(f"{dataset} repeat{repeat} fold{fold} complete ({time.time()-started:.0f}s)",flush=True)
        if any(not np.isfinite(p).all() for p in predictions.values()):
            raise ValueError("Missing fold predictions")
        scores={n:[score(y,p) for p in values] for n,values in predictions.items()}
        passing=[]
        for name in names[1:]:
            gains=np.array([s["pearson"]-b["pearson"] for s,b in zip(scores[name],scores["current"])])
            if gains.mean()>=.01 and (gains>0).sum()>=2 and np.mean([s["mae"] for s in scores[name]])<=np.mean([s["mae"] for s in scores["current"]]):
                passing.append(name)
        selected=max(passing,key=lambda n:np.mean([s["pearson"] for s in scores[n]])) if passing else "current"
        results[dataset]={"scores":scores,"passing":passing,"selected":selected}
        atomic_npz(OUT/f"{dataset}-inner-oof.npz",ids=ids,y=y,**predictions)
        write_json(OUT/"results.json",{"status":"partial" if dataset=="abraham" else "complete",
            "results":results,"main_validation_test_targets_scored":False,"reserved_targets_fitted_or_scored":False})
        print(json.dumps({"dataset":dataset,"selected":selected,"means":{n:{m:float(np.mean([s[m] for s in v])) for m in ("pearson","mae")} for n,v in scores.items()}}),flush=True)


if __name__=="__main__":
    with threadpool_limits(limits=2):
        run()
