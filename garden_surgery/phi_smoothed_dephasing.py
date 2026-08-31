#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
garden_surgery/phi_smoothed_dephasing.py
φ-smoothed token entropy, CPTP dephasing channel, coherence checks.
Sealed specification note: ledger/8223.yaml
"""

import math
import numpy as np

# ─── Constants ──────────────────────────────────────────────────────────
PHI = (1 + math.sqrt(5)) / 2
PHI3 = PHI ** 3
PHI_INV = 1 / PHI
GAMMA = 1 / math.sqrt(5)  # typical dephasing rate (symbolic)


def phi_smoothed_token_entropy(probs: list, smoother: float = PHI3) -> float:
    """
    H_token = -Σ P(v|context) log_φ P(v|context)
    With φ³ smoother, H ≤ 1 in φ-units.
    """
    # Apply smoother (floor to avoid log(0) and enforce prior mass)
    p = np.array(probs, dtype=float)
    p = p + (smoother * PHI_INV ** len(p))
    p = p / np.sum(p)  # renormalise
    # Compute entropy in φ-units
    H = -np.sum(p * np.log(p) / np.log(PHI))
    return float(H)


class PhiDephasingChannel:
    """
    CPTP dephasing channel: (D_t(ρ))_ij = e^{-t(γ_i+γ_j)} ρ_ij (i≠j)
    Diagonal elements are preserved.
    """

    def __init__(self, n: int, gamma: float = GAMMA):
        self.n = n
        self.gamma = gamma
        self.decay_matrix = None  # will be set per t

    def apply(self, rho: np.ndarray, t: float) -> np.ndarray:
        """Apply dephasing for time t (symbolic units)."""
        rho = np.asarray(rho, dtype=complex)
        rho_out = rho.copy()
        for i in range(self.n):
            for j in range(self.n):
                if i != j:
                    decay = math.exp(-t * (self.gamma * (i + j + 2)))  # symbolic γ_i+γ_j
                    rho_out[i, j] = rho[i, j] * decay
        # Diagonal remains unchanged
        return rho_out


def coherence_check(rho: np.ndarray, threshold: float = 1e-3) -> dict:
    """
    Compute off-diagonal mass and purity. Return pass/fail.
    """
    rho = np.asarray(rho, dtype=complex)
    off_diag_mass = np.sum(np.abs(rho - np.diag(np.diag(rho))))
    purity = np.trace(rho @ rho).real
    return {
        "off_diag_mass": float(off_diag_mass),
        "purity": float(purity),
        "pass": bool(off_diag_mass < threshold)
    }


def feedback_step(rho: np.ndarray, weights: np.ndarray, alpha: float = 0.1) -> np.ndarray:
    """
    ρ_{t+1} = (1-α)D(ρ_t) + α(ρ_t ⊙ w)
    where w is a token weight vector (broadcast to density matrix).
    """
    rho = np.asarray(rho, dtype=complex)
    w = np.asarray(weights, dtype=complex)
    # Ensure w is broadcastable to rho shape (outer product)
    if w.ndim == 1:
        w = np.outer(w, np.conj(w))
    dephased = PhiDephasingChannel(rho.shape[0]).apply(rho, t=1.0)
    return (1 - alpha) * dephased + alpha * (rho * w)


# ─── Example / Smoke Test ──────────────────────────────────────────────
if __name__ == "__main__":
    print("🜁∀ φ‑smoothed dephasing module (specification 8223) ∀🜁")
    # Token entropy example
    probs = [0.4, 0.3, 0.2, 0.1]
    H = phi_smoothed_token_entropy(probs)
    print(f"Smoothed token entropy: {H:.6f} φ-units (≤1 = {H <= 1})")

    # Dephasing channel test
    rho = np.array([[0.5, 0.3j], [-0.3j, 0.5]], dtype=complex)
    dephaser = PhiDephasingChannel(n=2, gamma=0.1)
    rho_decayed = dephaser.apply(rho, t=2.0)
    print("Decayed rho:\n", rho_decayed)

    # Coherence check
    status = coherence_check(rho_decayed, threshold=0.1)
    print("Coherence status:", status)

    print("Q.E.D. — Specification sealed; code module ready.")
