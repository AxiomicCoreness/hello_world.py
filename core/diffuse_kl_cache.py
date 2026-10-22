#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core/diffuse_kl_cache.py
Implementation of the DiffuseKLCache for entropy regularization.
"""

from __future__ import annotations

import hashlib
from typing import Any, List, Tuple

import numpy as np


class DiffuseKLCache:
    """
    Implements an entropy-regularized cache using KL divergence.
    Maps arbitrary entries to a fixed number of bins via hashing.
    """
    
    def __init__(self, M: int = 16, uniform_mix: float = 1e-3, eps: float = 1e-12):
        """
        Args:
            M (int): Number of bins in the cache distribution.
            uniform_mix (float): Amount of uniform distribution mixed in to prevent infinite KL.
            eps (float): Small epsilon for numerical stability.
        """
        self.M = M
        self.uniform_mix = uniform_mix
        self.eps = eps
        self.beta = 1.0  # Regularization weight, adjustable
        
        # Core counts
        self.counts = np.zeros(M, dtype=np.float64)
        self.total_entries = 0

    def add_entry(self, key: str, value: np.ndarray) -> None:
        """
        Adds an entry to the cache. The bin is determined by a hash of the key.
        """
        # Hash the key to a 32-bit integer using SHA-256
        h = hashlib.sha256(key.encode("utf-8")).digest()
        bin_idx = int.from_bytes(h[:4], "little") % self.M
        
        self.counts[bin_idx] += 1.0
        self.total_entries += 1

    def base_distribution(self) -> np.ndarray:
        """
        Returns the uniform base distribution.
        """
        return np.ones(self.M, dtype=np.float64) / self.M

    def cache_distribution(self) -> np.ndarray:
        """
        Returns the smoothed cache distribution.
        """
        p_base = self.base_distribution()
        
        if self.total_entries == 0:
            return p_base
            
        # Raw frequency
        p_raw = self.counts / self.total_entries
        
        # Mix with uniform base to prevent infinite KL divergence
        p_cache = (1.0 - self.uniform_mix) * p_raw + self.uniform_mix * p_base
        
        # Ensure it sums to 1.0
        return p_cache / p_cache.sum()

    def diffuse_kl(self) -> float:
        """
        Calculates the KL divergence between the cache distribution and the base distribution.
        D_KL(P || Q) = sum(P * log(P / Q))
        """
        p_cache = self.cache_distribution()
        p_base = self.base_distribution()
        
        # Add eps to avoid log(0)
        p_cache_safe = np.clip(p_cache, self.eps, None)
        p_base_safe = np.clip(p_base, self.eps, None)
        
        kl = np.sum(p_cache_safe * np.log(p_cache_safe / p_base_safe))
        
        # Due to numerical precision, KL might be a tiny negative number (e.g., -1e-16)
        return max(0.0, float(kl))

    def objective(self, logp: float) -> float:
        """
        Calculates the regularized objective.
        L = -logp + beta * KL
        """
        return -logp + self.beta * self.diffuse_kl()
