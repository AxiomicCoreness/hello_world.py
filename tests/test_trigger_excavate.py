#!/usr/bin/env python3
"""Hard-fail tests for trigger excavation. No MCP. No secret values."""

from garden_surgery.trigger_excavate import (
    KAPPA_DECLARED,
    diagnostic_scalars,
    golden_hash,
    kappa_decomposition,
)


def test_golden_hash_stable():
    assert golden_hash("garden") == golden_hash("garden")
    assert len(golden_hash("garden")) == 16


def test_diagnostic_finite():
    d = diagnostic_scalars()
    assert d["k_eff"] > 0
    assert d["F_eff"] > 0
    assert abs(d["W"] - 6.491) < 1e-12
    assert abs(d["fidelity_pct"] - 98.4) < 1e-12


def test_kappa_is_fitted_not_free():
    k = kappa_decomposition()
    assert abs(k["reconstructed"] - KAPPA_DECLARED) < 1e-12
    assert abs(k["phi4_sqrt7"] - 18.134249263375494) < 1e-9
    # χ is a residual; do not pretend it is 1
    assert 0.6 < k["chi_umbral_fitted"] < 0.8


if __name__ == "__main__":
    test_golden_hash_stable()
    test_diagnostic_finite()
    test_kappa_is_fitted_not_free()
    print("test_trigger_excavate: PASS")
