"""Independent-set probability and group-level conformal calibration."""
from __future__ import annotations

import math

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.special import expit, logit


class ProbabilityCalibrator:
    def fit(self, y, prediction, groups=None):
        y, p = np.asarray(y), np.clip(prediction, 1e-6, 1-1e-6)
        logits = logit(p)
        weights = np.ones(len(y))
        if groups is not None:
            for g in np.unique(groups):
                mask = groups == g
                weights[mask] = 1 / mask.sum()
        # One regularised temperature prevents fitting hundreds of parameters on a small panel.
        def loss(log_temp):
            z = logits / np.exp(log_temp)
            terms = np.logaddexp(0,z)-y*z
            observed = np.isfinite(y)
            weighted = observed * weights[:,None]
            return np.nansum(terms*weighted) / max(weighted.sum(),1) + 0.01*log_temp**2
        if not np.isfinite(y).any():
            raise ValueError("No observed calibration labels")
        self.temperature = float(np.exp(minimize_scalar(loss, bounds=(-2.3,2.3), method="bounded").x))
        return self

    def transform(self, prediction):
        return expit(logit(np.clip(prediction,1e-6,1-1e-6))/self.temperature)


class GroupConformal:
    def __init__(self, coverage=0.9):
        if not 0 < coverage < 1:
            raise ValueError("Coverage must lie between zero and one")
        self.coverage = coverage

    def fit(self, y, prediction, groups, scale=None):
        y, prediction = np.asarray(y), np.asarray(prediction)
        scale = np.ones_like(prediction) if scale is None else np.maximum(scale,1e-6)
        residual = np.abs(y-prediction) / scale
        self.quantiles, self.counts = [], []
        for j in range(y.shape[1]):
            scores = []
            for group in np.unique(groups):
                vals = residual[groups==group,j]
                if np.isfinite(vals).any():
                    scores.append(np.nanmax(vals))
            n = len(scores)
            k = math.ceil((n+1)*self.coverage)
            self.counts.append(n)
            self.quantiles.append(float(np.sort(scores)[k-1]) if n and k<=n else float("inf"))
        self.quantiles = np.array(self.quantiles)
        return self

    def interval(self, prediction, scale=None):
        scale = np.ones_like(prediction) if scale is None else np.maximum(scale,1e-6)
        half = scale*self.quantiles
        return prediction-half, prediction+half

