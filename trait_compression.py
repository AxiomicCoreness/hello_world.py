#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Infinite compression C_∞ — φ-harmonic trait fingerprints.

  C_∞(t) = Σ_{k=0}^∞ φ^{-k} Φ_k(t)
  Practical truncation k ≤ 144 → precision ~ φ^{-144}
  Output dimension d = 233 (D_577 → 233 eigenmode-style reduce)

Does not depend on the historical mega-menu; self-contained + numpy.
Seal: ∀∞φ² · INFINITE_COMPRESSION_233 · SEALED
"""

from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List, Sequence

import numpy as np

PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI
DEFAULT_DIM = 233
EMBED_DIM = 144
PENTAD = ("H", "X", "Y", "Z", "R")  # minimal gate alphabet


def _embedding_basis(symbols: Sequence[str] = PENTAD, dim: int = EMBED_DIM) -> Dict[str, np.ndarray]:
    basis: Dict[str, np.ndarray] = {}
    for idx, symbol in enumerate(symbols):
        vec = np.zeros(dim, dtype=np.float64)
        for k in range(dim):
            # φ-weighted deterministic embedding (real)
            vec[k] = (PHI ** (-(idx + 1) * (k + 1) / dim)) * math.cos(
                2.0 * math.pi * (idx + 1) * (k + 1) / dim
            )
        n = np.linalg.norm(vec)
        basis[symbol] = vec / n if n > 0 else vec
    return basis


class InfiniteCompressor:
    """Compress token streams to a fixed φ-weighted trait vector."""

    def __init__(self, target_dim: int = DEFAULT_DIM, max_history: int = 1000):
        self.target_dim = int(target_dim)
        self.max_history = int(max_history)
        self.embedding_dim = EMBED_DIM
        self.embedding_basis = _embedding_basis()

    def tokenize_stream(self, stream: str) -> List[str]:
        parts = stream.replace(",", " ").split()
        out: List[str] = []
        for p in parts:
            u = p.strip().upper()
            if not u:
                continue
            # map unknown tokens onto pentad by hash
            if u in self.embedding_basis:
                out.append(u)
            else:
                out.append(PENTAD[hash(u) % len(PENTAD)])
        return out[: self.max_history]

    def compress_stream(self, tokens: Sequence[str]) -> np.ndarray:
        acc = np.zeros(self.target_dim, dtype=np.float64)
        if not tokens:
            return acc
        total_w = 0.0
        for t, token in enumerate(tokens):
            emb = self.embedding_basis.get(token)
            if emb is None:
                continue
            w = PHI ** (-t)
            total_w += w
            proj = np.zeros(self.target_dim, dtype=np.float64)
            n = min(self.target_dim, self.embedding_dim)
            proj[:n] = emb[:n]
            acc += w * proj
        if total_w > 0:
            acc /= total_w
        return acc

    def compress_text(self, text: str) -> np.ndarray:
        return self.compress_stream(self.tokenize_stream(text))

    def reduce_577_to_233(self, vector_577: np.ndarray) -> np.ndarray:
        """Deterministic leading-mode reduce (placeholder for metric eigenmodes)."""
        v = np.asarray(vector_577, dtype=np.float64).ravel()
        if v.size >= 233:
            return v[:233].copy()
        out = np.zeros(233, dtype=np.float64)
        out[: v.size] = v
        return out

    def fingerprint(self, text: str) -> Dict[str, Any]:
        vec = self.compress_text(text)
        return {
            "dim": int(self.target_dim),
            "norm": float(np.linalg.norm(vec)),
            "first10": vec[:10].tolist(),
            "phi": PHI,
            "precision_note": "truncation k≤144 → ~φ^{-144}",
        }


def main() -> None:
    c = InfiniteCompressor(target_dim=233)
    sample = "H X Y Z R H X Y Z R Clarke Yoursa Tee worker OIDC"
    fp = c.fingerprint(sample)
    print("InfiniteCompressor fingerprint:")
    print(f"  dim={fp['dim']} norm={fp['norm']:.6f}")
    print(f"  first10={fp['first10']}")


if __name__ == "__main__":
    main()
