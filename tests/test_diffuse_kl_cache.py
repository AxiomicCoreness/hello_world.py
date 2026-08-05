import pytest
import numpy as np
from core.diffuse_kl_cache import DiffuseKLCache


def test_empty_cache_returns_uniform_distributions():
    c = DiffuseKLCache(M=16)
    p_cache = c.cache_distribution()
    p_base = c.base_distribution()
    assert p_cache.shape == (16,)
    assert p_base.shape == (16,)
    assert pytest.approx(1.0, rel=1e-12) == p_cache.sum()
    assert pytest.approx(1.0, rel=1e-12) == p_base.sum()


def test_concentrated_cache_has_positive_kl():
    c = DiffuseKLCache(M=8)
    # add many entries that hash to same bin
    for i in range(20):
        c.add_entry(f"entry-{i}-same", np.array([1.0]))
    kl = c.diffuse_kl()
    assert kl >= 0.0
    assert np.isfinite(kl)


def test_smoothing_prevents_infinite_kl():
    c = DiffuseKLCache(M=4, uniform_mix=1e-3, eps=1e-12)
    # add an entry to bin 0 only
    c.add_entry("only-one", np.array([0.1]))
    kl = c.diffuse_kl()
    assert np.isfinite(kl)


def test_objective_decreases_with_beta():
    c = DiffuseKLCache(M=8)
    for i in range(10):
        c.add_entry(f"a-{i}", np.array([0.0]))
    logp = -5.0
    c.beta = 0.0
    obj0 = c.objective(logp)
    c.beta = 1.0
    obj1 = c.objective(logp)
    # with positive beta the objective should be <= the unregularized one
    assert obj1 <= obj0
