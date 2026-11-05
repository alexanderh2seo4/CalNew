"""Study-conditioned Keller/Ravia training with structure-only Ravia serving."""
import numpy as np
from sklearn.impute import SimpleImputer
from xgboost import XGBRegressor

from .semantic import SEMANTIC_BASE
from .stages import stack


class JointStudyTrees:
    """Share chemical features across studies while preserving their endpoints.

    Ravia's internal coordinate is always zero, with study indicator one. That
    represents the highest-presentation endpoint; it is not a measured dilution.
    Keller source rows retain their nominal log dilution and study indicator zero.
    All inputs are structure-derived, so direct source/target fitting does not
    introduce target-derived training features requiring an additional cross-fit.
    """
    members = (SEMANTIC_BASE,)

    def __init__(self, threads=2):
        self.threads = threads

    def fit(self, source_blocks, source_dose, source_y, target_blocks, target_y, source_weight=.25):
        source, target = stack(source_blocks, SEMANTIC_BASE), stack(target_blocks, SEMANTIC_BASE)
        dose = np.asarray(source_dose, dtype=float)
        sy, ty = np.asarray(source_y, dtype=float), np.asarray(target_y, dtype=float)
        if dose.shape != (len(source),) or not np.isfinite(dose).all() or np.any(dose > 0):
            raise ValueError("Keller source dose must be an aligned finite log dilution <=0")
        if sy.shape != (len(source),) or ty.shape != (len(target),) or not np.isfinite(np.r_[sy, ty]).all() or np.any((np.r_[sy, ty] < 0) | (np.r_[sy, ty] > 100)):
            raise ValueError("Joint intensity targets must be aligned finite 0–100 vectors")
        if not np.isfinite(source_weight) or source_weight <= 0:
            raise ValueError("Keller source weight must be positive and finite")
        x = np.vstack([np.column_stack([source, np.zeros(len(source)), dose]),
            np.column_stack([target, np.ones(len(target)), np.zeros(len(target))])])
        self.imputer = SimpleImputer(strategy="median", keep_empty_features=True).fit(x)
        self.model = XGBRegressor(n_estimators=400, learning_rate=.03, max_depth=3, min_child_weight=5,
            reg_lambda=10, subsample=.8, colsample_bytree=.3, n_jobs=self.threads, random_state=42, verbosity=0,
            monotone_constraints=tuple([0]*(x.shape[1]-1)+[1]))
        self.model.fit(self.imputer.transform(x), np.r_[sy, ty],
            sample_weight=np.r_[np.full(len(source), source_weight), np.ones(len(target))])
        self.source_weight = source_weight
        return self

    def predict(self, blocks):
        structure = stack(blocks, SEMANTIC_BASE)
        x = np.column_stack([structure, np.ones(len(structure)), np.zeros(len(structure))])
        values = np.clip(self.model.predict(self.imputer.transform(x)), 0, 100)
        if not np.isfinite(values).all():
            raise ValueError("Non-finite shared-study prediction")
        return values


class RaviaJointIntensity:
    dataset = "ravia"
    recipe = "joint_0.25_current"

    def __init__(self, current, joint):
        self.current, self.joint = current, joint

    @property
    def feature_names(self):
        return sorted(set(self.current.feature_names) | set(SEMANTIC_BASE))

    def predict_parts(self, blocks, x=None):
        if x is not None:
            raise ValueError("Ravia shared-study head predicts a single endpoint, without a dilution input")
        current, joint = self.current.predict(blocks), self.joint.predict(blocks)
        return {"baseline": current, "candidate": joint, "selected": (current+joint)/2}

    def predict(self, blocks, x=None):
        return self.predict_parts(blocks, x)["selected"]
