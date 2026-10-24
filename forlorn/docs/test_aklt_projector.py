"""Numerical check of the AKLT projector P2 in aklt_projector_and_parse_timestamp.md.

Spin-1 matrices (basis m = +1, 0, -1):
  Sx = (1/√2) [[0,1,0],[1,0,1],[0,1,0]]
  Sy = (i/√2) [[0,-1,0],[1,0,-1],[0,1,0]]
  Sz = diag(1, 0, -1)
S1·S2 = Σ_a kron(Sa, Sa);  P2 = ((S1·S2)^2 + 3 S1·S2 + 2I) / 6.
No exact float equality: every comparison uses allclose / isclose / rounding.
"""
from __future__ import annotations

from collections import Counter

import pytest

np = pytest.importorskip("numpy", reason="numpy not installed; AKLT projector check needs it")

SX = (1 / np.sqrt(2)) * np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=complex)
SY = (1j / np.sqrt(2)) * np.array([[0, -1, 0], [1, 0, -1], [0, 1, 0]], dtype=complex)
SZ = np.diag([1, 0, -1]).astype(complex)
SPIN1 = (SX, SY, SZ)
I9 = np.eye(9)

X = sum(np.kron(s, s) for s in SPIN1)                     # S1·S2
P2 = (X @ X + 3 * X + 2 * I9) / 6.0
I3 = np.eye(3)
S_TOT = [np.kron(s, I3) + np.kron(I3, s) for s in SPIN1]  # S = S1 + S2
S2_TOT = sum(s @ s for s in S_TOT)                        # S^2


def test_spin1_matrices():
    assert np.allclose(SX @ SY - SY @ SX, 1j * SZ)
    assert np.allclose(SX @ SX + SY @ SY + SZ @ SZ, 2 * I3)   # s(s+1) = 2
    for s in SPIN1:
        assert np.allclose(s, s.conj().T)


def test_p2_rank_idempotent_trace_hermitian():
    assert np.linalg.matrix_rank(P2) == 5
    assert np.allclose(P2 @ P2, P2)
    assert np.isclose(np.trace(P2), 5)
    assert np.allclose(P2, P2.conj().T)


def test_x_eigenvalue_multiplicities():
    ev = np.linalg.eigvalsh(X)
    assert np.allclose(ev, np.round(ev))                    # integer spectrum, within tolerance
    assert Counter(int(np.round(v)) for v in ev) == {1: 5, -1: 3, -2: 1}
    assert np.allclose(X, (S2_TOT - 4 * I9) / 2.0)          # x = (S(S+1) - 4) / 2


def test_p2_matches_s2_eigenvalue_6_projector():
    w, v = np.linalg.eigh(S2_TOT)
    sel = v[:, np.isclose(w, 6.0)]                         # S^2 = 6  <=>  S = 2
    assert sel.shape[1] == 5
    assert np.allclose(P2, sel @ sel.conj().T)
