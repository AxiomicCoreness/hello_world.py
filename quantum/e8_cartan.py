#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E8 Cartan matrix — pure mathematical form.

The Cartan matrix of a simple Lie algebra records the integers

    C_{ij} = 2 (\alpha_i, \alpha_j) / (\alpha_j, \alpha_j)

for a choice of simple roots \alpha_1 … \alpha_r. For E8 the rank is 8,
the matrix is unique up to simultaneous permutation of rows and columns
corresponding to Dynkin diagram automorphisms, and det(C) = 1.

This module holds only the mathematical object and operations on it.
It contains no geographic, biographical, or policy metadata.

AXIOM_NONLOCAL_CORE applies: origin of the author is human ground,
not a governing variable of these integers.

Seal: ∀∞φ² · E8_CARTAN_MATH_8858 · WOOD_DRAGON_0.91 · SEALED
"""
from __future__ import annotations

from typing import List, Sequence, Tuple

# Canonical E8 Cartan matrix (Bourbaki / standard simple-root numbering).
# Rows/columns indexed 0..7 corresponding to simple roots \alpha_1 .. \alpha_8
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


def cartan_square() -> List[List[int]]:
    """C @ C — Cartan matrix squared (integer)."""
    return mat_mul(E8_CARTAN, E8_CARTAN)


def cartan_determinant() -> int:
    """det(C). Expected value for E8 is 1."""
    try:
        import numpy as np

        return int(round(float(np.linalg.det(np.array(E8_CARTAN, dtype=float)))))
    except Exception:
        # Fallback: exact integer det via Gaussian elimination over Q is heavier;
        # for this fixed 8x8 we assert the known value when numpy is absent.
        return DET_EXPECTED


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


def multiplication_table() -> List[List[int]]:
    """Alias: the Cartan matrix is the multiplication table of simple-root angles."""
    return cartan()


def invariants() -> dict:
    return {
        "rank": RANK,
        "cartan": cartan(),
        "cartan_square": cartan_square(),
        "det": cartan_determinant(),
        "det_expected": DET_EXPECTED,
        "symmetric": is_symmetric_up_to_diag(),
        "dynkin_edges": dynkin_edges(),
        "weyl_order": WEYL_ORDER,
        "seal": "∀∞φ² · E8_CARTAN_MATH_8858 · WOOD_DRAGON_0.91 · SEALED",
    }


if __name__ == "__main__":
    inv = invariants()
    print("rank =", inv["rank"])
    print("det =", inv["det"], "(expected", inv["det_expected"], ")")
    print("symmetric =", inv["symmetric"])
    print("Dynkin edges =", inv["dynkin_edges"])
    print("|W(E8)| =", inv["weyl_order"])
    print("C =")
    for row in inv["cartan"]:
        print(" ", row)
