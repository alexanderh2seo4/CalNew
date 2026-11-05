"""Intensity heads with an increasing response to nominal dilution."""
from __future__ import annotations

import numpy as np
from sklearn.impute import SimpleImputer
from xgboost import XGBRegressor

from .stages import stack

INTENSITY_STRUCTURE = ("rdkit", "transport", "hbond", "osmophore", "chain")
KELLER_DOSE_MEMBERS = (
    INTENSITY_STRUCTURE + ("quality", "direction"),
    INTENSITY_STRUCTURE + ("fingerprint",),
    ("unimol1",),
)


class RaviaRegularizedTrees:
    """Small-sample alternatives on the existing Ravia member feature sets."""

    def __init__(self, mode="regularized", seed=42, threads=2):
        from .stages import RAVIA_MEMBERS
        if mode not in ("regularized", "all_trees"):
            raise ValueError("Unknown Ravia tree mode")
        self.mode, self.seed, self.threads = mode, seed, threads
        self.members = RAVIA_MEMBERS

    def fit(self, blocks, y, groups):
        from sklearn.ensemble import ExtraTreesRegressor
        self.models = []
        for kind, names in self.members:
            features = stack(blocks, names).astype(float)
            imputer = SimpleImputer(strategy="median", keep_empty_features=True).fit(features)
            if kind == "extra_trees" or self.mode == "all_trees":
                model = ExtraTreesRegressor(n_estimators=500, max_features=.3,
                    min_samples_leaf=2, n_jobs=self.threads, random_state=self.seed)
            else:
                model = XGBRegressor(n_estimators=400, learning_rate=.03, max_depth=2,
                    min_child_weight=5, reg_lambda=10, subsample=.8, colsample_bytree=.3,
                    n_jobs=self.threads, random_state=self.seed, verbosity=0)
            self.models.append((imputer, model.fit(imputer.transform(features), y)))
        return self

    def predict(self, blocks):
        values = np.column_stack([model.predict(imputer.transform(stack(blocks, names)))
            for (_, names), (imputer, model) in zip(self.members, self.models)])
        if not np.isfinite(values).all():
            raise ValueError("Non-finite Ravia predictions")
        return values.mean(1)


class MonotoneDoseTrees:
    """Fit all observed dilutions, constraining intensity to increase with dose.

    Molecular features stay fixed when evaluating a dose curve. Imputation uses
    training rows only, and every tree constrains its final (log dilution) input.
    Clipping and equal averaging retain the increasing response and 0–100 range.
    """

    def __init__(self, members=KELLER_DOSE_MEMBERS, seed=42, threads=4,
            max_depth=4, min_child_weight=2, reg_lambda=1):
        self.members = [tuple(names) for names in members]
        self.seed, self.threads = seed, threads
        self.max_depth, self.min_child_weight, self.reg_lambda = max_depth, min_child_weight, reg_lambda

    @staticmethod
    def _x(blocks, names, x):
        dose = np.asarray(x, dtype=float)
        if dose.ndim != 1 or not np.isfinite(dose).all() or np.any(dose > 0):
            raise ValueError("Log10 dilution must be a finite vector <= 0")
        features = stack(blocks, names).astype(float)
        if len(features) != len(dose):
            raise ValueError("Molecular features and dilutions are not aligned")
        return np.column_stack([features, dose])

    def fit(self, blocks, x, intensity):
        y = np.asarray(intensity, dtype=float)
        if y.ndim != 1 or not np.isfinite(y).all() or np.any((y < 0) | (y > 100)):
            raise ValueError("Intensity must be a finite 0–100 vector")
        self.models = []
        for names in self.members:
            features = self._x(blocks, names, x)
            if len(features) != len(y):
                raise ValueError("Features and targets are not aligned")
            imputer = SimpleImputer(strategy="median", keep_empty_features=True).fit(features)
            model = XGBRegressor(n_estimators=400, learning_rate=0.03, max_depth=self.max_depth,
                subsample=0.8, colsample_bytree=0.3, min_child_weight=self.min_child_weight, reg_lambda=self.reg_lambda,
                monotone_constraints=tuple([0] * (features.shape[1] - 1) + [1]),
                n_jobs=self.threads, random_state=self.seed, verbosity=0)
            model.fit(imputer.transform(features), y)
            self.models.append((imputer, model))
        return self

    def predict_members(self, blocks, x):
        values = np.column_stack([model.predict(imputer.transform(self._x(blocks, names, x)))
            for names, (imputer, model) in zip(self.members, self.models)])
        if not np.isfinite(values).all():
            raise ValueError("Non-finite intensity prediction")
        return np.clip(values, 0, 100)

    def predict(self, blocks, x):
        return self.predict_members(blocks, x).mean(1)


