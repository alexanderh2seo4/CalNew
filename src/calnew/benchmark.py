"""Nested model selection; final holdout is accessible only through a separate audit.

Outer validation never trains base models OR organisers used to score that fold.
Inner out-of-fold predictions train each outer fold's organiser.
"""
from __future__ import annotations

import importlib.metadata
import itertools
import time
import shutil
from collections import Counter
from pathlib import Path

import joblib
import numpy as np

from .calibration import GroupConformal,ProbabilityCalibrator
from .chemistry import nearest_similarity
from .dataset import TaskDataset,load_task
from .ensemble import Organiser
from .io import digest,file_digest,read_json,write_json
from .metrics import evaluate,interval_metrics,paired_group_bootstrap,selective_error
from .models import make_model
from .splits import assert_disjoint,folds,freeze_split


def candidate_configs(base,trials,seed):
    base=dict(base)
    search=base.pop("search",{})
    keys=list(search)
    configurations=[{**base,**dict(zip(keys,values))} for values in itertools.product(*(search[k] for k in keys))]
    rng=np.random.default_rng(seed)
    rng.shuffle(configurations)
    return configurations[:trials]


def _score(y,p,task):
    score=evaluate(y,p,task)["primary"]
    if score is None:
        raise ValueError("No supported endpoint in this validation fold")
    return score if task=="classification" else -score


def _fit_predict(config,data,train,validation,cache):
    assert_disjoint(data,train,validation)
    model=make_model(config,data.task,cache)
    model.fit(data.subset(train))
    prediction=model.predict([data.smiles[i] for i in validation])
    if prediction.shape!=data.y[validation].shape or not np.isfinite(prediction).all():
        raise ValueError('Candidate produced incomplete/nonfinite predictions; it cannot receive a score on a selected subset')
    return model,prediction


def tune(base,data,groups,nfolds,trials,seed,cache):
    fold_list=folds(groups,nfolds,seed)
    results=[]
    best=None
    for config in candidate_configs(base,trials,seed):
        config["seed"]=seed
        p=np.full_like(data.y,np.nan)
        scores=[]
        for train,validation in fold_list:
            _,pp=_fit_predict(config,data,train,validation,cache)
            p[validation]=pp
            scores.append(_score(data.y[validation],pp,data.task))
        mean=float(np.mean(scores))
        result={"config":config,"fold_scores":scores,"mean_score":mean}
        results.append(result)
        if best is None or mean>best[0]:
            best=(mean,config,p)
    return best[1],best[2],results


def select_one_se(summary,complexity_order):
    if not summary:
        raise ValueError("No models completed evaluation")
    best=max(summary,key=lambda name:summary[name]["mean_score"])
    cutoff=summary[best]["mean_score"]-summary[best]["standard_error"]
    eligible=[name for name in complexity_order if name in summary and summary[name]["mean_score"]>=cutoff]
    return eligible[0],best,cutoff


def code_identity():
    root=Path(__file__).parent
    return digest({str(p.relative_to(root)):file_digest(p) for p in sorted(root.rglob("*.py"))})


