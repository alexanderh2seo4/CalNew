"""Export an auditable, canonical, globally endpoint-disjoint NOSE corpus."""
import os
from pathlib import Path
import json
import platform
import shutil
import zipfile

import numpy as np
import pandas as pd
from scipy import sparse
from rdkit import rdBase

from calnew.chemistry import identify
from calnew.io import file_digest, write_json
from nose_parity_progress import read_only_context
from nose_semantic_experiment import SOURCE, SHA256, URL, load_corpus

OUT = Path("data/curated/nose-20261028-v1")


def run():
    if platform.node().lower() != os.environ.get("CALNEW_COMPUTE_HOST", "").lower():
        raise ValueError("Dataset analysis requires authorized SSH host")
    if OUT.exists():
        raise ValueError("Immutable dataset export already exists")
    OUT.mkdir(parents=True)
    ctx = read_only_context(Path(json.loads(Path("data/current.json").read_text())["snapshot"]))
    if file_digest(SOURCE) != SHA256:
        raise ValueError("Release checksum mismatch")
    raw = pd.read_csv(SOURCE)
    if raw.columns.tolist() != ["SMILES", "TARGET_Descriptor"] or raw.isna().any().any():
        raise ValueError("Unexpected release schema/missing values")
    terms = sorted(raw.TARGET_Descriptor.unique())
    if any(not isinstance(t,str) or not t.strip() for t in terms):
        raise ValueError("Blank descriptor")
    with rdBase.BlockLogs():
        molecules, labels = load_corpus(ctx, OUT)
        invalid=[]
        canonical={}
        for value in raw.SMILES.unique():
            try:
                canonical[value] = identify(value).molecule_id
            except ValueError as exc:
                invalid.append({"SMILES":value,"reason":str(exc)})
    source_ids = set(molecules.molecule_id)
    mapped = raw.assign(molecule_id=raw.SMILES.map(canonical))
    canonical_unique = mapped.dropna(subset=["molecule_id"]).drop_duplicates(["molecule_id","TARGET_Descriptor"])
    allowed = canonical_unique[canonical_unique.molecule_id.isin(source_ids)]
    if len(allowed) != labels.nnz:
        raise ValueError("Independent canonical pair reconstruction differs")
    forbidden = {str(m).split("-")[0] for frame in (ctx.thr,ctx.keller,ctx.ravia) for m in frame.molecule_id}
    keep = ~molecules.molecule_id.str.split("-").str[0].isin(forbidden).to_numpy()
    safe_molecules = molecules.loc[keep].reset_index(drop=True)
    safe_labels = labels[keep].tocsr()
    safe_labels.sum_duplicates()
    safe_labels.eliminate_zeros()
    if set(safe_molecules.molecule_id.str.split("-").str[0]) & forbidden or not np.all(safe_labels.data==1):
        raise ValueError("Endpoint overlap or duplicate weights survived")
    coo = safe_labels.tocoo()
    pairs = pd.DataFrame({"molecule_id":safe_molecules.molecule_id.to_numpy()[coo.row],
        "descriptor":np.asarray(terms)[coo.col]})
    if pairs.duplicated().any() or pairs.isna().any().any():
        raise ValueError("Invalid exported associations")
    safe_molecules.to_parquet(OUT/"molecules.parquet",index=False)
    pairs.to_parquet(OUT/"associations.parquet",index=False)
    pd.DataFrame({"term_id":range(len(terms)),"descriptor":terms,
        "source_molecule_frequency":np.asarray(safe_labels.sum(axis=0)).ravel().astype(int)}).to_csv(OUT/"vocabulary.csv",index=False)
    pd.DataFrame(invalid,columns=["SMILES","reason"]).to_csv(OUT/"quarantine.csv",index=False)
    sparse.save_npz(OUT/"binary-associations.npz",safe_labels)
    pd.DataFrame({"connectivity_id":sorted(forbidden)}).to_csv(OUT/"excluded-development-connectivities.csv",index=False)
    if not pd.read_parquet(OUT/"associations.parquet").equals(pairs):
        raise ValueError("Parquet round trip failed")
    if (sparse.load_npz(OUT/"binary-associations.npz") != safe_labels).nnz:
        raise ValueError("Sparse round trip failed")
    manifest={"version":"20261028-v1","host":platform.node(),"source_url":URL,"source_sha256":SHA256,
        "raw_rows":len(raw),"raw_unique_pairs":len(raw.drop_duplicates()),
        "duplicate_raw_rows_removed":int(raw.duplicated().sum()),"raw_smiles":int(raw.SMILES.nunique()),
        "invalid_or_disconnected_smiles_quarantined":len(invalid),"valid_unique_molecules":len(set(canonical.values())),
        "canonical_unique_pairs_before_exclusions":len(canonical_unique),
        "reserved_filtered_molecules":len(molecules),"reserved_filtered_pairs":int(labels.nnz),
        "additional_development_connectivities_excluded":len(forbidden),
        "export_molecules":len(safe_molecules),"export_pairs":len(pairs),"vocabulary":len(terms),
        "rdkit":rdBase.rdkitVersion,"code_sha256":file_digest(Path(__file__)),
        "endpoint_connectivity_overlap":[],"reserved_targets_fitted_or_scored":False,
        "labels":"Unweighted binary LLM-augmented associations; strong/weak positive provenance unavailable; not measured sensory responses",
        "rights":"Research compilation; repository MIT does not replace upstream third-party data terms",
        "checks":{"independent_canonical_pair_count_matches":True,"unique_pairs":True,"binary_weights":True,
            "endpoint_connectivity_disjoint":True,"parquet_roundtrip":True,"sparse_roundtrip":True},
        "files":{p.name:file_digest(p) for p in OUT.iterdir() if p.is_file()}}
    write_json(OUT/"manifest.json",manifest)
    (OUT/"README.md").write_text("# Curated NOSE training associations\n\n"
        "The release is preserved under data/raw/nose/v1.0.0. This export canonicalizes molecules, removes repeated pairs, "
        "quarantines invalid/disconnected structures, excludes all existing reserved molecular groups, and additionally "
        "excludes every Abraham, Keller and Ravia development connectivity. Stereochemical IDs are preserved.\n\n"
        "associations.parquet joins molecules.parquet on molecule_id. binary-associations.npz uses molecules.parquet row "
        "order and vocabulary.csv term_id columns. Labels remain augmented associations with unknown strong/weak origin. "
        "Do not treat them as measured intensity, negative labels or independently validated sensory observations. "
        "The additional development exclusion creates a conservative transfer corpus; more exclusions may be needed for new endpoints.\n\n"
        "See manifest.json for counts, source checksum and all verification checks. Underlying source rights still apply.\n",encoding="utf-8")
    shutil.copy2(__file__,OUT/Path(__file__).name)
    bundle=OUT.with_suffix(".zip")
    with zipfile.ZipFile(bundle,"w",compression=zipfile.ZIP_DEFLATED) as archive:
        for p in OUT.iterdir():
            archive.write(p,arcname=OUT.name+"/"+p.name)
    print(json.dumps(manifest,indent=2),flush=True)


if __name__=="__main__":
    run()
