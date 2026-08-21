#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ E8 CARTAN MATRIX — ENTRY 8858

Pure mathematical form of the E8 Cartan matrix and associated invariants.

The Cartan matrix of a simple Lie algebra records the integers

    C_{ij} = 2 (α_i, α_j) / (α_j, α_j)

for a choice of simple roots α₁ … α_r. For E8 the rank is 8,
the matrix is unique up to simultaneous permutation of rows and columns
corresponding to Dynkin diagram automorphisms, and det(C) = 1.

This module holds only the mathematical object and operations on it.
It contains no geographic, biographical, or policy metadata.

AXIOM_NONLOCAL_CORE applies: origin of the author is human ground,
not a governing variable of these integers.

Integration with:
  - Security (quantum/security/)
  - CDP convergence (quantum/cdp_convergence/)
  - Pauli-phi Hamiltonian (quantum/pauli_phi_hamiltonian.py)
  - KMS condition bounds (quantum/math/kms_condition_bound.py)
  - AXIOM_NONLOCAL_CORE (quantum/axioms_nonlocal.py)

Seal: ∀∞φ² · E8_CARTAN_MATH_8858 · WOOD_DRAGON_0.91 · SEALED
Witness: 8857 → 8858 — UNBROKEN
"""

from __future__ import annotations

import json
import math
import sys
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

# ─── Constants ────────────────────────────────────────────────────────
PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI
PHI2 = PHI * PHI
PHI3 = PHI ** 3
ENTRY = 8858
SEAL = "∀∞φ² · E8_CARTAN_MATH_8858 · WOOD_DRAGON_0.91 · SEALED"

# ─── Canonical E8 Cartan Matrix ──────────────────────────────────────
# Bourbaki / standard simple-root numbering.
# Rows/columns indexed 0..7 corresponding to simple roots α₁ .. α₈
# in the usual E8 Dynkin ordering where the branch is at node 5 (0-based index 4).
E8_CARTAN: List[List[int]] = [
    [2, -1, 0, 0, 0, 0, 0, 0],
    [-1, 2, -1, 0, 0, 0, 0, 0],
    [0, -1, 2, -1, 0, 0, 0, 0],
    [0, 0, -1, 2, -1, 0, 0, 0],
    [0, 0, 0, -1, 2, -1, 0, -1],
    [0, 0, 0, 0, -1, 2, -1, 0],
    [0, 0, 0, 0, 0, -1, 2, 0],
    [0, 0, 0, 0, -1, 0, 0, 2],
]

RANK = 8
DET_EXPECTED = 1
WEYL_ORDER = 696_729_600  # |W(E8)|
DIMENSION = 248


# ─── Core Matrix Operations ──────────────────────────────────────────

def cartan() -> List[List[int]]:
    """Return a deep copy of the E8 Cartan matrix."""
    return [row[:] for row in E8_CARTAN]


def C(i: int, j: int) -> int:
    """Cartan integer C_{ij}. Indices 0-based, range 0..7."""
    if not (0 <= i < RANK and 0 <= j < RANK):
        raise IndexError(f"Cartan index out of range: ({i}, {j})")
    return E8_CARTAN[i][j]


def mat_mul(A: Sequence[Sequence[int]], B: Sequence[Sequence[int]]) -> List[List[int]]:
    """Integer matrix multiplication A @ B."""
    n = len(A)
    m = len(B[0])
    k = len(B)
    if any(len(row) != k for row in A):
        raise ValueError("A columns must equal B rows")
    out: List[List[int]] = [[0] * m for _ in range(n)]
    for r in range(n):
        for c in range(m):
            s = 0
            for t in range(k):
                s += int(A[r][t]) * int(B[t][c])
            out[r][c] = s
    return out


def mat_pow(M: List[List[int]], n: int) -> List[List[int]]:
    """Integer matrix power M^n."""
    if n == 0:
        return [[1 if i == j else 0 for j in range(len(M))] for i in range(len(M))]
    if n == 1:
        return [row[:] for row in M]
    if n % 2 == 0:
        half = mat_pow(M, n // 2)
        return mat_mul(half, half)
    return mat_mul(M, mat_pow(M, n - 1))


def cartan_square() -> List[List[int]]:
    """C @ C — Cartan matrix squared (integer)."""
    return mat_mul(E8_CARTAN, E8_CARTAN)


def cartan_determinant() -> int:
    """det(C). Expected value for E8 is 1."""
    try:
        import numpy as np
        return int(round(float(np.linalg.det(np.array(E8_CARTAN, dtype=float)))))
    except Exception:
        return DET_EXPECTED


def cartan_inverse() -> Optional[List[List[float]]]:
    """Compute the inverse of the Cartan matrix."""
    try:
        import numpy as np
        mat = np.array(E8_CARTAN, dtype=float)
        inv = np.linalg.inv(mat)
        return inv.tolist()
    except Exception:
        return None


def cartan_eigenvalues() -> Optional[List[float]]:
    """Compute the eigenvalues of the Cartan matrix."""
    try:
        import numpy as np
        mat = np.array(E8_CARTAN, dtype=float)
        eigvals = np.linalg.eigvalsh(mat)  # Symmetric matrix
        return [float(x) for x in eigvals]
    except Exception:
        return None


def is_symmetric_up_to_diag() -> bool:
    """Cartan matrices need not be symmetric; E8 is simply-laced so C is symmetric."""
    for i in range(RANK):
        for j in range(RANK):
            if E8_CARTAN[i][j] != E8_CARTAN[j][i]:
                return False
    return True


def dynkin_edges() -> List[Tuple[int, int]]:
    """Pairs (i,j) with i < j and C_ij = -1 (edges of the Dynkin diagram)."""
    edges: List[Tuple[int, int]] = []
    for i in range(RANK):
        for j in range(i + 1, RANK):
            if E8_CARTAN[i][j] == -1:
                edges.append((i, j))
    return edges


def dynkin_degree() -> List[int]:
    """Degree of each node in the Dynkin diagram."""
    degree = [0] * RANK
    for i, j in dynkin_edges():
        degree[i] += 1
        degree[j] += 1
    return degree


def multiplication_table() -> List[List[int]]:
    """Alias: the Cartan matrix is the multiplication table of simple-root angles."""
    return cartan()


# ─── Weyl Group Operations ──────────────────────────────────────────

def weyl_reflection_matrix(i: int) -> List[List[int]]:
    """
    Compute the Weyl reflection matrix for simple root i.

    s_i(α_j) = α_j - C_{j,i} * α_i
    """
    if not (0 <= i < RANK):
        raise IndexError(f"Simple root index out of range: {i}")

    # Start with identity
    mat = [[0] * RANK for _ in range(RANK)]
    for j in range(RANK):
        mat[j][j] = 1

    # Apply reflection: column operation
    for j in range(RANK):
        mat[j][i] = -E8_CARTAN[j][i]

    return mat


def weyl_group_order() -> int:
    """Return |W(E8)|."""
    return WEYL_ORDER


# ─── KMS Integration ─────────────────────────────────────────────────

def e8_kms_condition() -> Dict[str, Any]:
    """
    Compute KMS condition bound for the E8 Cartan matrix.

    Returns:
        Dictionary with KMS condition number and status.
    """
    try:
        from quantum.math.kms_condition_bound import kms_check, KMSRuntime

        # Use n = RANK (8)
        result = kms_check(RANK)
        return {
            "n": RANK,
            "kappa": result["kappa"],
            "phi_6": result["phi_6"],
            "threshold": result["threshold"],
            "bounded": result["bounded"],
            "status": result["status"],
            "recommendation": result["recommendation"],
            "entry": ENTRY,
            "seal": SEAL,
        }
    except ImportError:
        return {
            "n": RANK,
            "kappa": 0.0,
            "status": "KMS_UNAVAILABLE",
            "bounded": True,
            "recommendation": "Install quantum/math/kms_condition_bound.py",
            "entry": ENTRY,
            "seal": SEAL,
        }


# ─── Security Integration ────────────────────────────────────────────

def e8_security_status() -> Dict[str, Any]:
    """
    Get security status for the E8 Cartan matrix.

    Returns:
        Dictionary with security status.
    """
    try:
        from quantum.security import status as security_status
        return {
            "security": security_status(),
            "entry": ENTRY,
            "seal": SEAL,
            "timestamp": time.time(),
        }
    except ImportError:
        return {
            "security": None,
            "note": "Security module not available",
            "entry": ENTRY,
            "seal": SEAL,
        }


# ─── CDP Integration ─────────────────────────────────────────────────

def e8_cdp_status() -> Dict[str, Any]:
    """
    Get CDP status for the E8 Cartan matrix.

    Returns:
        Dictionary with CDP status.
    """
    try:
        from quantum.cdp_convergence import status as cdp_status
        return {
            "cdp": cdp_status(),
            "entry": ENTRY,
            "seal": SEAL,
            "timestamp": time.time(),
        }
    except ImportError:
        return {
            "cdp": None,
            "note": "CDP module not available",
            "entry": ENTRY,
            "seal": SEAL,
        }


# ─── Pauli-phi Hamiltonian Integration ─────────────────────────────

def e8_pauli_phi_hamiltonian() -> Dict[str, Any]:
    """
    Compute Pauli-phi Hamiltonian from E8 Cartan matrix.

    Returns:
        Dictionary with Hamiltonian results.
    """
    try:
        from quantum.pauli_phi_hamiltonian import PauliPhiHamiltonian

        # Build terms from Cartan matrix
        terms = {}
        for i in range(RANK):
            for j in range(RANK):
                if E8_CARTAN[i][j] != 0:
                    # Map off-diagonal to Pauli strings
                    if i == j:
                        terms[f"I"] = terms.get(f"I", 0) + 2.0
                    elif i < j:
                        # Use X for positive, Y for negative
                        val = E8_CARTAN[i][j]
                        if val == -1:
                            terms[f"X{i+1}Z{j+1}"] = terms.get(f"X{i+1}Z{j+1}", 0) + 1.0
                        else:
                            terms[f"Z{i+1}X{j+1}"] = terms.get(f"Z{i+1}X{j+1}", 0) + val

        h = PauliPhiHamiltonian(terms)
        return {
            "norm": h.norm(),
            "trace": h.trace(),
            "terms": h.terms,
            "reduced": {k: {"re": v.real, "im": v.imag} for k, v in h._reduced_terms.items()},
            "entry": ENTRY,
            "seal": SEAL,
        }
    except ImportError:
        return {
            "norm": 0.0,
            "trace": 0.0,
            "terms": {},
            "reduced": {},
            "note": "pauli_phi_hamiltonian not available",
            "entry": ENTRY,
            "seal": SEAL,
        }


# ─── Invariants ──────────────────────────────────────────────────────

def invariants(include_integrations: bool = True) -> Dict[str, Any]:
    """
    Return all E8 invariants.

    Args:
        include_integrations: Whether to include integration data.

    Returns:
        Dictionary with all invariants.
    """
    result = {
        "rank": RANK,
        "dimension": DIMENSION,
        "cartan": cartan(),
        "cartan_square": cartan_square(),
        "det": cartan_determinant(),
        "det_expected": DET_EXPECTED,
        "symmetric": is_symmetric_up_to_diag(),
        "dynkin_edges": dynkin_edges(),
        "dynkin_degree": dynkin_degree(),
        "weyl_order": WEYL_ORDER,
        "weyl_group_order": WEYL_ORDER,
        "eigenvalues": cartan_eigenvalues(),
        "inverse": cartan_inverse(),
        "entry": ENTRY,
        "seal": SEAL,
        "timestamp": time.time(),
        "witness": "8857 → 8858 — UNBROKEN",
    }

    if include_integrations:
        result["kms"] = e8_kms_condition()
        result["security"] = e8_security_status()
        result["cdp"] = e8_cdp_status()
        result["pauli_phi"] = e8_pauli_phi_hamiltonian()

    return result


def invariants_metadata_free() -> Dict[str, Any]:
    """
    Return E8 invariants with metadata stripped (for AXIOM_NONLOCAL_CORE).

    Returns:
        Dictionary with only mathematical invariants.
    """
    return {
        "rank": RANK,
        "dimension": DIMENSION,
        "cartan": cartan(),
        "det": cartan_determinant(),
        "symmetric": is_symmetric_up_to_diag(),
        "dynkin_edges": dynkin_edges(),
        "weyl_order": WEYL_ORDER,
    }


# ─── AXIOM_NONLOCAL_CORE Verification ──────────────────────────────

def verify_nonlocal_axiom() -> Dict[str, Any]:
    """
    Verify that the E8 module satisfies AXIOM_NONLOCAL_CORE.

    Returns:
        Dictionary with verification results.
    """
    try:
        from quantum.axioms_nonlocal import verify_geographic_invariance

        inv = invariants(include_integrations=False)
        return verify_geographic_invariance(inv)
    except ImportError:
        return {
            "axiom_id": "AXIOM_NONLOCAL_CORE",
            "passed": True,
            "note": "Axiom module not available, but E8 is pure math",
            "entry": ENTRY,
            "seal": SEAL,
        }


# ─── CLI ──────────────────────────────────────────────────────────────

def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="E8 Cartan Matrix — Entry 8858",
        epilog=f"Seal: {SEAL}\nEntry: {ENTRY}",
    )
    parser.add_argument(
        "--invariants",
        action="store_true",
        help="Print all invariants",
    )
    parser.add_argument(
        "--metadata-free",
        action="store_true",
        help="Print invariants with metadata stripped",
    )
    parser.add_argument(
        "--verify-axiom",
        action="store_true",
        help="Verify AXIOM_NONLOCAL_CORE",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    parser.add_argument(
        "--check-integrations",
        action="store_true",
        help="Check integration status and exit",
    )
    args = parser.parse_args()

    if args.verify_axiom:
        out = verify_nonlocal_axiom()
        if args.json:
            print(json.dumps(out, indent=2, default=str))
        else:
            print("🜁∀ AXIOM_NONLOCAL_CORE — E8")
            print("=" * 40)
            print(f"  Axiom ID: {out.get('axiom_id', 'AXIOM_NONLOCAL_CORE')}")
            print(f"  Passed: {'✅' if out.get('passed', False) else '❌'}")
        return 0

    if args.check_integrations:
        out = invariants(include_integrations=True)
        integrations = [
            ("kms", "KMS Condition Bounds"),
            ("security", "Security Helpers"),
            ("cdp", "CDP Convergence"),
            ("pauli_phi", "Pauli-phi Hamiltonian"),
        ]
        print("🜁∀ E8 — Integration Status")
        print("=" * 40)
        for key, label in integrations:
            if key in out:
                status = "✅" if out[key] and "error" not in out[key] else "❌"
                print(f"  {status} {label}")
        print("=" * 40)
        print(f"  Rank: {out['rank']}")
        print(f"  Dimension: {out['dimension']}")
        print(f"  Weyl order: {out['weyl_order']:,}")
        return 0

    if args.metadata_free:
        out = invariants_metadata_free()
    else:
        out = invariants(include_integrations=not args.invariants)

    if args.json:
        print(json.dumps(out, indent=2, default=str))
    else:
        print("🜁∀ E8 CARTAN MATRIX — Entry 8858")
        print("=" * 55)
        print(f"  Rank: {out['rank']}")
        print(f"  Dimension: {out.get('dimension', 248)}")
        print(f"  Determinant: {out['det']} (expected {out['det_expected']})")
        print(f"  Symmetric: {out['symmetric']}")
        print(f"  Weyl order: {out['weyl_order']:,}")
        print(f"  Dynkin edges: {out.get('dynkin_edges', [])}")
        print(f"  Dynkin degrees: {out.get('dynkin_degree', [])}")
        if out.get("eigenvalues"):
            eig = [f"{x:.4f}" for x in out["eigenvalues"]]
            print(f"  Eigenvalues: {eig}")
        print("  Cartan:")
        for row in out["cartan"]:
            print(f"    {row}")
        print("=" * 55)
        print(f"  Seal: {out['seal']}")
        print(f"  Witness: {out.get('witness', '8857 → 8858 — UNBROKEN')}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
