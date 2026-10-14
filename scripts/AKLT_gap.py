#!/usr/bin/env python3
"""
AKLT_gap.py — hard assertion that the spin-1 AKLT chain is gapped.
Standard library + numpy. No matplotlib, no torch.

The AKLT Hamiltonian on N sites with periodic boundaries:
    H = Σ_i [ (1/3) (S_i · S_{i+1}) + (2/9) (S_i · S_{i+1})^2 ]
Equivalently, on the projector to total spin 2:
    H = Σ_i P_2(S_i + S_{i+1})
with P_2 = (SS^2 + 3·SS + 2·I) / 6 where SS = S_i·S_{i+1}.

Ground state energy = 0 exactly (frustration-free).
The Haldane gap E_1 - E_0 > 0 for any finite N with PBC.

Exit codes:
    0 — gap > 1e-6, all sanity checks pass
    1 — one or more checks failed
    2 — numpy unavailable
"""
import math
import sys

try:
    import numpy as np
except ImportError:
    print("FATAL: numpy required. pip install numpy", file=sys.stderr)
    sys.exit(2)

SQRT2 = math.sqrt(2.0)
Sz = np.diag([1.0, 0.0, -1.0]).astype(complex)
Sp = np.array([[0.0, SQRT2, 0.0],
               [0.0, 0.0, SQRT2],
               [0.0, 0.0, 0.0]], dtype=complex)
Sm = Sp.conj().T
Sx = 0.5 * (Sp + Sm)
Sy = (Sp - Sm) / (2j)
I3 = np.eye(3, dtype=complex)


def embed_site(op, site, N):
    ops = [op if k == site else I3 for k in range(N)]
    out = ops[0]
    for o in ops[1:]:
        out = np.kron(out, o)
    return out


def two_site(A, B, i, j, N):
    return embed_site(A, i, N) @ embed_site(B, j, N)


def aklt_hamiltonian(N, periodic=True):
    dim = 3 ** N
    H = np.zeros((dim, dim), dtype=complex)
    bonds = [(k, k + 1) for k in range(N - 1)]
    if periodic and N > 2:
        bonds.append((N - 1, 0))
    for (i, j) in bonds:
        SS = (two_site(Sx, Sx, i, j, N)
              + two_site(Sy, Sy, i, j, N)
              + two_site(Sz, Sz, i, j, N))
        P2 = (SS @ SS + 3.0 * SS + 2.0 * np.eye(dim, dtype=complex)) / 6.0
        H += P2
    return H


def check_spin_algebra(tol=1e-12):
    err = float(np.max(np.abs(Sx @ Sy - Sy @ Sx - 1j * Sz)))
    return err < tol, f"[Sx,Sy]=iSz residual {err:.3e}"


def check_casimir(tol=1e-12):
    err = float(np.max(np.abs(Sx @ Sx + Sy @ Sy + Sz @ Sz - 2.0 * I3)))
    return err < tol, f"S^2=2I residual {err:.3e}"


def check_haldane_gap(N=6, tol=1e-6):
    H = aklt_hamiltonian(N, periodic=True)
    ev = np.linalg.eigvalsh(H)
    e0, e1 = float(ev[0]), float(ev[1])
    gap = e1 - e0
    ok = abs(e0) < 1e-8 and gap > tol
    return ok, f"N={N} PBC: E0={e0:.3e}, E1={e1:.3e}, gap={gap:.3e}"


def check_edge_degeneracy(N=4, tol=1e-6):
    H = aklt_hamiltonian(N, periodic=False)
    ev = np.linalg.eigvalsh(H)
    e0 = float(ev[0])
    deg = int(np.sum(np.abs(ev - e0) < 1e-6))
    return deg == 4, f"N={N} OBC: E0={e0:.3e}, degeneracy={deg}"


def main() -> int:
    gates = [
        ("spin algebra",        check_spin_algebra),
        ("Casimir",             check_casimir),
        ("Haldane gap (N=6)",   check_haldane_gap),
        ("edge degeneracy",     check_edge_degeneracy),
    ]
    all_ok = True
    for name, fn in gates:
        try:
            ok, msg = fn()
        except Exception as e:
            ok, msg = False, f"EXCEPTION {type(e).__name__}: {e}"
        mark = "OK  " if ok else "FAIL"
        print(f"[{mark}] {name:<22} {msg}")
        all_ok = all_ok and ok
    print("-" * 70)
    print("AKLT gap verified — ground state is gapped, edge modes present"
          if all_ok else "AKLT GAP CHECK FAILED")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
