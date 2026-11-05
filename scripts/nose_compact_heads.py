"""Registered compact CatBoost heads on original training cohorts, SSH only.

No main validation/test scores, no source refits, and no reserved targets.
Existing paired baseline folds are independently checked before new fitting.
"""
import os
from pathlib import Path
import json
import platform
import shutil
import time

import numpy as np
from catboost import CatBoostRegressor
from sklearn.model_selection import GroupKFold
from threadpoolctl import threadpool_limits

from calnew.io import digest, file_digest, write_json
from calnew.pipeline.blocks import EXPLICIT_BLOCKS
from calnew.pipeline.paper_benchmark import FRACTIONS, random_split
from calnew.pipeline.semantic import SEMANTIC_BASE
from calnew.pipeline.stages import stack
from nose_parity_progress import read_only_context, inspect_run, dependency_versions
from nose_threshold_semantic_refine import atomic_npz, score

OUT = Path("runs/nose-compact-heads-inner-20261028-v1")
BASELINES = {"abraham": Path("runs/nose-parity-threshold-water-inner-v2"),
    "keller": Path("runs/nose-parity-pleasantness-grouped-inner-v2")}
RECIPES = {"compact_rmse": ("compact", "RMSE"),
    "compact_mae": ("compact", "MAE"), "full_rmse": ("full", "RMSE")}


def learner(loss):
    return CatBoostRegressor(iterations=700, depth=4, learning_rate=.03,
        l2_leaf_reg=10, loss_function=loss, random_seed=42, thread_count=2,
        verbose=False, allow_writing_files=False, task_type="CPU")


