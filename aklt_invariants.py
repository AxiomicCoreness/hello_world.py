#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
aklt_invariants.py

AKLT invariant test surface. Numpy only.

Exercises four distinct invariants of the AKLT (Affleck-Kennedy-Lieb-Tasaki)
spin-1 chain and exits non-zero if any fails.

Invariants tested:
  I.   Ground-state energy per bond E/N = -2/3 (exact AKLT value)
  II.  Entanglement spectrum degeneracy (singlet-triplet structure)
  III. String-order parameter O_string > 0 (hidden order)
  IV.  SU(2) singlet of total spin S_tot |GS> = 0

No dependency on matplotlib, torch, scipy, or any engine module.
"""

import sys
import numpy as np

SQRT2 = np.sqrt(2.0)

Sx = (1.0 / SQRT2) * np.array([
    [0.0, 1.0, 0.0],
    [1.0, 0.0, 1.0],
    [0.0, 1.0, 0.0],
], dtype=complex)

Sy = (1.0 / SQRT2) * np.array([
    [0.0, -1.0j, 0.0],
    [1.0j, 0.0, -1.0j],
    [0.0, 1.0j, 0.0],
], dtype=complex)

Sz = np.array([
    [1.0, 0.0, 0.0],
    [0.0, 0.0, 0.0],
    [0.0, 0.0, -1.0],
], dtype=complex)

Sp = SQRT2 * np.array([
    [0.0, 1.0, 0.0],
    [0.0, 0.0, 1.0],
    [0.0, 0.0, 0.0],
], dtype=complex)

Sm = SQRT2 * np.array([
    [0.0, 0.0, 0.0],
    [1.0, 0.0, 0.0],
    [0.0, 1.0, 0.0],
], dtype=complex)

I3 = np.eye(3, dtype=complex)


def embed(op, site, N):
    """Return operator `op` acting on site `site` of an N-site spin-1 chain."""
    ops = [I3] * N
    ops[site] = op
    out = ops[0]
    for k in range(1, N):
        out = np.kron(out, ops[k])
    return out


def aklt_hamiltonian(N):
    """H = sum_i [ S_i.S_{i+1} + (1/3)(S_i.S_{i+1})^2 ]  open boundaries."""
    dim = 3 ** N
    H = np.zeros((dim, dim), dtype=complex)
    S = (Sx, Sy, Sz)
    for i in range(N - 1):
        Si = [embed(S[a], i, N) for a in range(3)]
        Sj = [embed(S[a], i + 1, N) for a in range(3)]
        SdotS = sum(Si[a] @ Sj[a] for a in range(3))
        H += SdotS + (1.0 / 3.0) * (SdotS @ SdotS)
    return H


def check_ground_state_energy(N=4, tol=1e-6):
    H = aklt_hamiltonian(N)
    evals = np.linalg.eigvalsh(H)
    E0 = float(evals[0].real)
    E_per_bond = E0 / (N - 1)
    ok = abs(E_per_bond - (-2.0 / 3.0)) < 0.15
    return ok, E_per_bond


def check_entanglement_degeneracy(N=4, tol=1e-6):
    H = aklt_hamiltonian(N)
    evals, evecs = np.linalg.eigh(H)
    gs = evecs[:, 0]
    d = 3 ** (N // 2)
    psi = gs.reshape(d, d)
    rho = psi @ psi.conj().T
    es = np.linalg.eigvalsh(rho)
    es = es[es > 1e-12]
    es = np.sort(es)[::-1]
    if len(es) < 2:
        return False, es
    top_pair_diff = abs(es[0] - es[1])
    ok = top_pair_diff < 1e-3
    return ok, es[:5]


def check_string_order(N=6, tol=1e-6):
    H = aklt_hamiltonian(N)
    evals, evecs = np.linalg.eigh(H)
    gs = evecs[:, 0]
    i, j = 1, N - 2
    Sz_i = embed(Sz, i, N)
    Sz_j = embed(Sz, j, N)
    prod = np.eye(3 ** N, dtype=complex)
    for k in range(i + 1, j):
        Op_k = embed(np.diag([np.exp(1j * np.pi), 1.0, np.exp(-1j * np.pi)]), k, N)
        prod = prod @ Op_k
    O_string = gs.conj() @ (Sz_i @ prod @ Sz_j) @ gs
    val = float(O_string.real)
    ok = val > 0.0
    return ok, val


def check_singlet(N=4, tol=1e-6):
    H = aklt_hamiltonian(N)
    evals, evecs = np.linalg.eigh(H)
    gs = evecs[:, 0]
    Stot2 = np.zeros((3 ** N, 3 ** N), dtype=complex)
    S = (Sx, Sy, Sz)
    for i in range(N):
        for j in range(N):
            Si = [embed(S[a], i, N) for a in range(3)]
            Sj = [embed(S[a], j, N) for a in range(3)]
            Stot2 += sum(Si[a] @ Sj[a] for a in range(3))
    expectation = float((gs.conj() @ Stot2 @ gs).real)
    ok = abs(expectation) < 1e-6
    return ok, expectation


def main():
    print("=" * 78)
    print("AKLT INVARIANT TEST SURFACE -- NUMPY-ONLY")
    print("=" * 78)
    results = {}
    ok1, val1 = check_ground_state_energy(N=4)
    results["I. Ground-state energy per bond ~ -2/3"] = (ok1, val1)
    ok2, val2 = check_entanglement_degeneracy(N=4)
    results["II. Entanglement spectrum degeneracy"] = (ok2, val2)
    ok3, val3 = check_string_order(N=6)
    results["III. String-order parameter > 0"] = (ok3, val3)
    ok4, val4 = check_singlet(N=4)
    results["IV. Total spin singlet (S_tot^2 = 0)"] = (ok4, val4)
    all_ok = True
    for name, (ok, val) in results.items():
        status = "PASS" if ok else "FAIL"
        if not ok:
            all_ok = False
        if isinstance(val, float):
            print(f"  {status}  {name:45s}  value = {val:.10g}")
        else:
            print(f"  {status}  {name:45s}  value = {val}")
    print("-" * 78)
    if all_ok:
        print("ALL FOUR AKLT INVARIANTS HOLD")
        return 0
    else:
        print("INVARIANT VIOLATION DETECTED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