def run_benchmark(snapshot: Path,endpoint: str,source: str,config: dict,out: Path,cache: Path) -> dict:
    out=Path(out)
    data=load_task(snapshot,endpoint,source)
    initial_signature=data.signature()
    out.mkdir(parents=True,exist_ok=True)
    identity={"snapshot":str(Path(snapshot).resolve()),"dataset_signature":initial_signature,"endpoint":endpoint,"source":source,
              "configuration":config,"code_identity":code_identity()}
    manifest_path=out/"run.json"
    if manifest_path.exists():
        if read_json(manifest_path)["identity"]!=identity:
            raise ValueError("Existing run has different data/code/configuration; choose a new run directory")
        if (out/"report.json").exists():
            return read_json(out/"report.json")
    packages={}
    for pkg in ("numpy","pandas","scipy","scikit-learn","rdkit","torch","xgboost","transformers","unimol-tools","chemprop"):
        try: packages[pkg]=importlib.metadata.version(pkg)
        except importlib.metadata.PackageNotFoundError: packages[pkg]=None
    write_json(manifest_path,{"identity":identity,"status":"running","packages":packages,"test_accessed":False})
    if not (out/'source-code').exists():
        shutil.copytree(Path(__file__).parent,out/'source-code',ignore=shutil.ignore_patterns('__pycache__'))
    split=freeze_split(data,out/"split.json",config.get("strategy","structural"),config.get("seed",42))
    dev_ix=np.array(split["partitions"]["development"])
    cal_ix=np.array(split["partitions"]["calibration"])
    if data.task=="classification":
        support=np.nansum(data.y[dev_ix],axis=0)
        negatives=np.sum(data.y[dev_ix]==0,axis=0)
        keep=(support>=config.get("minimum_positive_labels",20))&(negatives>=10)
        if not keep.any(): raise ValueError("No descriptors supported by development data")
        write_json(out/"label-selection.json",{"basis":"development_only","all_labels":data.labels,"kept_labels":[l for l,k in zip(data.labels,keep) if k]})
        data.y=data.y[:,keep]; data.lower=data.lower[:,keep]; data.upper=data.upper[:,keep]; data.censoring=data.censoring[:,keep]
        data.labels=[l for l,k in zip(data.labels,keep) if k]
    dev=data.subset(dev_ix); cal=data.subset(cal_ix)
    dev_groups=np.array(split["groups"])[dev_ix]
    outer=folds(dev_groups,config["outer_folds"],config.get("seed",42))
    candidates=[c for c in config["models"] if c.get("task",data.task)==data.task]
    oof={c["name"]:np.full_like(dev.y,np.nan) for c in candidates}
    organiser_oof={m:np.full_like(dev.y,np.nan) for m in config.get("organisers",["mean","stacking"])}
    scores={c["name"]:[] for c in candidates}
    organiser_scores={m:[] for m in organiser_oof}
    failures={}; best_configs={c["name"]:[] for c in candidates}
    expert_layout=None
    start=time.time()
    for fold_id,(train,validation) in enumerate(outer):
        fold_path=out/f"outer-{fold_id}"
        fold_path.mkdir(exist_ok=True)
        inner_predictions=[]; validation_predictions=[]; names=[]
        training=dev.subset(train)
        for base in candidates:
            name=base["name"]
            if name in failures: continue
            print(f"[{endpoint}] outer {fold_id+1}/{len(outer)}: {name}",flush=True)
            try:
                selected,inner_oof,trials=tune(base,training,dev_groups[train],config["inner_folds"],config["trials"],config.get("seed",42)+fold_id,cache)
                model,pred=_fit_predict(selected,dev,train,validation,cache)
                oof[name][validation]=pred
                scores[name].append(_score(dev.y[validation],pred,data.task))
                best_configs[name].append(selected)
                inner_predictions.append(inner_oof); validation_predictions.append(pred); names.append(name)
                np.savez_compressed(fold_path/f"{name}.npz",inner_oof=inner_oof,validation=pred,train_ids=training.ids.astype(str),validation_ids=dev.ids[validation].astype(str))
                write_json(fold_path/f"{name}.json",{"selected":selected,"trials":trials,"evaluation":evaluate(dev.y[validation],pred,data.task,data.labels)})
            except (ImportError,RuntimeError,ValueError,OSError) as exc:
                failures[name]={"type":type(exc).__name__,"reason":str(exc),"fold":fold_id}
                print(f"  unavailable: {name}: {exc}",flush=True)
                write_json(out/"failures.json",failures)
        if not names: raise RuntimeError("No candidate completed the outer fold")
        if expert_layout is None: expert_layout=names
        if names!=expert_layout:
            # A late failure changes the organiser's definition. Do not mix layouts across folds.
            organiser_scores={}; organiser_oof={}
        if organiser_oof:
            pin=np.stack(inner_predictions,axis=1); pout=np.stack(validation_predictions,axis=1)
            for method in organiser_oof:
                organiser=Organiser(method,data.task,config.get("seed",42)).fit(pin,training.y,row_ids=training.ids)
                pp=organiser.predict(pout)
                organiser_oof[method][validation]=pp
                organiser_scores[method].append(_score(dev.y[validation],pp,data.task))
    completed=[c["name"] for c in candidates if c["name"] not in failures and len(scores[c["name"]])==len(outer)]
    summary={}
    for name in completed:
        values=scores[name]
        summary[name]={"mean_score":float(np.mean(values)),"standard_error":float(np.std(values,ddof=1)/np.sqrt(len(values))),
                       "fold_scores":values,"evaluation":evaluate(dev.y,oof[name],data.task,data.labels)}
    if organiser_oof and completed==expert_layout:
        for method,values in organiser_scores.items():
            summary["organiser_"+method]={"mean_score":float(np.mean(values)),"standard_error":float(np.std(values,ddof=1)/np.sqrt(len(values))),
                                       "fold_scores":values,"evaluation":evaluate(dev.y,organiser_oof[method],data.task,data.labels)}
    order=completed+["organiser_"+m for m in config.get("organisers",[])]
    selected,best,cutoff=select_one_se(summary,order)
    final_models={}; final_configs={}
    for base in candidates:
        name=base["name"]
        if name not in completed: continue
        # Final tuning uses development only. Calibration/test never select hyperparameters.
        chosen,_,trials=tune(base,dev,dev_groups,config["inner_folds"],config["trials"],config.get("seed",42),cache)
        final_configs[name]=chosen
        final_models[name]=[]
        for seed in config.get("seeds",[42]):
            model=make_model({**chosen,"seed":seed},data.task,cache).fit(dev)
            final_models[name].append(model)
        write_json(out/f"final-{name}.json",{"configuration":chosen,"trials":trials})
    final_organiser=None
    if selected.startswith("organiser_"):
        final_organiser=Organiser(selected.removeprefix("organiser_"),data.task,config.get("seed",42)).fit(np.stack([oof[n] for n in completed],axis=1),dev.y,row_ids=dev.ids)
    bundle={"models":final_models,"organiser":final_organiser,"selected":selected,"expert_layout":completed,"task":data.task,
            "labels":data.labels,"endpoint":endpoint,"metadata":data.metadata,"training_smiles":dev.smiles,
            "training_groups":list(set(dev.groups)),"calibration_groups":list(set(cal.groups)),"run_id":digest(identity)}
    cal_prediction,cal_disagreement=predict_bundle(bundle,cal.smiles)
    if data.task=="classification":
        bundle["calibrator"]=ProbabilityCalibrator().fit(cal.y,cal_prediction,cal.groups)
    else:
        bundle["calibrator"]=GroupConformal().fit(cal.y,cal_prediction,cal.groups)
    joblib.dump(bundle,out/"model.joblib")
    arrays={"y":dev.y,"row_ids":dev.ids.astype(str),"groups":dev.groups.astype(str)}
    arrays.update({name:oof[name] for name in completed})
    arrays.update({"organiser_"+m:p for m,p in organiser_oof.items()})
    np.savez_compressed(out/"development-predictions.npz",**arrays)
    comparisons={}
    if len(completed)>1:
        for name in completed[1:]:
            comparisons[name]=paired_group_bootstrap(dev.y,oof[name],oof[completed[0]],dev.groups,data.task,config.get("bootstrap_repeats",100))
    report={"profile":config.get("profile","custom"),"endpoint":endpoint,"source":source,"rows":len(data.ids),"labels":data.labels,
            "development_rows":len(dev.ids),"calibration_rows":len(cal.ids),"reserved_test_rows":len(split["partitions"]["test"]),
            "status":"computational_pilot" if config.get("profile")=="pilot" else "retrospective_development_complete",
            "final_test_accessed":False,"prospective_validation":"not_performed", "selected":selected,"best_point_estimate":best,
            "selection_rule":"simplest candidate in declared order within one standard error of best outer-CV score",
            "one_se_cutoff":cutoff,"summary":summary,"failures":failures,"paired_comparisons_vs_first_control":comparisons,
            "runtime_seconds":time.time()-start,"data_caveats":data.metadata,
            "limitations":["No source-disjoint or prospective result is inferred from structural CV.","Abraham processed duplicates are already aggregated.","Pilot results do not establish the final architecture winner."]}
    write_json(out/"report.json",report)
    manifest=read_json(manifest_path); manifest["status"]="complete"; write_json(manifest_path,manifest)
    return report


