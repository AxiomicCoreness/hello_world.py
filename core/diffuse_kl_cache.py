#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pytest suite for DiffuseKLCache — entropy regularization cache.
"""

import math
import sys
from pathlib import Path
from typing import Dict, Any, Union

import pytest
import numpy as np

# --- Path setup ---
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# --- Imports ---
try:
    from core.diffuse_kl_cache import DiffuseKLCache
except ImportError:
    DiffuseKLCache = None

# --- Cryptography (Soft Check) ---
try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


def test_empty_cache_returns_uniform_distributions():
    if DiffuseKLCache is None:
        pytest.skip("DiffuseKLCache not available")

    c = DiffuseKLCache(M=16)
    p_cache = c.cache_distribution()
    p_base = c.base_distribution()

    assert p_cache.shape == (16,), "Cache distribution shape mismatch"
    assert p_base.shape == (16,), "Base distribution shape mismatch"
    assert pytest.approx(1.0, rel=1e-12) == p_cache.sum(), "Cache distribution sum != 1"
    assert pytest.approx(1.0, rel=1e-12) == p_base.sum(), "Base distribution sum != 1"


def test_concentrated_cache_has_positive_kl():
    if DiffuseKLCache is None:
        pytest.skip("DiffuseKLCache not available")

    c = DiffuseKLCache(M=8)
    for i in range(20):
        # Force the same string hash
        c.add_entry("entry-same", np.array([1.0]))

    kl = c.diffuse_kl()
    assert kl >= 0.0, f"KL divergence should be >= 0, got {kl}"
    assert np.isfinite(kl), f"KL divergence should be finite, got {kl}"


def test_smoothing_prevents_infinite_kl():
    if DiffuseKLCache is None:
        pytest.skip("DiffuseKLCache not available")

    c = DiffuseKLCache(M=4, uniform_mix=1e-3, eps=1e-12)
    c.add_entry("only-one", np.array([0.1]))

    kl = c.diffuse_kl()
    assert np.isfinite(kl), f"KL divergence should be finite with smoothing, got {kl}"


def test_objective_decreases_with_beta():
    if DiffuseKLCache is None:
        pytest.skip("DiffuseKLCache not available")

    c = DiffuseKLCache(M=8)
    for i in range(10):
        c.add_entry("same-entry", np.array([0.0]))

    logp = -5.0

    # Beta = 0 (no regularization)
    c.beta = 0.0
    obj0 = c.objective(logp)

    # Beta = 1 (full regularization)
    c.beta = 1.0
    obj1 = c.objective(logp)

    # With positive beta, the objective should be <= the unregularized one
    assert obj1 <= obj0, f"Regularized objective {obj1} should be <= unregularized {obj0}"


def test_cache_distribution_after_additions():
    if DiffuseKLCache is None:
        pytest.skip("DiffuseKLCache not available")

    c = DiffuseKLCache(M=8)
    p0 = c.cache_distribution()
    assert pytest.approx(p0.sum(), rel=1e-12) == 1.0

    for i in range(10):
        c.add_entry(f"entry-{i}", np.array([0.5]))

    p1 = c.cache_distribution()
    assert pytest.approx(p1.sum(), rel=1e-12) == 1.0
    assert not np.allclose(p0, p1), "Cache distribution should change after additions"


def test_kl_non_negative():
    if DiffuseKLCache is None:
        pytest.skip("DiffuseKLCache not available")

    c = DiffuseKLCache(M=16)
    for seed in range(5):
        np.random.seed(seed)
        values = np.random.randn(5)
        for i, val in enumerate(values):
            c.add_entry(f"rand-{seed}-{i}", np.array([val]))

        kl = c.diffuse_kl()
        assert kl >= 0.0, f"KL divergence should be >= 0, got {kl}"
        assert np.isfinite(kl), f"KL divergence should be finite, got {kl}"
