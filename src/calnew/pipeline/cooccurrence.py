"""Descriptor co-occurrence transfer learned from an endpoint-disjoint source."""
import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.feature_extraction.text import TfidfTransformer
from .fusion import BlockScaler


def direction_features(values):
    values = np.asarray(values, dtype=np.float64)
    if values.ndim != 2 or not np.isfinite(values).all():
        raise ValueError("Invalid latent descriptor representation")
    norms = np.linalg.norm(values,axis=1)
    return np.column_stack([values/np.maximum(norms[:,None],1e-12),norms])


class CooccurrenceTransfer:
    """TF-IDF/SVD axes use source associations only; source trees use structures.

    Unlike generic language vectors, the axes describe actual descriptor
    co-occurrence in the released augmented corpus. No endpoint labels fit them.
    """
    def fit(self,features,labels):
        if len(features)!=labels.shape[0] or labels.shape[1]<64:
            raise ValueError("Misaligned source matrix")
        self.tfidf=TfidfTransformer(norm="l2")
        weighted=self.tfidf.fit_transform(labels)
        self.svd=TruncatedSVD(n_components=64,n_iter=7,random_state=173)
        targets=self.svd.fit_transform(weighted).astype(np.float32)
        self.target_mean=targets.mean(0)
        self.target_sd=np.maximum(targets.std(0),1e-4)
        self.scaler=BlockScaler().fit({"x":features})
        self.model=ExtraTreesRegressor(n_estimators=150,max_features=.3,
            min_samples_leaf=4,n_jobs=2,random_state=173).fit(
                self.scaler.transform({"x":features})["x"],
                (targets-self.target_mean)/self.target_sd)
        return self

    def predict(self,features):
        result=self.model.predict(self.scaler.transform({"x":features})["x"])*self.target_sd+self.target_mean
        if result.shape!=(len(features),64) or not np.isfinite(result).all():
            raise ValueError("Invalid co-occurrence prediction")
        return result
