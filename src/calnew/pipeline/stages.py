"""Stage models: A quality, B1 threshold potency, B2 dose-response intensity, C combiner.

Interfaces between stages are physically or geometrically meaningful: A emits calibrated
catalogue probabilities (the quality meta-feature), B2 emits Hill parameters so intensity
can be evaluated at any dilution, and C multiplies a quality direction by an
intensity-driven magnitude (profile length tracks intensity, direction tracks quality).
"""
from __future__ import annotations

import numpy as np
import torch
from scipy.special import logit
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.model_selection import GroupKFold
from torch import nn

from ..losses import censored_normal_nll
from .fusion import BlockScaler, predict_fusion, to_tensors, train_fusion

ALPHAS = (0.1, 1.0, 10.0, 100.0, 1000.0)


def quality_features(probabilities: np.ndarray) -> np.ndarray:
    return logit(np.clip(probabilities, 1e-4, 1 - 1e-4)).astype(np.float32)


def stack(blocks: dict, names) -> np.ndarray:
    return np.concatenate([blocks[n] for n in names], axis=1)


class GroupedRidge:
    """Ridge whose alpha is chosen by grouped inner CV (no structural leakage in tuning)."""

    def fit(self, x, y, groups, alphas=ALPHAS, inner=3):
        self.scaler = BlockScaler().fit({"x": x})
        xs = self.scaler.transform({"x": x})["x"].astype(np.float64)
        y = np.asarray(y, float)
        n_splits = min(inner, len(np.unique(groups)))
        scores = []
        for alpha in alphas:
            error = []
            for tr, va in GroupKFold(n_splits).split(xs, y, groups):
                model = Ridge(alpha=alpha).fit(xs[tr], y[tr])
                error.append(np.mean((model.predict(xs[va]) - y[va]) ** 2))
            scores.append(np.mean(error))
        self.alpha = float(alphas[int(np.argmin(scores))])
        self.model = Ridge(alpha=self.alpha).fit(xs, y)
        return self

    def predict(self, x):
        return self.model.predict(self.scaler.transform({"x": x})["x"].astype(np.float64))


# ---------------------------------------------------------------- Stage A: quality
class QualityStage:
    def __init__(self, blocks, anchor, seeds=(0, 1), epochs=40, width=96, orth_weight=0.1):
        self.block_names, self.anchor, self.seeds = list(blocks), anchor, seeds
        self.epochs, self.width, self.orth_weight = epochs, width, orth_weight

    def fit(self, blocks: dict, y: np.ndarray, direction: np.ndarray | None = None, direction_weight: float = 5.0):
        """`y`: catalogue labels (NaN = not assessed). `direction`: optional unit descriptor-profile
        targets in a second vocabulary (NaN rows = molecule not panel-rated), learned by a second head."""
        self.scaler = BlockScaler().fit(blocks)
        xb = self.scaler.transform(blocks)
        yt = torch.as_tensor(y, dtype=torch.float32)
        observed = np.isfinite(y)
        positives = np.nansum(y, 0)
        negatives = observed.sum(0) - positives
        pos_weight = torch.as_tensor(np.clip(negatives / np.maximum(positives, 1), 1, 30), dtype=torch.float32)
        labels = y.shape[1]
        self.direction_dim = 0 if direction is None else direction.shape[1]
        dt = None if direction is None else torch.as_tensor(direction, dtype=torch.float32)

        def loss(raw, index):
            target = yt[index]
            mask = torch.isfinite(target)
            total = raw.sum() * 0
            if mask.any():
                weights = torch.where(target == 1, pos_weight.expand_as(target), torch.ones_like(target))
                total = total + nn.functional.binary_cross_entropy_with_logits(raw[:, :labels][mask], target[mask], weight=weights[mask])
            if dt is not None:
                d = dt[index]
                rows = torch.isfinite(d).all(1)
                if rows.any():
                    predicted = nn.functional.normalize(nn.functional.softplus(raw[rows, labels:]), dim=1)
                    total = total + direction_weight * (1 - (predicted * d[rows]).sum(1)).mean()
            return total

        self.nets = [train_fusion(xb, loss, labels + self.direction_dim, self.anchor, epochs=self.epochs, width=self.width,
                                  orth_weight=self.orth_weight, seed=s) for s in self.seeds]
        self.labels = labels
        # Positive weighting inflates raw probabilities; rank metrics are the honest summary.
        return self

    def predict(self, blocks: dict):
        """Returns (label probabilities, fused embedding, unit direction or None)."""
        xb = self.scaler.transform(blocks)
        outs = [predict_fusion(net, xb) for net in self.nets]
        probabilities = np.mean([1 / (1 + np.exp(-raw[:, :self.labels])) for raw, _ in outs], axis=0)
        embedding = np.mean([emb for _, emb in outs], axis=0)
        direction = None
        if getattr(self, "direction_dim", 0):
            softplus = lambda v: np.logaddexp(0, v)
            direction = np.mean([softplus(raw[:, self.labels:]) for raw, _ in outs], axis=0)
            direction = (direction / np.maximum(np.linalg.norm(direction, axis=1, keepdims=True), 1e-9)).astype(np.float32)
        return probabilities.astype(np.float32), embedding.astype(np.float32), direction

    def gates(self):
        return [net.fusion.gates() for net in self.nets]


