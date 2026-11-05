"""Evaluate independent Abraham physical descriptors inside development training only.

E/S/A/B/L/V are physical solute properties, not odor thresholds. Read only those
columns from the registered source. No assay/source indicator or ODT is loaded.
This is a property-assisted experiment, not a structure-only NOSE reproduction.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from scipy.stats import pearsonr
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.model_selection import KFold
from threadpoolctl import threadpool_limits

from calnew.chemistry import identify
from calnew.io import file_digest, write_json
from calnew.pipeline.paper_benchmark import Context, FRACTIONS, random_split
from calnew.pipeline.stages import GroupedRidge

PROPERTIES = ("E", "S", "A", "B", "L", "V")
RESERVED = [Path("runs/basic-threshold-models"), Path("runs/basic-descriptor-models")]


def property_table():
    folder = Path("data/raw/abraham_2012/8054ea98ed675005ec10e67359902f500e4911b0")
    properties = pd.read_csv(folder / "behavior.csv", usecols=["Stimulus", *PROPERTIES]).set_index("Stimulus")
    molecules = pd.read_csv(folder / "molecules.csv", usecols=["CID", "IsomericSMILES"])
    rows = []
    for cid, smiles in molecules.itertuples(index=False, name=None):
        try:
            identity = identify(smiles)
        except ValueError:
            continue
        if cid in properties.index:
            rows.append((identity.molecule_id.split("-")[0], *properties.loc[cid].to_numpy(float)))
    return pd.DataFrame(rows, columns=["connectivity", *PROPERTIES]).groupby("connectivity").mean(), {
        "source": "Abraham et al. 2012, DOI 10.1093/chemse/bjr094",
        "property_columns": list(PROPERTIES), "odor_target_columns_loaded": False,
        "behavior_sha256": file_digest(folder / "behavior.csv"), "molecules_sha256": file_digest(folder / "molecules.csv")}


def run(args):
    out = Path(args.out)
    if (out / "results.json").exists():
        raise ValueError("Choose a new output directory")
    out.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(8)
    snapshot = Path(json.loads(Path("data/current.json").read_text())["snapshot"])
    ctx = Context(snapshot, RESERVED)
    table, source = property_table()
    physical = table.reindex([m.split("-")[0] for m in ctx.universe]).to_numpy(float)
    available = np.isfinite(physical).all(1)
    xphys = np.column_stack([physical, np.where(available, physical[:, 4] ** 2, np.nan), available])
    # Separate chemistry indicators remain calculable for previously unknown molecules.
    from calnew.pipeline.blocks import OSMOPHORES
    indicators = ctx.B["osmophore"][:, [list(OSMOPHORES).index(n) for n in ("thiol", "aldehyde", "carboxylic_acid", "unsaturated_ester")]]
    xphys = np.column_stack([xphys, indicators, ctx.B["chain"][:, :2]])
    results = {}
    for ds, frame, target in (("abraham", ctx.thr, "y"), ("keller", ctx.keller, "pleasantness")):
        train, _, _ = random_split(len(frame), FRACTIONS[ds], 42)
        ids, y = frame.molecule_id.to_numpy()[train], frame[target].to_numpy()[train]
        rows = ctx.rows(ids)
        base = np.column_stack([ctx.B[n][rows] for n in ("rdkit", "transport", "hbond", "osmophore", "chain", "fingerprint")])
        px = xphys[rows]
        if ds == "keller":
            base = np.column_stack([base, frame.x.to_numpy()[train]])
            px = np.column_stack([px, frame.x.to_numpy()[train]])
        predictions = {name: np.zeros((args.repeats, len(y))) for name in ("structure", "physical_ridge", "structure_physical", "equal_ensemble")}
        for rep in range(args.repeats):
            for a, b in KFold(5, shuffle=True, random_state=100 + rep).split(y):
                for name, features in (("structure", base), ("structure_physical", np.column_stack([base, px]))):
                    from sklearn.impute import SimpleImputer
                    imputer = SimpleImputer(keep_empty_features=True).fit(features[a])
                    model = ExtraTreesRegressor(n_estimators=500, max_features=0.3, min_samples_leaf=2, n_jobs=8, random_state=42)
                    predictions[name][rep, b] = model.fit(imputer.transform(features[a]), y[a]).predict(imputer.transform(features[b]))
                ridge = GroupedRidge().fit(px[a], y[a], ids[a], alphas=(0.001, 0.01, 0.1, 1.0, 10.0, 100.0))
                predictions["physical_ridge"][rep, b] = ridge.predict(px[b])
            predictions["equal_ensemble"][rep] = 0.5 * (predictions["structure"][rep] + predictions["physical_ridge"][rep])
            print(ds, rep, {name: round(float(pearsonr(y, p[rep]).statistic), 4) for name, p in predictions.items()}, flush=True)
        results[ds] = {"training_molecules": len(y), "physical_properties_available": int(available[rows].sum()),
            "inner_cv_pearson": {name: [float(pearsonr(y, p).statistic) for p in values] for name, values in predictions.items()}}
        np.savez_compressed(out / f"{ds}-oof.npz", y=y, ids=np.asarray(ids, dtype=str), **predictions)
    write_json(out / "results.json", {"source": source, "results": results, "reserved_holdouts_scored": False,
        "protocol": "Repeated five-fold inner CV in split-42 train only; additional measured physical inputs"})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--repeats", type=int, default=3)
    with threadpool_limits(limits=8):
        run(parser.parse_args())
