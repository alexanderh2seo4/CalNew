"""Training-only threshold check of nonlinear kernels and fixed v2 blends."""
import argparse
import json
import shutil
from pathlib import Path

import numpy as np
from scipy.stats import pearsonr
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.model_selection import GridSearchCV, KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR
from threadpoolctl import threadpool_limits

from calnew.io import file_digest, write_json
from calnew.models.classical import TanimotoGP
from calnew.pipeline.blocks import EXPLICIT_BLOCKS
from calnew.pipeline.paper_benchmark import Context, FRACTIONS, random_split
from nose_semantic_experiment import RESERVED, frozen_molecular_vectors


def run(args):
    out = Path(args.out)
    if (out/"results.json").exists():
        raise ValueError("Choose a new output directory")
    out.mkdir(parents=True,exist_ok=True)
    shutil.copy2(__file__,out/"source.py")
    write_json(out/"selection-plan.json",{"fold_seeds":[100,101,102],"baseline":"runs/nose-semantic-trees-inner-v2",
        "candidates":["explicit_svr","rdkit_svr","unimol1_svr","tanimoto_gp","equal v2 blends"],
        "promotion":"Mean Pearson gain >=0.01; positive gain in at least two repeats",
        "inner_tuning":"3-fold CV inside each training fold; C={1,10,100}, gamma={0.01,0.1,1} times scale",
        "test_based_selection":False,"reserved_holdouts_opened":False})
    snapshot=Path(json.loads(Path("data/current.json").read_text())["snapshot"])
    ctx=Context(snapshot,RESERVED)
    tr,_,_=random_split(len(ctx.thr),FRACTIONS["abraham"],42)
    ids=ctx.thr.molecule_id.to_numpy()[tr]
    y=ctx.thr.y.to_numpy()[tr]
    rows=ctx.rows(ids)
    molecular,manifest=frozen_molecular_vectors(Path("data/features/unimol1-research/vectors.npz"),ctx.smiles)
    features={"explicit_svr":np.column_stack([ctx.B[n][rows] for n in EXPLICIT_BLOCKS]),
        "rdkit_svr":ctx.B["rdkit"][rows],"unimol1_svr":molecular[rows],"tanimoto_gp":ctx.B["fingerprint"][rows]}
    predictions={name:np.zeros((3,len(y))) for name in features}
    for repeat in range(3):
        for fold,(a,b) in enumerate(KFold(5,shuffle=True,random_state=100+repeat).split(y)):
            for name,x in features.items():
                if name=="tanimoto_gp":
                    model=TanimotoGP().fit(x[a],y[a])
                else:
                    steps=[("imputer",SimpleImputer(keep_empty_features=True)),("scaler",StandardScaler())]
                    if name!="explicit_svr":
                        steps.append(("pca",PCA(n_components=25,svd_solver="full")))
                    steps.append(("svr",SVR(kernel="rbf",epsilon=0.1)))
                    dimensions=25 if name!="explicit_svr" else x.shape[1]
                    grid={"svr__C":[1.,10.,100.],"svr__gamma":[v/dimensions for v in (0.01,0.1,1.)]}
                    model=GridSearchCV(Pipeline(steps),grid,cv=KFold(3,shuffle=True,random_state=173),
                        scoring="neg_mean_squared_error",n_jobs=1).fit(x[a],y[a])
                predictions[name][repeat,b]=model.predict(x[b])
            print(f"repeat {repeat+1}/3 fold {fold+1}/5",flush=True)
        print({name:round(float(pearsonr(y,p[repeat]).statistic),4) for name,p in predictions.items()},flush=True)
    if not all(np.isfinite(p).all() for p in predictions.values()):
        raise ValueError("Non-finite kernel predictions")
    np.savez_compressed(out/"abraham-inner-oof.npz",ids=np.asarray(ids,dtype=str),y=y,**predictions)
    scores={name:[float(pearsonr(y,p).statistic) for p in predictions[name]] for name in predictions}
    write_json(out/"results.json",{"results":{"abraham":{"inner_cv_pearson":scores}},
        "molecular_vectors":manifest,"reserved_holdouts_opened":False,"source_sha256":file_digest(out/"source.py")})


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",required=True)
    args=parser.parse_args()
    with threadpool_limits(limits=2):
        run(args)
