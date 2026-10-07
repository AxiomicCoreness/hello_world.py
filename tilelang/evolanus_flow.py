#!/usr/bin/env python3
"""Surface 4. Constructed for small n. n=32 is the bound only."""

from __future__ import annotations

import importlib.util
import math
import py_compile
from pathlib import Path
from typing import List

FAMILY = "evolanus_flow"
SIBLING_FAMILY = "eridanus_flow"
SPLIT_SURFACES = {"eridanus_flow": 3, "evolanus_flow": 4}

PHI = (1 + math.sqrt(5)) / 2
PHI_SQ = PHI * PHI
PHI_INV_SQ = 1.0 / PHI_SQ
DENSE_CEILING = 8
ACTION_CEILING = 14
DESIGN_N = 32

Matrix = List[List[complex]]


def zeros(n: int) -> Matrix:
    return [[0j for _ in range(n)] for _ in range(n)]


def eye(n: int) -> Matrix:
    m = zeros(n)
    for i in range(n):
        m[i][i] = 1 + 0j
    return m


def add(a: Matrix, b: Matrix) -> Matrix:
    return [[x + y for x, y in zip(ra, rb)] for ra, rb in zip(a, b)]


def scale(a: Matrix, s: complex) -> Matrix:
    return [[x * s for x in row] for row in a]


def matmul(a: Matrix, b: Matrix) -> Matrix:
    n = len(a)
    out = zeros(n)
    for i in range(n):
        for k in range(n):
            aik = a[i][k]
            if aik == 0:
                continue
            for j in range(n):
                out[i][j] += aik * b[k][j]
    return out


def kron(a: Matrix, b: Matrix) -> Matrix:
    na, nb = len(a), len(b)
    n = na * nb
    out = zeros(n)
    for i in range(na):
        for j in range(na):
            for k in range(nb):
                for l in range(nb):
                    out[i * nb + k][j * nb + l] = a[i][j] * b[k][l]
    return out


PX: Matrix = [[0j, 1 + 0j], [1 + 0j, 0j]]
PZ: Matrix = [[1 + 0j, 0j], [0j, -1 + 0j]]
I2: Matrix = [[1 + 0j, 0j], [0j, 1 + 0j]]


def pauli_on(n: int, site: int, p: Matrix) -> Matrix:
    op: Matrix = [[1 + 0j]]
    for s in range(n):
        op = kron(op, p if s == site else I2)
    return op


def build_h0(n: int) -> Matrix:
    if n > DENSE_CEILING:
        raise ValueError(f"n={n} exceeds dense ceiling {DENSE_CEILING}")
    dim = 1 << n
    h = zeros(dim)
    sx = zeros(dim)
    for i in range(n):
        h = add(h, pauli_on(n, i, PZ))
        sx = add(sx, pauli_on(n, i, PX))
    h = scale(h, PHI_SQ)
    pair = scale(add(matmul(sx, sx), scale(eye(dim), -n)), 0.5)
    return add(h, scale(pair, PHI_INV_SQ))


def spectral_norm_bound(n: int) -> float:
    """Triangle bound. Not a spectral gap."""
    return PHI_SQ * n + PHI_INV_SQ * (n * n - n) / 2.0


def step(state: List[complex], dtau: float, n: int) -> List[complex]:
    if n > ACTION_CEILING:
        raise ValueError(f"n={n} exceeds action ceiling {ACTION_CEILING}")
    if n > DENSE_CEILING:
        raise ValueError("action form above dense ceiling is not built here")
    h = build_h0(n)
    u = eye(len(h))
    term = eye(len(h))
    a = scale(h, -1j * dtau)
    for k in range(1, 8):
        term = scale(matmul(term, a), 1.0 / k)
        u = add(u, term)
    return [sum(u[i][j] * state[j] for j in range(len(state))) for i in range(len(u))]


def cross_ref_check() -> None:
    if SPLIT_SURFACES != {"eridanus_flow": 3, "evolanus_flow": 4}:
        raise SystemExit(1)
    sibling = Path(__file__).with_name("eridanus_flow.py")
    text = sibling.read_text(encoding="utf-8")
    if 'SPLIT_SURFACES = {"eridanus_flow": 3, "evolanus_flow": 4}' not in text:
        raise SystemExit(1)
    if 'FAMILY = "eridanus_flow"' not in text:
        raise SystemExit(1)
    py_compile.compile(str(sibling), doraise=True)
    spec = importlib.util.spec_from_file_location("eridanus_flow_sibling", sibling)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if mod.FAMILY != SIBLING_FAMILY or mod.SPLIT_SURFACES != SPLIT_SURFACES:
        raise SystemExit(1)


def main() -> int:
    cross_ref_check()
    state = [1 + 0j, 0j, 0j, 0j]
    out = step(state, 0.01, 2)
    norm = math.sqrt(sum(abs(z) ** 2 for z in out))
    print(f"step n=2 norm={norm:.12f}")
    print(f"n={DESIGN_N} bound={spectral_norm_bound(DESIGN_N):.6f} operator-form-only")
    try:
        build_h0(DESIGN_N)
    except ValueError as exc:
        print(exc)
    return 0 if abs(norm - 1.0) < 1e-6 else 1


if __name__ == "__main__":
    raise SystemExit(main())