class IntensityRecipe:
    """A frozen training-selected head, optionally averaged with the current head."""

    def __init__(self, dataset, recipe, potency_blocks=(), epochs=150, seed=42, threads=2):
        self.dataset, self.recipe = dataset, recipe
        self.potency_blocks, self.epochs = list(potency_blocks), epochs
        self.seed, self.threads = seed, threads
        self.candidate_name = recipe.removeprefix("blend_")
        self.blend = recipe.startswith("blend_")

    def fit(self, blocks, y, groups, x=None):
        from .semantic import SEMANTIC_BASE
        from .stages import IntensityStage, RAVIA_MEMBERS, TabularEnsemble
        self.baseline, self.candidate = None, None
        if self.blend or self.recipe == "baseline":
            self.baseline = (IntensityStage(self.potency_blocks, "fingerprint", seeds=(self.seed,), epochs=self.epochs).fit(
                {n: blocks[n] for n in self.potency_blocks}, x, y) if self.dataset == "keller" else
                TabularEnsemble(RAVIA_MEMBERS, self.seed, self.threads).fit(blocks, y, groups))
        if self.recipe != "baseline":
            if self.dataset == "keller":
                members = {"dose_trees": KELLER_DOSE_MEMBERS,
                    "dose_semantic": (SEMANTIC_BASE + ("semantic",),),
                    "dose_molecular": (INTENSITY_STRUCTURE + ("fingerprint", "unimol1"),)}[self.candidate_name]
                self.candidate = MonotoneDoseTrees(members, self.seed, self.threads).fit(blocks, x, y)
            elif self.dataset == "ravia":
                if self.candidate_name in ("regularized", "all_trees"):
                    self.candidate = RaviaRegularizedTrees(self.candidate_name, self.seed, self.threads).fit(blocks, y, groups)
                elif self.candidate_name == "molecular_svr":
                    from sklearn.decomposition import PCA
                    from sklearn.model_selection import GridSearchCV, GroupKFold
                    from sklearn.pipeline import Pipeline
                    from sklearn.preprocessing import StandardScaler
                    from sklearn.svm import SVR
                    self.candidate = GridSearchCV(Pipeline([("impute", SimpleImputer(keep_empty_features=True)),
                        ("scale", StandardScaler()), ("pca", PCA(n_components=25, svd_solver="full")), ("svr", SVR(epsilon=1.0))]),
                        {"svr__C": [10., 100., 1000.], "svr__gamma": [v/25 for v in (.1, 1., 10.)]},
                        cv=GroupKFold(3, shuffle=True, random_state=173), scoring="neg_mean_squared_error", n_jobs=1)
                    self.candidate.fit(blocks["unimol1"], y, groups=groups)
                else:
                    members = {"molecular": (("extra_trees", ("unimol1",)),),
                        "structure_molecular": (("extra_trees", SEMANTIC_BASE + ("unimol1",)),),
                        "molecular_boost": (("xgboost", INTENSITY_STRUCTURE + ("unimol1",)),),
                        "semantic": (("extra_trees", SEMANTIC_BASE + ("semantic",)),)}[self.candidate_name]
                    self.candidate = TabularEnsemble(members, self.seed, self.threads).fit(blocks, y, groups)
            else:
                raise ValueError("Unknown intensity dataset")
        return self

    @property
    def feature_names(self):
        names = set()
        for model in (self.baseline, self.candidate):
            if model is None:
                continue
            if isinstance(model, MonotoneDoseTrees):
                names.update(n for member in model.members for n in member)
            elif hasattr(model, "fusion_blocks"):
                names.update(model.fusion_blocks)
            elif hasattr(model, "members"):
                names.update(n for _, member in model.members for n in member)
            else:
                names.add("unimol1")
        return sorted(names)

    def predict_parts(self, blocks, x=None):
        def prediction(model):
            if self.dataset == "keller":
                return model.predict(blocks, x) if isinstance(model, MonotoneDoseTrees) else model.predict(blocks, x)[0]
            return np.clip(model.predict(blocks["unimol1"]), 0, 100) if not hasattr(model, "members") else model.predict(blocks)
        values = {}
        if self.baseline is not None:
            values["baseline"] = prediction(self.baseline)
        if self.candidate is not None:
            values["candidate"] = prediction(self.candidate)
        values["selected"] = (values["baseline"]+values["candidate"])/2 if self.blend else values[
            "baseline" if self.recipe == "baseline" else "candidate"]
        if not all(np.isfinite(p).all() for p in values.values()):
            raise ValueError("Non-finite intensity recipe predictions")
        return values

    def predict(self, blocks, x=None):
        return self.predict_parts(blocks, x)["selected"]


