"""Independently reconstruct new trial gates and frozen benchmark metrics on SSH."""
import os
import json
from pathlib import Path
import platform

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.stats import pearsonr
from sklearn.metrics import r2_score
from sklearn.model_selection import GroupKFold

from calnew.io import file_digest,write_json
from calnew.pipeline.paper_benchmark import FRACTIONS,benchmark_split
from nose_parity_progress import read_only_context


def metrics(y,p):
    if y.shape!=p.shape or not np.isfinite(p).all():
        raise ValueError("Invalid saved predictions")
    return {"pearson":float(pearsonr(y,p).statistic),"mae":float(np.mean(np.abs(y-p))),
        "rmse":float(np.sqrt(np.mean((y-p)**2))),"r2":float(r2_score(y,p)),"mse":float(np.mean((y-p)**2))}


def trial(root,ctx):
    result=json.loads((root/"results.json").read_text())
    if result["status"]!="complete" or result["main_validation_test_targets_scored"] or result["reserved_targets_fitted_or_scored"]:
        raise ValueError("Incomplete or out-of-scope trial")
    audited={}
    for dataset,saved in result["results"].items():
        frame=ctx.thr if dataset=="abraham" else ctx.keller
        tr,_,_=benchmark_split(len(frame),FRACTIONS[dataset],42,False)
        ids=frame.molecule_id.to_numpy(dtype=str)[tr]
        y=frame["y" if dataset=="abraham" else "pleasantness"].to_numpy()[tr]
        groups=np.array([m.split("-")[0] for m in ids])
        with np.load(root/f"{dataset}-inner-oof.npz",allow_pickle=False) as data:
            if not np.array_equal(data["ids"],ids) or not np.array_equal(data["y"],y):
                raise ValueError("Trial OOF cohort differs")
            oof={n:data[n].copy() for n in saved["scores"]}
        reconstructed={n:np.full((3,len(ids)),np.nan) for n in oof}
        for repeat in range(3):
            coverage=np.zeros(len(ids),int)
            for fold,(a,b) in enumerate(GroupKFold(5,shuffle=True,random_state=100+repeat).split(ids,groups=groups)):
                path=root/f"{dataset}-repeat-{repeat}-fold-{fold}.npz"
                record=json.loads(path.with_suffix(".json").read_text())
                if (record["sha256"]!=file_digest(path) or record["train_ids"]!=ids[a].tolist()
                        or record["evaluate_ids"]!=ids[b].tolist() or record["targets"]!=y[b].tolist()
                        or set(groups[a]) & set(groups[b]) or not record["connectivity_disjoint"]):
                    raise ValueError("Trial fold checksum/assignment differs")
                baseline=Path("runs")/("nose-parity-threshold-water-inner-v2" if dataset=="abraham" else "nose-parity-pleasantness-grouped-inner-v2")/path.name
                if file_digest(baseline)!=record["baseline_sha256"]:
                    raise ValueError("Paired baseline changed")
                with np.load(path,allow_pickle=False) as data,np.load(baseline,allow_pickle=False) as old:
                    if not np.array_equal(data["ids"],ids[b]) or not np.array_equal(data["y"],y[b]) or not np.array_equal(data["current"],old["current"]):
                        raise ValueError("Saved trial IDs/targets/comparator differ")
                    for name in reconstructed:
                        reconstructed[name][repeat,b]=data[name]
                        if name.startswith("blend_") and not np.array_equal(data[name],(data["current"]+data[name[6:]])/2):
                            raise ValueError("Fixed blend differs")
                coverage[b]+=1
            if not np.all(coverage==1):
                raise ValueError("Fold coverage differs")
        scores={}
        for name,p in reconstructed.items():
            if not np.array_equal(p,oof[name]):
                raise ValueError("OOF values differ from folds")
            scores[name]=[metrics(y,row) for row in p]
            for actual,expected in zip(scores[name],saved["scores"][name]):
                if any(not np.isclose(actual[m],v,atol=1e-12,rtol=0) for m,v in expected.items()):
                    raise ValueError("Saved scores differ from reconstruction")
        passing=[]
        for name in scores:
            if name=="current":continue
            gains=np.array([s["pearson"]-b["pearson"] for s,b in zip(scores[name],scores["current"])])
            if gains.mean()>=.01 and (gains>0).sum()>=2 and np.mean([s["mae"] for s in scores[name]])<=np.mean([s["mae"] for s in scores["current"]]):
                passing.append(name)
        selected=max(passing,key=lambda n:np.mean([s["pearson"] for s in scores[n]])) if passing else "current"
        if sorted(passing)!=sorted(saved["passing"]) or selected!=saved["selected"]:
            raise ValueError("Reconstructed gate differs")
        audited[dataset]={"verified_folds":15,"selected":selected,"passing":passing,
            "mean_scores":{n:{m:float(np.mean([s[m] for s in rows])) for m in ("pearson","mae")} for n,rows in scores.items()}}
    return audited


