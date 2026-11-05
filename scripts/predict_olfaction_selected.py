"""Serve CALNEW's selected threshold, Keller intensity and pleasantness heads."""
import os
import argparse
import json
from pathlib import Path
import platform

from threadpoolctl import threadpool_limits
from calnew.pipeline.run import predict
from calnew.pipeline.threshold_direction import predict_threshold


def predict_selected(smiles,dilution=1e-3):
    result=predict(Path("runs/modular-pipeline-fingerprint-v5"),smiles,dilution,
        semantic_run=Path("runs/nose-semantic-pleasantness-v3"),
        intensity_run=Path("runs/nose-intensity-keller-refit-v3"))
    thresholds=predict_threshold("runs/nose-threshold-direction-serving-20261028-v1",smiles)
    for record,new in zip(result["molecules"],thresholds["molecules"],strict=True):
        if record["molecule_id"]!=new["molecule_id"]:
            raise ValueError("Threshold and profile molecular identities differ")
        # Replace the full old threshold object: its old interval does not
        # calibrate the changed model and must not accompany the new estimate.
        record["threshold"]={key:new[key] for key in ("log10_ppbv","ppbv","baseline_log10_ppbv","branch_log10_ppbv")}
    result["threshold_model"]={"run":thresholds["run"],"recipe":thresholds["model"],
        "endpoint":thresholds["endpoint"],"uncertainty":"Not calibrated for this head"}
    return result


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smiles",nargs="+",required=True)
    parser.add_argument("--dilution",type=float,default=1e-3)
    parser.add_argument("--out",type=Path)
    args=parser.parse_args()
    if platform.node().lower()!=os.environ.get("CALNEW_COMPUTE_HOST", "").lower():
        raise ValueError("Run inference on compute-host using scripts/ssh_compute.py")
    with threadpool_limits(limits=2):
        result=predict_selected(args.smiles,args.dilution)
    output=json.dumps(result,indent=2)
    if args.out:
        if args.out.exists():raise ValueError("Existing prediction output preserved")
        args.out.write_text(output,encoding="utf-8")
    else:
        print(output)
