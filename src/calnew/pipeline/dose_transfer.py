"""A structure-only Ravia endpoint head using Keller dose-response proxies."""
import numpy as np

from .semantic import SEMANTIC_BASE

REFERENCE_DOSES = (-5., -3., -1.)


class RaviaDoseTransfer:
    """Equal blend of the established Ravia head and a cross-fitted dose proxy.

    The ridge is fitted on training proxy values computed without their molecular
    connectivity in the Keller source. At prediction time the source tree uses
    the complete eligible source cohort for that fit. Fixed Keller reference
    doses are latent inputs; they do not constitute a Ravia dilution-response.
    """
    dataset = "ravia"
    recipe = "blend_proxy_ridge"

    def __init__(self, baseline, source_model, ridge):
        self.baseline, self.source_model, self.ridge = baseline, source_model, ridge

    @property
    def feature_names(self):
        return sorted(set(SEMANTIC_BASE) | {n for _, names in self.baseline.members for n in names})

    def predict_parts(self, blocks, x=None):
        if x is not None:
            raise ValueError("Ravia dose transfer predicts a single endpoint, without a dilution input")
        n = len(blocks["rdkit"])
        values = np.column_stack([self.source_model.predict(blocks, np.full(n, dose)) for dose in REFERENCE_DOSES])
        baseline = np.clip(self.baseline.predict(blocks), 0, 100)
        candidate = np.clip(self.ridge.predict(values), 0, 100)
        selected = (baseline+candidate)/2
        if not np.isfinite(selected).all():
            raise ValueError("Non-finite Ravia dose-transfer prediction")
        return {"baseline": baseline, "candidate": candidate, "selected": selected}

    def predict(self, blocks, x=None):
        return self.predict_parts(blocks, x)["selected"]
