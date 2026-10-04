#!/usr/bin/env python3
"""evolanus_flow.py — stdlib kinetic counterpart.

H0(n) = phi^2 * sum_i sigma_z(i) + phi^-2 * (Sx^2 - n*I) / 2
Dense build and step only for n <= 5. n = 32 is the bound only.
No numpy. No seal. No os._exit.
"""

from __future__ import annotations

import math
from typing import List

PHI = (1 + math.sqrt(5)) / 2
PHI_SQ = PHI * PHI
PHI_INV_SQ = 1.0 / PHI_SQ
MAX_DENSE_N = 5
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
    if n > MAX_DENSE_N:
        raise ValueError(f"n={n} exceeds dense ceiling {MAX_DENSE_N}")
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
    return PHI_SQ * n + PHI_INV_SQ * (n * n - n) / 2.0


def hermitian(h: Matrix) -> bool:
    n = len(h)
    return all(abs(h[i][j] - h[j][i].conjugate()) < 1e-9 for i in range(n) for j in range(n))


def expm_i(h: Matrix, dtau: float) -> Matrix:
    """U = exp(-i H dtau) by scaling and squaring. Small n only."""
    n = len(h)
    a = scale(h, -1j * dtau)
    norm = max(sum(abs(x) for x in row) for row in a)
    s = max(0, math.ceil(math.log2(norm)) if norm > 1 else 0)
    a = scale(a, 2.0 ** (-s))
    term = eye(n)
    acc = eye(n)
    for k in range(1, 12):
        term = scale(matmul(term, a), 1.0 / k)
        acc = add(acc, term)
    for _ in range(s):
        acc = matmul(acc, acc)
    return acc


def step(state: List[complex], dtau: float, n: int) -> List[complex]:
    if n > MAX_DENSE_N:
        raise ValueError("step refused above dense ceiling")
    u = expm_i(build_h0(n), dtau)
    return [sum(u[i][j] * state[j] for j in range(len(state))) for i in range(len(state))]


def main() -> int:
    for n in range(1, 6):
        h = build_h0(n)
        print(f"n={n} hermitian={hermitian(h)} dim={len(h)}")
    print(f"n={DESIGN_N} bound={spectral_norm_bound(DESIGN_N):.6f} dense=REFUSED")
    try:
        build_h0(DESIGN_N)
    except ValueError as exc:
        print(f"n={DESIGN_N} {exc}")
    state = [0j] * 4
    state[0] = 1 + 0j
    out = step(state, 0.01, 2)
    norm = math.sqrt(sum(abs(z) ** 2 for z in out))
    print(f"step n=2 norm={norm:.12f}")
    return 0 if abs(norm - 1.0) < 1e-8 else 1


if __name__ == "__main__":
    raise SystemExit(main())
