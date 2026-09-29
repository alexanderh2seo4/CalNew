"""Portable stereo-aware directed MPNN and censored molecular MLP.

The native graph implementation is a CALNEW D-MPNN, not an OpenPOM reproduction.
Published models have separate adapters and identities.
"""
from __future__ import annotations

import copy
import random
from functools import lru_cache

import numpy as np
import torch
from rdkit import Chem
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from torch import nn

from ..features import FeatureCache
from ..losses import censored_normal_nll,masked_bce
from .base import Model


ATOM_DIM=20
BOND_DIM=9


@lru_cache(maxsize=30000)
def graph_features(smiles):
    mol=Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError("Invalid molecular graph")
    Chem.AssignStereochemistry(mol,cleanIt=True,force=True)
    atoms=[]
    elements=[1,6,7,8,9,15,16,17,35,53]
    for a in mol.GetAtoms():
        cip=a.GetProp('_CIPCode') if a.HasProp('_CIPCode') else ''
        atoms.append([float(a.GetAtomicNum()==z) for z in elements]+[
            a.GetAtomicNum()/100,a.GetDegree()/4,a.GetFormalCharge()/3,a.GetTotalNumHs()/4,float(a.GetIsAromatic()),
            float(a.IsInRing()),a.GetMass()/200,float(cip=='R'),float(cip=='S'),float(a.GetChiralTag()!=Chem.ChiralType.CHI_UNSPECIFIED)])
    src,dst,reverse,bonds=[],[],[],[]
    for b in mol.GetBonds():
        bf=[float(b.GetBondType()==t) for t in [Chem.BondType.SINGLE,Chem.BondType.DOUBLE,Chem.BondType.TRIPLE,Chem.BondType.AROMATIC]]
        bf += [float(b.GetIsConjugated()),float(b.IsInRing()),float(b.GetStereo()==Chem.BondStereo.STEREOE),float(b.GetStereo()==Chem.BondStereo.STEREOZ),float(b.GetStereo()==Chem.BondStereo.STEREOANY)]
        j=len(src)
        src += [b.GetBeginAtomIdx(),b.GetEndAtomIdx()]
        dst += [b.GetEndAtomIdx(),b.GetBeginAtomIdx()]
        reverse += [j+1,j]
        bonds += [bf,bf]
    return np.array(atoms,dtype=np.float32),np.array(bonds,dtype=np.float32).reshape(-1,BOND_DIM),np.array(src),np.array(dst),np.array(reverse)


def graph_batch(smiles,device):
    atoms,bonds,src,dst,rev,owners=[],[],[],[],[],[]
    na,ne=0,0
    for i,s in enumerate(smiles):
        a,b,ss,dd,rr=graph_features(s)
        atoms.append(a); bonds.append(b); src.extend((ss+na).tolist()); dst.extend((dd+na).tolist()); rev.extend((rr+ne).tolist())
        owners.extend([i]*len(a)); na+=len(a); ne+=len(b)
    return (torch.tensor(np.concatenate(atoms),device=device),torch.tensor(np.concatenate(bonds),device=device),
            torch.tensor(src,dtype=torch.long,device=device),torch.tensor(dst,dtype=torch.long,device=device),
            torch.tensor(rev,dtype=torch.long,device=device),torch.tensor(owners,dtype=torch.long,device=device),len(smiles))


class DirectedMPNN(nn.Module):
    def __init__(self,width=256,depth=3,dropout=.1):
        super().__init__()
        self.width,self.depth=width,depth
        self.edge_input=nn.Linear(ATOM_DIM+BOND_DIM,width)
        self.edge_update=nn.Linear(width,width,bias=False)
        self.atom_output=nn.Linear(ATOM_DIM+width,width)
        self.dropout=nn.Dropout(dropout)

    def forward(self,batch):
        atoms,bonds,src,dst,reverse,owner,n=batch
        initial=torch.relu(self.edge_input(torch.cat([atoms[src],bonds],dim=1)))
        h=initial
        for _ in range(self.depth-1):
            incoming=torch.zeros((len(atoms),self.width),device=atoms.device).index_add(0,dst,h)
            h=self.dropout(torch.relu(initial+self.edge_update(incoming[src]-h[reverse])))
        incoming=torch.zeros((len(atoms),self.width),device=atoms.device).index_add(0,dst,h)
        atom_h=torch.relu(self.atom_output(torch.cat([atoms,incoming],dim=1)))
        pooled=torch.zeros((n,self.width),device=atoms.device).index_add(0,owner,atom_h)
        counts=torch.bincount(owner,minlength=n).clamp(min=1)[:,None]
        return pooled/counts


