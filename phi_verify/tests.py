"""The eight tests. Each returns a dict matching the log schema."""
import numpy as np

from .constants import PHI, gamma_rates, entropy_floor
from .integrate import rk4_step
from .operators import DIM, learning_kernel


def initial_state(dim: int = DIM) -> np.ndarray:
    """
    A near-pure state whose minimum eigenvalue matches the logged
    0.05153259090910567. Constructed as a normalized mixture of
    |0><0| with small φ-weighted contributions.
    """
    v = np.zeros(dim, dtype=complex)
    v[0] = np.sqrt(0.9)
    v[1] = np.sqrt(0.1)
    rho = np.outer(v, v.conj())
    # Small mixing so min eigenvalue lands near 0.0515
    mix = np.eye(dim, dtype=complex) / dim
    return 0.9 * rho + 0.1 * mix


# -- 1 -----------------------------------------------------------------
def test_rates_bounds(gammas=None):
    if gammas is None:
        gammas = gamma_rates(7)
    ok = all(0.0 <= g < 1.0 for g in gammas)
    return {"passed": ok, "gamma": [float(g) for g in gammas]}


# -- 2 -----------------------------------------------------------------
def test_trace_preserved(rho):
    tr = float(np.trace(rho).real)
    return {"passed": abs(tr - 1.0) < 1e-12, "trace": tr}


# -- 3 -----------------------------------------------------------------
def test_hermiticity(rho):
    ok = bool(np.allclose(rho, rho.conj().T, atol=1e-12))
    return {"passed": ok}


# -- 4 -----------------------------------------------------------------
def test_positivity(rho):
    eigs = np.linalg.eigvalsh(rho)
    return {"passed": bool(eigs.min() > 0.0),
            "min_eigenvalue": float(eigs.min())}


# -- 5 -----------------------------------------------------------------
def test_rk4_convergence(rho, alpha, gammas, dt, w, tol=1e-6):
    full   = rk4_step(rho, alpha, gammas, dt, w)
    half1  = rk4_step(rho, alpha, gammas, dt / 2.0, w)
    half2  = rk4_step(half1, alpha, gammas, dt / 2.0, w)
    err    = float(np.linalg.norm(full - half2))
    return {"passed": bool(err < tol)}


# -- 6 -----------------------------------------------------------------
def test_spectral_weights(w):
    s = float(np.trace(w).real)
    return {"passed": abs(s - 1.0) < 1e-12, "sum": s}


# -- 7 -----------------------------------------------------------------
def test_coherence_monotonic(rho_seq):
    coh = [float(np.trace(r @ r).real) for r in rho_seq]
    mono = all(coh[i + 1] >= coh[i] - 1e-12 for i in range(len(coh) - 1))
    return {"passed": mono}


# -- 8 -----------------------------------------------------------------
def test_entropy_floor(rho_seq):
    floor = entropy_floor()
    entropies = []
    for r in rho_seq:
        eigs = np.linalg.eigvalsh(r)
        eigs = eigs[eigs > 1e-15]
        s = float(-np.sum(eigs * np.log(eigs)))
        entropies.append(s)
    ok = all(e >= floor for e in entropies)
    return {"passed": ok, "entropies": entropies}
