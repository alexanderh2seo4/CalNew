"""Source-local IDF descriptor transfer, with no endpoint-label fitting."""
from __future__ import annotations

import hashlib

import numpy as np
from sklearn.ensemble import ExtraTreesRegressor

from .fusion import BlockScaler


def array_sha256(value):
    """Content identity includes dtype/shape and preserves missing values."""
    value = np.ascontiguousarray(value)
    h = hashlib.sha256()
    h.update(str(value.dtype).encode())
    h.update(str(value.shape).encode())
    h.update(value.tobytes())
    return h.hexdigest()


class BalancedDescriptorTransfer:
    """Two fixed representations learned solely from allowed source molecules.

    IDF = log((1 + source rows)/(1 + source document frequency)) + 1.
    ``idf_average`` projects each molecule's IDF-weighted L1 descriptor average.
    ``idf_unit`` gives the corresponding projected vector unit Euclidean norm.
    Term projection depends on generic word embeddings and a fixed random seed;
    frequencies are recomputed after every source connectivity exclusion.
    """

    REPRESENTATIONS = ("idf_average", "idf_unit")

    def __init__(self, molecules, labels, features, term_vectors, threads=2):
        self.ids = molecules.molecule_id.to_numpy(dtype=str)
        self.connectivity = np.array([m.split("-")[0] for m in self.ids])
        self.labels = labels.tocsr(copy=True)
        self.labels.sum_duplicates()
        self.labels.eliminate_zeros()
        self.labels.data[:] = 1
        self.features = np.asarray(features)
        self.threads = threads
        vectors = np.asarray(term_vectors, np.float32)
        if (len(self.ids) != self.labels.shape[0] or len(self.ids) != len(self.features)
                or vectors.ndim != 2 or len(vectors) != self.labels.shape[1]
                or not np.isfinite(vectors).all()):
            raise ValueError("Balanced descriptor source IDs/features/vocabulary mismatch")
        rng = np.random.default_rng(173)
        self.projection = (vectors-vectors.mean(0)) @ (
            rng.normal(size=(vectors.shape[1], 128)).astype(np.float32)/np.sqrt(128))

    def source_targets(self, excluded_ids, representation):
        if representation not in self.REPRESENTATIONS:
            raise ValueError("Unknown balanced descriptor representation")
        forbidden = {str(m).split("-")[0] for m in excluded_ids}
        keep = ~np.isin(self.connectivity, sorted(forbidden))
        if not keep.any() or set(self.connectivity[keep]) & forbidden:
            raise ValueError("Empty source or held connectivity entered balanced source")
        allowed = self.labels[keep]
        # Critically, excluded association rows never enter this calculation.
        df = np.asarray((allowed > 0).sum(axis=0)).ravel()
        idf = (np.log((1+int(keep.sum()))/(1+df))+1).astype(np.float32)
        weighted = allowed.multiply(idf).tocsr()
        mass = np.asarray(weighted.sum(axis=1)).ravel()
        if (mass <= 0).any():
            raise ValueError("Allowed source molecule has no descriptor associations")
        probabilities = weighted.multiply(1/mass[:, None]).tocsr()
        if not np.allclose(np.asarray(probabilities.sum(axis=1)).ravel(), 1, atol=1e-5):
            raise ValueError("IDF descriptor probability weights do not sum to one")
        target = np.asarray(probabilities @ self.projection, np.float32)
        if representation == "idf_unit":
            norms = np.linalg.norm(target, axis=1, keepdims=True)
            target /= np.maximum(norms, 1e-12)
            actual = np.linalg.norm(target, axis=1)
            if not np.allclose(actual[norms.ravel() > 1e-12], 1, atol=1e-5):
                raise ValueError("IDF projected source targets are not unit vectors")
        if not np.isfinite(target).all():
            raise ValueError("Non-finite balanced source targets")
        audit = {"representation": representation, "source_rows": int(keep.sum()),
            "excluded_connectivities": sorted(forbidden), "held_connectivity_overlap": [],
            "source_ids_sha256": array_sha256(self.ids[keep]), "idf_sha256": array_sha256(idf),
            "targets_sha256": array_sha256(target), "target_shape": list(target.shape),
            "idf_range": [float(idf.min()), float(idf.max())],
            "target_norm_range": [float(np.linalg.norm(target, axis=1).min()),
                float(np.linalg.norm(target, axis=1).max())],
            "descriptor_weights_sum_one_verified": True,
            "idf_uses_allowed_source_only": True}
        return keep, target, idf, audit

    def fit(self, excluded_ids, representation):
        keep, target, _, audit = self.source_targets(excluded_ids, representation)
        scaler = BlockScaler().fit({"x": self.features[keep]})
        train = scaler.transform({"x": self.features[keep]})["x"]
        model = ExtraTreesRegressor(n_estimators=100, max_features=.3,
            min_samples_leaf=4, n_jobs=self.threads, random_state=173).fit(train, target)
        return scaler, model, audit

    @staticmethod
    def predict(model, task_features):
        scaler, learner, _ = model
        values = learner.predict(scaler.transform({"x": task_features})["x"]).astype(np.float32)
        if values.shape != (len(task_features), 128) or not np.isfinite(values).all():
            raise ValueError("Non-finite/misaligned balanced source predictions")
        return values


def verify_balanced_targets():
    """Numerical exclusion test: changing forbidden labels cannot alter IDF/targets."""
    import pandas as pd
    from scipy import sparse
    molecules = pd.DataFrame({"molecule_id": ["A-X", "A-Y", "B-X", "C-X"]})
    labels = sparse.csr_matrix([[1, 1, 0, 0], [0, 1, 1, 0],
        [1, 0, 0, 1], [0, 0, 1, 1]], dtype=np.float32)
    words = np.eye(4, dtype=np.float32)
    source = BalancedDescriptorTransfer(molecules, labels, np.ones((4, 2)), words)
    modified = labels.toarray()
    modified[:2] = [[0, 0, 0, 1], [1, 1, 1, 1]]
    other = BalancedDescriptorTransfer(molecules, sparse.csr_matrix(modified), np.ones((4, 2)), words)
    for name in source.REPRESENTATIONS:
        keep, target, idf, audit = source.source_targets(["A-OTHER"], name)
        keep2, target2, idf2, _ = other.source_targets(["A-OTHER"], name)
        if not (np.array_equal(keep, [False, False, True, True])
                and np.array_equal(keep, keep2) and np.array_equal(target, target2)
                and np.array_equal(idf, idf2) and audit["source_rows"] == 2):
            raise ValueError("Forbidden source labels influenced balanced targets")
    return {"same_connectivity_variants_excluded": True,
        "excluded_label_perturbation_leaves_idf_and_targets_identical": True,
        "both_normalization_assertions_passed": True}
