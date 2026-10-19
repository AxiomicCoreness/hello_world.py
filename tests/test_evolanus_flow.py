"""Tests for scripts/evolanus_flow.py. Reference matrices are built with numpy.kron."""

from __future__ import annotations

import importlib.util
import itertools
import time
from pathlib import Path

import pytest

np = pytest.importorskip("numpy")

_PATH = Path(__file__).resolve().parents[1] / "scripts" / "evolanus_flow.py"
_spec = importlib.util.spec_from_file_location("evolanus_flow", _PATH)
ef = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ef)

X = np.array([[0.0, 1.0], [1.0, 0.0]])
Z = np.array([[1.0, 0.0], [0.0, -1.0]])
I2 = np.eye(2)


def _site_op(n, ops):
    out = np.array([[1.0]])
    for s in range(n):
        out = np.kron(out, ops.get(s, I2))
    return out


def _h0_reference(n):
    """Direct sum of kron terms; the (Sx^2 - nI)/2 reduction is not used."""
    dim = 1 << n
    h = np.zeros((dim, dim))
    for i in range(n):
        h += ef.PHI_SQ * _site_op(n, {i: Z})
    for i, j in itertools.combinations(range(n), 2):
        h += ef.PHI_INV_SQ * _site_op(n, {i: X, j: X})
    return h


@pytest.mark.parametrize("sa,sb", [((2, 2), (2, 2)), ((2, 3), (3, 2)), ((3, 2), (2, 3)), ((2, 3), (2, 3))])
def test_kron2_matches_numpy(sa, sb):
    rng = np.random.default_rng(1)
    a, b = rng.normal(size=sa), rng.normal(size=sb)
    got = np.array(ef._kron2(tuple(map(tuple, a)), tuple(map(tuple, b))))
    assert got.shape == np.kron(a, b).shape
    assert np.allclose(got, np.kron(a, b))


def test_pauli_string_matches_numpy():
    got = np.array(ef._pauli_string(3, {0: ef._PAULI_X, 2: ef._PAULI_Z}))
    assert np.allclose(got, _site_op(3, {0: X, 2: Z}))


@pytest.mark.parametrize("n", [1, 2, 3, 4, 5])
def test_h0_matches_kron_reference(n):
    ref = _h0_reference(n)
    assert np.allclose(np.array(ef.build_h0_dense(n)), ref, atol=1e-12)
    assert np.allclose(ef.build_h0_numpy(n), ref, atol=1e-12)


@pytest.mark.parametrize("n", [1, 2, 3, 4, 5])
def test_pair_reduction_identity(n):
    sx = sum(_site_op(n, {i: X}) for i in range(n))
    pair = sum(_site_op(n, {i: X, j: X}) for i, j in itertools.combinations(range(n), 2))
    if n == 1:
        pair = np.zeros((2, 2))
    assert np.allclose(pair, (sx @ sx - n * np.eye(1 << n)) / 2)


@pytest.mark.parametrize("n", range(1, 7))
def test_spectral_norm_within_bound(n):
    w = np.linalg.eigvalsh(ef.build_h0_numpy(n))
    assert np.max(np.abs(w)) <= ef.spectral_norm_bound(n) + 1e-9


@pytest.mark.parametrize("n", [1, 2, 3, 4, 5])
def test_hermiticity(n):
    assert ef.hermiticity_check_dense(n)


@pytest.mark.parametrize("n,dtau", [(1, 0.3), (3, 0.01), (4, 1.7), (5, -0.5)])
def test_step_unitary_and_matches_expm(n, dtau):
    rng = np.random.default_rng(n)
    psi = rng.normal(size=1 << n) + 1j * rng.normal(size=1 << n)
    psi /= np.linalg.norm(psi)
    out = ef.step(psi, dtau, n)
    assert out["unitary"] is True and out["n"] == n
    assert abs(np.linalg.norm(out["state"]) - 1.0) < 1e-12
    h = _h0_reference(n)
    try:
        from scipy.linalg import expm
        u = expm(-1j * dtau * h)
    except ImportError:
        w, v = np.linalg.eigh(h)
        u = v @ np.diag(np.exp(-1j * w * dtau)) @ v.conj().T
    assert np.allclose(out["state"], u @ psi, atol=1e-10)


def test_step_zero_dtau_is_identity():
    psi = np.zeros(4, dtype=complex)
    psi[2] = 1.0
    assert np.allclose(ef.step(psi, 0.0, 2)["state"], psi)


@pytest.mark.parametrize("n", [13, 32])
def test_refuses_above_ceiling(n):
    with pytest.raises(ValueError):
        ef.step(np.zeros(2, dtype=complex), 0.01, n)
    with pytest.raises(ValueError):
        ef.build_h0_dense(n)


def test_step_rejects_bad_inputs():
    with pytest.raises(ValueError):
        ef.step(np.zeros(3, dtype=complex), 0.01, 2)
    with pytest.raises(ValueError):
        ef.step(np.zeros(4, dtype=complex), float("nan"), 2)
    with pytest.raises(ValueError):
        ef.build_h0_dense(0)


def test_bound_formula_n32():
    assert ef.spectral_norm_bound(32) == pytest.approx(ef.PHI_SQ * 32 + ef.PHI_INV_SQ * 496)


@pytest.mark.parametrize("n", [8, 10, 12])
def test_build_timing_is_feasible(n):
    t = time.perf_counter()
    h = ef.build_h0_dense(n)
    assert len(h) == 1 << n
    assert time.perf_counter() - t < 30.0
