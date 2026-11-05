"""Preregistered measured-profile transfer into original Keller training only."""
import os
from pathlib import Path
import json
import platform
import shutil

import numpy as np
import pandas as pd
from scipy.io import loadmat
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from calnew.io import file_digest,write_json
from calnew.pipeline.blocks import BlockCache,EXPLICIT_BLOCKS
from calnew.pipeline.paper_benchmark import FRACTIONS,random_split
from calnew.pipeline.semantic import SEMANTIC_BASE
from calnew.pipeline.semantic_balanced import array_sha256
from calnew.pipeline.stages import stack
from nose_parity_progress import read_only_context,inspect_run,dependency_versions
from nose_threshold_semantic_refine import atomic_npz,score

ROOT=Path("data/raw/sagar_2023/6c4169b7d92b063d9ce011afe8cb4790a4ffe8aa")
AUDIT=Path("runs/sagar-source-audit-20261028-v2")
BASELINE=Path("runs/nose-parity-pleasantness-grouped-inner-v2")
OUT=Path("runs/nose-sagar-measured-profile-inner-20261028-v1")
ALIASES={"flowery":"floral","bakery-like":"bakery","spicey":"spicy"}
TERMS=sorted(["intensity","pleasantness","fishy","burnt","sour","decayed","musky","fruity","sweaty","cool","floral","sweet","warm","bakery","spicy"])


def source_data():
    manifest=json.loads((ROOT/"download.json").read_text())
    for item in manifest["files"]:
        if file_digest(ROOT/item["path"])!=item["sha256"]:raise ValueError("Sagar source changed")
    allowed=pd.read_csv(AUDIT/"allowed-identities.csv").set_index("cid")
    records=[]
    for path in ROOT.rglob("behav_ratings*.mat"):
        subject=loadmat(path,simplify_cells=True)["behav"]
        cid=np.asarray(subject["cid"]).astype(int).ravel()
        names=[ALIASES.get(str(v).strip().lower(),str(v).strip().lower()) for v in np.asarray(subject["percepts"]).ravel()]
        if len(names)!=len(set(names)) or not set(TERMS)<=set(names):raise ValueError("Common source vocabulary differs")
        keep=np.array([i for i,c in enumerate(cid) if c in allowed.index])
        ratings=np.asarray(subject["ratings"])[keep][:,[names.index(t) for t in TERMS]].astype(float)
        if not np.isfinite(ratings).all() or (np.abs(ratings)>1.000001).any():raise ValueError("Unverified source scale/missing values")
        for row,index in enumerate(keep):
            identity=allowed.loc[cid[index]]
            records.append({"molecule_id":identity.molecule_id,"smiles":identity.smiles,"subject":path.stem,
                **{t:ratings[row,j] for j,t in enumerate(TERMS)}})
    observations=pd.DataFrame(records)
    # Equal subject weight within each molecule. These remain native [-1,1]
    # study ratings, never relabeled as Keller's measurements.
    profile=observations.groupby("molecule_id",sort=True)[TERMS].mean()
    molecules=observations.drop_duplicates("molecule_id").set_index("molecule_id").loc[profile.index]
    return molecules.reset_index()[["molecule_id","smiles"]],profile.to_numpy(),observations


def fit_source(x,y,source_ids,excluded):
    forbidden={str(m).split("-")[0] for m in excluded}
    connectivity=np.array([str(m).split("-")[0] for m in source_ids])
    keep=~np.isin(connectivity,sorted(forbidden))
    if keep.sum()<15 or set(connectivity[keep])&forbidden:raise ValueError("Source boundary too small or overlapping")
    imputer=SimpleImputer(strategy="median",keep_empty_features=True).fit(x[keep])
    center=y[keep].mean(0)
    spread=np.maximum(y[keep].std(0),1e-4)
    model=ExtraTreesRegressor(n_estimators=150,min_samples_leaf=3,max_features=.3,random_state=173,n_jobs=2).fit(
        imputer.transform(x[keep]),(y[keep]-center)/spread)
    return (imputer,model,center,spread),{"source_molecules":int(keep.sum()),
        "source_ids_sha256":array_sha256(source_ids[keep]),"source_targets_sha256":array_sha256(y[keep]),
        "excluded_connectivities":sorted(forbidden),"held_connectivity_overlap":[]}