def predict_bundle(bundle,smiles):
    estimates=[]
    seed_variances=[]
    for name in bundle["expert_layout"]:
        pp=np.stack([m.predict(smiles) for m in bundle["models"][name]],axis=1)
        estimates.append(np.mean(pp,axis=1)); seed_variances.append(np.var(pp,axis=1))
    experts=np.stack(estimates,axis=1)
    if bundle["organiser"] is not None:
        prediction=bundle["organiser"].predict(experts)
    else:
        prediction=estimates[bundle["expert_layout"].index(bundle["selected"])]
    disagreement=np.sqrt(np.var(experts,axis=1)+np.mean(np.stack(seed_variances,axis=1),axis=1))
    return prediction,disagreement


def audit_holdout(run: Path) -> dict:
    run=Path(run)
    if (run/"holdout.json").exists():
        return read_json(run/"holdout.json")
    manifest=read_json(run/"run.json")
    if manifest["identity"]["configuration"].get("profile")=="pilot":
        raise ValueError("Pilot runs reserve the final holdout. Run the full programme before final audit")
    if manifest.get("test_accessed"):
        raise ValueError("Test access was already recorded; inspect interrupted audit instead of rerunning")
    identity=manifest["identity"]
    data=load_task(Path(identity["snapshot"]),identity["endpoint"],identity["source"])
    bundle=joblib.load(run/"model.joblib")
    keep=[data.labels.index(l) for l in bundle["labels"]]
    data.y=data.y[:,keep]; data.lower=data.lower[:,keep]; data.upper=data.upper[:,keep]; data.censoring=data.censoring[:,keep]; data.labels=bundle["labels"]
    split=read_json(run/"split.json")
    test=data.subset(split["partitions"]["test"])
    if set(test.groups)&(set(bundle["training_groups"])|set(bundle["calibration_groups"])):
        raise ValueError("Holdout leakage detected")
    manifest["test_accessed"]=True; write_json(run/"run.json",manifest)
    p,disagreement=predict_bundle(bundle,test.smiles)
    cal=bundle["calibrator"]
    if data.task=="classification": p=cal.transform(p)
    result=evaluate(test.y,p,data.task,test.labels)
    if data.task=="regression":
        lo,hi=cal.interval(p); result["intervals"]=interval_metrics(test.y,lo,hi)
    result["nearest_training_similarity"]=nearest_similarity(test.smiles,bundle["training_smiles"]).tolist()
    result["selective_error"]=selective_error(test.y,p,disagreement,data.task)
    result["prospective_validation"]=False
    write_json(run/"holdout.json",result)
    np.savez_compressed(run/"holdout-predictions.npz",y=test.y,prediction=p,disagreement=disagreement,ids=test.ids.astype(str))
    return result
