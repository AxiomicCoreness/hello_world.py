#!/usr/bin/env python3
"""
Octonion Multiplication Table — Fano Plane (7 oriented triples)
Identity e0 + 7 imaginary units e1 … e7.
Non-associative, alternative, normed division algebra.

Convention: the seven oriented triples below are the table used on
Wikipedia ("Octonion", multiplication table), i.e.
    (1,2,3) (1,4,5) (1,7,6) (2,4,6) (2,5,7) (3,4,7) (3,6,5)
Each triple (a, b, c) in cyclic order gives
    e_a e_b = e_c,  e_b e_c = e_a,  e_c e_a = e_b
and reversing any pair flips the sign (e_b e_a = -e_c).

Note: flipping only (1,7,6)->(1,6,7) and (3,6,5)->(3,5,6) does NOT give an
octonion algebra: the result is still anticommuting on basis units but fails
alternativity on general elements, the Moufang identities and norm
multiplicativity (see tests/test_octonion_table.py::test_flipped_orientation_is_not_octonions).
"""
from __future__ import annotations

import math
from typing import Dict, List, Sequence, Tuple

FANO_TRIPLES: List[Tuple[int, int, int]] = [
    (1, 2, 3),
    (1, 4, 5),
    (1, 7, 6),
    (2, 4, 6),
    (2, 5, 7),
    (3, 4, 7),
    (3, 6, 5),
]


def build_table(triples: Sequence[Tuple[int, int, int]]) -> Dict[Tuple[int, int], Tuple[int, int]]:
    """Return {(i, j): (k, sign)} with e_i * e_j = sign * e_k."""
    table: Dict[Tuple[int, int], Tuple[int, int]] = {}
    for i in range(8):                      # e0 is the identity
        table[(i, 0)] = (i, 1)
        table[(0, i)] = (i, 1)
    for i in range(1, 8):                   # e_i^2 = -1
        table[(i, i)] = (0, -1)
    for a, b, c in triples:
        for x, y, z in ((a, b, c), (b, c, a), (c, a, b)):
            table[(x, y)] = (z, 1)
            table[(y, x)] = (z, -1)
    if len(table) != 64:
        raise ValueError(f"triples do not cover all 64 products ({len(table)})")
    return table


OCTONION_MUL: Dict[Tuple[int, int], Tuple[int, int]] = build_table(FANO_TRIPLES)


def octonion_mul(i: int, j: int) -> Tuple[int, int]:
    """Basis product: returns (k, sign) where e_i * e_j = sign * e_k."""
    return OCTONION_MUL[(i, j)]


def basis_mul3_left(i: int, j: int, k: int) -> Tuple[int, int]:
    """(e_i * e_j) * e_k as (index, sign)."""
    m, s1 = octonion_mul(i, j)
    n, s2 = octonion_mul(m, k)
    return n, s1 * s2


def basis_mul3_right(i: int, j: int, k: int) -> Tuple[int, int]:
    """e_i * (e_j * e_k) as (index, sign)."""
    m, s1 = octonion_mul(j, k)
    n, s2 = octonion_mul(i, m)
    return n, s1 * s2


def octonion_conjugate(i: int) -> Tuple[int, int]:
    """Conjugate of e_i as (index, sign): conj(e0) = +e0, conj(e_i) = -e_i."""
    if not 0 <= i <= 7:
        raise ValueError(f"basis index out of range: {i}")
    return (0, 1) if i == 0 else (i, -1)


def octonion_norm(i: int) -> int:
    """Norm of basis element e_i: every e_i (including e0) has norm 1."""
    if not 0 <= i <= 7:
        raise ValueError(f"basis index out of range: {i}")
    return 1


# ── general octonions as length-8 coefficient sequences ──
def mul(x: Sequence[float], y: Sequence[float]) -> List[float]:
    out = [0.0] * 8
    for i in range(8):
        if x[i] == 0:
            continue
        for j in range(8):
            if y[j] == 0:
                continue
            k, s = OCTONION_MUL[(i, j)]
            out[k] += s * x[i] * y[j]
    return out


def conj(x: Sequence[float]) -> List[float]:
    return [x[0]] + [-v for v in x[1:]]


def norm(x: Sequence[float]) -> float:
    return math.sqrt(sum(v * v for v in x))


def _fmt(k: int, s: int) -> str:
    return f"{'+' if s > 0 else '-'}e{k}"


if __name__ == "__main__":
    print("OCTONION MULTIPLICATION TABLE (FANO PLANE) — row * column")
    print("=" * 50)
    print("     " + " ".join(f"{'e' + str(j):>4}" for j in range(8)))
    for i in range(8):
        print(f"e{i}: " + " ".join(f"{_fmt(*octonion_mul(i, j)):>4}" for j in range(8)))

    k, s = octonion_mul(1, 2)
    print(f"\ne1 * e2 = {_fmt(k, s)} (expected +e3) -> {'PASS' if (k, s) == (3, 1) else 'FAIL'}")

    # (e1 e2) e4 vs e1 (e2 e4), computed rather than hard-coded.
    # (e1e2)e4 = e3e4 = +e7 ; e1(e2e4) = e1e6 = -e7  (from (1,7,6): e6e1 = e7)
    left = basis_mul3_left(1, 2, 4)
    right = basis_mul3_right(1, 2, 4)
    print("\nNon-associativity check:")
    print(f"  (e1 * e2) * e4 = {_fmt(*left)}")
    print(f"  e1 * (e2 * e4) = {_fmt(*right)}")
    print(f"  -> {'NON-ASSOCIATIVE' if left != right else 'ASSOCIATIVE (unexpected)'}")
