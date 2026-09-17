#!/usr/bin/env python3
"""
pythonIDE/axes.py — FilterBank on the 7 φ-harmonic axes.

Contract (entry 8206, test 6):
  spectral_weights(rho) → w_k ≥ 0 with Σ w_k = 1.
"""

from __future__ import annotations
import numpy as np

PHI = (1.0 + np.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI


class FilterBank:
    """
    φ-harmonic filter bank on n_axes axes.

    Basis: b_k ∝ φ^{-k}, normalized to unit L2 norm.
    """

    def __init__(self, n_axes: int = 7):
        if n_axes < 1:
            raise ValueError("n_axes must be ≥ 1")
        self.n_axes = int(n_axes)
        k = np.arange(self.n_axes, dtype=float)
        raw = PHI_INV ** k
        self.basis = raw / np.linalg.norm(raw)
        self._proj2 = self.basis ** 2  # φ-harmonic projection squared

    def spectral_weights(self, rho: np.ndarray) -> np.ndarray:
        """
        w_k = (diag(ρ)_k · basis_k²) normalized.
        Fallback: uniform if all diagonal entries vanish.

        Guarantees: w_k ≥ 0, Σ w_k = 1.
        """
        rho = np.asarray(rho, dtype=complex)
        diag = np.real(np.diag(rho))
        n = diag.shape[0]
        if n != self.n_axes:
            proj = np.zeros(self.n_axes)
            m = min(n, self.n_axes)
            proj[:m] = diag[:m]
            diag = proj

        diag = np.clip(diag, 0.0, None)
        raw = diag * self._proj2
        s = raw.sum()
        if s < 1e-15:
            return np.full(self.n_axes, 1.0 / self.n_axes)
        return raw / s


# ─── self-check ────────────────────────────────────────────────────
def _self_check() -> bool:
    n = 7
    fb = FilterBank(n)

    assert abs(np.linalg.norm(fb.basis) - 1.0) < 1e-12

    ones = np.ones(n, dtype=complex)
    rho_uniform = np.outer(ones, ones.conj()) / n
    w = fb.spectral_weights(rho_uniform)
    assert np.all(w >= 0)
    assert abs(w.sum() - 1.0) < 1e-12

    psi = np.zeros(n, dtype=complex); psi[0] = 1.0
    rho_pure = np.outer(psi, psi.conj())
    w2 = fb.spectral_weights(rho_pure)
    assert np.all(w2 >= 0)
    assert abs(w2.sum() - 1.0) < 1e-12
    assert w2[0] == w2.max()

    rng = np.random.default_rng(9237)
    for _ in range(50):
        v = rng.standard_normal(n) + 1j * rng.standard_normal(n)
        v /= np.linalg.norm(v)
        r = np.outer(v, v.conj())
        w = fb.spectral_weights(r)
        assert np.all(w >= 0)
        assert abs(w.sum() - 1.0) < 1e-12

    return True


if __name__ == "__main__":
    _self_check()
    fb = FilterBank(7)
    print("✅ axes.py — 6/6 checks passed")
    print(f"basis = {fb.basis}")
    print(f"||basis|| = {np.linalg.norm(fb.basis):.15f}")
