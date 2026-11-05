"""NOSE-lite block fusion (after arXiv:2604.10452, simplified for local CPU training).

NOSE projects each modality, removes from every adapter the component parallel to the
molecular anchor (hard Gram-Schmidt), penalises residual cosine overlap between subspaces
(soft orthogonality) and fuses with softmax weights. Here the "modalities" are the named
structure blocks, so each non-anchor block can only contribute information the anchor
representation does not already carry. No Qwen3 descriptor encoder or ESM-2 receptor
encoder is used; this is not a NOSE reproduction.
"""
from __future__ import annotations

import numpy as np
import torch
from torch import nn


class BlockScaler:
    """Train-only imputation/standardisation per block (fingerprint bits are left binary)."""

    def fit(self, blocks: dict[str, np.ndarray]):
        self.stats = {}
        for name, x in blocks.items():
            median = np.nanmedian(np.where(np.isfinite(x), x, np.nan), axis=0)
            median = np.where(np.isfinite(median), median, 0.0)
            filled = np.where(np.isfinite(x), x, median)
            binary = bool(np.isin(filled, (0, 1)).all())
            mean, std = (np.zeros(x.shape[1]), np.ones(x.shape[1])) if binary else (filled.mean(0), filled.std(0))
            self.stats[name] = (median, mean, np.where(std > 1e-8, std, 1.0))
        return self

    def transform(self, blocks: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
        out = {}
        for name, x in blocks.items():
            median, mean, std = self.stats[name]
            filled = np.where(np.isfinite(x), x, median)
            out[name] = np.clip((filled - mean) / std, -8, 8).astype(np.float32)
        return out


def gram_schmidt(adapter: torch.Tensor, anchor: torch.Tensor, eps: float = 1e-6) -> torch.Tensor:
    """Remove the component of each adapter row parallel to the matching anchor row."""
    coefficient = (adapter * anchor).sum(-1, keepdim=True) / (anchor.pow(2).sum(-1, keepdim=True) + eps)
    return adapter - coefficient * anchor


class BlockFusion(nn.Module):
    def __init__(self, dims: dict[str, int], anchor: str, width: int = 96, dropout: float = 0.2):
        super().__init__()
        if anchor not in dims:
            raise ValueError(f"Anchor block {anchor} is not among the fused blocks")
        self.names, self.anchor = list(dims), anchor
        self.projections = nn.ModuleDict({n: nn.Sequential(nn.Linear(d, width), nn.GELU(), nn.Dropout(dropout), nn.Linear(width, width))
                                          for n, d in dims.items()})
        # One logit per block, as in NOSE's three-weight fusion: few parameters, inspectable.
        self.gate_logits = nn.Parameter(torch.zeros(len(self.names)))
        self.norm = nn.LayerNorm(width)

    def forward(self, blocks: dict[str, torch.Tensor]):
        z = {n: self.projections[n](blocks[n]) for n in self.names}
        anchor = z[self.anchor]
        z = {n: (v if n == self.anchor else gram_schmidt(v, anchor)) for n, v in z.items()}
        weights = torch.softmax(self.gate_logits, 0)
        fused = sum(w * z[n] for w, n in zip(weights, self.names))
        return self.norm(fused), z

    def orthogonality_loss(self, z: dict[str, torch.Tensor]) -> torch.Tensor:
        unit = [nn.functional.normalize(v, dim=-1) for v in z.values()]
        terms = [(unit[i] * unit[j]).sum(-1).pow(2).mean() for i in range(len(unit)) for j in range(i + 1, len(unit))]
        return torch.stack(terms).mean() if terms else torch.zeros(())

    def gates(self) -> dict[str, float]:
        return dict(zip(self.names, torch.softmax(self.gate_logits.detach(), 0).tolist()))


class FusionNet(nn.Module):
    """Fusion encoder plus a task head producing `outputs` raw values."""

    def __init__(self, dims, anchor, outputs, width=96, dropout=0.2):
        super().__init__()
        self.fusion = BlockFusion(dims, anchor, width, dropout)
        self.head = nn.Sequential(nn.GELU(), nn.Dropout(dropout), nn.Linear(width, outputs))

    def forward(self, blocks):
        fused, z = self.fusion(blocks)
        return self.head(fused), fused, z


def to_tensors(blocks: dict[str, np.ndarray], index=None) -> dict[str, torch.Tensor]:
    return {n: torch.as_tensor(x if index is None else x[index]) for n, x in blocks.items()}


def train_fusion(blocks, loss_fn, outputs, anchor, *, epochs=60, batch_size=64, lr=2e-3, weight_decay=1e-4,
                 orth_weight=0.1, width=96, dropout=0.2, seed=0):
    """Generic minibatch trainer; `loss_fn(raw_output, batch_index)` returns the task loss."""
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    dims = {n: x.shape[1] for n, x in blocks.items()}
    net = FusionNet(dims, anchor, outputs, width, dropout)
    optimiser = torch.optim.AdamW(net.parameters(), lr=lr, weight_decay=weight_decay)
    schedule = torch.optim.lr_scheduler.OneCycleLR(optimiser, max_lr=lr, total_steps=epochs * max(1, int(np.ceil(len(next(iter(blocks.values()))) / batch_size))))
    n = len(next(iter(blocks.values())))
    tensors = to_tensors(blocks)
    net.train()
    for _ in range(epochs):
        order = rng.permutation(n)
        for start in range(0, n, batch_size):
            index = order[start:start + batch_size]
            if len(index) < 2:
                continue
            raw, _, z = net({k: v[index] for k, v in tensors.items()})
            loss = loss_fn(raw, index) + orth_weight * net.fusion.orthogonality_loss(z)
            optimiser.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(net.parameters(), 5.0)
            optimiser.step()
            schedule.step()
    net.eval()
    return net


@torch.no_grad()
def predict_fusion(net, blocks):
    raw, fused, _ = net(to_tensors(blocks))
    return raw.numpy(), fused.numpy()
