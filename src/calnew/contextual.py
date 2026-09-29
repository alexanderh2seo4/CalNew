"""Small, inspectable likelihoods for context-dependent endpoints.

These components are trainable, but are not claims of validated population or
receptor predictions. Context-conditioned data must be supplied explicitly.
"""
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from sklearn.isotonic import IsotonicRegression


class ConcentrationCurve:
    def __init__(self,kind='intensity',flexible=False,alternatives=3):
        if kind not in ('intensity','detection'): raise ValueError('Unknown curve endpoint')
        if alternatives<2: raise ValueError('Forced-choice task requires at least two alternatives')
        self.kind,self.flexible,self.alternatives=kind,flexible,alternatives

    def fit(self,log_concentration,response,*,protocol,matrix,unit):
        x,y=np.asarray(log_concentration,float),np.asarray(response,float)
        if len(x)<4 or not np.isfinite(x).all() or not np.isfinite(y).all(): raise ValueError('At least four finite observations required')
        if self.kind=='detection' and not np.isin(y,[0,1]).all(): raise ValueError('Detection responses must be binary correctness')
        self.context=dict(protocol=protocol,matrix=matrix,unit=unit)
        self.range=(float(x.min()),float(x.max()))
        if self.flexible:
            self.model=IsotonicRegression(increasing=True,out_of_bounds='nan',y_min=1/self.alternatives if self.kind=='detection' else None).fit(x,y)
        else:
            def loss(theta):
                slope=np.exp(theta[1]); p=expit(slope*(x-theta[0]))
                if self.kind=='detection':
                    p=1/self.alternatives+(1-1/self.alternatives)*p
                    return -np.sum(y*np.log(p+1e-10)+(1-y)*np.log(1-p+1e-10))
                pred=theta[2]+np.exp(theta[3])*p
                return np.mean((y-pred)**2)
            theta=[np.median(x),0,float(y.min()),float(np.log(max(np.ptp(y),1)))]
            self.parameters=minimize(loss,theta,method='L-BFGS-B',bounds=[(x.min()-5,x.max()+5),(-6,6),(None,None),(-10,10)]).x
        return self

    def predict(self,log_concentration,*,protocol,matrix,unit,allow_extrapolation=False):
        if dict(protocol=protocol,matrix=matrix,unit=unit)!=self.context: raise ValueError('Unseen protocol or incompatible concentration basis')
        x=np.asarray(log_concentration,float)
        if not allow_extrapolation and ((x<self.range[0])|(x>self.range[1])).any(): raise ValueError('Concentration outside measured range')
        if self.flexible: return self.model.predict(x)
        midpoint,log_slope,base,log_amplitude=self.parameters
        p=expit(np.exp(log_slope)*(x-midpoint))
        return 1/self.alternatives+(1-1/self.alternatives)*p if self.kind=='detection' else base+np.exp(log_amplitude)*p


def participant_variation(frame):
    """Within-stimulus between-person spread; no assumed general-population coverage."""
    required={'stimulus_id','subject_id','value'}
    if not required.issubset(frame.columns): raise ValueError('Participant observations required')
    means=frame.groupby(['stimulus_id','subject_id']).value.mean()
    return means.groupby('stimulus_id').agg(['mean','std','count']).rename(columns={'std':'between_participant_sd','count':'participants'})


def receptor_network(molecule_dim,protein_dim,context_dim,width=128):
    """Cross-attention over supplied sequence embeddings; a CALNEW extension, not LORAX reproduction."""
    import torch
    from torch import nn
    class ReceptorNetwork(nn.Module):
        def __init__(self):
            super().__init__()
            self.molecule=nn.Linear(molecule_dim,width); self.protein=nn.Linear(protein_dim,width)
            self.attention=nn.MultiheadAttention(width,4,batch_first=True)
            self.head=nn.Sequential(nn.Linear(width*2+context_dim,width),nn.ReLU(),nn.Linear(width,1))
        def forward(self,molecule,sequence,context,padding_mask=None):
            direct=self.molecule(molecule)
            tokens=self.protein(sequence)
            attended,_=self.attention(direct[:,None],tokens,tokens,key_padding_mask=padding_mask)
            return self.head(torch.cat([direct,attended[:,0],context],dim=-1))
    return ReceptorNetwork()
