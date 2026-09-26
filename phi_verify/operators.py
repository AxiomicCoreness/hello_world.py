"""Lindblad operators and the learning kernel.

DIM = 7 is inferred from the entropy test: entropies in the log
converge toward ln(7) ≈ 1.9459101490553135, and the last logged
value (1.9459004343383905) is within 1e-5 of that ceiling.
"""
import numpy as np

from .constants import PHI, gamma_rates

DIM = 7


def lindblad_ops(dim: int = DIM, n: int = 7):
    """
    n diagonal Lindblad operators. σ_z-like on consecutive index pairs
    so that the D(ρ) update is trace-preserving and Hermiticity-preserving.
    """
    ops = []
    for k in range(n):
        L = np.zeros((dim, dim), dtype=complex)
        i = k % dim
        j = (k + 1) % dim
        L[i, i] =  1.0
        L[j, j] = -1.0
        ops.append(L)
    return ops


def attenuation(rho: np.ndarray, gammas, dt: float) -> np.ndarray:
    """
    D(ρ) = ρ + dt · Σ_k γ_k ( L_k ρ L_k† − ½ {L_k† L_k, ρ} )
    """
    out = rho.copy()
    for gamma, L in zip(gammas, lindblad_ops(rho.shape[0])):
        Ld = L.conj().T
        anti = Ld @ L @ rho + rho @ Ld @ L
        out = out + dt * gamma * (L @ rho @ Ld - 0.5 * anti)
    return out


def learning_kernel(dim: int = DIM) -> np.ndarray:
    """
    w — elementwise φ-harmonic weight matrix.
    Diagonal, weights φ^(-floor(k/2)), normalized so Tr(w) = 1.
    """
    diag = np.array([PHI ** (-(k // 2)) for k in range(dim)])
    diag = diag / diag.sum()
    return np.diag(diag).astype(complex)
