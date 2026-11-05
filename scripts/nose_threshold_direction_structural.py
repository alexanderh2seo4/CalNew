"""Structural sensitivity check of the frozen blend using retained baseline OOF.

This is development CV, not independent nested selection or a final holdout.
No new quality/baseline models fit, and no recipe is selected from these scores.
"""
import os
from pathlib import Path
import json
import platform

import numpy as np
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.impute import SimpleImputer
from sklearn.model_selection import GroupKFold
from threadpoolctl import threadpool_limits

from calnew.io import file_digest,write_json
from calnew.pipeline.threshold_direction import source_direction
from nose_parity_progress import read_only_context
from nose_threshold_semantic_refine import cohort,atomic_npz
from nose_research_audit_20261028 import metrics

OUT=Path("runs/nose-threshold-direction-structural-20261028-v2")
BASELINE=Path("runs/nose-threshold-grouped-tenfold-v2")
SOURCE=Path("runs/nose-threshold-disjoint-semantic-inner-v1/source-idf_unit.npz")


def main():
    if platform.node().lower()!=os.environ.get("CALNEW_COMPUTE_HOST", "").lower():raise ValueError("SSH only")
    if OUT.exists():raise ValueError("Preserve existing analysis")
    OUT.mkdir(parents=True)
    plan=json.loads((BASELINE/"protocol.json").read_text())
    for name,sha in plan["code_sha256"].items():
        if file_digest(BASELINE/"source-code"/name)!=sha:
            raise ValueError("Historical baseline source archive differs")
    write_json(OUT/"protocol.json",{"recipe":"Previously frozen half/current + half direction-confidence ET",
        "purpose":"Connectivity-disjoint development sensitivity check; no new selection",
        "baseline_oof_sha256":file_digest(BASELINE/"oof.npz"),"source_sha256":file_digest(SOURCE),
        "folds":"GroupKFold10 seed42; all186 development molecules",
        "source_boundary":"All186 development connectivities excluded before source training",
        "not_independent_nested_model_selection":True,"reserved_targets_fitted_or_scored":False,
        "model_selection":False,"code_sha256":file_digest(Path(__file__))})
    ctx=read_only_context(Path(json.loads(Path("data/current.json").read_text())["snapshot"]))
    ids,_,_,_,_,_,base=cohort(ctx)
    y=ctx.thr.y.to_numpy()
    groups=np.array([m.split("-")[0] for m in ids])
    with np.load(BASELINE/"oof.npz",allow_pickle=False) as saved:
        if not np.array_equal(saved["ids"],ids) or not np.array_equal(saved["y"],y):
            raise ValueError("Baseline OOF cohort differs")
        baseline=saved["predictions"].copy()
        old_folds=saved["folds"].copy()
        seeds=saved["model_seeds"].copy()
    with np.load(SOURCE,allow_pickle=False) as saved:
        if not np.array_equal(saved["ids"],ids):raise ValueError("Source ID order differs")
        raw=saved["features"].copy()
    source_record=json.loads(SOURCE.with_suffix(".json").read_text())
    if source_record["sha256"]!=file_digest(SOURCE):raise ValueError("Source checksum differs")
    features=np.column_stack([base["trees"],source_direction(raw)])
    branch=np.full(len(ids),np.nan)
    counts=[]
    for fold,(a,b) in enumerate(GroupKFold(10,shuffle=True,random_state=42).split(ids,groups=groups)):
        if set(groups[a])&set(groups[b]) or not np.all(old_folds[b]==fold):raise ValueError("Old structural folds differ")
        x=np.where(np.isfinite(features),features,np.nan)
        imputer=SimpleImputer(strategy="median",keep_empty_features=True).fit(x[a])
        model=ExtraTreesRegressor(n_estimators=500,min_samples_leaf=2,max_features=.3,random_state=42,n_jobs=2)
        branch[b]=model.fit(imputer.transform(x[a]),y[a]).predict(imputer.transform(x[b]))
        counts.append(len(a))
    selected=(baseline+branch[None,:])/2
    scores={name:[metrics(y,p) for p in values] for name,values in (("baseline",baseline),("selected",selected))}
    # Check the retained baseline's published summary rather than accepting it on trust.
    previous=json.loads((BASELINE/"results.json").read_text())
    if not np.allclose([r["pearson"] for r in scores["baseline"]],previous["pooled_pearson_per_model_seed"],atol=1e-12,rtol=0):
        raise ValueError("Retained baseline summary differs")
    atomic_npz(OUT/"oof.npz",ids=ids,y=y,folds=old_folds,seeds=seeds,baseline=baseline,branch=branch,selected=selected)
    result={"status":"complete","host":platform.node(),"scores":scores,
        "mean":{name:{metric:float(np.mean([r[metric] for r in rows])) for metric in ("pearson","mae","r2","mse")} for name,rows in scores.items()},
        "training_counts":counts,"primary_train_held_connectivity_overlap":[],
        "no_new_model_selection":True,"not_independent_nested_model_selection":True,"reserved_targets_fitted_or_scored":False}
    write_json(OUT/"results.json",result)
    print(json.dumps(result,indent=2),flush=True)


if __name__=="__main__":
    with threadpool_limits(limits=2):main()
