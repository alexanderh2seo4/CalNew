"""Strong statistical controls with train-only preprocessing."""
from __future__ import annotations

import ctypes
import sys
from pathlib import Path

import numpy as np
from scipy.linalg import cho_factor, cho_solve
from scipy.optimize import minimize
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.preprocessing import StandardScaler

from ..features import FeatureCache
from .base import Model


def load_xgboost():
    if sys.platform == "darwin":
        import sklearn
        lib = Path(sklearn.__file__).parent / ".dylibs" / "libomp.dylib"
        if lib.exists():
            ctypes.CDLL(str(lib), mode=ctypes.RTLD_GLOBAL)
    import xgboost
    return xgboost


def tanimoto(a, b):
    dot = a @ b.T
    denominator = np.sum(a*a,axis=1)[:,None]+np.sum(b*b,axis=1)[None,:]-dot
    return np.divide(dot,denominator,out=np.zeros_like(dot),where=denominator>0)


class TanimotoGP:
    def fit(self,x,y):
        self.x = np.asarray(x,dtype=float)
        self.mean = float(np.mean(y))
        centered = y-self.mean
        k = tanimoto(self.x,self.x)
        def objective(v):
            cov = np.exp(v[0])*k+(np.exp(v[1])+1e-7)*np.eye(len(k))
            c = cho_factor(cov)
            return .5*centered@cho_solve(c,centered)+np.log(np.diag(c[0])).sum()+len(k)/2*np.log(2*np.pi)
        opt = minimize(objective,[0,-1],bounds=[(-8,8),(-10,5)],method="L-BFGS-B")
        self.amplitude,self.noise = np.exp(opt.x)
        self.factor=cho_factor(self.amplitude*k+(self.noise+1e-7)*np.eye(len(k)))
        self.alpha=cho_solve(self.factor,centered)
        return self

    def predict(self,x,return_std=False):
        k=self.amplitude*tanimoto(np.asarray(x,dtype=float),self.x)
        mean=k@self.alpha+self.mean
        if not return_std:
            return mean
        var=np.maximum(self.amplitude+self.noise-np.sum(k*cho_solve(self.factor,k.T).T,axis=1),1e-9)
        return mean,np.sqrt(var)


class ClassicalModel(Model):
    def __init__(self,config,task,cache_root):
        self.config,self.task = dict(config),task
        self.cache=FeatureCache(cache_root)

    def embed(self,molecules):
        return self.cache.get(molecules,self.config.get("features","morgan"),self.config.get("radius",2),self.config.get("size",2048))

    def fit(self,dataset,split=None,configuration=None):
        if split is not None:
            dataset=dataset.subset(split)
        if configuration:
            self.config.update(configuration)
        if np.any(dataset.censoring != "exact"):
            raise ValueError("Classical point estimators cannot silently replace censored outcomes; use censored_mlp or an explicitly exact-only benchmark")
        self.labels=dataset.labels
        self.training_ids=dataset.ids.tolist()
        self.training_groups=set(dataset.groups)
        x=self.embed(dataset.smiles)
        self.imputer=SimpleImputer(add_indicator=True,keep_empty_features=True)
        x=self.imputer.fit_transform(x)
        self.scaler=None
        kind=self.config.get("estimator","ridge")
        if kind in ("ridge","linear"):
            self.scaler=StandardScaler()
            x=self.scaler.fit_transform(x)
        self.models=[]
        y=dataset.y
        seed=self.config.get("seed",42)
        self.joint=False
        if kind=="rf" and np.isfinite(y).all():
            cls=RandomForestClassifier if self.task=="classification" else RandomForestRegressor
            self.joint_model=cls(n_estimators=self.config.get("n_estimators",200),min_samples_leaf=self.config.get("min_samples_leaf",2),
                                max_features=self.config.get("max_features","sqrt"),max_depth=self.config.get("max_depth"),random_state=seed,n_jobs=self.config.get("n_jobs",4))
            self.joint_model.fit(x,y.ravel() if y.shape[1]==1 else y)
            self.joint=True
            return self
        for j in range(y.shape[1]):
            mask=np.isfinite(y[:,j])
            yy=y[mask,j]
            if not len(yy):
                self.models.append(float("nan")); continue
            if len(np.unique(yy))==1:
                self.models.append(float(yy[0])); continue
            if kind in ("ridge","linear"):
                model=LogisticRegression(C=self.config.get("C",1.0),max_iter=1500,solver="liblinear",random_state=seed) if self.task=="classification" else Ridge(alpha=self.config.get("alpha",10.0))
            elif kind=="nearest":
                cls=KNeighborsClassifier if self.task=="classification" else KNeighborsRegressor
                model=cls(n_neighbors=min(self.config.get("neighbors",5),len(yy)),weights="distance")
            elif kind=="xgb":
                xgb=load_xgboost()
                cls=xgb.XGBClassifier if self.task=="classification" else xgb.XGBRegressor
                model=cls(n_estimators=self.config.get("n_estimators",150),max_depth=self.config.get("max_depth",4),
                          learning_rate=self.config.get("learning_rate",.05),subsample=.9,colsample_bytree=.8,
                          n_jobs=self.config.get("n_jobs",4),random_state=seed,tree_method="hist")
            elif kind=="gp":
                if self.task!="regression" or self.config.get("features","morgan")!="morgan":
                    raise ValueError("Tanimoto GP requires regression and nonnegative fingerprints")
                model=TanimotoGP()
            elif kind=="rf":
                cls=RandomForestClassifier if self.task=="classification" else RandomForestRegressor
                model=cls(n_estimators=self.config.get("n_estimators",200),min_samples_leaf=2,n_jobs=4,random_state=seed)
            else:
                raise ValueError(f"Unknown estimator {kind}")
            model.fit(x[mask],yy)
            self.models.append(model)
        return self

    def predict(self,molecules,context=None):
        x=self.imputer.transform(self.embed(molecules))
        if self.scaler is not None:
            x=self.scaler.transform(x)
        if self.joint:
            if self.task=="regression":
                return self.joint_model.predict(x).reshape(len(x),-1)
            probabilities=self.joint_model.predict_proba(x)
            classes=self.joint_model.classes_
            if not isinstance(probabilities,list):
                probabilities,classes=[probabilities],[classes]
            return np.column_stack([p[:,list(c).index(1)] if 1 in c else np.zeros(len(x)) for p,c in zip(probabilities,classes)])
        columns=[]
        for model in self.models:
            if isinstance(model,float):
                columns.append(np.full(len(x),model))
            elif self.task=="classification":
                columns.append(model.predict_proba(x)[:,1])
            else:
                columns.append(model.predict(x))
        return np.column_stack(columns)