def predict_intensity(run, smiles, dataset="keller", dilution=None, cache_root="data/features", return_curve=False):
    """Serve an intensity bundle with its measurement protocol made explicit."""
    from pathlib import Path
    import joblib
    from ..chemistry import identify
    from ..io import file_digest, read_json
    from .blocks import BlockCache
    from .molecular import unimol1_vectors
    from .stages import quality_features
    if dataset not in ("keller", "ravia"):
        raise ValueError("Intensity dataset must be keller or ravia")
    if dataset == "ravia" and dilution is not None:
        raise ValueError("The Ravia head predicts its highest-presentation endpoint; it has no validated dilution input")
    if dataset == "keller":
        dilution = 1e-3 if dilution is None else dilution
        if not np.isfinite(dilution) or not 0 < dilution <= 1:
            raise ValueError("Dilution must be in (0, 1]")
    run = Path(run)
    artifact = run/f"intensity-{dataset}.joblib"
    manifest = read_json(run/f"serving-{dataset}.json")
    if manifest["artifact_sha256"] != file_digest(artifact):
        raise ValueError("Intensity bundle checksum mismatch")
    bundle = joblib.load(artifact)  # trusted local model
    canonical = [identify(s).smiles for s in smiles]
    names = set(bundle["model"].feature_names)
    if "semantic" in names:
        names.update(("rdkit", "fingerprint"))
    if "quality" in names or "direction" in names:
        names.update(bundle["quality_blocks"])
    blocks = BlockCache(Path(cache_root)).blocks(sorted(names-{"quality", "direction", "semantic", "unimol1"}), canonical)
    if "unimol1" in names:
        blocks["unimol1"] = unimol1_vectors(canonical, Path(bundle["molecular_artifact"]))
    if "quality" in names or "direction" in names:
        probabilities, _, direction = bundle["quality"].predict({n: blocks[n] for n in bundle["quality_blocks"]})
        blocks.update(quality=quality_features(probabilities), direction=direction)
    if "semantic" in names:
        source = np.column_stack([blocks["rdkit"], blocks["fingerprint"]])
        blocks["semantic"] = bundle["semantic_model"].predict(bundle["semantic_scaler"].transform({"x": source})["x"])
    x = np.full(len(canonical), np.log10(dilution)) if dataset == "keller" else None
    values = bundle["model"].predict_parts(blocks, x)
    curve, curve_x, hill_component = None, None, None
    if dataset == "keller" and return_curve:
        curve_x = np.unique(np.r_[np.arange(-7., 1.), x[0]])
        curve = np.stack([bundle["model"].predict(blocks, np.full(len(canonical), dose)) for dose in curve_x])
        if bundle["model"].baseline is not None:
            hill_component = bundle["model"].baseline.params(blocks).mean(0)
    records = []
    for i, s in enumerate(canonical):
        record = {"smiles": s, "intensity_0_100": float(values["selected"][i])}
        if dataset == "keller":
            record["dilution"] = dilution
            if return_curve:
                record["dose_response"] = {"representation": bundle["model"].recipe,
                    "curve": [{"log10_dilution": float(dose), "intensity_0_100": float(curve[j, i])}
                        for j, dose in enumerate(curve_x)]}
                if hill_component is not None:
                    record["dose_response"]["hill_component"] = dict(zip(
                        ("I_max", "x50_log10_dilution", "slope"), map(float, hill_component[i])))
        records.append(record)
    return {"run": str(run), "dataset": dataset, "recipe": bundle["model"].recipe,
        "validated_endpoint": manifest["validated_endpoint"], "molecules": records}