def run():
    if platform.node().lower() != os.environ.get("CALNEW_COMPUTE_HOST", "").lower():
        raise ValueError("Numerical work requires authorized SSH host")
    if OUT.exists():
        raise ValueError("Use a fresh immutable run; existing evidence preserved")
    OUT.mkdir(parents=True)
    plan = {"scope": "Original split42 training111/260 only", "host": platform.node(),
        "candidates": RECIPES, "model_parameters": learner("RMSE").get_params(),
        "features": {"compact": ["rdkit", *EXPLICIT_BLOCKS], "full": list(SEMANTIC_BASE)},
        "folds": "GroupKFold5 connectivity; repeats100/101/102",
        "gate": {"mean_pearson_gain_min": .01, "positive_repeats_min": 2, "no_mean_mae_increase": True},
        "blends": "Each standalone and fixed equal blend with frozen current comparator",
        "main_validation_test_targets_scored": False, "reserved_targets_fitted_or_scored": False,
        "source_fits": 0, "baseline_paths": {k: str(v) for k,v in BASELINES.items()},
        "code_sha256": file_digest(Path(__file__)), "dependencies": dependency_versions(),
        "catboost_version": __import__("catboost").__version__}
    write_json(OUT/"selection-plan.json", plan)
    shutil.copy2(__file__, OUT/Path(__file__).name)
    print("Plan frozen before fitting", flush=True)
    ctx = read_only_context(Path(json.loads(Path("data/current.json").read_text())["snapshot"]))
    results = {}
    for dataset, baseline in BASELINES.items():
        audit = inspect_run(ctx, baseline)
        if audit["datasets"][dataset]["status"] != "complete":
            raise ValueError("Incomplete baseline")
        write_json(OUT/f"{dataset}-baseline-audit.json", audit)
        frame = ctx.thr if dataset == "abraham" else ctx.keller
        tr, va, te = random_split(len(frame), FRACTIONS[dataset], 42)
        ids = frame.molecule_id.to_numpy(dtype=str)[tr]
        y = frame["y" if dataset == "abraham" else "pleasantness"].to_numpy()[tr]
        rows = ctx.rows(ids)
        groups = np.array([m.split("-")[0] for m in ids])
        blocks = {"compact": stack(ctx.B, ("rdkit", *EXPLICIT_BLOCKS))[rows],
            "full": stack(ctx.B, SEMANTIC_BASE)[rows]}
        if dataset == "keller":
            blocks = {k: np.column_stack([x, frame.x.to_numpy()[tr]]) for k,x in blocks.items()}
        blocks = {k: np.where(np.isfinite(x), np.clip(x, -1e6, 1e6), np.nan).astype(np.float32)
            for k,x in blocks.items()}
        write_json(OUT/f"{dataset}-resources.json", {"ids": ids.tolist(), "targets": y.tolist(),
            "features": {k: digest(x.tolist()) for k,x in blocks.items()},
            "baseline_plan_sha256": file_digest(baseline/"selection-plan.json")})
        names = ["current", *RECIPES, *("blend_"+n for n in RECIPES)]
        predictions = {n: np.full((3,len(ids)), np.nan) for n in names}
        started = time.time()
        for repeat in range(3):
            for fold,(a,b) in enumerate(GroupKFold(5,shuffle=True,random_state=100+repeat).split(ids,groups=groups)):
                if set(groups[a]) & set(groups[b]):
                    raise ValueError("Connectivity leakage")
                path = baseline/f"{dataset}-repeat-{repeat}-fold-{fold}.npz"
                record = json.loads(path.with_suffix(".json").read_text())
                identity = record["identity"]
                if (record["sha256"] != file_digest(path) or identity["train_ids"] != ids[a].tolist()
                        or identity["evaluate_ids"] != ids[b].tolist() or identity["targets"] != y[b].tolist()):
                    raise ValueError("Baseline alignment failed")
                with np.load(path,allow_pickle=False) as saved:
                    predictions["current"][repeat,b] = saved["current"]
                for name,(features,loss) in RECIPES.items():
                    model = learner(loss).fit(blocks[features][a],y[a])
                    p = model.predict(blocks[features][b])
                    if dataset == "keller":
                        p = np.clip(p,0,100)
                    predictions[name][repeat,b] = p
                    predictions["blend_"+name][repeat,b] = (p+predictions["current"][repeat,b])/2
                checkpoint = OUT/f"{dataset}-repeat-{repeat}-fold-{fold}.npz"
                atomic_npz(checkpoint,ids=ids[b],y=y[b],**{n:p[repeat,b] for n,p in predictions.items()})
                write_json(checkpoint.with_suffix(".json"), {"train_ids":ids[a].tolist(),
                    "evaluate_ids":ids[b].tolist(),"targets":y[b].tolist(),"baseline_sha256":file_digest(path),
                    "sha256":file_digest(checkpoint),"connectivity_disjoint":True})
                print(f"{dataset} repeat{repeat} fold{fold} complete ({time.time()-started:.0f}s)",flush=True)
        if any(not np.isfinite(p).all() for p in predictions.values()):
            raise ValueError("Missing predictions")
        scores = {n:[score(y,p) for p in values] for n,values in predictions.items()}
        passing=[]
        for name in names[1:]:
            gains=np.array([s["pearson"]-b["pearson"] for s,b in zip(scores[name],scores["current"])])
            if gains.mean() >= .01 and (gains>0).sum()>=2 and np.mean([s["mae"] for s in scores[name]])<=np.mean([s["mae"] for s in scores["current"]]):
                passing.append(name)
        selected=max(passing,key=lambda n:np.mean([s["pearson"] for s in scores[n]])) if passing else "current"
        results[dataset]={"scores":scores,"passing":passing,"selected":selected}
        atomic_npz(OUT/f"{dataset}-inner-oof.npz",ids=ids,y=y,**predictions)
        write_json(OUT/"results.json",{"status":"partial" if dataset=="abraham" else "complete",
            "results":results,"main_validation_test_targets_scored":False,"reserved_targets_fitted_or_scored":False})
        print(json.dumps({"dataset":dataset,"selected":selected,"means":{n:{m:float(np.mean([s[m] for s in v])) for m in ("pearson","mae")} for n,v in scores.items()}}),flush=True)


if __name__ == "__main__":
    with threadpool_limits(limits=2):
        run()