class QualityBaseline:
    """Per-label logistic regression on explicit + fingerprint blocks."""

    def fit(self, x, y):
        self.scaler = BlockScaler().fit({"x": x})
        xs = self.scaler.transform({"x": x})["x"].astype(np.float64)
        self.models = []
        for j in range(y.shape[1]):
            mask = np.isfinite(y[:, j])
            if len(np.unique(y[mask, j])) < 2:
                self.models.append(float(np.nanmean(y[:, j])))
                continue
            self.models.append(LogisticRegression(C=0.05, max_iter=400, class_weight="balanced").fit(xs[mask], y[mask, j]))
        return self

    def predict(self, x):
        xs = self.scaler.transform({"x": x})["x"].astype(np.float64)
        return np.column_stack([np.full(len(xs), m) if isinstance(m, float) else m.predict_proba(xs)[:, 1] for m in self.models])


# ---------------------------------------------------------------- Stage B1: threshold
THRESHOLD_VARIANTS = {
    "ridge_fingerprint": ("fingerprint",),
    "ridge_explicit": ("transport", "hbond", "osmophore", "chain"),
    "ridge_explicit_fingerprint": ("transport", "hbond", "osmophore", "chain", "fingerprint"),
    "ridge_explicit_quality": ("transport", "hbond", "osmophore", "chain", "quality"),
}


class ThresholdStage:
    """Ablation-ready ridge variants, a NOSE-lite fusion net with a Gaussian head, and their ensemble."""

    def __init__(self, fusion_blocks, anchor, seeds=(0, 1, 2, 3, 4), epochs=120):
        self.fusion_blocks, self.anchor, self.seeds, self.epochs = list(fusion_blocks), anchor, seeds, epochs

    def fit(self, blocks: dict, y: np.ndarray, groups: np.ndarray):
        self.ridges = {name: GroupedRidge().fit(stack(blocks, cols), y, groups) for name, cols in THRESHOLD_VARIANTS.items()}
        fb = {n: blocks[n] for n in self.fusion_blocks}
        self.scaler = BlockScaler().fit(fb)
        xb = self.scaler.transform(fb)
        self.center, self.spread = float(np.mean(y)), float(np.std(y) or 1.0)
        target = torch.as_tensor((y - self.center) / self.spread, dtype=torch.float32)
        codes = torch.zeros(len(y), dtype=torch.long)
        nan = torch.full((len(y),), float("nan"))

        def loss(raw, index):
            # Exact observations reduce censored_normal_nll to a Gaussian NLL with a learned scale;
            # left/right/interval rows would use the same call unchanged once censored data exist.
            return censored_normal_nll(raw[:, 0], raw[:, 1], target[index], nan[index], nan[index], codes[index])

        self.nets = [train_fusion(xb, loss, 2, self.anchor, epochs=self.epochs, batch_size=32, lr=1e-3, weight_decay=1e-3,
                                  dropout=0.3, width=64, seed=s) for s in self.seeds]
        return self

    def predict(self, blocks: dict) -> dict:
        out = {name: model.predict(stack(blocks, THRESHOLD_VARIANTS[name])) for name, model in self.ridges.items()}
        xb = self.scaler.transform({n: blocks[n] for n in self.fusion_blocks})
        raw = np.stack([predict_fusion(net, xb)[0] for net in self.nets])
        mean = raw[:, :, 0] * self.spread + self.center
        aleatoric = np.exp(np.clip(raw[:, :, 1], -6, 5)) * self.spread
        out["fusion"] = mean.mean(0)
        out["fusion_sd"] = np.sqrt(mean.var(0) + (aleatoric ** 2).mean(0))
        out["ensemble"] = 0.5 * (out["fusion"] + out["ridge_explicit_quality"])
        return out


