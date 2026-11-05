"""Inspect public source schemas on SSH, without printing sensory targets."""
import os
from pathlib import Path
import json
import platform

import pandas as pd
from scipy.io import loadmat,whosmat
from calnew.io import write_json


if __name__=="__main__":
    if platform.node().lower()!=os.environ.get("CALNEW_COMPUTE_HOST", "").lower():raise ValueError("SSH only")
    root=Path("data/raw/sagar_2023/6c4169b7d92b063d9ce011afe8cb4790a4ffe8aa")
    result={"host":platform.node(),"spreadsheet":{},"subjects":{}}
    for path in (root/"Data/Behavioral").glob("*.xlsx"):
        sheets=pd.read_excel(path,sheet_name=None)
        result["spreadsheet"][path.name]={name:{"shape":list(frame.shape),"columns":frame.columns.astype(str).tolist(),
            "identity_preview":frame.head(3).astype(str).to_dict("records") if path.name=="odor_names.xlsx" else None}
            for name,frame in sheets.items()}
    for path in root.rglob("behav_ratings*.mat"):
        saved=loadmat(path,simplify_cells=True)
        result["subjects"][path.name]={"mat_variables":whosmat(path),"fields":{}}
        for name,value in saved.items():
            if name.startswith("__"):continue
            if isinstance(value,dict):
                result["subjects"][path.name]["fields"][name]={k:{"type":type(v).__name__,
                    "shape":list(getattr(v,"shape",[])),
                    "labels":v.tolist() if (getattr(v,"dtype",None) is not None and v.dtype.kind in ("U","S")) else None}
                    for k,v in value.items()}
    write_json(root/"schema-inspection.json",result)
    print(json.dumps(result,indent=2,default=str))
