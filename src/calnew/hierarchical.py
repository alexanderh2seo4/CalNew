"""Robust threshold observation model with audited, overlapping source effects."""
import numpy as np
from scipy.optimize import minimize
from scipy.stats import t


class ThresholdObservationModel:
    """Calibrate molecular predictions against study effects using a Student-t likelihood.

    Input molecular predictions must be cross-fitted. Effects are shrinkage nuisance
    terms, not identifiable biological mechanisms. Unknown studies keep uncertainty.
    """
    def __init__(self,prior_scale=.5,min_overlap=5,df=4):
        if prior_scale<=0 or df<=2: raise ValueError('Positive prior scale and df>2 required')
        self.prior_scale,self.min_overlap,self.df=prior_scale,min_overlap,df

    def fit(self,prediction,value,censoring,lower,upper,studies,molecule_groups,*,cross_fitted):
        if not cross_fitted: raise ValueError('Observation model requires cross-fitted molecular predictions')
        p,y=np.asarray(prediction,float),np.asarray(value,float)
        c=np.asarray(censoring);lo,hi=np.asarray(lower,float),np.asarray(upper,float)
        studies,groups=np.asarray(studies),np.asarray(molecule_groups)
        if not np.isfinite(p).all(): raise ValueError('Finite molecular predictions required')
        group_sources={g:set(studies[groups==g]) for g in np.unique(groups)}
        overlap={s:sum(s in ss and len(ss)>1 for ss in group_sources.values()) for s in np.unique(studies)}
        self.levels=[s for s in sorted(overlap) if overlap[s]>=self.min_overlap]
        self.overlap=overlap
        index={s:i for i,s in enumerate(self.levels)}
        design=np.zeros((len(p),len(index)))
        for row,s in enumerate(studies):
            if s in index: design[row,index[s]]=1
        def objective(theta):
            mu=p+theta[0]+design@theta[2:];scale=np.exp(theta[1]);loss=0
            for code in ('exact','left','right','interval'):
                mask=c==code
                if not mask.any(): continue
                if code=='exact': logp=t.logpdf((y[mask]-mu[mask])/scale,self.df)-np.log(scale)
                elif code=='left': logp=t.logcdf((hi[mask]-mu[mask])/scale,self.df)
                elif code=='right': logp=t.logsf((lo[mask]-mu[mask])/scale,self.df)
                else:
                    a=(lo[mask]-mu[mask])/scale;b=(hi[mask]-mu[mask])/scale
                    probability=np.where(a>0,t.sf(a,self.df)-t.sf(b,self.df),t.cdf(b,self.df)-t.cdf(a,self.df))
                    logp=np.log(np.maximum(probability,1e-300))
                loss-=np.sum(logp)
            return loss+.5*np.sum((theta[2:]/self.prior_scale)**2)
        result=minimize(objective,np.zeros(2+len(index)),method='L-BFGS-B',bounds=[(None,None),(-6,6)]+[(None,None)]*len(index))
        if not result.success: raise RuntimeError(f'Observation likelihood optimisation failed: {result.message}')
        self.offset,self.scale=result.x[0],np.exp(result.x[1]);self.effects=dict(zip(self.levels,result.x[2:]))
        return self

    def predict(self,molecular_prediction,study=None):
        known=study in self.effects
        center=np.asarray(molecular_prediction)+self.offset+self.effects.get(study,0)
        variance=self.scale**2*self.df/(self.df-2)+(0 if known else self.prior_scale**2)
        return {'mean':center,'observation_sd':np.full_like(center,np.sqrt(variance)),
                'study_effect':self.effects.get(study),'study_status':'estimated_from_overlap' if known else 'unknown_integrated_prior_variance',
                'participant_variation':'unavailable_without_participant_records'}