def source_predict(model,x):
    imputer,trees,center,spread=model
    return trees.predict(imputer.transform(x))*spread+center


def crossfit_source(source_x,source_y,source_ids,task_x,train_ids,held_ids,evaluate_ids):
    groups=np.array([str(m).split("-")[0] for m in train_ids])
    values=np.full((len(train_ids),len(TERMS)),np.nan)
    records=[]
    for inner,(a,b) in enumerate(GroupKFold(3,shuffle=True,random_state=173).split(train_ids,groups=groups)):
        model,record=fit_source(source_x,source_y,source_ids,np.r_[held_ids,train_ids[b]])
        values[b]=source_predict(model,task_x[0][b])
        records.append({"fold":inner,**record})
    model,record=fit_source(source_x,source_y,source_ids,held_ids)
    held=source_predict(model,task_x[1])
    records.append({"fold":"held",**record})
    if not np.isfinite(values).all() or held.shape!=(len(evaluate_ids),len(TERMS)):raise ValueError("Misaligned source crossfit")
    return values,held,records


def main():
    if platform.node().lower()!=os.environ.get("CALNEW_COMPUTE_HOST", "").lower():raise ValueError("Use SSH host")
    if OUT.exists():raise ValueError("Preserve existing study")
    OUT.mkdir(parents=True)
    plan={"host":platform.node(),"scope":"Original Keller split42 training260 only",
        "source":"Sagar2023 measured common15 profiles; equal subject average per molecule; native [-1,1] retained",
        "source_revision":"6c4169b7d92b063d9ce011afe8cb4790a4ffe8aa","aliases":ALIASES,"terms":TERMS,
        "source_model":"ET150 leaf3 maxfeatures.3 seed173, train-source-only median imputation and target standardization",
        "source_crossfit":"GroupKFold3 seed173; every source fit excludes all main-held/outer-held connectivities and its feature-fold connectivities",
        "outer_cv":"Three connectivity GroupKFold5 repeats seeds100/101/102",
        "heads":{"trees":"ET500 leaf2 maxfeatures.3 seed42, SEMANTIC_BASE+dilution+source15",
            "ridge":"Training-only median/scale/Ridge100, EXPLICIT_BLOCKS+dilution+source15"},
        "candidates":"Two standalone and two fixed half/current blends",
        "gate":{"mean_pearson_gain_min":.01,"positive_repeats_min":2,"no_mean_mae_increase":True},
        "main_validation_test_targets_scored":False,"reserved_targets_fitted_or_scored":False,
        "code_sha256":file_digest(Path(__file__)),"dependencies":dependency_versions(),
        "source_identity_audit_sha256":file_digest(AUDIT/"report.json")}
    write_json(OUT/"selection-plan.json",plan)
    shutil.copy2(__file__,OUT/Path(__file__).name)
    print("Measured-source plan frozen before all fitting",flush=True)
    ctx=read_only_context(Path(json.loads(Path("data/current.json").read_text())["snapshot"]))
    audit=inspect_run(ctx,BASELINE)
    if audit["datasets"]["keller"]["status"]!="complete":raise ValueError("Incomplete baseline")
    write_json(OUT/"baseline-audit.json",audit)
    molecules,target,observations=source_data()
    observations.to_parquet(OUT/"allowed-source-observations.parquet",index=False)
    b=BlockCache(Path("data/features")).blocks(("rdkit","fingerprint"),molecules.smiles.tolist())
    sx=np.column_stack([b[n] for n in ("rdkit","fingerprint")])
    source_ids=molecules.molecule_id.to_numpy(dtype=str)
    frame=ctx.keller
    tr,va,te=random_split(len(frame),FRACTIONS["keller"],42)
    all_ids=frame.molecule_id.to_numpy(dtype=str)
    ids,main_held=all_ids[tr],all_ids[np.r_[va,te]]
    y=frame.pleasantness.to_numpy()[tr]
    rows=ctx.rows(ids)
    tx=np.column_stack([ctx.B[n][rows] for n in ("rdkit","fingerprint")])
    bases={"trees":stack(ctx.B,SEMANTIC_BASE)[rows],"ridge":stack(ctx.B,EXPLICIT_BLOCKS)[rows]}
    bases={n:np.column_stack([x,frame.x.to_numpy()[tr]]) for n,x in bases.items()}
    write_json(OUT/"resources.json",{"training_ids":ids.tolist(),"targets":y.tolist(),
        "source_ids":source_ids.tolist(),"source_features_sha256":array_sha256(sx),"source_targets_sha256":array_sha256(target),
        "base_features":{n:array_sha256(x) for n,x in bases.items()},"source_observations_sha256":file_digest(OUT/"allowed-source-observations.parquet")})
    groups=np.array([m.split("-")[0] for m in ids])
    names=("current","trees","ridge","blend_trees","blend_ridge")
    predictions={n:np.full((3,len(ids)),np.nan) for n in names}
    for repeat in range(3):
        for fold,(a,b) in enumerate(GroupKFold(5,shuffle=True,random_state=100+repeat).split(ids,groups=groups)):
            held=np.r_[main_held,ids[b]]
            path=BASELINE/f"keller-repeat-{repeat}-fold-{fold}.npz"
            record=json.loads(path.with_suffix(".json").read_text())
            identity=record["identity"]
            if (record["sha256"]!=file_digest(path) or identity["train_ids"]!=ids[a].tolist()
                    or identity["held_ids"]!=held.tolist() or identity["evaluate_ids"]!=ids[b].tolist()
                    or identity["targets"]!=y[b].tolist() or set(groups[a])&set(groups[b])):raise ValueError("Paired baseline differs")
            with np.load(path,allow_pickle=False) as old:predictions["current"][repeat,b]=old["current"]
            source_train,source_held,source_audit=crossfit_source(sx,target,source_ids,(tx[a],tx[b]),ids[a],held,ids[b])
            for name in ("trees","ridge"):
                x,z=np.column_stack([bases[name][a],source_train]),np.column_stack([bases[name][b],source_held])
                model=make_pipeline(SimpleImputer(strategy="median",keep_empty_features=True),
                    ExtraTreesRegressor(n_estimators=500,min_samples_leaf=2,max_features=.3,random_state=42,n_jobs=2)) if name=="trees" else make_pipeline(
                    SimpleImputer(strategy="median",keep_empty_features=True),StandardScaler(),Ridge(alpha=100))
                p=np.clip(model.fit(x,y[a]).predict(z),0,100)
                predictions[name][repeat,b]=p
                predictions["blend_"+name][repeat,b]=(p+predictions["current"][repeat,b])/2
            checkpoint=OUT/f"keller-repeat-{repeat}-fold-{fold}.npz"
            atomic_npz(checkpoint,ids=ids[b],y=y[b],source_train=source_train,source_held=source_held,
                **{n:p[repeat,b] for n,p in predictions.items()})
            write_json(checkpoint.with_suffix(".json"),{"train_ids":ids[a].tolist(),"held_ids":held.tolist(),
                "evaluate_ids":ids[b].tolist(),"targets":y[b].tolist(),"baseline_sha256":file_digest(path),
                "sha256":file_digest(checkpoint),"connectivity_disjoint":True,"source_fits":source_audit})
            print(f"repeat{repeat} fold{fold} complete",flush=True)
    if any(not np.isfinite(p).all() for p in predictions.values()):raise ValueError("Missing predictions")
    scores={n:[score(y,p) for p in values] for n,values in predictions.items()}
    passing=[]
    for name in names[1:]:
        gains=np.array([s["pearson"]-b["pearson"] for s,b in zip(scores[name],scores["current"])])
        if gains.mean()>=.01 and (gains>0).sum()>=2 and np.mean([s["mae"] for s in scores[name]])<=np.mean([s["mae"] for s in scores["current"]]):passing.append(name)
    selected=max(passing,key=lambda n:np.mean([s["pearson"] for s in scores[n]])) if passing else "current"
    atomic_npz(OUT/"keller-inner-oof.npz",ids=ids,y=y,**predictions)
    write_json(OUT/"results.json",{"status":"complete","host":platform.node(),"results":{"keller":{
        "selected":selected,"passing":passing,"scores":scores}},"main_validation_test_targets_scored":False,"reserved_targets_fitted_or_scored":False})
    summary={"selected":selected,"means":{
        n:{m:float(np.mean([s[m] for s in v])) for m in ("pearson","mae")}
        for n,v in scores.items()}}
    print(json.dumps(summary),flush=True)


if __name__=="__main__":
    with threadpool_limits(limits=2):main()
