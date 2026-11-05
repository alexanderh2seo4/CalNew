"""Predict with the verified threshold bundle on authorized SSH compute."""
import os
import argparse
import json
import platform
from threadpoolctl import threadpool_limits
from calnew.pipeline.threshold_direction import predict_threshold

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run",default="runs/nose-threshold-direction-serving-20261028-v1")
    parser.add_argument("--smiles",nargs="+",required=True)
    args=parser.parse_args()
    if platform.node().lower()!=os.environ.get("CALNEW_COMPUTE_HOST", "").lower():
        raise ValueError("Run inference on compute-host through scripts/ssh_compute.py")
    with threadpool_limits(limits=2):
        print(json.dumps(predict_threshold(args.run,args.smiles),indent=2))
