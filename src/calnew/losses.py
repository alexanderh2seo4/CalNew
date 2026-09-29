"""Likelihoods for censored thresholds, masked targets and forced-choice responses."""
from __future__ import annotations

import torch
from torch import nn


def logdiffexp(log_a,log_b):
    return log_a+torch.log(-torch.expm1(torch.clamp(log_b-log_a,max=-1e-7)))


def censored_normal_nll(mean,log_scale,value,lower,upper,codes):
    """Codes: exact=0, left=1, right=2, interval=3, missing=4."""
    scale=torch.exp(log_scale.clamp(-6,5))
    terms=[]
    exact=codes==0
    if exact.any():
        z=(value[exact]-mean[exact])/scale[exact]
        # Gaussian observed-data likelihood; source noise is modelled separately.
        terms.append(.5*z*z+torch.log(scale[exact])+.5*torch.log(torch.tensor(2*torch.pi,device=mean.device)))
    left=codes==1
    if left.any():
        terms.append(-torch.special.log_ndtr((upper[left]-mean[left])/scale[left]))
    right=codes==2
    if right.any():
        terms.append(-torch.special.log_ndtr((mean[right]-lower[right])/scale[right]))
    interval=codes==3
    if interval.any():
        a=(lower[interval]-mean[interval])/scale[interval]
        b=(upper[interval]-mean[interval])/scale[interval]
        # Use survival probabilities on the positive tail to avoid cancellation.
        logp=torch.where(a>0,logdiffexp(torch.special.log_ndtr(-a),torch.special.log_ndtr(-b)),
                         logdiffexp(torch.special.log_ndtr(b),torch.special.log_ndtr(a)))
        terms.append(-logp)
    if not terms:
        return mean.sum()*0
    return torch.cat([t.reshape(-1) for t in terms]).mean()


def masked_bce(logits,y):
    mask=torch.isfinite(y)
    return nn.functional.binary_cross_entropy_with_logits(logits[mask],y[mask]) if mask.any() else logits.sum()*0


def forced_choice_probability(log_concentration,midpoint,slope,lapse=0.0,alternatives=3):
    if alternatives<2:
        raise ValueError("Forced-choice tasks require at least two alternatives")
    chance=1/alternatives
    if not 0<=lapse<1-chance:
        raise ValueError('Lapse must preserve probability above chance')
    if torch.any(torch.as_tensor(slope)<=0):
        raise ValueError('Detection curve slope must be positive')
    return chance+(1-chance-lapse)*torch.sigmoid(slope*(log_concentration-midpoint))


def pairwise_loss(score_a,score_b,outcome,lower_is_better=True):
    """Outcome 1 means A wins; 0.5 is an explicitly observed tie/soft outcome."""
    logits=score_b-score_a if lower_is_better else score_a-score_b
    return nn.functional.binary_cross_entropy_with_logits(logits,outcome)
