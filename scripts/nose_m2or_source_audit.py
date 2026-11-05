"""Curate a globally endpoint-disjoint human WT receptor screening source on SSH."""
import os
from pathlib import Path
import json
import platform

import numpy as np
import pandas as pd
from rdkit import rdBase

from calnew.chemistry import identify
from calnew.io import file_digest,write_json
from calnew.pipeline.data import exclude_reserved
from nose_parity_progress import read_only_context
from nose_semantic_experiment import RESERVED

ROOT=Path("data/raw/m2or/b5cf2f1714b28e591b07539559363d0a6205cf2a")
OUT=Path("data/curated/m2or-human-screening-20261028-v1")
UNITS={"m":1.,"mm":1e-3,"um":1e-6,"μm":1e-6,"µm":1e-6,"nm":1e-9,"pm":1e-12}


def main():
    if platform.node().lower()!=os.environ.get("CALNEW_COMPUTE_HOST", "").lower():raise ValueError("Use authorized SSH host")
    if OUT.exists():raise ValueError("Immutable source export already exists")
    OUT.mkdir(parents=True)
    acquisition=json.loads((ROOT/"download.json").read_text())
    for item in acquisition["files"]:
        if file_digest(ROOT/item["path"])!=item["sha256"]:raise ValueError("Pinned M2OR source differs")
    raw=pd.read_csv(ROOT/"M2OR_20230428.csv",sep=";",low_memory=False)
    metadata={col:raw[col].fillna("<missing>").astype(str).value_counts().head(20).to_dict()
        for col in ("species","Mutation","Parameter","Unit_Screen","Mixture","Type")}
    candidate=raw[(raw.species.str.lower()=="homo sapiens") & raw.Mutation.fillna("").str.strip().eq("")].copy()
    candidate=candidate[candidate.Mixture.isin(["mono","sum of isomers"])].copy()
    candidate["response"]=pd.to_numeric(candidate.Responsive,errors="coerce")
    dose=pd.to_numeric(candidate.Value_Screen,errors="coerce")
    multiplier=candidate.Unit_Screen.fillna("").str.strip().str.lower().map(UNITS)
    candidate["molar"]=dose*multiplier
    candidate=candidate[candidate.response.isin([0,1]) & candidate.molar.gt(0) & candidate.molar.le(1)].copy()
    candidate["log10_molar"]=np.log10(candidate.molar)
    candidate["declared_key"]=candidate["InChI Key"].fillna("").str.strip()
    # Resolve identities from existing pinned source graphs, never by odor labels.
    wanted=set(candidate.declared_key)
    identities={}
    with rdBase.BlockLogs():
        for path in sorted(Path("data/raw").glob("*/*/molecules.csv")):
            frame=pd.read_csv(path)
            column=next((n for n in ("IsomericSMILES","CanonicalSMILES","SMILES","smiles") if n in frame),None)
            if column is None:continue
            for smi in frame[column].dropna().unique():
                try:mol=identify(smi)
                except ValueError:continue
                if mol.molecule_id in wanted:
                    identities.setdefault(mol.molecule_id,{})[mol.smiles]=str(path)
        for row in candidate[["declared_key","canonicalSMILES"]].drop_duplicates().itertuples(index=False):
            if not isinstance(row.canonicalSMILES,str) or not row.canonicalSMILES.strip():continue
            try:mol=identify(row.canonicalSMILES)
            except ValueError:continue
            if not row.declared_key or row.declared_key==mol.molecule_id:
                identities.setdefault(mol.molecule_id,{})[mol.smiles]="M2OR canonicalSMILES"
    unique={key:next(iter(graphs)) for key,graphs in identities.items() if len(graphs)==1}
    candidate["smiles"]=candidate.declared_key.map(unique)
    candidate=candidate[candidate.smiles.notna()].copy()
    candidate["molecule_id"]=candidate.declared_key
    molecules=candidate[["molecule_id","smiles"]].drop_duplicates().sort_values("molecule_id")
    ctx=read_only_context(Path(json.loads(Path("data/current.json").read_text())["snapshot"]))
    allowed=exclude_reserved(molecules,ctx.data,RESERVED,ctx.all_molecules)
    forbidden={str(m).split("-")[0] for f in (ctx.thr,ctx.keller,ctx.ravia) for m in f.molecule_id}
    allowed=allowed[~allowed.molecule_id.str.split("-").str[0].isin(forbidden)].reset_index(drop=True)
    candidate=candidate[candidate.molecule_id.isin(allowed.molecule_id)].copy()
    candidate["receptor"]=candidate["Uniprot ID"].fillna("").str.strip()
    missing=candidate.receptor.eq("")
    candidate.loc[missing,"receptor"]=candidate.loc[missing,"Gene ID"].fillna("").str.upper().str.strip()
    candidate=candidate[candidate.receptor.ne("")].copy()
    for col in ("DOI","Type","Cell_line"):
        candidate[col]=candidate[col].fillna("").astype(str).str.strip()
    keys=["molecule_id","receptor","log10_molar","DOI","Type","Cell_line"]
    grouped=candidate.groupby(keys,dropna=False).response.agg(["min","max","size"]).reset_index()
    conflicts=grouped[grouped["min"]!=grouped["max"]].copy()
    clean=grouped[grouped["min"]==grouped["max"]].rename(columns={"min":"response","size":"raw_repeats"}).drop(columns="max")
    clean.response=clean.response.astype(int)
    # Unmeasured pairs stay absent; no dense negative labels are manufactured.
    clean.to_parquet(OUT/"observations.parquet",index=False)
    conflicts.to_parquet(OUT/"conflicting-conditions.parquet",index=False)
    allowed.to_parquet(OUT/"molecules.parquet",index=False)
    counts=clean.groupby("receptor").agg(observations=("response","size"),molecules=("molecule_id","nunique"),positives=("response","sum"))
    counts.to_csv(OUT/"receptor-counts.csv")
    report={"host":platform.node(),"revision":acquisition["revision"],"raw_rows":len(raw),
        "metadata_distributions":metadata,"identity_ambiguous_keys":sorted(k for k,v in identities.items() if len(v)>1),
        "human_WT_screening_molecules_resolved_before_exclusions":len(molecules),
        "globally_disjoint_source_molecules":len(allowed),"observations":len(clean),"receptors":len(counts),
        "positive_observations":int(clean.response.sum()),"negative_observations":int((clean.response==0).sum()),
        "quarantined_conflicting_conditions":len(conflicts),"candidate_rows_after_exclusions":len(candidate),
        "receptors_with_20_molecules":int((counts.molecules>=20).sum()),
        "molar_range":[float(candidate.molar.min()),float(candidate.molar.max())] if len(candidate) else None,
        "source_primary_connectivity_overlap":sorted(set(allowed.molecule_id.str.split("-").str[0])&forbidden),
        "reserved_targets_fitted_or_scored":False,"source_semantics":"Observed author-binarized agonism at stated assay screening dose; heterogeneous assay settings retained",
        "missing_pairs":"Not measured, never negative","rights":"Pinned repository Apache-2.0; original references and experimental provenance retained",
        "files":{p.name:file_digest(p) for p in OUT.iterdir() if p.is_file()}}
    if report["source_primary_connectivity_overlap"]:raise ValueError("Primary connectivity reached receptor source")
    write_json(OUT/"manifest.json",report)
    print(json.dumps({k:v for k,v in report.items() if k!="metadata_distributions"},indent=2),flush=True)


if __name__=="__main__":main()
