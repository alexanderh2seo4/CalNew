"""Fit and verify a usable bundle for the previously selected threshold recipe."""
import os
import json
from pathlib import Path
import platform
import shutil

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.impute import SimpleImputer
import torch
from threadpoolctl import threadpool_limits

from calnew.io import file_digest,write_json
from calnew.pipeline.auxiliary import exclude_touching
from calnew.pipeline.blocks import BlockCache
from calnew.pipeline.semantic import SEMANTIC_BASE
from calnew.pipeline.semantic_balanced import BalancedDescriptorTransfer
from calnew.pipeline.stages import QualityStage,THRESHOLD_MEMBERS,TabularEnsemble,ThresholdStage,stack
from calnew.pipeline.threshold_direction import source_direction,predict_threshold,predict_bundle
from nose_parity_progress import read_only_context
from nose_semantic_experiment import SOURCE,load_corpus
from nose_threshold_direction_benchmark import verify_selection,SOURCE_RUN
from nose_threshold_semantic_refine import cohort
from nose_threshold_semantic_direction_refine import load_pinned_source

OUT=Path("runs/nose-threshold-direction-serving-20261028-v1")
BENCH=Path("runs/nose-threshold-direction-original-v1")


def run():
    if platform.node().lower()!=os.environ.get("CALNEW_COMPUTE_HOST", "").lower():
        raise ValueError("All numerical work requires authorized SSH host")
    if OUT.exists():
        raise ValueError("Existing fit preserved")
    benchmark=json.loads((BENCH/"results.json").read_text())
    if (benchmark["status"]!="complete" or benchmark["test_based_selection"]
            or benchmark["paired"]["mean_pearson_gain"]<=0 or benchmark["paired"]["mean_mae_change"]>=0):
        raise ValueError("Frozen recipe lacks completed favorable paired evaluation")
    OUT.mkdir(parents=True)
    paths=[Path(__file__),Path("src/calnew/pipeline/threshold_direction.py")]
    write_json(OUT/"fit-plan.json",{"recipe":"Original frozen half-current/half-idf-unit-direction-ET",
        "source_recipe_unchanged":True,"benchmark_sha256":file_digest(BENCH/"results.json"),
        "final_training":"All eligible186 development molecules; existing reserved exclusions preserved",
        "source_fitting":"Same pinned7000 corpus; exclude ALL186 primary connectivities",
        "no_new_model_selection":True,"reserved_targets_fitted_or_scored":False,
        "code_sha256":{str(p):file_digest(p) for p in paths}})
    for p in paths:
        shutil.copy2(p,OUT/p.name)
    torch.set_num_threads(2)
    ctx=read_only_context(Path(json.loads(Path("data/current.json").read_text())["snapshot"]))
    all_ids,ids,held,y,tr,task_inputs,base=cohort(ctx)
    original,evidence=load_pinned_source(SOURCE_RUN,ctx,all_ids,ids,held,y,task_inputs,base)
    _,selection=verify_selection(ctx,all_ids,ids,held,y,tr,base,original,evidence)
    write_json(OUT/"frozen-selection-verified.json",selection)
    molecules,labels=load_corpus(ctx,OUT)
    terms=sorted(pd.read_csv(SOURCE,usecols=["TARGET_Descriptor"]).TARGET_Descriptor.unique())
    with np.load("data/features/nose-descriptor-minilm.npz",allow_pickle=False) as data:
        if data["terms"].tolist()!=terms:
            raise ValueError("Word vocabulary mismatch")
        words=data["vectors"].copy()
    source_blocks=BlockCache(Path("data/features")).blocks(("rdkit","fingerprint"),molecules.smiles.tolist())
    source_x=np.column_stack([source_blocks[n] for n in ("rdkit","fingerprint")])
    transfer=BalancedDescriptorTransfer(molecules,labels,source_x,words,threads=2)
    print("Fit identical globally disjoint descriptor source for serialization",flush=True)
    source=transfer.fit(all_ids,"idf_unit")
    source_predictions=transfer.predict(source,task_inputs)
    deviation=float(np.max(np.abs(source_predictions-original["idf_unit"])))
    if not np.allclose(source_predictions,original["idf_unit"],rtol=1e-6,atol=1e-7):
        raise ValueError("Serialized source recipe fails parity with evaluated source arrays")
    rows=ctx.rows(all_ids)
    target=ctx.thr.y.to_numpy()
    inputs=np.column_stack([base["trees"],source_direction(source_predictions)])
    imputer=SimpleImputer(strategy="median",keep_empty_features=True).fit(np.where(np.isfinite(inputs),inputs,np.nan))
    branch=ExtraTreesRegressor(n_estimators=500,min_samples_leaf=2,max_features=.3,random_state=42,n_jobs=2).fit(imputer.transform(inputs),target)
    print("Fit cross-fitted quality inputs for all186 endpoint training molecules",flush=True)
    q,d,_=ctx.stage_a_features(all_ids,[],42)
    enriched={**ctx.B,"quality":q,"direction":d}
    pick={n:enriched[n][rows] for _,names in THRESHOLD_MEMBERS for n in names}
    keep=exclude_touching(ctx.aux,[])
    auxiliary=({n:v[keep] for n,v in ctx.aux_blocks.items()},ctx.aux.y.to_numpy()[keep],1.)
    members=TabularEnsemble(THRESHOLD_MEMBERS,seed=42,threads=2).fit(pick,target,ctx.connectivity[rows],auxiliary=auxiliary)
    threshold=ThresholdStage(ctx.cfg["potency_blocks"],"fingerprint",seeds=tuple(range(420,425)),
        epochs=ctx.cfg["threshold"]["epochs"]).fit({n:enriched[n][rows] for n in ctx.cfg["potency_blocks"]},target,ctx.connectivity[rows])
    print("Fit final source quality model for new-molecule inference",flush=True)
    quality=QualityStage(ctx.cfg["quality_blocks"],"fingerprint",seeds=(42,),epochs=ctx.cfg["quality"]["epochs"]).fit(
        {n:ctx.B[n][ctx.a_rows] for n in ctx.cfg["quality_blocks"]},ctx.labels[ctx.a_rows],ctx.direction[ctx.a_rows])
    names=sorted(set(ctx.cfg["quality_blocks"]) | set(ctx.cfg["potency_blocks"])-{"quality"} | set(SEMANTIC_BASE) |
        {n for _,nn in THRESHOLD_MEMBERS for n in nn if n not in ("quality","direction")})
    bundle={"source":source,"imputer":imputer,"branch":branch,"quality":quality,
        "quality_blocks":ctx.cfg["quality_blocks"],"potency_blocks":ctx.cfg["potency_blocks"],
        "threshold":threshold,"members":members,"feature_blocks":names,"training_ids":all_ids,
        "source_parity_max_abs_error":deviation}
    path=OUT/"threshold-transfer.joblib"
    joblib.dump(bundle,path,compress=3)
    write_json(OUT/"serving.json",{"artifact_sha256":file_digest(path),"host":platform.node(),
        "endpoint":"air_detection_threshold","training_molecules":len(all_ids),"source_molecules":source[2]["source_rows"],
        "source_parity_max_abs_error":deviation,"source_held_connectivity_overlap":source[2]["held_connectivity_overlap"],
        "original_development_metrics":benchmark["metrics"],"paired":benchmark["paired"],
        "reserved_targets_fitted_or_scored":False,"NOSE_reference_reached":False,
        "uncertainty":"No calibrated prospective prediction interval is claimed"})
    examples=ctx.thr.smiles.tolist()[:3]
    smoke=predict_threshold(OUT,examples)
    reloaded=joblib.load(path)
    blocks={n:ctx.B[n][rows[:3]] for n in names}
    a=predict_bundle(bundle,blocks)[2]
    b=predict_bundle(reloaded,blocks)[2]
    if not np.allclose(a,b,rtol=1e-10,atol=1e-10):
        raise ValueError("Serialized prediction parity failed")
    write_json(OUT/"smoke.json",{"serialization_parity_max_error":float(np.max(np.abs(a-b))),"prediction":smoke})
    print(json.dumps({"status":"saved_and_smoke_verified","run":str(OUT),"source_parity_max_error":deviation}),flush=True)


if __name__=="__main__":
    with threadpool_limits(limits=2):
        run()
