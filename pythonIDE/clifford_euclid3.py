#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
clifford_euclid3.py — Euclidean Cl(3) minimal algebra.

No Cl(3,1), no PHI, no ledger write, no kubectl. Standard library only.
"""
from __future__ import annotations

import math
from typing import Tuple

BLADE_LABELS = ("1", "e12", "e13", "e23", "e1", "e2", "e3", "e123")
SCALAR, E12, E13, E23, E1, E2, E3, PSEUDO = range(8)

Multivector = Tuple[float, ...]


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


def _blade_sign(i: int, j: int) -> Tuple[float, int]:
    sets = [
        frozenset(),
        frozenset({0, 1}),
        frozenset({0, 2}),
        frozenset({1, 2}),
        frozenset({0}),
        frozenset({1}),
        frozenset({2}),
        frozenset({0, 1, 2}),
    ]
    a, b = sets[i], sets[j]
    sign = 1
    for x in a:
        for y in b:
            if y < x:
                sign = -sign
    result = a ^ b
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
    return float(sign), mapping[tuple(sorted(result))]


_BLADE_TABLE = [[_blade_sign(i, j) for j in range(8)] for i in range(8)]


def geometric(a: Multivector, b: Multivector) -> Multivector:
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
    return geometric(a, b)[SCALAR]


def wedge(a: Multivector, b: Multivector) -> Multivector:
    ax, ay, az = a[E1], a[E2], a[E3]
    bx, by, bz = b[E1], b[E2], b[E3]
    return bivector(ax * by - ay * bx, ax * bz - az * bx, ay * bz - az * by)


def norm_squared(a: Multivector) -> float:
    return geometric(a, reverse(a))[SCALAR]


def norm(a: Multivector) -> float:
    ns = norm_squared(a)
    if ns < 0.0:
        raise ValueError(f"negative norm2 in Cl(3): {ns}")
    return math.sqrt(ns)


def inverse(a: Multivector) -> Multivector:
    ns = norm_squared(a)
    if ns == 0.0:
        raise ZeroDivisionError("multivector is not invertible (norm2 = 0)")
    return scale(reverse(a), 1.0 / ns)


def rotor_from_bivector_angle(b: Multivector, theta: float) -> Multivector:
    B = (0.0, b[E12], b[E13], b[E23], 0.0, 0.0, 0.0, 0.0)
    b2 = geometric(B, B)[SCALAR]
    half = -theta / 2.0
    if b2 > 0:
        s = math.sqrt(b2)
        ch = math.cosh(abs(half) * s)
        sh = math.sinh(abs(half) * s)
        return add(scalar(ch), scale(B, (sh if half >= 0 else -sh) / s))
    if b2 < 0:
        s = math.sqrt(-b2)
        return add(scalar(math.cos(abs(half) * s)), scale(B, math.sin(half * s) / s))
    return add(scalar(1.0), scale(B, half))


def rotor_apply(r: Multivector, x: Multivector) -> Multivector:
    return geometric(geometric(r, x), reverse(r))


def rotor_compose(r1: Multivector, r2: Multivector) -> Multivector:
    return geometric(r1, r2)


def rotor_identity() -> Multivector:
    return scalar(1.0)


def rotor_check_unit(r: Multivector, tol: float = 1e-12) -> bool:
    p = geometric(r, reverse(r))
    return abs(p[SCALAR] - 1.0) < tol and all(abs(p[i]) < tol for i in range(1, 8))


def rotate_orientation_between_impacts(
    r_prev: Multivector,
    contact_normal: Tuple[float, float, float],
    angle: float,
) -> Multivector:
    """R(gamma+) = R_impact R(gamma-). Scalar TOI for gamma is external."""
    nx, ny, nz = contact_normal
    B = bivector(nz, -ny, nx)
    R_impact = rotor_from_bivector_angle(B, angle)
    return rotor_compose(R_impact, r_prev)


def _smoke() -> None:
    e1 = vector(1.0, 0.0, 0.0)
    e2 = vector(0.0, 1.0, 0.0)
    e3 = vector(0.0, 0.0, 1.0)

    p = geometric(e1, e1)
    assert abs(p[SCALAR] - 1.0) < 1e-12

    p = geometric(e1, e2)
    assert abs(p[E12] - 1.0) < 1e-12

    p = geometric(e2, e1)
    assert abs(p[E12] + 1.0) < 1e-12

    I = geometric(geometric(e1, e2), e3)
    assert abs(I[PSEUDO] - 1.0) < 1e-12
    I2 = geometric(I, I)
    assert abs(I2[SCALAR] + 1.0) < 1e-12

    B = bivector(1.0, 0.0, 0.0)
    R = rotor_from_bivector_angle(B, math.pi / 2)
    assert rotor_check_unit(R)
    y = rotor_apply(R, e1)
    assert abs(y[E2] - 1.0) < 1e-9 and abs(y[E1]) < 1e-9

    R2 = rotor_from_bivector_angle(B, math.pi)
    y2 = rotor_apply(R2, e1)
    assert abs(y2[E1] + 1.0) < 1e-9

    R_after = rotate_orientation_between_impacts(rotor_identity(), (1.0, 0.0, 0.0), math.pi / 2)
    assert rotor_check_unit(R_after)
    v = rotor_apply(R_after, e1)
    v_norm = math.sqrt(v[E1] ** 2 + v[E2] ** 2 + v[E3] ** 2)
    assert abs(v_norm - 1.0) < 1e-9

    print("clifford_euclid3 smoke: PASS")


if __name__ == "__main__":
    _smoke()
