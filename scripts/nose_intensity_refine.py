"""Select a further intensity change inside original split-42 training only.

Promotion compares against the already-improved head, requires +0.01 mean
Pearson in three repeated grouped CVs, and does not allow increased mean MAE.
No development validation/test target is scored by this script.
"""
import argparse
import json
import platform
import shutil
import time
from pathlib import Path

import numpy as np
import torch
from sklearn.linear_model import HuberRegressor, QuantileRegressor, Ridge
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR
from threadpoolctl import threadpool_limits

from calnew.io import file_digest, write_json
from calnew.pipeline.intensity import IntensityRecipe, MonotoneDoseTrees
from calnew.pipeline.paper_benchmark import Context, FRACTIONS, random_split
from calnew.pipeline.semantic import SEMANTIC_BASE
from nose_intensity_experiment import cached_meta, cached_semantic, load_transfer, metrics
from nose_ravia_dose_transfer import crossfit
from nose_semantic_experiment import RESERVED


def robust_head(name):
    model = {"huber": lambda: HuberRegressor(epsilon=1.35, alpha=.1, max_iter=2000),
        "median": lambda: QuantileRegressor(quantile=.5, alpha=.1, solver="highs"),
        "svr": lambda: SVR(C=30, epsilon=3, gamma="scale")}[name]()
    return make_pipeline(StandardScaler(), model)


def select(scores):
    base_r = np.array([p["pearson"] for p in scores["current"]])
    base_mae = np.mean([p["mae"] for p in scores["current"]])
    passing = []
    for name, values in scores.items():
        gain = np.array([p["pearson"] for p in values])-base_r
        if gain.mean() >= .01 and (gain > 0).sum() >= 2 and np.mean([p["mae"] for p in values]) <= base_mae:
            passing.append(name)
    selected = max(passing, key=lambda n: np.mean([p["pearson"] for p in scores[n]])) if passing else "current"
    return selected, passing


