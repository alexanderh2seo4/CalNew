"""Apply a registered promotion rule to exactly aligned training-only predictions."""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.stats import pearsonr
from calnew.io import file_digest, write_json


def compare(baseline_path, candidate_path):
    with np.load(baseline_path,allow_pickle=False) as data:
        ids,y,v2 = data["ids"],data["y"],data["v2"]
    with np.load(candidate_path,allow_pickle=False) as data:
        if not np.array_equal(ids,data["ids"]) or not np.array_equal(y,data["y"]):
            raise ValueError("Training IDs/targets differ; cached baseline comparison is invalid")
        candidates = {name:data[name].copy() for name in data.files if name not in ("ids","y","structure","v2","v2_plus_semantic")}
    for name,prediction in list(candidates.items()):
        if prediction.shape != v2.shape or not np.isfinite(prediction).all():
            raise ValueError("Prediction repeats/shape/finiteness do not match baseline")
        candidates[f"v2_plus_{name}"] = (v2+prediction)/2
    reference = np.asarray([pearsonr(y,p).statistic for p in v2])
    result = {}
    for name,prediction in candidates.items():
        scores = np.asarray([pearsonr(y,p).statistic for p in prediction])
        delta = scores-reference
        result[name] = {"pearson":scores.tolist(),"mean":float(scores.mean()),
            "gain_vs_v2":delta.tolist(),"mean_gain":float(delta.mean()),
            "passes_registered_rule":bool(delta.mean()>=0.01 and (delta>0).sum()>=2)}
    return {"baseline_pearson":reference.tolist(),"baseline_mean":float(reference.mean()),
        "baseline_sha256":file_digest(baseline_path),"candidate_sha256":file_digest(candidate_path),
        "ids_and_targets_exactly_aligned":True,"candidates":result}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline",type=Path,default=Path("runs/nose-semantic-trees-inner-v2"))
    parser.add_argument("--candidate",type=Path,required=True)
    args = parser.parse_args()
    datasets = json.loads((args.candidate/"results.json").read_text())["results"]
    result = {name:compare(args.baseline/f"{name}-inner-oof.npz",args.candidate/f"{name}-inner-oof.npz") for name in datasets}
    write_json(args.candidate/"aligned-comparison.json",result)
    for name,task in result.items():
        print(name, "baseline", round(task["baseline_mean"],4))
        for candidate,scores in task["candidates"].items():
            print(candidate,round(scores["mean"],4),"promotable",scores["passes_registered_rule"])
