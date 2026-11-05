"""Verify frozen feature migration and the saved threshold model on SSH."""
import os
from pathlib import Path
import json
import platform
import tarfile

import joblib
import numpy as np
from threadpoolctl import threadpool_limits

from calnew.io import file_digest,write_json
from calnew.pipeline.threshold_direction import predict_threshold,predict_bundle
from nose_parity_progress import read_only_context

RUN=Path("runs/nose-threshold-direction-serving-20261028-v1")


def main():
    if platform.node().lower()!=os.environ.get("CALNEW_COMPUTE_HOST", "").lower():
        raise ValueError("Use authorized SSH host")
    archive=Path("calnew-unimol2-cache-20261028.tar.gz")
    copied=0
    with tarfile.open(archive) as package:
        for item in package:
            if not item.isfile():continue
            dest=Path(item.name)
            if (dest.is_absolute() or ".." in dest.parts or dest.parts[:3]!=("data","features","unimol2")
                    or dest.suffix not in (".json",".npy")):
                raise ValueError("Unexpected cache archive member")
            data=package.extractfile(item).read()
            if dest.exists():
                if dest.read_bytes()!=data:
                    raise ValueError("Existing frozen cache differs; preserve both copies for investigation")
            else:
                dest.parent.mkdir(parents=True,exist_ok=True)
                dest.write_bytes(data)
                copied+=1
    for meta in Path("data/features/unimol2").glob("*.json"):
        identity=json.loads(meta.read_text())
        if "feature_sha256" in identity and file_digest(meta.with_suffix(".npy"))!=identity["feature_sha256"]:
            raise ValueError("Migrated per-molecule feature checksum differs")
    ctx=read_only_context(Path(json.loads(Path("data/current.json").read_text())["snapshot"]))
    bundle=joblib.load(RUN/"threshold-transfer.joblib")
    rows=ctx.rows(ctx.thr.molecule_id.to_numpy()[:3])
    blocks={n:ctx.B[n][rows] for n in bundle["feature_blocks"]}
    expected=predict_bundle(bundle,blocks)[2]
    reloaded=predict_bundle(joblib.load(RUN/"threshold-transfer.joblib"),blocks)[2]
    if not np.allclose(expected,reloaded,rtol=1e-10,atol=1e-10):
        raise ValueError("Serialization prediction parity failed")
    smoke=predict_threshold(RUN,ctx.thr.smiles.tolist()[:3])
    actual=np.array([3-r["log10_ppbv"] for r in smoke["molecules"]])
    if not np.allclose(expected,actual,rtol=1e-8,atol=1e-8):
        raise ValueError("Public serving and training feature matrices disagree")
    write_json(RUN/"smoke.json",{"host":platform.node(),"status":"verified",
        "migrated_cache_files":copied,"cache_archive_sha256":file_digest(archive),
        "per_molecule_cache_checksums_verified":True,
        "serialization_parity_max_error":float(np.max(np.abs(expected-reloaded))),
        "public_api_feature_parity_max_error":float(np.max(np.abs(expected-actual))),"prediction":smoke})
    print(json.dumps({"status":"saved_model_and_public_API_verified","run":str(RUN)}),flush=True)


if __name__=="__main__":
    with threadpool_limits(limits=2):
        main()
