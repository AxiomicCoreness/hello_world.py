#!/usr/bin/env python3
"""
scripts/aklt_e2e_test.py — end-to-end test of AKLT model invariants.

Independent of prior thread claims. Assertions reference values from
docs/aklt_research_notes.md, which cite published sources.

Verifies:
  G1  spin-1 algebra             [S^x, S^y] = i S^z  (ħ=1)
  G2  spin-1 Casimir             S^2 eigenvalue = 2 on triplet
  G3  π_2 projector              idempotent, hermitian, rank 5
  G4  AKLT spectrum              E_0 >= -1e-12 (PSD floor)
  G5  ground state energy        |E_0| < 1e-9 (kernel)
  G6  PBC ground-state degeneracy 1
  G7  OBC ground-state degeneracy 4
  G8  MPS transfer matrix        exactly one |λ| = 1, next |λ_2| = 1/3
  G9  correlation length         ξ = 1/ln(3) from λ_2
  G10 hidden Z2 × Z2             each R^α (α=x,y,z) has (R^α)^2 = 1 on spin-1
  G11 string order               O^z = -4/9 from the MPS (r = 1..6)

Exit 0 iff all gates pass. Exit 1 otherwise.
"""

from __future__ import annotations
import math
import sys

import numpy as np

TOL_EIG      = 1e-9
TOL_ALG      = 1e-12
TOL_MPS      = 1e-10
TOL_PSD      = 1e-12

S2 = math.sqrt(2.0)
Sz = np.diag([1.0, 0.0, -1.0]).astype(complex)
Sp = np.array([[0.0, S2, 0.0],
               [0.0, 0.0, S2],
               [0.0, 0.0, 0.0]], dtype=complex)
Sm = Sp.conj().T
Sx = 0.5 * (Sp + Sm)
Sy = (Sp - Sm) / (2j)
I3 = np.eye(3, dtype=complex)


def kron_ops(ops):
    """Kronecker product left-to-right."""
    out = ops[0]
    for op in ops[1:]:
        out = np.kron(out, op)
    return out


def embed_site(op, site, N):
    """Place `op` on `site` (0-indexed) of an N-site chain."""
    return kron_ops([op if k == site else I3 for k in range(N)])


def total_two_site_op(A, B, i, j, N):
    """A_i B_j for i != j."""
    return embed_site(A, i, N) @ embed_site(B, j, N)


def I3_embed(N):
    return np.eye(3 ** N, dtype=complex)


def aklt_hamiltonian(N, periodic):
    """H = Σ_k π_2(k, k+1) on N spin-1 sites."""
    dim = 3 ** N
    H = np.zeros((dim, dim), dtype=complex)

    bond_list = [(k, k + 1) for k in range(N - 1)]
    if periodic and N > 2:
        bond_list.append((N - 1, 0))

    for (i, j) in bond_list:
        SS = (total_two_site_op(Sx, Sx, i, j, N)
              + total_two_site_op(Sy, Sy, i, j, N)
              + total_two_site_op(Sz, Sz, i, j, N))
        SS2 = SS @ SS
        pi2 = (SS2 + 3.0 * SS + 2.0 * I3_embed(N)) / 6.0
        H += pi2

    return H


def gate_G1():
    comm = Sx @ Sy - Sy @ Sx
    err = np.max(np.abs(comm - 1j * Sz))
    return err < TOL_ALG, f"max|[Sx,Sy] - i Sz| = {err:.3e}"


def gate_G2():
    S2op = Sx @ Sx + Sy @ Sy + Sz @ Sz
    err = np.max(np.abs(S2op - 2.0 * I3))
    return err < TOL_ALG, f"max|S^2 - 2I| = {err:.3e}"


def gate_G3():
    SS = (np.kron(Sx, Sx) + np.kron(Sy, Sy) + np.kron(Sz, Sz))
    pi2 = (SS @ SS + 3.0 * SS + 2.0 * np.eye(9, dtype=complex)) / 6.0

    idem_err = np.max(np.abs(pi2 @ pi2 - pi2))
    herm_err = np.max(np.abs(pi2 - pi2.conj().T))
    rank = np.linalg.matrix_rank(pi2, tol=1e-9)

    ok = (idem_err < TOL_ALG) and (herm_err < TOL_ALG) and (rank == 5)
    return ok, (f"idem={idem_err:.2e} herm={herm_err:.2e} rank={rank} "
                f"(expected rank 5)")


def gate_G4_G5_G6(N=6):
    """Spectrum of AKLT for periodic BC, even N."""
    H = aklt_hamiltonian(N, periodic=True)
    evals = np.linalg.eigvalsh(H)
    min_e = evals[0]
    psd_ok = min_e >= -TOL_PSD
    kernel_ok = abs(min_e) < TOL_EIG
    gap = evals[1] - evals[0]
    unique_gs = gap > 1e-6
    return (psd_ok and kernel_ok and unique_gs,
            f"N={N} PBC: E_0={min_e:.3e} E_1={evals[1]:.3e} gap={gap:.3e}")


def gate_G7(N=4):
    """Open BC ground state degeneracy = 4."""
    H = aklt_hamiltonian(N, periodic=False)
    evals = np.linalg.eigvalsh(H)
    e0 = evals[0]
    deg = int(np.sum(np.abs(evals - e0) < 1e-6))
    return deg == 4, f"N={N} OBC: E_0={e0:.3e}, degenerate count = {deg} (expected 4)"


