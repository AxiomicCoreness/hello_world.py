"""Numerical check of the AKLT projector P2 in aklt_projector_and_parse_timestamp.md."""
from __future__ import annotations

from collections import Counter

import pytest

np = pytest.importorskip("numpy", reason="numpy not installed; AKLT projector check needs it")


def _spin1():
    r = np.sqrt(2.0) / 2.0
    sx = r * np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=complex)
    sy = r * np.array([[0, -1j, 0], [1j, 0, -1j], [0, 1j, 0]], dtype=complex)
    sz = np.diag([1.0, 0.0, -1.0]).astype(complex)
    return sx, sy, sz


def _ops():
    i3 = np.eye(3)
    s1 = [np.kron(s, i3) for s in _spin1()]
    s2 = [np.kron(i3, s) for s in _spin1()]
    x = sum(a @ b for a, b in zip(s1, s2))                       # S1·S2
    stot2 = sum((a + b) @ (a + b) for a, b in zip(s1, s2))       # (S1+S2)^2
    p2 = (x @ x + 3 * x + 2 * np.eye(9)) / 6.0
    return x, stot2, p2


def test_spin1_algebra():
    sx, sy, sz = _spin1()
    assert np.allclose(sx @ sy - sy @ sx, 1j * sz)
    assert np.allclose(sx @ sx + sy @ sy + sz @ sz, 2 * np.eye(3))   # s(s+1) = 2


def test_p2_idempotent_hermitian_rank5():
    _, _, p2 = _ops()
    assert np.allclose(p2 @ p2, p2)
    assert np.allclose(p2, p2.conj().T)
    assert np.linalg.matrix_rank(p2) == 5
    assert np.isclose(np.trace(p2).real, 5.0)


def test_x_eigenvalues_and_formula():
    x, stot2, _ = _ops()
    ev = Counter(int(round(v)) for v in np.linalg.eigvalsh(x))
    assert ev == {1: 5, -1: 3, -2: 1}
    assert np.allclose(x, (stot2 - 4 * np.eye(9)) / 2.0)    # x = (S(S+1) - 4) / 2


def test_p2_is_projector_onto_s2_sector():
    _, stot2, p2 = _ops()
    w, v = np.linalg.eigh(stot2)
    sel = v[:, np.isclose(w, 6.0)]                           # S^2 = 6  <=>  S = 2
    assert sel.shape[1] == 5
    assert np.allclose(p2, sel @ sel.conj().T)
