#!/usr/bin/env python3
"""evolanus_flow.py: dense small-n construction of H0 and an exact unitary step.

Relation to other files on main (checked, not assumed):
  - scripts/eridanus_flow.py has step(phi_state, dtau) -> float and
    run(n, ...) -> dict, where n is a position label. This module does NOT
    share that interface: here step(state, dtau, n) -> dict and n is the
    number of sites (Hilbert dimension 2**n), not a position label.
  - tilelang/evolanus_flow.py (surface 4) builds the same H0 with a dense
    ceiling of 8 and a truncated Taylor step. This file is independent of it.
  - tilelang/eridanus_dual.py names Phi(x) = (i/phi)(N(x)A - A(x)N)x only.

No ledger write, no seal. A flow run is not a ledger event.

Generator:

    H0(n) = phi^2 * sum_i Z_i  +  phi^-2 * sum_{i<j} X_i X_j

sum_{i<j} X_i X_j = (Sx^2 - n I) / 2 with Sx = sum_i X_i, for every n.

Construction: H0 is built entry by entry from bit operations.
  diagonal  <b|H0|b>          = phi^2 * sum_i (1 - 2 b_i)
  off-diag  <b ^ m_ij|H0|b>   = phi^-2   for each pair i<j (flip bits i, j)
This costs O(4**n) to allocate plus O(2**n * n**2) to fill, so n = 12
(4096 x 4096) is feasible. The reduction is checked in the tests, not used
here. The paste's pure-Python Sx @ Sx matmul was O(8**n) and did not reach 12.

Limit: n <= MAX_DENSE_N builds and steps exactly. For n > MAX_DENSE_N only
spectral_norm_bound (a triangle-inequality upper bound, not the norm) is
available.
"""

from __future__ import annotations

import math

PHI = (1 + math.sqrt(5)) / 2
PHI_SQ = PHI ** 2
PHI_INV_SQ = PHI ** -2

FAMILY = "evolanus_flow"
MAX_DENSE_N = 12
DESIGN_N = 32

_PAULI_X = ((0.0, 1.0), (1.0, 0.0))
_PAULI_Z = ((1.0, 0.0), (0.0, -1.0))
_IDENTITY = ((1.0, 0.0), (0.0, 1.0))


# Small dense helpers (reference construction, used by tests at small n)

def _kron2(a, b):
    """(A (x) B)[i*p + k][j*q + l] = A[i][j] * B[k][l]; any rectangular shapes."""
    return tuple(
        tuple(a_ij * b_kl for a_ij in arow for b_kl in br)
        for arow in a
        for br in b
    )


def _matrix_add(a, b):
    return tuple(tuple(x + y for x, y in zip(ra, rb)) for ra, rb in zip(a, b))


def _matrix_scale(a, s):
    return tuple(tuple(x * s for x in r) for r in a)


def _zeros(n):
    return tuple(tuple(0.0 for _ in range(n)) for _ in range(n))


def _identity(n):
    return tuple(tuple(1.0 if i == j else 0.0 for j in range(n)) for i in range(n))


def _pauli_string(n, single):
    """Dense 2**n operator; site 0 is the most significant (leftmost) factor."""
    op = ((1.0,),)
    for site in range(n):
        op = _kron2(op, single.get(site, _IDENTITY))
    return op


def _check_n(n):
    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        raise ValueError(f"n must be a positive int, got {n!r}")
    if n > MAX_DENSE_N:
        raise ValueError(
            f"n={n} exceeds dense ceiling {MAX_DENSE_N}; operator form only"
        )


# H0

def _h0_entries(n):
    """Yield (row, col, value) for the nonzero entries of H0(n)."""
    dim = 1 << n
    # site i (0 = leftmost kron factor) is bit (n - 1 - i) of the index
    masks = [(1 << (n - 1 - i)) | (1 << (n - 1 - j))
             for i in range(n) for j in range(i + 1, n)]
    for b in range(dim):
        ones = bin(b).count("1")
        yield b, b, PHI_SQ * (n - 2 * ones)
        for m in masks:
            yield b ^ m, b, PHI_INV_SQ