def run(args):
    out = Path(args.out)
    if (out/"results.json").exists():
        raise ValueError("Choose a fresh output directory")
    out.mkdir(parents=True, exist_ok=True)
    baseline_path = (Path("runs/nose-intensity-inner-v1/keller-inner-oof.npz") if args.dataset == "keller" else
        Path("runs/nose-intensity-ravia-dose-transfer-inner-v1/ssh-baseline-verification.npz"))
    source_hashes = {}
    for path in [Path(__file__), Path("scripts/nose_intensity_experiment.py"), Path("scripts/nose_ravia_dose_transfer.py")]+sorted(Path("src/calnew").rglob("*.py")):
        if path.name.startswith("."):
            continue
        dest = out/"source-code"/path.resolve().relative_to(Path.cwd())
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        source_hashes[str(path)] = file_digest(dest)
    write_json(out/"selection-plan.json", {"host": platform.node(), "dataset": args.dataset,
        "selection_data": "Original split-42 training only; connectivity GroupKFold(5), repeated with seeds 100,101,102",
        "comparison": "Already-improved current head; identical inner held assignments",
        "promotion": "Mean Pearson gain >=0.01, positive in >=2 repeats, mean MAE <= current head",
        "candidates": {"keller": ["equal Hill + quality/semantic monotone trees", "equal Hill + shallow quality/semantic monotone trees"],
            "ravia": ["equal baseline + Huber dose proxy", "equal baseline + median dose proxy", "equal baseline + nonlinear SVR dose proxy"]}[args.dataset],
        "parameters": {"keller": "400 trees; depth4/child2/lambda1 or depth2/child5/lambda10; same quality/direction/semantic inputs",
            "ravia": "Huber epsilon1.35 alpha.1; quantile.5 alpha.1; RBF SVR C30 epsilon3 gamma=scale; standardized three fixed-dose proxies"},
        "transfer_exclusions": "Every held connectivity; own training feature folds also excluded from source training",
        "baseline_sha256": file_digest(baseline_path), "test_based_model_selection": False,
        "reserved_holdouts_opened": False, "source_sha256": source_hashes})
    started = time.time()
    torch.set_num_threads(args.threads)
    ctx = Context(Path(json.loads(Path("data/current.json").read_text())["snapshot"]), RESERVED)
    frame = ctx.keller if args.dataset == "keller" else ctx.ravia
    tr, va, te = random_split(len(frame), FRACTIONS[args.dataset], 42)
    all_ids = frame.molecule_id.to_numpy()
    ids, fixed_held = all_ids[tr], all_ids[np.r_[va, te]]
    y = frame["intensity" if args.dataset == "keller" else "y"].to_numpy()[tr]
    with np.load(baseline_path, allow_pickle=False) as saved:
        if not np.array_equal(ids, saved["ids"]) or not np.array_equal(y, saved["y"]):
            raise ValueError("Frozen original training IDs/targets changed")
        frozen_baseline = saved["baseline"].copy()
        frozen_current = saved["blend_dose_semantic" if args.dataset == "keller" else "selected"].copy()
    predictions = {"current": np.zeros_like(frozen_current)}
    if args.dataset == "ravia":
        with np.load("runs/nose-intensity-ravia-dose-transfer-inner-v1/ravia-inner-oof.npz", allow_pickle=False) as saved:
            if not np.array_equal(ids, saved["ids"]):
                raise ValueError("Frozen proxy training IDs changed")
            frozen_proxy = saved["proxy_ridge"].copy()
        predictions["current"] = frozen_current
        ktr, _, _ = random_split(len(ctx.keller), FRACTIONS["keller"], 42)
        source_ids = ctx.keller.molecule_id.to_numpy()[ktr]
        for name in ("huber", "median", "svr"):
            predictions["blend_proxy_"+name] = np.zeros_like(frozen_current)
    else:
        transfer, _ = load_transfer(ctx, out, args.threads)
        for name in ("blend_dose_quality_semantic", "blend_dose_quality_semantic_shallow"):
            predictions[name] = np.zeros_like(frozen_current)
    groups = np.array([i.split("-")[0] for i in ids])
    audit = []
    for rep in range(3):
        for fold, (a, b) in enumerate(GroupKFold(5, shuffle=True, random_state=100+rep).split(ids, groups=groups)):
            held = np.r_[fixed_held, ids[b]]
            if args.dataset == "ravia":
                pa, pb, counts = crossfit(ctx, source_ids, ids[a], held, ids[b], args.threads)
                ridge = make_pipeline(StandardScaler(), Ridge(alpha=10)).fit(pa, y[a])
                old_proxy = np.clip(ridge.predict(pb), 0, 100)
                np.testing.assert_allclose(old_proxy, frozen_proxy[rep, b], rtol=1e-6, atol=1e-4,
                    err_msg="Fixed proxy recipe changed; do not compare incompatible baselines")
                for name in ("huber", "median", "svr"):
                    head = robust_head(name).fit(pa, y[a])
                    candidate = np.clip(head.predict(pb), 0, 100)
                    predictions["blend_proxy_"+name][rep, b] = (frozen_baseline[rep, b]+candidate)/2
                audit.append({"repeat": rep, "fold": fold, "source_molecules_per_fit": counts})
            else:
                blocks = cached_meta(ctx, ids[a], held)
                semantic, count = cached_semantic(ctx, transfer, ids[a], held, 300+rep*5+fold)
                blocks = {**blocks, "semantic": semantic}
                mask = np.isin(ctx.data.panel["molecule_ids"], ids[a])
                rows, dose, target = ctx.p_rows[mask], ctx.data.panel["x"][mask], ctx.data.panel["intensity"][mask]
                train = {n: v[rows] for n, v in blocks.items()}
                rb = ctx.rows(ids[b])
                test = {n: v[rb] for n, v in blocks.items()}
                x = ctx.keller.set_index("molecule_id").loc[ids[b], "x"].to_numpy()
                current = IntensityRecipe("keller", "blend_dose_semantic", ctx.cfg["potency_blocks"],
                    ctx.cfg["intensity"]["epochs"], threads=args.threads).fit(train, target, ctx.connectivity[rows], dose)
                values = current.predict_parts(test, x)
                predictions["current"][rep, b] = values["selected"]
                for shallow in (False, True):
                    name = "blend_dose_quality_semantic"+("_shallow" if shallow else "")
                    model = MonotoneDoseTrees((SEMANTIC_BASE+("quality", "direction", "semantic"),), threads=args.threads,
                        max_depth=2 if shallow else 4, min_child_weight=5 if shallow else 2, reg_lambda=10 if shallow else 1)
                    model.fit(train, dose, target)
                    predictions[name][rep, b] = (values["baseline"]+model.predict(test, x))/2
                audit.append({"repeat": rep, "fold": fold, "source_rows": count})
            print(f"{args.dataset} refinement repeat {rep+1}/3 fold {fold+1}/5", flush=True)
        print({n: metrics(y, p[rep]) for n, p in predictions.items()}, flush=True)
        np.savez_compressed(out/f"{args.dataset}-inner-oof.npz", ids=ids.astype(str), y=y, **predictions)
        write_json(out/"partial.json", {n: [metrics(y, p) for p in values[:rep+1]] for n, values in predictions.items()})
    scores = {n: [metrics(y, p) for p in values] for n, values in predictions.items()}
    selected, passing = select(scores)
    write_json(out/"results.json", {"results": {args.dataset: {"n": len(ids), "selected": selected,
        "passing": passing, "scores": scores}}, "host": platform.node(), "source_audit": audit,
        "seconds": round(time.time()-started), "reserved_holdouts_opened": False,
        "max_current_cv_difference_from_previous_artifact": float(np.max(np.abs(predictions["current"]-frozen_current)))})
    print(f"Selected {selected}; passing {passing}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=("keller", "ravia"), required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args()
    with threadpool_limits(limits=args.threads):
        run(args)
