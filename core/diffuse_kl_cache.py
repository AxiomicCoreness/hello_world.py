"""
core/diffuse_kl_cache.py

Diffuse KL hashed cache implementation (Entry 616 materialised).

API: DiffuseKLCache(hash_entry, add_entry, cache_distribution, base_distribution,
                     diffuse_kl, objective, summary, health_report)

This implementation is deterministic, uses SHA3-256 modulo M, stable softmax,
and safe handling of p_base zeros (mix with small uniform prior).

Embedding dtype: numpy.float64
"""

import hashlib
from typing import Dict, List, Tuple, Optional

import numpy as np


class DiffuseKLCache:
    """φ-scaled KV cache with diffuse KL regularisation.

    Attributes:
        M: number of hash bins
        T: softmax temperature
        beta: regularisation weight
        eps: small smoothing to avoid log(0)
        uniform_mix: mixing weight for p_base smoothing
    """

    def __init__(self, M: int = 1024, T: float = 1.0, beta: float = 0.1,
                 eps: float = 1e-12, uniform_mix: float = 1e-6):
        self.M = int(M)
        self.T = float(T)
        self.beta = float(beta)
        self.eps = float(eps)
        self.uniform_mix = float(uniform_mix)

        # cache: map bin -> list of (entry_id, embedding)
        self.cache: Dict[int, List[Tuple[int, np.ndarray]]] = {}
        # ledger of bin indices (append-only)
        self.ledger: List[int] = []

    def hash_entry(self, entry: str) -> int:
        """SHA3-256 hash modulo M (deterministic)."""
        h = hashlib.sha3_256(entry.encode("utf-8")).hexdigest()
        return int(h, 16) % self.M

    def add_entry(self, entry: str, embedding: np.ndarray, entry_id: Optional[int] = None):
        """Add entry to cache and ledger. Embedding converted to float64.

        Args:
            entry: canonical string blob to be hashed
            embedding: numpy array (any dtype) — will be cast to float64
            entry_id: optional identifier, if None the bin is used as id
        """
        k = self.hash_entry(entry)
        emb = np.asarray(embedding, dtype=np.float64)
        eid = entry_id if entry_id is not None else k
        self.cache.setdefault(k, []).append((eid, emb))
        self.ledger.append(k)

    def _score_vector(self) -> np.ndarray:
        """Compute raw scores per bin (frequency-based)."""
        scores = np.zeros(self.M, dtype=np.float64)
        for k, entries in self.cache.items():
            scores[k] = float(len(entries))
        return scores

    def cache_distribution(self) -> np.ndarray:
        """P_cache(h): stable softmax of scores/T."""
        scores = self._score_vector()
        if self.T <= 0:
            raise ValueError("Temperature T must be > 0")
        scaled = scores / float(self.T)
        # stable softmax
        m = np.max(scaled)
        ex = np.exp(scaled - m)
        denom = np.sum(ex)
        if denom == 0:
            # fallback to uniform
            return np.ones(self.M, dtype=np.float64) / float(self.M)
        return ex / denom

    def base_distribution(self) -> np.ndarray:
        """P_base(h): empirical distribution over the ledger with smoothing."""
        counts = np.zeros(self.M, dtype=np.float64)
        for k in self.ledger:
            counts[k] += 1.0
        total = np.sum(counts)
        if total == 0:
            # no ledger entries -> uniform
            base = np.ones(self.M, dtype=np.float64) / float(self.M)
        else:
            base = counts / total
            # mix with small uniform prior to avoid zeros
            if self.uniform_mix > 0:
                base = (1.0 - self.uniform_mix) * base + self.uniform_mix * (np.ones(self.M) / float(self.M))
        # final clipping with eps
        base = np.maximum(base, self.eps)
        # renormalise
        base = base / np.sum(base)
        return base

    def diffuse_kl(self) -> float:
        """Compute D_KL^diffuse(P_cache || P_base)."""
        p_cache = self.cache_distribution()
        p_base = self.base_distribution()
        # mask where p_cache > 0 to avoid 0*log issues
        mask = p_cache > 0
        # safe division and log
        ratio = np.zeros_like(p_cache)
        ratio[mask] = p_cache[mask] / p_base[mask]
        # clip ratio to avoid nan
        ratio = np.maximum(ratio, self.eps)
        return float(np.sum(p_cache[mask] * np.log(ratio[mask])))

    def objective(self, trajectory_log_prob: float) -> float:
        """Agent improvement objective: log-prob minus beta * diffuse KL."""
        return float(trajectory_log_prob) - float(self.beta) * float(self.diffuse_kl())

    def summary(self) -> Dict:
        """Return a brief summary dict for health reporting."""
        p_cache = self.cache_distribution()
        p_base = self.base_distribution()
        top_cache_idx = int(np.argmax(p_cache))
        top_cache_mass = float(p_cache[top_cache_idx])
        return {
            "M": self.M,
            "entries": int(len(self.ledger)),
            "top_bin": top_cache_idx,
            "top_bin_mass": top_cache_mass,
            "diffuse_kl": self.diffuse_kl()
        }

    def health_report(self) -> Dict:
        return {
            "status": "ok",
            "summary": self.summary()
        }