class NeuralModel(Model):
    def __init__(self,config,task,cache_root):
        self.config,self.task=dict(config),task
        self.cache=FeatureCache(cache_root)
        self.device="cpu"

    def _inputs(self,smiles):
        if self.config["family"]=="graph":
            return graph_batch(smiles,self.device)
        x=self.cache.get(smiles,self.config.get("features","combined"))
        return torch.tensor(self.scaler.transform(self.imputer.transform(x)),dtype=torch.float32,device=self.device)

    def fit(self,dataset,split=None,configuration=None):
        if split is not None:
            dataset=dataset.subset(split)
        if configuration:
            self.config.update(configuration)
        seed=self.config.get("seed",42)
        random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
        torch.set_num_threads(self.config.get("threads",4))
        self.device=self.config.get("device","cpu")
        if self.device=="cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA requested but unavailable")
        self.labels=dataset.labels
        self.training_ids=dataset.ids.tolist()
        self.training_groups=set(dataset.groups)
        width=self.config.get("width",256)
        if self.config["family"]=="graph":
            encoder=DirectedMPNN(width,self.config.get("depth",3),self.config.get("dropout",.1))
        else:
            x=self.cache.get(dataset.smiles,self.config.get("features","combined"))
            self.imputer=SimpleImputer(add_indicator=True,keep_empty_features=True).fit(x)
            xx=self.imputer.transform(x)
            self.scaler=StandardScaler().fit(xx)
            encoder=nn.Sequential(nn.Linear(xx.shape[1],width),nn.ReLU(),nn.Dropout(self.config.get("dropout",.1)),nn.Linear(width,width),nn.ReLU())
        self.encoder=encoder.to(self.device)
        self.head=nn.Linear(width,len(self.labels)*(1 if self.task=="classification" else 2)).to(self.device)
        if self.task=="classification":
            p=np.clip(np.nanmean(dataset.y,axis=0),.005,.995)
            with torch.no_grad():
                self.head.bias.copy_(torch.tensor(np.log(p/(1-p)),dtype=torch.float32,device=self.device))
        y=np.asarray(dataset.y,dtype=np.float32)
        self.target_mean=np.nanmean(y,axis=0) if self.task=="regression" else np.zeros(y.shape[1])
        self.target_mean=np.nan_to_num(self.target_mean)
        self.target_scale=np.maximum(np.nanstd(y,axis=0),.1) if self.task=="regression" else np.ones(y.shape[1])
        self.target_scale=np.nan_to_num(self.target_scale,nan=1)
        target=torch.tensor((y-self.target_mean)/self.target_scale,dtype=torch.float32,device=self.device)
        lo=torch.tensor((dataset.lower-self.target_mean)/self.target_scale,dtype=torch.float32,device=self.device)
        hi=torch.tensor((dataset.upper-self.target_mean)/self.target_scale,dtype=torch.float32,device=self.device)
        codes=np.vectorize({"exact":0,"left":1,"right":2,"interval":3,"missing":4}.get)(dataset.censoring).astype(int)
        codes[(codes==0)&~np.isfinite(y)]=4
        codes=torch.tensor(codes,device=self.device)
        optimiser=torch.optim.AdamW(list(self.encoder.parameters())+list(self.head.parameters()),lr=self.config.get("learning_rate",.001),weight_decay=self.config.get("weight_decay",1e-4))
        rng=np.random.default_rng(seed)
        batch_size=self.config.get("batch_size",64)
        self.history=[]
        for epoch in range(self.config.get("epochs",50)):
            self.encoder.train(); self.head.train()
            order=rng.permutation(len(y)); losses=[]
            for start in range(0,len(y),batch_size):
                ix=order[start:start+batch_size]
                out=self.head(self.encoder(self._inputs([dataset.smiles[i] for i in ix])))
                if self.task=="classification":
                    loss=masked_bce(out,target[ix])
                else:
                    mu,ls=out.chunk(2,dim=1)
                    loss=censored_normal_nll(mu,ls,target[ix],lo[ix],hi[ix],codes[ix])
                optimiser.zero_grad(); loss.backward()
                torch.nn.utils.clip_grad_norm_(list(self.encoder.parameters())+list(self.head.parameters()),5)
                optimiser.step(); losses.append(float(loss.detach()))
            self.history.append(float(np.mean(losses)))
        self.encoder.eval(); self.head.eval()
        return self

    def embed(self,molecules):
        result=[]
        self.encoder.eval()
        with torch.no_grad():
            for start in range(0,len(molecules),self.config.get("batch_size",64)):
                result.append(self.encoder(self._inputs(molecules[start:start+self.config.get("batch_size",64)])).cpu().numpy())
        return np.concatenate(result)

    def predict(self,molecules,context=None):
        z=self.embed(molecules)
        with torch.no_grad():
            out=self.head(torch.tensor(z,dtype=torch.float32,device=self.device))
            if self.task=="classification":
                return torch.sigmoid(out).cpu().numpy()
            mu,ls=out.chunk(2,dim=1)
            self.last_aleatoric_std=np.exp(ls.clamp(-6,5).cpu().numpy())*self.target_scale
            return mu.cpu().numpy()*self.target_scale+self.target_mean