# ---------------------------------------------------------------- Stage B2: dose-response
def hill(x, params):
    """Intensity (0-100) at log10 dilution x from (I_max, x50, slope) rows."""
    imax, x50, slope = params[..., 0], params[..., 1], params[..., 2]
    return imax / (1 + np.exp(-slope * (x - x50)))


def _hill_params_torch(raw):
    imax = 100 * torch.sigmoid(raw[:, 0] + 0.5)
    x50 = -6.0 + 2.0 * raw[:, 1]
    slope = nn.functional.softplus(raw[:, 2]) * 0.5 + 0.05
    return torch.stack([imax, x50, slope], 1)


class IntensityStage:
    """Predicts per-molecule Hill parameters; trained on intensity at the observed dilutions."""

    def __init__(self, fusion_blocks, anchor, seeds=(0, 1, 2), epochs=150):
        self.fusion_blocks, self.anchor, self.seeds, self.epochs = list(fusion_blocks), anchor, seeds, epochs

    def fit(self, blocks: dict, x: np.ndarray, intensity: np.ndarray):
        fb = {n: blocks[n] for n in self.fusion_blocks}
        self.scaler = BlockScaler().fit(fb)
        xb = self.scaler.transform(fb)
        xt = torch.as_tensor(x, dtype=torch.float32)
        yt = torch.as_tensor(intensity, dtype=torch.float32)

        def loss(raw, index):
            p = _hill_params_torch(raw)
            pred = p[:, 0] * torch.sigmoid(p[:, 2] * (xt[index] - p[:, 1]))
            return nn.functional.mse_loss(pred, yt[index]) / 100.0

        self.nets = [train_fusion(xb, loss, 3, self.anchor, epochs=self.epochs, batch_size=32, lr=1e-3, weight_decay=1e-3,
                                  dropout=0.3, width=64, seed=s) for s in self.seeds]
        return self

    @torch.no_grad()
    def params(self, blocks: dict) -> np.ndarray:
        xb = to_tensors(self.scaler.transform({n: blocks[n] for n in self.fusion_blocks}))
        return np.stack([_hill_params_torch(net(xb)[0]).numpy() for net in self.nets])  # seeds x n x 3

    def predict(self, blocks: dict, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        curves = hill(np.asarray(x)[None, :], self.params(blocks))
        return curves.mean(0), curves.std(0)


# ---------------------------------------------------------------- Stage C: combiner
def _inverse_softplus(y):
    y = np.maximum(np.asarray(y, float), 1e-4)
    return np.log(np.expm1(y))


class ProfileCombiner(nn.Module):
    """profile = magnitude(I, x) * direction(quality); pleasantness from quality and intensity.

    The direction depends only on the stage-A quality representation; the magnitude only on
    intensity and dilution. Biases start at the training mean profile, so with zero weights
    the combiner predicts the average odour at the predicted intensity; every learned
    deviation is penalised. A linear residual on quality absorbs what the factorised form
    cannot express.
    """

    def __init__(self, quality_dim, mean_profile, mean_pleasantness):
        super().__init__()
        # Mixing weight between the learned direction and stage A's predicted panel direction.
        self.prior_gate = nn.Parameter(torch.tensor(1.0))
        descriptors = len(mean_profile)
        norm = float(np.linalg.norm(mean_profile)) or 1.0
        self.direction = nn.Linear(quality_dim, descriptors)
        self.magnitude = nn.Linear(2, 1)
        self.residual = nn.Linear(quality_dim, descriptors)
        self.pleasant_quality = nn.Linear(quality_dim, 1)
        self.pleasant_interaction = nn.Linear(quality_dim, 1)
        with torch.no_grad():
            for layer in (self.direction, self.residual, self.pleasant_quality, self.pleasant_interaction):
                layer.weight.zero_()
                layer.bias.zero_()
            self.direction.bias.copy_(torch.as_tensor(_inverse_softplus(np.asarray(mean_profile) / norm), dtype=torch.float32))
            self.magnitude.weight.zero_()
            self.magnitude.bias.fill_(float(_inverse_softplus(norm / 25)))
            self.pleasant_quality.bias.fill_((float(mean_pleasantness) - 50) / 10)

    def forward(self, q, intensity, x, prior=None):
        s = torch.stack([intensity / 100.0, x / 5.0], 1)
        base = nn.functional.softplus(self.direction(q))
        if prior is not None:
            g = torch.sigmoid(self.prior_gate)
            base = (1 - g) * nn.functional.normalize(base, dim=1) + g * prior
        direction = nn.functional.normalize(base, dim=1)
        magnitude = 25 * nn.functional.softplus(self.magnitude(s))
        profile = magnitude * direction + self.residual(q)
        pleasant = 50 + 10 * (self.pleasant_quality(q) + (intensity / 100.0)[:, None] * self.pleasant_interaction(q))
        return profile, pleasant[:, 0]

    def penalty(self):
        return sum(layer.weight.pow(2).sum() for layer in (self.direction, self.residual, self.pleasant_quality, self.pleasant_interaction))

    @torch.no_grad()
    def unit_direction(self, q, prior=None):
        base = nn.functional.softplus(self.direction(q))
        if prior is not None:
            g = torch.sigmoid(self.prior_gate)
            base = (1 - g) * nn.functional.normalize(base, dim=1) + g * prior
        return nn.functional.normalize(base, dim=1)


class CombinerStage:
    """Teacher-forced combiner; its L2 strength is chosen by grouped inner CV."""

    PENALTIES = (1e-2, 1e-1, 1.0, 10.0, 100.0)

    def __init__(self, epochs=400, lr=1e-2, seed=0, penalty=None, inner=3):
        self.epochs, self.lr, self.seed, self.penalty, self.inner = epochs, lr, seed, penalty, inner

    def _train(self, q, intensity, x, profile, pleasantness, penalty, prior=None):
        torch.manual_seed(self.seed)
        scaler = BlockScaler().fit({"q": q})
        qt = torch.as_tensor(scaler.transform({"q": q})["q"])
        it, xt = torch.as_tensor(intensity, dtype=torch.float32), torch.as_tensor(x, dtype=torch.float32)
        pt, lt = torch.as_tensor(profile, dtype=torch.float32), torch.as_tensor(pleasantness, dtype=torch.float32)
        dt = None if prior is None else torch.as_tensor(prior, dtype=torch.float32)
        net = ProfileCombiner(q.shape[1], profile.mean(0), pleasantness.mean())
        optimiser = torch.optim.Adam(net.parameters(), lr=self.lr)
        for _ in range(self.epochs):
            pred_profile, pred_pleasant = net(qt, it, xt, dt)
            loss = nn.functional.mse_loss(pred_profile, pt) + nn.functional.mse_loss(pred_pleasant, lt) / 4 + penalty * net.penalty()
            optimiser.zero_grad()
            loss.backward()
            optimiser.step()
        net.eval()
        return scaler, net

    def fit(self, q, intensity, x, profile, pleasantness, groups=None, prior=None):
        """Trained on measured intensity (teacher forcing); evaluated on predicted intensity."""
        if self.penalty is None:
            if groups is None:
                raise ValueError("Penalty selection needs molecular groups for grouped inner CV")
            scores = []
            for penalty in self.PENALTIES:
                error = []
                for tr, va in GroupKFold(min(self.inner, len(np.unique(groups)))).split(q, groups=groups):
                    sub = None if prior is None else prior[tr]
                    scaler, net = self._train(q[tr], intensity[tr], x[tr], profile[tr], pleasantness[tr], penalty, sub)
                    with torch.no_grad():
                        pp, pl = net(torch.as_tensor(scaler.transform({"q": q[va]})["q"]), torch.as_tensor(intensity[va], dtype=torch.float32),
                                     torch.as_tensor(x[va], dtype=torch.float32), None if prior is None else torch.as_tensor(prior[va]))
                    error.append(np.mean((pp.numpy() - profile[va]) ** 2) + np.mean((pl.numpy() - pleasantness[va]) ** 2) / 4)
                scores.append(np.mean(error))
            self.selected_penalty = float(self.PENALTIES[int(np.argmin(scores))])
            self.inner_scores = dict(zip(map(str, self.PENALTIES), map(float, scores)))
        else:
            self.selected_penalty = self.penalty
        self.scaler, self.net = self._train(q, intensity, x, profile, pleasantness, self.selected_penalty, prior)
        self.uses_prior = prior is not None
        self.prior_weight = float(torch.sigmoid(self.net.prior_gate)) if self.uses_prior else 0.0
        return self

    def _prior(self, prior):
        if self.uses_prior != (prior is not None):
            raise ValueError("Combiner was trained with a different direction-prior setting")
        return None if prior is None else torch.as_tensor(prior, dtype=torch.float32)

    @torch.no_grad()
    def predict(self, q, intensity, x, prior=None):
        qt = torch.as_tensor(self.scaler.transform({"q": q})["q"])
        profile, pleasant = self.net(qt, torch.as_tensor(intensity, dtype=torch.float32), torch.as_tensor(x, dtype=torch.float32),
                                     self._prior(prior))
        return profile.numpy(), pleasant.numpy()

    def direction(self, q, prior=None):
        return self.net.unit_direction(torch.as_tensor(self.scaler.transform({"q": q})["q"]), self._prior(prior)).numpy()


# ---------------------------------------------------------------- End-to-end baseline
class FlatBaseline:
    """One model from structure + dilution straight to [intensity, pleasantness, profile]."""

    def __init__(self, kind="extra_trees"):
        self.kind = kind

    def fit(self, x, targets, groups):
        if self.kind == "ridge":
            self.models = [GroupedRidge().fit(x, targets[:, j], groups) for j in range(targets.shape[1])]
        else:
            self.scaler = BlockScaler().fit({"x": x})
            self.model = ExtraTreesRegressor(n_estimators=300, min_samples_leaf=3, max_features=0.3, n_jobs=-1,
                                             random_state=0).fit(self.scaler.transform({"x": x})["x"], targets)
        return self

    def predict(self, x):
        if self.kind == "ridge":
            return np.column_stack([m.predict(x) for m in self.models])
        return self.model.predict(self.scaler.transform({"x": x})["x"])


# ---------------------------------------------------------------- Tabular heads (v2)
class TabularEnsemble:
    """Equal-weight average of tree / ridge members, each on its own block combination.

    Members are (kind, block names); kinds are "extra_trees", "xgboost" and "ridge" (grouped-CV
    alpha). Missing descriptor values are imputed with training medians. Optional `columns`
    (e.g. the stimulus log dilution) are appended to every member's inputs.

    Tree kinds with a "+aux" suffix also train on `auxiliary` rows (blocks, targets, weight) from a
    related measurement, with a trailing medium flag (0 = task rows, 1 = auxiliary rows); they
    always predict with the flag at 0. Without auxiliary rows they reduce to the plain tree.
    """

    def __init__(self, members, seed=0, threads=-1):
        self.members, self.seed, self.threads = [(k, tuple(b)) for k, b in members], seed, threads

    def _x(self, blocks, names, columns):
        x = stack(blocks, names).astype(np.float64)
        return x if columns is None else np.column_stack([x, columns])

    def fit(self, blocks: dict, y: np.ndarray, groups: np.ndarray, columns=None, auxiliary=None):
        from sklearn.impute import SimpleImputer
        from xgboost import XGBRegressor
        y = np.asarray(y, float)
        self.models, self.auxiliary_rows = [], 0
        for kind, names in self.members:
            x = self._x(blocks, names, columns)
            if kind == "ridge":
                self.models.append(GroupedRidge().fit(x, y, groups))
                continue
            weight, target = None, y
            if kind.endswith("+aux"):
                if columns is not None:
                    raise ValueError("+aux members do not take extra columns")
                kind = kind[:-4]
                x = np.column_stack([x, np.zeros(len(x))])
                if auxiliary is not None and len(auxiliary[1]):
                    aux_blocks, aux_y, aux_weight = auxiliary
                    xa = np.column_stack([self._x(aux_blocks, names, None), np.ones(len(aux_y))])
                    x, target = np.vstack([x, xa]), np.concatenate([y, np.asarray(aux_y, float)])
                    weight = np.concatenate([np.ones(len(y)), np.full(len(aux_y), float(aux_weight))])
                    self.auxiliary_rows = len(aux_y)
            imputer = SimpleImputer(strategy="median", keep_empty_features=True).fit(x)
            if kind == "extra_trees":
                model = ExtraTreesRegressor(n_estimators=500, max_features=0.3, min_samples_leaf=2, n_jobs=self.threads, random_state=self.seed)
            elif kind == "xgboost":
                model = XGBRegressor(n_estimators=400, learning_rate=0.03, max_depth=4, subsample=0.8, colsample_bytree=0.3,
                                     min_child_weight=2, n_jobs=self.threads if self.threads > 0 else None, random_state=self.seed, verbosity=0)
            else:
                raise ValueError(f"Unknown member kind: {kind}")
            self.models.append((imputer, model.fit(imputer.transform(x), target, sample_weight=weight)))
        return self

    def predict_members(self, blocks: dict, columns=None) -> np.ndarray:
        out = []
        for (kind, names), model in zip(self.members, self.models):
            x = self._x(blocks, names, columns)
            if kind.endswith("+aux"):
                x = np.column_stack([x, np.zeros(len(x))])  # predict as a task (air) row
            out.append(model.predict(x) if kind == "ridge" else model[1].predict(model[0].transform(x)))
        return np.column_stack(out)

    def predict(self, blocks: dict, columns=None) -> np.ndarray:
        return self.predict_members(blocks, columns).mean(1)


_RDKIT_EXPLICIT = ("rdkit",) + ("transport", "hbond", "osmophore", "chain")
# Member sets chosen by repeated inner CV on the NOSE split-42 training portion only (docs/PIPELINE.md).
# `unimol2` members use frozen Uni-Mol2 embeddings (NaN + availability column when conformers fail).
# Threshold trees also learn from Li et al. 2025 water thresholds (pipeline/auxiliary.py) via "+aux".
THRESHOLD_MEMBERS = (("xgboost+aux", _RDKIT_EXPLICIT + ("fingerprint",)), ("extra_trees+aux", _RDKIT_EXPLICIT + ("fingerprint",)),
                     ("ridge", ("fingerprint",)), ("ridge", ("unimol2",)))
HEDONIC_MEMBERS = (("extra_trees", _RDKIT_EXPLICIT + ("quality", "direction")), ("extra_trees", _RDKIT_EXPLICIT + ("fingerprint",)))
RAVIA_MEMBERS = (("xgboost", _RDKIT_EXPLICIT + ("quality", "direction")), ("xgboost", _RDKIT_EXPLICIT + ("quality",)),
                 ("xgboost", _RDKIT_EXPLICIT + ("fingerprint",)), ("extra_trees", ("unimol2",)))


# ---------------------------------------------------------------- Mixtures (analytic, unvalidated)
def combine_mixture(components: list[dict], primacy_fraction=0.2, weighting="uniform") -> dict:
    """Analytic mixture rule from the literature; no mixture data train or validate it here.

    Each component supplies `hill` (I_max, x50, slope) or an intensity already evaluated
    at primacy (`intensity_at_primacy`), `x` (log10 dilution in the mixture),
    `direction` (unit quality vector) and `pleasantness`. Component intensity is evaluated at
    `primacy_fraction` of its concentration (Primacy model); mixture intensity is their
    intensity-weighted average; quality direction is the (by default unweighted) normalised
    mean of component directions; pleasantness is intensity-weighted.
    """
    if not components:
        raise ValueError("A mixture requires at least one component")
    shift = np.log10(primacy_fraction)
    intensities = np.array([float(c["intensity_at_primacy"]) if "intensity_at_primacy" in c else
        float(hill(np.array(c["x"]) + shift, np.asarray(c["hill"]))) for c in components])
    weights = np.maximum(intensities, 1e-6)
    mixture_intensity = float(np.sum(weights * intensities) / np.sum(weights))
    directions = np.stack([np.asarray(c["direction"], float) for c in components])
    w = np.ones(len(components)) if weighting == "uniform" else weights
    direction = (w[:, None] * directions).sum(0)
    direction = direction / (np.linalg.norm(direction) or 1.0)
    pleasantness = float(np.sum(weights * np.array([c["pleasantness"] for c in components])) / np.sum(weights))
    return {"intensity": mixture_intensity, "component_intensities_at_primacy": intensities.tolist(), "direction": direction.tolist(),
            "pleasantness": pleasantness, "rule": f"primacy({primacy_fraction}) intensity-weighted; {weighting} direction average",
            "validation": "unvalidated: no mixture observations are used by this pipeline"}
