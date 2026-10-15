#!/usr/bin/env python3
"""
scripts/rank_check_su2_p2.py

Rank verifier for the P2 projector of SU(2) acting on 3 ⊗ 3.

Claim:
    spin-1 ⊗ spin-1 decomposes as  1 ⊗ 1 = 0 ⊕ 1 ⊕ 2,
    so the projector onto the J = 2 (quintet) subspace
    has rank 5 on a 9-dimensional Hilbert space.

Two independent methods:
    (A) Eigendecomposition of total S² = (S⁽¹⁾ + S⁽²⁾)²,
        extract the eigenspace for eigenvalue J(J+1) = 6.
    (B) Symmetric projector minus singlet:
            P_{J=2} = (I + P_exch) / 2  -  |0,0⟩⟨0,0|
        exploiting that J=0 and J=2 are the two symmetric irreps,
        while J=1 is antisymmetric.

Both must yield a rank-5 projector, with P² = P, P† = P, Tr(P) = 5.
Residuals are expected at machine precision (~1e-16); the 1e-10
threshold is not tight.

Constraint: numpy only. No external CAS. Runs in < 1 s.
"""

from __future__ import annotations

import argparse
import json
import sys

import numpy as np

# ---------- spin-1 generators (ħ = 1) ----------

SQRT2 = np.sqrt(2.0)

SX = (1.0 / SQRT2) * np.array(
    [[0, 1, 0],
     [1, 0, 1],
     [0, 1, 0]], dtype=complex
)

SY = (1.0 / SQRT2) * np.array(
    [[0, -1j,  0],
     [1j, 0, -1j],
     [0,  1j, 0]], dtype=complex
)

SZ = np.array(
    [[ 1, 0,  0],
     [ 0, 0,  0],
     [ 0, 0, -1]], dtype=complex
)

I3 = np.eye(3, dtype=complex)
DIM1 = 3
DIM2 = DIM1 * DIM1  # 9

# ---------- embedding into 3 ⊗ 3 ----------

def embed(op: np.ndarray, slot: int) -> np.ndarray:
    """Embed a single-factor operator into slot 1 or 2 of 3 ⊗ 3."""
    if slot == 1:
        return np.kron(op, I3)
    if slot == 2:
        return np.kron(I3, op)
    raise ValueError(f"slot must be 1 or 2, got {slot}")

def S_total(axis: str) -> np.ndarray:
    """Total spin component S_a on 3 ⊗ 3:  S_a^(1) + S_a^(2)."""
    S_a = {"x": SX, "y": SY, "z": SZ}[axis]
    return embed(S_a, 1) + embed(S_a, 2)

def build_S2() -> np.ndarray:
    """Total Casimir S² = Sx² + Sy² + Sz²."""
    Sx = S_total("x")
    Sy = S_total("y")
    Sz = S_total("z")
    return Sx @ Sx + Sy @ Sy + Sz @ Sz

# ---------- method A: eigendecomposition of S² ----------

def projector_method_A(J: int, tol: float = 1e-10):
    """
    Return (P_J, evals, residuals).

    P_J is the spectral projector of S² onto the eigenvalue J(J+1).
    """
    S2 = build_S2()
    evals, evecs = np.linalg.eigh(S2)          # S² is Hermitian

    target = float(J * (J + 1))
    mask = np.isclose(evals, target, atol=tol)

    V = evecs[:, mask]
    P = V @ V.conj().T

    resid_idem = float(np.linalg.norm(P @ P - P))
    resid_herm = float(np.linalg.norm(P - P.conj().T))
    return P, evals, (resid_idem, resid_herm)

# ---------- method B: exchange + singlet subtraction ----------

def build_exchange() -> np.ndarray:
    """
    Particle-exchange permutation P_exch acting on 3 ⊗ 3 in the
    kron basis  |i⟩ ⊗ |j⟩  ↦  index  3*i + j.
    P_exch maps |i⟩⊗|j⟩ → |j⟩⊗|i⟩.
    """
    P = np.zeros((DIM2, DIM2), dtype=complex)
    for i in range(3):
        for j in range(3):
            k_from = 3 * i + j
            k_to   = 3 * j + i
            P[k_to, k_from] = 1.0
    return P

def singlet_vector() -> np.ndarray:
    """
    |0,0⟩ = (|1,-1⟩ − |0,0⟩ + |-1,1⟩) / √3,
    with kron index 3*(m1+1) + (m2+1).
    """
    v = np.zeros(DIM2, dtype=complex)
    v[3 * 2 + 0] =  1.0 / np.sqrt(3.0)   # |1,-1⟩
    v[3 * 1 + 1] = -1.0 / np.sqrt(3.0)   # |0,0⟩
    v[3 * 0 + 2] =  1.0 / np.sqrt(3.0)   # |-1,1⟩
    return v

