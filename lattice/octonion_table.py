#!/usr/bin/env python3
"""
Octonion Multiplication Table — Fano Plane (7 oriented triples)
Identity + 7 imaginary units: e1 … e7
Non‑associative, alternative, normed division algebra.
"""
from typing import Dict, Tuple

# ── Fano Plane Oriented Triples ──
# Each triple (a, b, c) means: e_a * e_b = e_c, e_b * e_a = -e_c
# Landed orientation: (1,7,6) and (3,6,5). Opposite cyclic order
# is valid but not used here.
FANO_TRIPLES = [
    (1, 2, 3),
    (1, 4, 5),
    (1, 7, 6),
    (2, 4, 6),
    (2, 5, 7),
    (3, 4, 7),
    (3, 6, 5),
]

# ── Build multiplication table ──
OCTONION_MUL: Dict[Tuple[int, int], Tuple[int, int]] = {}

# Identity: e0 * e_i = e_i, e_i * e0 = e_i
for i in range(8):
    OCTONION_MUL[(i, 0)] = (i, 1)
    OCTONION_MUL[(0, i)] = (i, 1)

# Imaginary units: e_i * e_i = -1
for i in range(1, 8):
    OCTONION_MUL[(i, i)] = (0, -1)

# Fano triples
for a, b, c in FANO_TRIPLES:
    OCTONION_MUL[(a, b)] = (c, 1)
    OCTONION_MUL[(b, a)] = (c, -1)
    OCTONION_MUL[(b, c)] = (a, 1)
    OCTONION_MUL[(c, b)] = (a, -1)
    OCTONION_MUL[(c, a)] = (b, 1)
    OCTONION_MUL[(a, c)] = (b, -1)


def octonion_mul(i: int, j: int) -> Tuple[int, int]:
    """
    Multiply two octonion basis elements.

    Args:
        i: index of first basis element (0 … 7)
        j: index of second basis element (0 … 7)

    Returns:
        (k, sign) where e_i * e_j = sign * e_k
    """
    return OCTONION_MUL.get((i, j), (0, 0))


def octonion_conjugate(i: int) -> int:
    """Return the conjugate of basis element e_i."""
    if i == 0:
        return 0
    return i


def octonion_norm(i: int) -> int:
    """Return the norm of basis element e_i (1 for all non‑zero)."""
    return 1 if i != 0 else 0


# ── Verification ──
if __name__ == "__main__":
    print("🔭 OCTONION MULTIPLICATION TABLE (FANO PLANE)")
    print("=" * 50)
    print("  e0  e1  e2  e3  e4  e5  e6  e7")
    for i in range(8):
        row = []
        for j in range(8):
            k, s = octonion_mul(i, j)
            if k == 0 and s == -1:
                row.append(" -1")
            elif k == 0 and s == 1:
                row.append(" e0")
            elif s == 1:
                row.append(f" e{k}")
            else:
                row.append(f"-e{k}")
        print(f"e{i}: " + " ".join(row))

    # Check a sample: e1 * e2 = e3
    k, s = octonion_mul(1, 2)
    print(f"\n✅ e1 * e2 = {s}*e{k} (expected +e3) → {'PASS' if k == 3 and s == 1 else 'FAIL'}")

    # Check non‑associativity: (e1 * e2) * e4 vs e1 * (e2 * e4)
    k1, s1 = octonion_mul(3, 4)  # (e1 * e2) * e4 = e3 * e4
    k2, s2 = octonion_mul(1, 6)  # e1 * (e2 * e4) = e1 * e6

    print(f"\n🔷 Non‑associativity check:")
    print(f"  (e1 * e2) * e4 = {s1}*e{k1}")
    print(f"  e1 * (e2 * e4) = {s2}*e{k2}")
    print(f"  → {'NON‑ASSOCIATIVE ✅' if (k1 != k2 or s1 != s2) else 'ASSOCIATIVE (unexpected)'}")