def gate_G8_G9():
    """MPS transfer matrix and correlation length."""
    Ap = math.sqrt(2.0 / 3.0) * np.array([[0.0, 1.0], [0.0, 0.0]], dtype=complex)
    A0 = (1.0 / math.sqrt(3.0)) * np.array([[-1.0, 0.0], [0.0, 1.0]], dtype=complex)
    Am = math.sqrt(2.0 / 3.0) * np.array([[0.0, 0.0], [-1.0, 0.0]], dtype=complex)

    T = np.zeros((4, 4), dtype=complex)
    for A in (Ap, A0, Am):
        T += np.kron(A, A.conj())

    evals = np.linalg.eigvals(T)
    mags = np.sort(np.abs(evals))[::-1]

    count_one = int(np.sum(np.abs(mags - 1.0) < TOL_MPS))
    lam2 = mags[count_one] if count_one < len(mags) else 0.0

    ok_uniq = (count_one == 1)
    ok_lam2 = abs(lam2 - 1.0 / 3.0) < TOL_MPS

    xi_computed = -1.0 / math.log(lam2) if lam2 > 0 else float("inf")
    xi_published = 1.0 / math.log(3.0)
    ok_xi = abs(xi_computed - xi_published) < 1e-9

    msg = (f"eigenvalues of T: {np.round(mags, 6).tolist()}; "
           f"count |λ|=1: {count_one}; |λ_2|={lam2:.10f} "
           f"(expected 1/3); ξ={xi_computed:.10f} "
           f"(published 1/ln3={xi_published:.10f})")
    return (ok_uniq and ok_lam2 and ok_xi), msg


def _expm_i_pi_S(S):
    """exp(iπ S) for Hermitian S. Diagonalize πS, then exp(1j*w)."""
    M = math.pi * S
    w, V = np.linalg.eigh(M)
    return V @ np.diag(np.exp(1j * w)) @ V.conj().T


def gate_G10():
    """Hidden Z2 × Z2: each R^α = exp(iπ S^α) has (R^α)^2 = +I on spin-1."""
    results = {}
    for name, S in (("x", Sx), ("y", Sy), ("z", Sz)):
        R = _expm_i_pi_S(S)
        sq = R @ R
        err = np.max(np.abs(sq - I3))
        results[name] = err < 1e-10
    ok = all(results.values())
    msg = "  ".join(f"{k}:{'OK' if results[k] else 'FAIL'}" for k in results)
    return ok, msg


def aklt_mps():
    """AKLT MPS matrices A^{+1}, A^0, A^{-1} (left-normalized: Σ A†A = I)."""
    Ap = math.sqrt(2.0 / 3.0) * np.array([[0.0, 1.0], [0.0, 0.0]], dtype=complex)
    A0 = (1.0 / math.sqrt(3.0)) * np.array([[-1.0, 0.0], [0.0, 1.0]], dtype=complex)
    Am = math.sqrt(2.0 / 3.0) * np.array([[0.0, 0.0], [-1.0, 0.0]], dtype=complex)
    return {1: Ap, 0: A0, -1: Am}


def string_order(r):
    """<S^z_0 exp(iπ Σ_{0<j<r} S^z_j) S^z_r> in the infinite AKLT MPS."""
    A = aklt_mps()

    def E(f):
        return sum(f(m) * np.kron(A[m], A[m].conj()) for m in A)

    T = E(lambda m: 1.0)
    Esz = E(lambda m: float(m))
    Eexp = E(lambda m: np.exp(1j * math.pi * m))
    wr, Vr = np.linalg.eig(T)
    wl, Vl = np.linalg.eig(T.T)
    rv = Vr[:, np.argmax(np.abs(wr))]
    lv = Vl[:, np.argmax(np.abs(wl))]
    M = Esz @ np.linalg.matrix_power(Eexp, r - 1) @ Esz
    return complex(lv @ M @ rv / (lv @ rv))


def gate_G11():
    vals = [string_order(r) for r in range(1, 7)]
    err = max(abs(v - (-4.0 / 9.0)) for v in vals)
    return err < 1e-12, (f"O^z(r=1..6) = {[round(v.real, 12) for v in vals]} "
                         f"(expected -4/9), max err {err:.1e}")


def main() -> int:
    print("AKLT e2e test — independent verification against published values")
    print("=" * 70)

    gates = [
        ("G1  spin-1 algebra",             gate_G1),
        ("G2  spin-1 Casimir",             gate_G2),
        ("G3  π_2 projector",              gate_G3),
        ("G4/G5/G6  PBC spectrum (N=6)",   lambda: gate_G4_G5_G6(N=6)),
        ("G7  OBC degeneracy (N=4)",       lambda: gate_G7(N=4)),
        ("G8/G9  MPS ξ = 1/ln(3)",         gate_G8_G9),
        ("G10 hidden Z2 × Z2",             gate_G10),
        ("G11 string order -4/9",          gate_G11),
    ]

    all_ok = True
    for label, fn in gates:
        try:
            ok, msg = fn()
        except Exception as exc:
            ok, msg = False, f"EXCEPTION: {type(exc).__name__}: {exc}"
        mark = "OK  " if ok else "FAIL"
        print(f"[{mark}] {label:<32} {msg}")
        all_ok = all_ok and ok

    print("=" * 70)
    if all_ok:
        print("all AKLT e2e gates passed")
        return 0
    print("AKLT E2E FAILURE", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
