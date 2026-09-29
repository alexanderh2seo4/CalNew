"""Endpoint-specific organisers trained exclusively from held-out predictions."""
from __future__ import annotations

import numpy as np
from scipy.special import logit
from sklearn.linear_model import LogisticRegression,Ridge
from sklearn.preprocessing import StandardScaler


class Organiser:
    def __init__(self,method="stacking",task="regression",seed=42):
        if method not in ("mean","stacking","gating"):
            raise ValueError("Unknown organiser method")
        self.method,self.task,self.seed=method,task,seed

    def fit(self,predictions,y,*,row_ids,training_ids_by_prediction=None):
        """predictions: rows x experts x targets. Caller supplies and audits fold lineage."""
        p=np.asarray(predictions,dtype=float)
        if p.ndim!=3 or p.shape[0]!=len(y) or p.shape[2]!=y.shape[1]:
            raise ValueError("Expected rows x experts x targets")
        if training_ids_by_prediction is not None:
            for rid,training in zip(row_ids,training_ids_by_prediction):
                if rid in training:
                    raise ValueError("In-sample prediction cannot train the organiser")
        self.fit_row_ids=list(row_ids)
        self.experts=p.shape[1]; self.targets=p.shape[2]
        self.models=[]; self.scalers=[]
        self.fill=np.nanmean(p,axis=0)
        self.fill=np.nan_to_num(self.fill,nan=.5 if self.task=="classification" else 0)
        if self.method=="mean":
            return self
        if self.method=="gating":
            return self._fit_gate(p,y)
        for j in range(self.targets):
            x=self._features(p,j)
            mask=np.isfinite(y[:,j]) & np.isfinite(p[:,:,j]).any(axis=1)
            scaler=StandardScaler().fit(x[mask] if mask.any() else np.zeros((1,x.shape[1])))
            self.scalers.append(scaler)
            yy=y[mask,j]
            if len(np.unique(yy))<2:
                self.models.append(float(yy[0]) if len(yy) else float("nan")); continue
            model=LogisticRegression(C=.1,max_iter=1000) if self.task=="classification" else Ridge(alpha=10)
            model.fit(scaler.transform(x[mask]),yy)
            self.models.append(model)
        return self

    def _features(self,p,j):
        missing=~np.isfinite(p[:,:,j])
        x=np.where(missing,self.fill[:,j],p[:,:,j])
        if self.task=="classification":
            x=logit(np.clip(x,1e-5,1-1e-5))
        return np.concatenate([x,missing.astype(float)],axis=1)

    def _fit_gate(self,p,y):
        import torch
        from torch import nn
        torch.manual_seed(self.seed)
        self.gates=nn.ModuleList([nn.Sequential(nn.Linear(self.experts*2,16),nn.Tanh(),nn.Linear(16,self.experts)) for _ in range(self.targets)])
        optimiser=torch.optim.AdamW(self.gates.parameters(),lr=.01,weight_decay=.05)
        xx=[torch.tensor(self._features(p,j),dtype=torch.float32) for j in range(self.targets)]
        pp=torch.tensor(np.nan_to_num(p),dtype=torch.float32)
        present=torch.tensor(np.isfinite(p))
        truth=torch.tensor(y,dtype=torch.float32)
        for _ in range(150):
            total=0
            for j,gate in enumerate(self.gates):
                valid=torch.isfinite(truth[:,j]) & present[:,:,j].any(dim=1)
                if not valid.any():
                    continue
                logits=gate(xx[j][valid]).masked_fill(~present[valid,:,j],-1e9)
                weights=torch.softmax(logits,dim=1)
                estimate=(weights*pp[valid,:,j]).sum(dim=1)
                loss=nn.functional.binary_cross_entropy(estimate.clamp(1e-6,1-1e-6),truth[valid,j]) if self.task=="classification" else nn.functional.mse_loss(estimate,truth[valid,j])
                total=total+loss+.01*(weights*torch.log(weights.clamp(min=1e-8))).sum(dim=1).mean()
            optimiser.zero_grad(); total.backward(); optimiser.step()
        self.gates.eval()
        return self

    def predict(self,predictions):
        p=np.asarray(predictions,dtype=float)
        if p.shape[1:]!=(self.experts,self.targets):
            raise ValueError("Expert layout changed")
        if self.method=="mean":
            count=np.isfinite(p).sum(axis=1)
            return np.divide(np.nansum(p,axis=1),count,out=np.full((len(p),self.targets),np.nan),where=count>0)
        result=[]
        for j in range(self.targets):
            x=self._features(p,j)
            if self.method=="gating":
                import torch
                with torch.no_grad():
                    present=torch.tensor(np.isfinite(p[:,:,j]))
                    logits=self.gates[j](torch.tensor(x,dtype=torch.float32)).masked_fill(~present,-1e9)
                    pred=(torch.softmax(logits,dim=1)*torch.tensor(np.nan_to_num(p[:,:,j]),dtype=torch.float32)).sum(dim=1).numpy()
            else:
                model=self.models[j]
                xx=self.scalers[j].transform(x)
                if isinstance(model,float):
                    pred=np.full(len(p),model)
                else:
                    pred=model.predict_proba(xx)[:,1] if self.task=="classification" else model.predict(xx)
            pred[~np.isfinite(p[:,:,j]).any(axis=1)]=np.nan
            result.append(pred)
        return np.column_stack(result)
