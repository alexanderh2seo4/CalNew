"""Serve the frozen, development-evaluated descriptor direction threshold blend."""
from pathlib import Path
import json

import joblib
import numpy as np

from ..chemistry import identify
from ..io import file_digest
from .blocks import BlockCache
from .semantic import SEMANTIC_BASE
from .stages import quality_features, stack


def source_direction(values):
    values=np.asarray(values,dtype=np.float64)
    if values.ndim!=2 or values.shape[1]!=128 or not np.isfinite(values).all():
        raise ValueError("Expected finite 128-dimensional source vectors")
    norm=np.linalg.norm(values,axis=1)
    return np.column_stack([values/np.maximum(norm[:,None],1e-12),norm])


def predict_bundle(bundle,blocks):
    q,_,d=bundle["quality"].predict({n:blocks[n] for n in bundle["quality_blocks"]})
    enriched={**blocks,"quality":quality_features(q),"direction":d}
    fusion=bundle["threshold"].predict({n:enriched[n] for n in bundle["potency_blocks"]})["ensemble"]
    pick={n:enriched[n] for _,names in bundle["members"].members for n in names}
    baseline=np.column_stack([fusion,bundle["members"].predict_members(pick)]).mean(1)
    source_input=np.column_stack([blocks["rdkit"],blocks["fingerprint"]])
    scaler,model,_=bundle["source"]
    semantic=model.predict(scaler.transform({"x":source_input})["x"]).astype(np.float32)
    inputs=np.column_stack([stack(blocks,SEMANTIC_BASE),source_direction(semantic)])
    inputs=np.where(np.isfinite(inputs),inputs,np.nan)
    branch=bundle["branch"].predict(bundle["imputer"].transform(inputs))
    return baseline,branch,(baseline+branch)/2


def predict_threshold(run,smiles,cache_root="data/features"):
    run=Path(run)
    manifest=json.loads((run/"serving.json").read_text())
    path=run/"threshold-transfer.joblib"
    if file_digest(path)!=manifest["artifact_sha256"]:
        raise ValueError("Trusted local model checksum mismatch")
    if not smiles:
        raise ValueError("At least one molecular SMILES is required")
    canonical=[identify(s).smiles for s in smiles]
    bundle=joblib.load(path)
    blocks=BlockCache(Path(cache_root)).blocks(bundle["feature_blocks"],canonical)
    baseline,branch,selected=predict_bundle(bundle,blocks)
    if not np.isfinite(selected).all():
        raise ValueError("Non-finite threshold predictions")
    return {"run":str(run),"endpoint":"air_detection_threshold",
        "model":"0.5 frozen current-v2 + 0.5 descriptor direction/confidence tree",
        "evaluation":"Ten original development splits; final reserved holdouts remain closed",
        "molecules":[{"smiles":s,"molecule_id":identify(s).molecule_id,
            "log10_ppbv":float(3-p),"ppbv":float(10**(3-p)),
            "baseline_log10_ppbv":float(3-a),"branch_log10_ppbv":float(3-b)}
            for s,p,a,b in zip(canonical,selected,baseline,branch)]}
