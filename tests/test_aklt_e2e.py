# tests/test_aklt_e2e.py
import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import aklt_e2e_test as a  # noqa: E402

GATES = ["gate_G1", "gate_G2", "gate_G3", "gate_G4_G5_G6", "gate_G7",
         "gate_G8_G9", "gate_G10", "gate_G11"]


@pytest.mark.parametrize("name", GATES)
def test_gate_passes(name):
    ok, msg = getattr(a, name)()
    assert ok, msg


def test_pi2_rank_is_five():
    SS = sum(np.kron(S, S) for S in (a.Sx, a.Sy, a.Sz))
    pi2 = (SS @ SS + 3 * SS + 2 * np.eye(9)) / 6
    assert np.linalg.matrix_rank(pi2, tol=1e-9) == 5
    assert np.allclose(sorted(np.linalg.eigvalsh(pi2)), [0] * 4 + [1] * 5)


def test_hamiltonian_forms_equivalent():
    SS = sum(np.kron(S, S) for S in (a.Sx, a.Sy, a.Sz))
    HA = SS + SS @ SS / 3
    HB = (SS @ SS + 3 * SS + 2 * np.eye(9)) / 6
    assert np.allclose(HB, HA / 2 + np.eye(9) / 3)


def test_pbc_unique_zero_ground_state():
    ev = np.linalg.eigvalsh(a.aklt_hamiltonian(6, periodic=True))
    assert abs(ev[0]) < 1e-9
    assert ev[1] - ev[0] > 0.3


def test_obc_fourfold_degeneracy():
    ev = np.linalg.eigvalsh(a.aklt_hamiltonian(4, periodic=False))
    assert int(np.sum(np.abs(ev) < 1e-9)) == 4
    assert ev[4] > 1e-3


def test_transfer_matrix_spectrum_and_xi():
    A = a.aklt_mps()
    assert np.allclose(sum(M.conj().T @ M for M in A.values()), np.eye(2))
    T = sum(np.kron(M, M.conj()) for M in A.values())
    ev = np.sort_complex(np.linalg.eigvals(T))
    assert np.allclose(ev, [-1 / 3, -1 / 3, -1 / 3, 1])
    assert math.isclose(-1 / math.log(1 / 3), 1 / math.log(3))


def test_rotations_are_exact_involutions_and_z2xz2():
    Rx, Ry, Rz = (a._expm_i_pi_S(S) for S in (a.Sx, a.Sy, a.Sz))
    for R in (Rx, Ry, Rz):
        assert np.allclose(R @ R, a.I3)
    assert np.allclose(Rx @ Ry, Ry @ Rx)
    assert np.allclose(Rx @ Ry, Rz)


def test_string_order_ed_small_chain():
    N = 6
    _, v = np.linalg.eigh(a.aklt_hamiltonian(N, periodic=True))
    g = v[:, 0]
    Rz = np.diag(np.exp(1j * np.pi * np.array([1, 0, -1])))
    op = a.kron_ops([a.Sz, Rz, a.Sz, a.I3, a.I3, a.I3])
    val = (g.conj() @ op @ g).real
    assert abs(val + 4 / 9) < 5e-3   # finite-size: -0.44809 at N=6


@pytest.mark.parametrize("N,pbc,nb,deg", [(6, True, 6, 1), (4, False, 3, 4)])
def test_form_A_equals_2B_minus_two_thirds_per_bond(N, pbc, nb, deg):
    bonds = [(k, k + 1) for k in range(N - 1)] + ([(N - 1, 0)] if pbc else [])
    HA = np.zeros((3 ** N,) * 2, dtype=complex)
    for i, j in bonds:
        SS = sum(a.total_two_site_op(S, S, i, j, N) for S in (a.Sx, a.Sy, a.Sz))
        HA += SS + SS @ SS / 3
    HB = a.aklt_hamiltonian(N, periodic=pbc)
    assert np.allclose(HA, 2 * HB - (2 / 3) * nb * np.eye(3 ** N))
    ea = np.linalg.eigvalsh(HA)
    assert abs(ea[0] + 2 * nb / 3) < 1e-9
    assert int(np.sum(np.abs(ea - ea[0]) < 1e-9)) == deg