def build_h0_dense(n):
    """Exact dense H0 as a list of lists of floats, n <= MAX_DENSE_N."""
    _check_n(n)
    dim = 1 << n
    h = [[0.0] * dim for _ in range(dim)]
    for r, c, v in _h0_entries(n):
        h[r][c] += v
    return h


def build_h0_numpy(n):
    """Same matrix as build_h0_dense, as a numpy float64 array."""
    import numpy as np

    _check_n(n)
    dim = 1 << n
    h = np.zeros((dim, dim), dtype=np.float64)
    for r, c, v in _h0_entries(n):
        h[r, c] += v
    return h


def spectral_norm_bound(n):
    """Triangle bound phi^2 n + phi^-2 n(n-1)/2. An upper bound, not the norm."""
    if n < 0:
        raise ValueError("n must be non-negative")
    return PHI_SQ * n + PHI_INV_SQ * (n * n - n) / 2.0


def hermiticity_check_dense(n):
    """True when the pure-Python build of H0(n) is symmetric (real Hermitian)."""
    h = build_h0_dense(n)
    dim = len(h)
    return all(h[i][j] == h[j][i] for i in range(dim) for j in range(i + 1, dim))


# Step

def step(state, dtau, n):
    """psi -> exp(-i H0 dtau) psi, exact by eigendecomposition (numpy eigh).

    Refuses n > MAX_DENSE_N, a state whose length is not 2**n, and a
    non-finite dtau. Returns a dict; "unitary" is the measured norm
    ratio check, not a constant.
    """
    import numpy as np

    _check_n(n)
    if not math.isfinite(dtau):
        raise ValueError("dtau must be finite")
    psi = np.asarray(state, dtype=complex).reshape(-1)
    if psi.shape[0] != (1 << n):
        raise ValueError(f"state length {psi.shape[0]} != 2**n = {1 << n}")
    w, v = np.linalg.eigh(build_h0_numpy(n))
    evolved = v @ (np.exp(-1j * w * dtau) * (v.conj().T @ psi))
    n_in, n_out = float(np.linalg.norm(psi)), float(np.linalg.norm(evolved))
    return {
        "family": FAMILY,
        "state": evolved,
        "n": n,
        "dtau": dtau,
        "unitary": math.isclose(n_in, n_out, rel_tol=1e-10, abs_tol=1e-12),
    }


def main() -> int:
    print(f"family      : {FAMILY}")
    print(f"phi^2       : {PHI_SQ:.15f}")
    print(f"phi^-2      : {PHI_INV_SQ:.15f}")
    print(f"MAX_DENSE_N : {MAX_DENSE_N}")
    ok = True
    for n in (1, 2, 3, 4, 5):
        herm = hermiticity_check_dense(n)
        ok &= herm
        print(f"  n={n:2d}  hermitian={herm}  ||H0||<={spectral_norm_bound(n):.6f}")
    print(f"  n={DESIGN_N} bound (operator form only): {spectral_norm_bound(DESIGN_N):.6f}")
    try:
        build_h0_dense(DESIGN_N)
        ok = False
    except ValueError as exc:
        print(f"  n={DESIGN_N} dense: refused ({exc})")
    try:
        import numpy as np
    except ImportError:
        print("  step skipped (numpy absent)")
        return 0 if ok else 1
    psi0 = np.zeros(8, dtype=complex)
    psi0[0] = 1.0
    out = step(psi0, 0.01, 3)
    norm = float(np.linalg.norm(out["state"]))
    print(f"  step n=3 dtau=0.01: ||psi||={norm:.15f} unitary={out['unitary']}")
    return 0 if ok and out["unitary"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
