#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
clifford_euclid3.py — Euclidean Cl(3) minimal algebra.

Scope
-----
Vectors in R^3 with orthonormal basis e1, e2, e3 satisfying
    e_i e_j + e_j e_i = 2 δ_ij.

Multivectors are stored as tuples of coefficients in the canonical
basis {1, e12, e13, e23, e1, e2, e3, e123} with the ordering:
    index 0 → scalar      1
    index 1 → bivector    e12
    index 2 → bivector    e13
    index 3 → bivector    e23
    index 4 → vector      e1
    index 5 → vector      e2
    index 6 → vector      e3
    index 7 → pseudoscalar e123 = I

Geometric product is implemented directly from the basis
multiplication table. Rotor application uses the sandwich R x R~.

Limits
------
- No Cl(3,1) spacetime algebra here; that is a separate module.
- No matrix representation; if you need one, use Pauli matrices
  and the standard isomorphism Cl(3) ≅ M_2(C) restricted to even
  subalgebra for rotors.
- No φ-harmonics. This file does not import PHI, does not reference
  the North Star, and does not seal anything. It is a pure algebra
  helper.

Discipline
----------
No ledger write. No kubectl. No forbidden imports from the AST
guard's FORBIDDEN_IMPORTS set.
"""
from __future__ import annotations

import math
from typing import List, Tuple

# ── basis layout ────────────────────────────────────────────────────
# tuple index : basis blade
#   0 : 1
#   1 : e12
#   2 : e13
#   3 : e23
#   4 : e1
#   5 : e2
#   6 : e3
#   7 : e123 = I

BLADE_LABELS = ("1", "e12", "e13", "e23", "e1", "e2", "e3", "e123")
SCALAR = 0
E12 = 1
E13 = 2
E23 = 3
E1 = 4
E2 = 5
E3 = 6
PSEUDO = 7

Multivector = Tuple[float, ...]   # length 8


def zero() -> Multivector:
    return (0.0,) * 8


def scalar(s: float) -> Multivector:
    return (s, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)


def vector(x: float, y: float, z: float) -> Multivector:
    return (0.0, 0.0, 0.0, 0.0, x, y, z, 0.0)


def bivector(b12: float, b13: float, b23: float) -> Multivector:
    return (0.0, b12, b13, b23, 0.0, 0.0, 0.0, 0.0)


def pseudoscalar(s: float) -> Multivector:
    return (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, s)


def add(a: Multivector, b: Multivector) -> Multivector:
    return tuple(x + y for x, y in zip(a, b))


def sub(a: Multivector, b: Multivector) -> Multivector:
    return tuple(x - y for x, y in zip(a, b))


def scale(a: Multivector, s: float) -> Multivector:
    return tuple(x * s for x in a)


def grade(a: Multivector, k: int) -> Multivector:
    out = [0.0] * 8
    if k == 0:
        out[SCALAR] = a[SCALAR]
    elif k == 1:
        out[E1], out[E2], out[E3] = a[E1], a[E2], a[E3]
    elif k == 2:
        out[E12], out[E13], out[E23] = a[E12], a[E13], a[E23]
    elif k == 3:
        out[PSEUDO] = a[PSEUDO]
    return tuple(out)


def reverse(a: Multivector) -> Multivector:
    """Reversion: flips sign of grade 2 and grade 3 in Cl(3)."""
    return (
        a[SCALAR],
        -a[E12],
        -a[E13],
        -a[E23],
        a[E1],
        a[E2],
        a[E3],
        -a[PSEUDO],
    )


# ── basis multiplication table ──────────────────────────────────────
# Each basis blade is a product of distinct e_i with i1 < i2 < ...,
# so the sign of a product of two blades is determined by counting
# anticommutation swaps. Precompute the table for the 8 basis blades.
def _blade_sign(i: int, j: int) -> Tuple[float, int]:
    """Return (sign, result_blade_index) for blade_i * blade_j."""
    # Represent each blade as a set of generator indices 0, 1, 2.
    sets = [
        frozenset(),           # 0: 1
        frozenset({0, 1}),     # 1: e12
        frozenset({0, 2}),     # 2: e13
        frozenset({1, 2}),     # 3: e23
        frozenset({0}),        # 4: e1
        frozenset({1}),         # 5: e2
        frozenset({2}),         # 6: e3
        frozenset({0, 1, 2}),  # 7: e123
    ]
    a, b = sets[i], sets[j]
    # Count swaps: for each element of a, count how many elements of b
    # come before it in the canonical order {0, 1, 2}.
    sign = 1
    for x in a:
        for y in b:
            if y < x:
                sign = -sign
    # Symmetric difference gives the result blade (up to reordering).
    result = a ^ b
    # A generator that appears in both a and b squares to +1 in Cl(3),
    # so its contribution is a scalar factor of +1. Nothing to do.
    label = tuple(sorted(result))
    mapping = {
        (): 0,
        (0, 1): 1,
        (0, 2): 2,
        (1, 2): 3,
        (0,): 4,
        (1,): 5,
        (2,): 6,
        (0, 1, 2): 7,
    }
    return float(sign), mapping[label]


_BLADE_TABLE = [
    [_blade_sign(i, j) for j in range(8)]
    for i in range(8)
]


def geometric(a: Multivector, b: Multivector) -> Multivector:
    """Full geometric product a b in Cl(3)."""
    out = [0.0] * 8
    for i in range(8):
        if a[i] == 0.0:
            continue
        for j in range(8):
            if b[j] == 0.0:
                continue
            sign, k = _BLADE_TABLE[i][j]
            out[k] += a[i] * b[j] * sign
    return tuple(out)


def dot(a: Multivector, b: Multivector) -> float:
    """Scalar part of the geometric product (inner product of grade 1 parts)."""
    return geometric(a, b)[SCALAR]


def wedge(a: Multivector, b: Multivector) -> Multivector:
    """Outer product: only grade-1 × grade-1 for this minimal file."""
    ax, ay, az = a[E1], a[E2], a[E3]
    bx, by, bz = b[E1], b[E2], b[E3]
    return bivector(
        ax * by - ay * bx,
        ax * bz - az * bx,
        ay * bz - az * by,
    )


def norm_squared(a: Multivector) -> float:
    """⟨a reverse(a)⟩_0."""
    return geometric(a, reverse(a))[SCALAR]


def norm(a: Multivector) -> float:
    ns = norm_squared(a)
    if ns < 0.0:
        raise ValueError(f"negative norm² in Cl(3): {ns}")
    return math.sqrt(ns)


def inverse(a: Multivector) -> Multivector:
    ns = norm_squared(a)
    if ns == 0.0:
        raise ZeroDivisionError("multivector is not invertible (norm² = 0)")
    return scale(reverse(a), 1.0 / ns)


# ── rotors ──────────────────────────────────────────────────────────
def rotor_from_bivector_angle(b: Multivector, theta: float) -> Multivector:
    """Rotor R = exp(-B θ / 2) where B is a unit bivector.

    The caller must supply a unit bivector (norm² == 1) if they want
    a pure rotation; this function does not normalize.
    """
    # Split b into its bivector part.
    B = (0.0, b[E12], b[E13], b[E23], 0.0, 0.0, 0.0, 0.0)
    b2 = geometric(B, B)[SCALAR]
    # In Cl(3), for a unit bivector B, B² = -1.
    half = -theta / 2.0
    if b2 > 0:
        # hyperbolic-like (should not occur for unit bivector in Cl(3))
        ch = math.cosh(abs(half) * math.sqrt(b2))
        sh = math.sinh(abs(half) * math.sqrt(b2))
        return add(
            scalar(ch),
            scale(B, (sh if half >= 0 else -sh) / math.sqrt(b2)),
        )
    elif b2 < 0:
        s = math.sqrt(-b2)
        return add(
            scalar(math.cos(abs(half) * s)),
            scale(B, math.sin(half * s) / s),
        )
    else:
        # degenerate bivector, B² = 0
        return add(scalar(1.0), scale(B, half))


def rotor_apply(r: Multivector, x: Multivector) -> Multivector:
    """Sandwich x → R x R~."""
    return geometric(geometric(r, x), reverse(r))


def rotor_compose(r1: Multivector, r2: Multivector) -> Multivector:
    """Composition of two rotors: R1 applied after R2 is R1 R2."""
    return geometric(r1, r2)


def rotor_identity() -> Multivector:
    return scalar(1.0)


def rotor_check_unit(r: Multivector, tol: float = 1e-12) -> bool:
    """Return True iff R R~ == 1 to tolerance."""
    p = geometric(r, reverse(r))
    return (
        abs(p[SCALAR] - 1.0) < tol
        and all(abs(p[i]) < tol for i in range(1, 8))
    )


# ── contact / TOI bridge (structural only) ──────────────────────────
def rotate_orientation_between_impacts(
    r_prev: Multivector,
    contact_normal: Tuple[float, float, float],
    angle: float,
) -> Multivector:
    """Return R(γ⁺) = R_impact R(γ⁻).

    The contact normal defines the bivector plane; the angle is the
    rotation to apply at the impact. This is a structural helper, not
    a physical law: the scalar TOI solve for γ is external and is not
    performed here.
    """
    nx, ny, nz = contact_normal
    # Bivector dual to the normal: B = I n  (with I = e123)
    # I (n1 e1 + n2 e2 + n3 e3) = n1 e23 - n2 e13 + n3 e12
    B = bivector(n3, -ny, nx)
    R_impact = rotor_from_bivector_angle(B, angle)
    return rotor_compose(R_impact, r_prev)


# ── demo / smoke ────────────────────────────────────────────────────
def _smoke() -> None:
    e1 = vector(1.0, 0.0, 0.0)
    e2 = vector(0.0, 1.0, 0.0)
    e3 = vector(0.0, 0.0, 1.0)

    # e1 e1 = +1
    p = geometric(e1, e1)
    assert abs(p[SCALAR] - 1.0) < 1e-12
    assert all(abs(p[i]) < 1e-12 for i in range(1, 8))

    # e1 e2 = e12
    p = geometric(e1, e2)
    assert abs(p[E12] - 1.0) < 1e-12
    assert all(abs(p[i]) < 1e-12 for i in (SCALAR, E13, E23, E1, E2, E3, PSEUDO))

    # e2 e1 = -e12
    p = geometric(e2, e1)
    assert abs(p[E12] + 1.0) < 1e-12

    # e1 e2 e3 = e123 = I, I² = -1
    I = geometric(geometric(e1, e2), e3)
    assert abs(I[PSEUDO] - 1.0) < 1e-12
    I2 = geometric(I, I)
    assert abs(I2[SCALAR] + 1.0) < 1e-12

    # Rotor: rotate e1 by π/2 in the e12 plane → e2
    B = bivector(1.0, 0.0, 0.0)          # B = e12, B² = -1
    R = rotor_from_bivector_angle(B, math.pi / 2)
    assert rotor_check_unit(R)

    x = e1
    y = rotor_apply(R, x)
    # Expected: e2, up to numerical precision.
    assert abs(y[SCALAR]) < 1e-9
    assert abs(y[E1]) < 1e-9
    assert abs(y[E2] - 1.0) < 1e-9
    assert abs(y[E3]) < 1e-9

    # Rotate by π → -e1
    R2 = rotor_from_bivector_angle(B, math.pi)
    y2 = rotor_apply(R2, e1)
    assert abs(y2[E1] + 1.0) < 1e-9

    # Contact/TOI bridge: identity rotor, rotate π/2 about x-axis normal.
    R_prev = rotor_identity()
    R_after = rotate_orientation_between_impacts(R_prev, (1.0, 0.0, 0.0), math.pi / 2)
    assert rotor_check_unit(R_after)
    # The contact-normal rotation of a point initially along +e1
    # should land somewhere on the e2–e3 great circle; check norm
    # conservation of the vector part.
    v = rotor_apply(R_after, e1)
    v_norm = math.sqrt(v[E1] ** 2 + v[E2] ** 2 + v[E3] ** 2)
    assert abs(v_norm - 1.0) < 1e-9

    print("clifford_euclid3 smoke: PASS")


if __name__ == "__main__":
    _smoke()
