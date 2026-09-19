#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
symplectic_euler.py — Symplectic integrators for separable Hamiltonians.

H(q, p) = T(p) + V(q). Callers supply grad_V(q) and grad_T(p).

Schemes: symplectic Euler (order 1), Stormer-Verlet / leapfrog (order 2).
No ledger write, no kubectl, no PHI. Standard library only.
"""
from __future__ import annotations

import math
from typing import Callable, List, Tuple

Vector = List[float]
GradFn = Callable[[Vector], Vector]


def _axpy(a: Vector, s: float, b: Vector) -> Vector:
    return [x + s * y for x, y in zip(a, b)]


def symplectic_euler_step(
    q: Vector,
    p: Vector,
    h: float,
    grad_V: GradFn,
    grad_T: GradFn,
) -> Tuple[Vector, Vector]:
    """p := p - h grad_V(q); q := q + h grad_T(p_new)."""
    p_next = _axpy(p, -h, grad_V(q))
    q_next = _axpy(q, h, grad_T(p_next))
    return q_next, p_next


def stormer_verlet_step(
    q: Vector,
    p: Vector,
    h: float,
    grad_V: GradFn,
    grad_T: GradFn,
) -> Tuple[Vector, Vector]:
    """Leapfrog: half-kick, drift, half-kick."""
    half = h / 2.0
    p_half = _axpy(p, -half, grad_V(q))
    q_next = _axpy(q, h, grad_T(p_half))
    p_next = _axpy(p_half, -half, grad_V(q_next))
    return q_next, p_next


def integrate(
    q0: Vector,
    p0: Vector,
    h: float,
    n_steps: int,
    grad_V: GradFn,
    grad_T: GradFn,
    method: str = "verlet",
) -> List[Tuple[Vector, Vector]]:
    if method not in ("euler", "verlet"):
        raise ValueError(f"unknown method: {method!r}")
    step = symplectic_euler_step if method == "euler" else stormer_verlet_step
    q, p = list(q0), list(p0)
    trace: List[Tuple[Vector, Vector]] = [(list(q), list(p))]
    for _ in range(n_steps):
        q, p = step(q, p, h, grad_V, grad_T)
        trace.append((list(q), list(p)))
    return trace


def energy(
    q: Vector,
    p: Vector,
    T: Callable[[Vector], float],
    V: Callable[[Vector], float],
) -> float:
    return T(p) + V(q)


def energy_drift(
    trace: List[Tuple[Vector, Vector]],
    T: Callable[[Vector], float],
    V: Callable[[Vector], float],
) -> float:
    E0 = energy(*trace[0], T, V)
    return max(abs(energy(q, p, T, V) - E0) for q, p in trace)


def check_reversibility(
    q0: Vector,
    p0: Vector,
    h: float,
    grad_V: GradFn,
    grad_T: GradFn,
    tol: float = 1e-9,
) -> bool:
    q1, p1 = stormer_verlet_step(q0, p0, h, grad_V, grad_T)
    q2, p2 = stormer_verlet_step(q1, p1, -h, grad_V, grad_T)
    err = max(
        max(abs(a - b) for a, b in zip(q0, q2)),
        max(abs(a - b) for a, b in zip(p0, p2)),
    )
    return err < tol


def _smoke() -> None:
    m, k = 1.0, 4.0
    omega = math.sqrt(k / m)

    def grad_V(q: Vector) -> Vector:
        return [k * q[0]]

    def grad_T(p: Vector) -> Vector:
        return [p[0] / m]

    def T(p: Vector) -> float:
        return p[0] * p[0] / (2 * m)

    def V(q: Vector) -> float:
        return 0.5 * k * q[0] * q[0]

    q0, p0, h = [1.0], [0.0], 0.01
    trace = integrate(q0, p0, h, 1000, grad_V, grad_T, method="verlet")
    drift = energy_drift(trace, T, V)
    # O(h^2) oscillation amplitude for Verlet; not secular growth
    assert drift < 5e-4, f"Verlet energy drift too large: {drift}"
    print(f"Verlet energy drift over 1000 steps: {drift:.3e} PASS")

    trace_e = integrate(q0, p0, h, 1000, grad_V, grad_T, method="euler")
    drift_e = energy_drift(trace_e, T, V)
    print(f"Euler energy drift over 1000 steps: {drift_e:.3e} (baseline)")

    assert check_reversibility(q0, p0, h, grad_V, grad_T)
    print("Verlet reversibility check: PASS")

    period = 2 * math.pi / omega
    n = int(round(period / h))
    trace = integrate(q0, p0, h, n, grad_V, grad_T, method="verlet")
    q_end, _ = trace[-1]
    assert abs(q_end[0] - q0[0]) < 1e-3, q_end
    print(f"Verlet period return (T={period:.4f}, n={n}): PASS")

    eps = 1e-7
    z = [q0[0], p0[0]]
    J = [[0.0, 1.0], [-1.0, 0.0]]

    def f(z):
        qn, pn = stormer_verlet_step([z[0]], [z[1]], h, grad_V, grad_T)
        return [qn[0], pn[0]]

    J_M = [[0.0, 0.0], [0.0, 0.0]]
    for i in range(2):
        zp, zm = list(z), list(z)
        zp[i] += eps
        zm[i] -= eps
        fp, fm = f(zp), f(zm)
        for j in range(2):
            J_M[j][i] = (fp[j] - fm[j]) / (2 * eps)

    def matmul(A, B):
        return [
            [sum(A[i][k] * B[k][j] for k in range(2)) for j in range(2)]
            for i in range(2)
        ]

    def transpose(A):
        return [[A[j][i] for j in range(2)] for i in range(2)]

    lhs = matmul(matmul(transpose(J_M), J), J_M)
    err = max(abs(lhs[i][j] - J[i][j]) for i in range(2) for j in range(2))
    assert err < 1e-5, f"symplectic form not preserved: err={err}"
    print(f"Symplectic form preservation (J_M^T J J_M = J): PASS (err={err:.2e})")


if __name__ == "__main__":
    _smoke()
