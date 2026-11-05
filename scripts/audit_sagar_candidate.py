"""Resolve Sagar identities and inspect allowed-source scales before any training."""
import os
from pathlib import Path
import json
import platform

import numpy as np
import pandas as pd
from scipy.io import loadmat
from rdkit import rdBase

from calnew.chemistry import identify
from calnew.io import file_digest,write_json
from calnew.pipeline.data import exclude_reserved
from nose_parity_progress import read_only_context
from nose_semantic_experiment import RESERVED

ROOT=Path("data/raw/sagar_2023/6c4169b7d92b063d9ce011afe8cb4790a4ffe8aa")
OUT=Path("runs/sagar-source-audit-20261028-v2")


def main():
    if platform.node().lower()!=os.environ.get("CALNEW_COMPUTE_HOST", "").lower():raise ValueError("SSH only")
    if OUT.exists():raise ValueError("Existing audit preserved")
    OUT.mkdir(parents=True)
    acquisition=json.loads((ROOT/"download.json").read_text())
    for item in acquisition["files"]:
        if file_digest(ROOT/item["path"])!=item["sha256"]:raise ValueError("Pinned source changed")
    ctx=read_only_context(Path(json.loads(Path("data/current.json").read_text())["snapshot"]))
    subjects={p.stem:loadmat(p,simplify_cells=True)["behav"] for p in ROOT.rglob("behav_ratings*.mat")}
    cids={int(cid) for subject in subjects.values() for cid in np.asarray(subject["cid"]).ravel()}
    candidates={cid:{} for cid in cids}
    identity_files={}
    with rdBase.BlockLogs():
        for path in Path("data/raw").glob("*/*/molecules.csv"):
            frame=pd.read_csv(path)
            cid_name=next((n for n in ("CID","cid","PubChem CID") if n in frame),None)
            smi_name=next((n for n in ("IsomericSMILES","CanonicalSMILES","SMILES","smiles") if n in frame),None)
            if cid_name is None or smi_name is None:continue
            identity_files[str(path)]=file_digest(path)
            numeric=pd.to_numeric(frame[cid_name],errors="coerce")
            for _,row in frame[numeric.isin(cids)].iterrows():
                try:mol=identify(row[smi_name])
                except ValueError:continue
                candidates[int(row[cid_name])][mol.molecule_id]={"molecule_id":mol.molecule_id,
                    "smiles":mol.smiles,"identity_source":str(path)}
    ambiguous={str(cid):list(values) for cid,values in candidates.items() if len(values)>1}
    resolved=[{"cid":cid,**next(iter(values.values()))} for cid,values in candidates.items() if len(values)==1]
    if not resolved:raise ValueError("No resolved identity rows; copy pinned source identity CSVs before retrying")
    table=pd.DataFrame(resolved)
    allowed=exclude_reserved(table,ctx.data,RESERVED,ctx.all_molecules).reset_index(drop=True)
    # Reserved-group filtering happens before sensory target summaries/export.
    allowed_ids=set(allowed.cid)
    identities=allowed.set_index("cid")
    table.to_csv(OUT/"resolved-identities.csv",index=False)
    allowed.to_csv(OUT/"allowed-identities.csv",index=False)
    report={"host":platform.node(),"source_revision":acquisition["revision"],"candidate_cids":len(cids),
        "identity_files_sha256":identity_files,
        "resolved_unique_cids":len(table),"allowed_after_reserved_groups":len(allowed),
        "unresolved_cids":sorted(cid for cid,values in candidates.items() if not values),"ambiguous_cids":ambiguous,
        "subjects":{},"target_rows_from_reserved_molecules_summarized_or_exported":False,
        "endpoint_training_or_evaluation_performed":False,"training_admission":"Pending study-specific held-connectivity exclusions and protocol-scale assessment"}
    records=[]
    for name,subject in subjects.items():
        cid=np.asarray(subject["cid"]).astype(int).ravel()
        labels=[str(v).strip().lower() for v in np.asarray(subject["percepts"]).ravel()]
        if len(set(labels))!=len(labels):raise ValueError("Ambiguous descriptor names")
        rows=np.array([i for i,c in enumerate(cid) if c in allowed_ids])
        ratings=np.asarray(subject["ratings"])[rows].astype(float)
        if ratings.shape!=(len(rows),len(labels)):raise ValueError("Subject ratings/identity shape mismatch")
        selected={}
        for term in ("pleasantness","intensity"):
            if term not in labels:raise ValueError("Missing perceptual endpoint")
            values=ratings[:,labels.index(term)]
            finite=values[np.isfinite(values)]
            selected[term]={"finite":len(finite),"min":float(finite.min()),"max":float(finite.max())}
        report["subjects"][name]={"raw_rows":len(cid),"allowed_rows":len(rows),"percepts":labels,"allowed_endpoint_ranges":selected}
        for i,source_row in enumerate(rows):
            molecule=identities.loc[cid[source_row]]
            records.append({"subject":name,"cid":int(cid[source_row]),"molecule_id":molecule.molecule_id,
                "smiles":molecule.smiles,"pleasantness_source_scale":ratings[i,labels.index("pleasantness")],
                "intensity_source_scale":ratings[i,labels.index("intensity")]})
    pd.DataFrame(records).to_parquet(OUT/"allowed-observations.parquet",index=False)
    report["allowed_observations_sha256"]=file_digest(OUT/"allowed-observations.parquet")
    write_json(OUT/"report.json",report)
    print(json.dumps(report,indent=2),flush=True)


if __name__=="__main__":main()