def benchmark(root,ctx,refit):
    result=json.loads((root/"results.json").read_text())
    if result["status"]!="complete" or result["test_based_selection"] or result["reserved_targets_fitted_or_scored"]:
        raise ValueError("Benchmark status/boundary differs")
    all_ids=ctx.thr.molecule_id.to_numpy(dtype=str)
    y=ctx.thr.y.to_numpy()
    rows={}
    for split in range(42,52):
        tr,va,te=benchmark_split(len(all_ids),FRACTIONS["abraham"],split,refit)
        path=root/f"split-{split}.npz"
        record=json.loads(path.with_suffix(".json").read_text())
        pref=json.loads((root/f"split-{split}-prefit-resource.json").read_text())
        if record["sha256"]!=file_digest(path) or record["identity"]!=pref["identity"] or result["per_split"][str(split)]["checkpoint_sha256"]!=file_digest(path):
            raise ValueError("Frozen prefit/checkpoint identity differs")
        if (record["identity"]["train_ids"]!=all_ids[tr].tolist() or record["identity"]["test_ids"]!=all_ids[te].tolist()
                or record["identity"]["water_held_connectivity_overlap"]):
            raise ValueError("Benchmark source or primary assignments differ")
        with np.load(path,allow_pickle=False) as data:
            if not np.array_equal(data["ids"],all_ids[te]) or not np.array_equal(data["y"],y[te]) or not np.array_equal(data["train_ids"],all_ids[tr]) or not np.array_equal(data["train_y"],y[tr]):
                raise ValueError("Actual benchmark IDs/targets differ")
            if not np.array_equal(data["selected"],(data["baseline"]+data["branch"])/2):
                raise ValueError("Frozen selected blend differs")
            rows[split]={n:metrics(y[te],data[n]) for n in ("baseline","branch","selected")}
        for n,actual in rows[split].items():
            for m,v in result["per_split"][str(split)]["scores"][n].items():
                if not np.isclose(v,actual[m],atol=1e-12,rtol=0):
                    raise ValueError("Saved split metric differs")
    summary={n:{m:{"mean":float(np.mean([r[n][m] for r in rows.values()])),"sd":float(np.std([r[n][m] for r in rows.values()]))}
        for m in ("pearson","mae","r2","mse")} for n in ("baseline","branch","selected")}
    for n,scores in summary.items():
        for m,values in scores.items():
            for key,v in values.items():
                if not np.isclose(v,result["metrics"][n][m][key],atol=1e-12,rtol=0):
                    raise ValueError("Benchmark summary differs")
    return {"verified_splits":10,"metrics":summary,"paired":result["paired"],
        "full_precision_NOSE_reference":.836,"reference_reached":summary["selected"]["pearson"]["mean"]>=.836,
        "comparison_limit":"Original random assignments retain recorded primary connectivity overlaps; proxy targets differ from paper"}


def main():
    if platform.node().lower()!=os.environ.get("CALNEW_COMPUTE_HOST", "").lower():
        raise ValueError("Use authorized SSH host")
    ctx=read_only_context(Path(json.loads(Path("data/current.json").read_text())["snapshot"]))
    out={"host":platform.node(),"trials":{},"benchmarks":{},"reserved_targets_fitted_or_scored":False}
    for name in ("nose-compact-heads-inner-20261028-v1","nose-cooccurrence-inner-20261028-v1",
            "nose-sagar-measured-profile-inner-20261028-v1"):
        out["trials"][name]=trial(Path("runs")/name,ctx)
    for name,refit in (("nose-threshold-direction-original-v1",False),("nose-threshold-direction-refit-v1",True)):
        root=Path("runs")/name
        out["benchmarks"][name]=benchmark(root,ctx,refit) if (root/"results.json").exists() else {"status":"pending"}
    root=Path("data/curated/nose-20261028-v1")
    manifest=json.loads((root/"manifest.json").read_text())
    for name,sha in manifest["files"].items():
        if file_digest(root/name)!=sha:raise ValueError("Curated file checksum differs")
    molecules=pd.read_parquet(root/"molecules.parquet")
    pairs=pd.read_parquet(root/"associations.parquet")
    labels=sparse.load_npz(root/"binary-associations.npz")
    forbidden={str(m).split("-")[0] for f in (ctx.thr,ctx.keller,ctx.ravia) for m in f.molecule_id}
    if (set(molecules.molecule_id.str.split("-").str[0]) & forbidden or pairs.duplicated().any()
            or len(pairs)!=labels.nnz or not np.all(labels.data==1) or len(molecules)!=labels.shape[0]
            or not set(pairs.molecule_id)<=set(molecules.molecule_id)):
        raise ValueError("Curated dataset joins/uniqueness/disjointness differ")
    out["curated_dataset"]={"molecules":len(molecules),"pairs":len(pairs),"all_file_checksums_verified":True,
        "endpoint_connectivity_overlap":[],"binary_unique_associations_verified":True}
    out["status"]="verified"
    write_json(Path("runs/nose-research-independent-audit-20261028.json"),out)
    print(json.dumps(out,indent=2),flush=True)


if __name__=="__main__":
    main()
