"""Raw response preservation and bounds for an ascending forced-choice series."""
import math
import numpy as np


def threshold_bounds(concentrations,correct):
    pairs=sorted(zip(concentrations,correct))
    if not pairs or any(not math.isfinite(c) or c<=0 or ok not in (0,1) for c,ok in pairs):
        raise ValueError('Positive concentrations and binary responses required; retain blanks separately')
    first=next((i for i,(_,ok) in enumerate(pairs) if ok and all(o for _,o in pairs[i:])),None)
    if first is None: return {'censoring':'right','lower':pairs[-1][0],'upper':None,'value':None}
    if first==0: return {'censoring':'left','lower':None,'upper':pairs[0][0],'value':None}
    lo,hi=pairs[first-1][0],pairs[first][0]
    if lo==hi:
        return {'censoring':'missing','lower':None,'upper':None,'value':None,'reason':'Mixed responses at transition concentration; fit trial-level psychometric likelihood'}
    return {'censoring':'interval','lower':lo,'upper':hi,'value':None,'derived_bet':math.sqrt(lo*hi)}


def power_simulation(paired_improvements,practical_effect,sample_sizes=(24,48,96,192),repeats=2000,seed=42):
    """Resample molecule-level paired errors from a pilot; participants are not molecules."""
    from scipy.stats import ttest_1samp
    values=np.asarray(paired_improvements,float)
    if len(values)<8 or not np.isfinite(values).all() or np.std(values)==0: raise ValueError('At least eight variable, finite pilot molecule differences required')
    if practical_effect<=0: raise ValueError('Declare a positive practically meaningful improvement')
    centered=values-values.mean()+practical_effect
    rng=np.random.default_rng(seed); result={}
    for n in sample_sizes:
        draws=rng.choice(centered,size=(repeats,n),replace=True)
        tests=ttest_1samp(draws,0,axis=1)
        result[int(n)]=float(np.mean((tests.pvalue<.05)&(tests.statistic>0)))
    return {'power':result,'target':.8,'experimental_unit':'molecule','assumption':'Pilot variance and sampling design remain representative','seed':seed}
