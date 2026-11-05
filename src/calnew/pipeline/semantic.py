"""Filtered descriptor transfer and a serializable downstream regression head."""
from __future__ import annotations

import numpy as np
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold

from .fusion import BlockScaler

SEMANTIC_BASE = ("rdkit", "transport", "hbond", "osmophore", "chain", "fingerprint")


class TorchDescriptorRegressor:
    """Small molecular adapter trained on descriptor vectors, without endpoint labels."""

    def __init__(self, seed=173, epochs=40):
        self.seed, self.epochs = seed, epochs

    def fit(self, x, y):
        import torch
        from torch import nn
        torch.manual_seed(self.seed)
        self.mean = y.mean(0).astype(np.float32)
        self.std = np.maximum(y.std(0), 1e-4).astype(np.float32)
        target = torch.as_tensor(((y-self.mean)/self.std).astype(np.float32))
        features = torch.as_tensor(x.astype(np.float32))
        self.model = nn.Sequential(nn.Linear(x.shape[1],256),nn.GELU(),nn.Dropout(0.15),
            nn.Linear(256,128),nn.GELU(),nn.Linear(128,y.shape[1]))
        optimizer = torch.optim.AdamW(self.model.parameters(),lr=1e-3,weight_decay=1e-3)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer,self.epochs)
        rng = np.random.default_rng(self.seed)
        self.model.train()
        for _ in range(self.epochs):
            for start in range(0,len(x),128):
                if start == 0:
                    order = rng.permutation(len(x))
                rows = order[start:start+128]
                loss = nn.functional.mse_loss(self.model(features[rows]),target[rows])
                optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(self.model.parameters(),5.0)
                optimizer.step()
            scheduler.step()
        self.model.eval()
        return self

    def predict(self,x):
        import torch
        with torch.inference_mode():
            values = self.model(torch.as_tensor(x.astype(np.float32))).numpy()
        return values*self.std+self.mean


class DescriptorTransfer:
    """Predict fixed projections of augmented descriptor profiles."""

    def __init__(self, molecules, labels, features, alpha=100.0, encoder="ridge", threads=8, term_vectors=None):
        self.connectivity = molecules.molecule_id.str.split("-").str[0].to_numpy()
        self.labels, self.features, self.alpha = labels, features, alpha
        self.encoder, self.threads = encoder, threads
        # Fixed projection: no data-dependent axes can disclose excluded descriptors.
        rng = np.random.default_rng(173)
        if term_vectors is None:
            projection = rng.normal(size=(labels.shape[1], 128)).astype(np.float32) / np.sqrt(128)
        else:
            if term_vectors.shape[0] != labels.shape[1] or not np.isfinite(term_vectors).all():
                raise ValueError("Text vectors do not match the descriptor vocabulary")
            # Center using word vocabulary only, independently of any molecular labels.
            centered = term_vectors - term_vectors.mean(0)
            projection = centered @ (rng.normal(size=(term_vectors.shape[1], 128)).astype(np.float32) / np.sqrt(128))
        self.targets = np.asarray(labels @ projection)
        self.targets /= np.maximum(np.sqrt(labels.getnnz(axis=1))[:, None], 1)

    def fit(self, excluded_ids):
        excluded = {str(i).split("-")[0] for i in excluded_ids}
        keep = ~np.isin(self.connectivity, list(excluded))
        scaler = BlockScaler().fit({"x": self.features[keep]})
        train = scaler.transform({"x": self.features[keep]})["x"]
        if self.encoder == "ridge":
            model = Ridge(alpha=self.alpha)
        elif self.encoder == "extra_trees":
            model = ExtraTreesRegressor(n_estimators=100, max_features=0.3, min_samples_leaf=4,
                n_jobs=self.threads, random_state=173)
        elif self.encoder == "mlp":
            model = TorchDescriptorRegressor()
        else:
            raise ValueError(f"Unknown transfer encoder: {self.encoder}")
        model.fit(train, self.targets[keep])
        return scaler, model, int(keep.sum())

    def predict(self, excluded_ids, task_features):
        scaler, model, count = self.fit(excluded_ids)
        test = scaler.transform({"x": task_features})["x"]
        predictions = model.predict(test).astype(np.float32)
        if not np.isfinite(predictions).all():
            raise ValueError("Non-finite descriptor transfer predictions")
        return predictions, count

    def crossfit(self, train_ids, held_ids, train_features, held_features, seed):
        predictions = np.zeros((len(train_ids), 128), np.float32)
        for tr, va in KFold(3, shuffle=True, random_state=seed).split(train_ids):
            predictions[va], _ = self.predict(list(held_ids) + list(train_ids[va]), train_features[va])
        if len(held_features):
            held, count = self.predict(held_ids, held_features)
        else:
            held = np.empty((0, 128), np.float32)
            count = int((~np.isin(self.connectivity, [str(i).split("-")[0] for i in held_ids])).sum())
        return predictions, held, count


class SemanticHead:
    """Fit endpoint labels using cross-fitted descriptor predictions only."""

    def fit(self, transfer, train_ids, held_ids, train_source, held_source,
            train_base, y, seed=300, threads=4):
        semantic, _, self.source_rows = transfer.crossfit(
            train_ids, held_ids, train_source, held_source[:0], seed)
        self.scaler, self.transfer = transfer.fit(held_ids)[:2]
        self.head = ExtraTreesRegressor(n_estimators=500, max_features=0.3,
            min_samples_leaf=2, n_jobs=threads, random_state=42)
        self.head.fit(np.column_stack([train_base, semantic]), y)
        return self

    def predict(self, source, base):
        semantic = self.transfer.predict(self.scaler.transform({"x": source})["x"])
        values = self.head.predict(np.column_stack([base, semantic]))
        if not np.isfinite(values).all():
            raise ValueError("Non-finite semantic head predictions")
        return values


def predict_pleasantness(run, smiles, dilution=1e-3, cache_root="data/features"):
    """Serve a trusted locally trained semantic benchmark bundle."""
    from pathlib import Path
    import joblib
    from ..chemistry import identify
    from .blocks import BlockCache
    from .stages import quality_features

    if not 0 < dilution <= 1:
        raise ValueError("Dilution must be in (0, 1]")
    bundle = joblib.load(Path(run) / "semantic-pleasantness.joblib")
    canonical = [identify(s).smiles for s in smiles]
    names = sorted(set(SEMANTIC_BASE) | set(bundle["quality_blocks"]))
    blocks = BlockCache(Path(cache_root)).blocks(names, canonical)
    x = np.full((len(canonical), 1), np.log10(dilution))
    probabilities, _, direction = bundle["quality"].predict({n: blocks[n] for n in bundle["quality_blocks"]})
    enriched = {**blocks, "quality": quality_features(probabilities), "direction": direction}
    pick = {n: enriched[n] for _, names in bundle["hedonic"].members for n in names}
    v2 = bundle["hedonic"].predict(pick, columns=x)
    base = np.column_stack([blocks[n] for n in SEMANTIC_BASE] + [x])
    source = np.column_stack([blocks["rdkit"], blocks["fingerprint"]])
    semantic = bundle["semantic"].predict(source, base)
    return {"run": str(run), "endpoint": "Keller pleasantness, higher-concentration stimulus",
        "validated_concentration_axis": "nominal log10 paraffin-oil dilution (Keller protocol)",
        "molecules": [{"smiles": s, "dilution": dilution,
            "pleasantness_0_100": float((a + b) / 2), "v2": float(a), "semantic": float(b)}
            for s, a, b in zip(canonical, v2, semantic)]}