def projector_method_B():
    """Return (P_J2, residuals)."""
    I9 = np.eye(DIM2, dtype=complex)
    P_exch = build_exchange()
    P_sym  = 0.5 * (I9 + P_exch)
    v0 = singlet_vector()
    P_singlet = np.outer(v0, v0.conj())
    P = P_sym - P_singlet

    resid_idem = float(np.linalg.norm(P @ P - P))
    resid_herm = float(np.linalg.norm(P - P.conj().T))
    return P, (resid_idem, resid_herm)

# ---------- checks ----------

def check_spectral_multiplicities(evals: np.ndarray,
                                  tol: float = 1e-8) -> dict:
    """Casimir eigenvalues on 3 ⊗ 3 should be 0 (×1), 2 (×3), 6 (×5)."""
    expected = {0.0: 1, 2.0: 3, 6.0: 5}
    found = {}
    for e in evals.real:
        matched = False
        for k in expected:
            if abs(e - k) < tol:
                found[k] = found.get(k, 0) + 1
                matched = True
                break
        if not matched:
            found.setdefault(round(float(e), 6), 0)
            found[round(float(e), 6)] += 1
    return {"expected": expected, "observed": found,
            "match": found == expected}

def rank_via_svd(P: np.ndarray, tol: float = 1e-10) -> int:
    return int(np.linalg.matrix_rank(P, tol=tol))

# ---------- main ----------

def run(emit_json: bool = False) -> int:
    report = {"script": "rank_check_su2_p2.py", "checks": {}}

    # --- method A ---
    P_A, evals, res_A = projector_method_A(J=2)
    rank_A = rank_via_svd(P_A)
    trace_A = float(np.trace(P_A).real)
    report["checks"]["method_A_eigendecomposition"] = {
        "rank": rank_A,
        "trace": trace_A,
        "idempotency_residual": res_A[0],
        "hermiticity_residual": res_A[1],
        "spectral_multiplicities": check_spectral_multiplicities(evals),
    }

    # --- method B ---
    P_B, res_B = projector_method_B()
    rank_B = rank_via_svd(P_B)
    trace_B = float(np.trace(P_B).real)
    report["checks"]["method_B_sym_minus_singlet"] = {
        "rank": rank_B,
        "trace": trace_B,
        "idempotency_residual": res_B[0],
        "hermiticity_residual": res_B[1],
    }

    # --- cross: methods agree on the projector ---
    delta = float(np.linalg.norm(P_A - P_B))
    report["checks"]["method_agreement"] = {
        "frobenius_norm_difference": delta,
        "agree": delta < 1e-10,
    }

    # --- overall verdict ---
    ok = (
        rank_A == 5
        and rank_B == 5
        and abs(trace_A - 5.0) < 1e-10
        and abs(trace_B - 5.0) < 1e-10
        and res_A[0] < 1e-10
        and res_A[1] < 1e-10
        and res_B[0] < 1e-10
        and res_B[1] < 1e-10
        and delta < 1e-10
        and report["checks"]["method_A_eigendecomposition"]
                ["spectral_multiplicities"]["match"]
    )
    report["verdict"] = "PASS" if ok else "FAIL"
    report["claim"] = "rank(P2) == 5 on 3 ⊗ 3"

    if emit_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("rank_check_su2_p2 — SU(2) P2 projector rank verifier")
        print("=" * 56)
        print(f"dim(3 ⊗ 3)                     = {DIM2}")
        print(f"Casimir eigenvalues expected   = {{0:×1, 2:×3, 6:×5}}")
        print(f"Casimir eigenvalues observed   = "
              f"{report['checks']['method_A_eigendecomposition']['spectral_multiplicities']['observed']}")
        print()
        print(f"Method A  rank(P2)             = {rank_A}")
        print(f"Method A  Tr(P2)               = {trace_A:.12f}")
        print(f"Method A  ‖P²−P‖               = {res_A[0]:.3e}")
        print(f"Method A  ‖P−P†‖               = {res_A[1]:.3e}")
        print()
        print(f"Method B  rank(P2)             = {rank_B}")
        print(f"Method B  Tr(P2)               = {trace_B:.12f}")
        print(f"Method B  ‖P²−P‖               = {res_B[0]:.3e}")
        print(f"Method B  ‖P−P†‖               = {res_B[1]:.3e}")
        print()
        print(f"‖P_A − P_B‖_F                  = {delta:.3e}")
        print("-" * 56)
        print(f"VERDICT: {report['verdict']}   ({report['claim']})")

    return 0 if ok else 1

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Verify rank(P2) == 5 for the J=2 projector on 3 ⊗ 3."
    )
    ap.add_argument("--json", action="store_true",
                    help="emit machine-readable JSON report")
    args = ap.parse_args()
    sys.exit(run(emit_json=args.json))

if __name__ == "__main__":
    main()
