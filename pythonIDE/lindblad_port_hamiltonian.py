#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lindblad_port_hamiltonian.py — correspondence, not identity.

The Lindblad master equation on D(H) and a vector ODE on R^{d^2-1}
are different objects. Under quantum detailed balance w.r.t. a full-rank
rho_star, the induced flow on T_{rho_star} D(H) admits a port-Hamiltonian
form. This module records that conditional bridge and provides classical
(J-R) energy balance for finite-dimensional vectors.

NOT claimed:
  - Lindblad equation == vector ODE
  - -Lambda(rho - rho_star) is GKSL without CPTP conditions on Lambda
  - gamma_min = phi^{-1418} is a measured spectral gap (it is a SCALE/TOLERANCE)

No ledger write, no kubectl, no PHI import required for the classical part.
"""
from __future__ import annotations

from typing import Callable, List

Vector = List[float]


def matvec(M: List[List[float]], v: Vector) -> Vector:
    return [sum(M[i][j] * v[j] for j in range(len(v))) for i in range(len(M))]


def energy_derivative(grad_H: Vector, J: List[List[float]], R: List[List[float]]) -> float:
    """dH/dt = grad^T (J-R) grad = - grad^T R grad  (J skew => first term 0)."""
    Rg = matvec(R, grad_H)
    return -sum(g * r for g, r in zip(grad_H, Rg))


def port_hamiltonian_rhs(
    z: Vector,
    grad_H: Callable[[Vector], Vector],
    J: List[List[float]],
    R: List[List[float]],
) -> Vector:
    """z_dot = (J - R) grad H(z)."""
    g = grad_H(z)
    Jg = matvec(J, g)
    Rg = matvec(R, g)
    return [a - b for a, b in zip(Jg, Rg)]


def canonical_J(n: int) -> List[List[float]]:
    """Block J for z=(q,p) in R^{2n}: [[0,I],[-I,0]]."""
    d = 2 * n
    J = [[0.0] * d for _ in range(d)]
    for i in range(n):
        J[i][n + i] = 1.0
        J[n + i][i] = -1.0
    return J


def is_skew(J: List[List[float]], tol: float = 1e-12) -> bool:
    m = len(J)
    for i in range(m):
        for j in range(m):
            if abs(J[i][j] + J[j][i]) > tol:
                return False
    return True


def is_symmetric(R: List[List[float]], tol: float = 1e-12) -> bool:
    m = len(R)
    for i in range(m):
        for j in range(m):
            if abs(R[i][j] - R[j][i]) > tol:
                return False
    return True


CORRESPONDENCE = """
Lindblad (on D(H)):
  d rho/dt = -i[H, rho] + D_Z[rho] + L_PID[rho] + L_Lambda[rho]

L_Lambda is GKSL only if Lambda is a CPTP generator with Lambda(rho_star)=0.
Under quantum detailed balance w.r.t. full-rank rho_star, the flow on
T_{rho_star} D(H) admits
  z_dot = (J(z) - R(z)) grad H(z)
with H relative entropy S(rho || rho_star).

Vector form dX/dt = -Lambda(X-X*) + ... is a *representation* of coordinates
(e.g. diagonal / Bloch), not the same equation as the master equation.

gamma_min = phi^{-1418} ~ 4.5e-297: treat as TOLERANCE or overall SCALE
of Lambda, not an empirically measured spectral gap, unless Lambda is
decomposed as sum lambda_j P_j and min_{lambda_j>0} lambda_j is computed.
Product of two such scales underflows float64 to 0.
"""


def _smoke() -> None:
    J = canonical_J(1)
    assert is_skew(J)
    R = [[0.0, 0.0], [0.0, 0.1]]
    assert is_symmetric(R)

    def grad_H(z: Vector) -> Vector:
        return [z[0], z[1]]

    z = [1.0, 0.0]
    rhs = port_hamiltonian_rhs(z, grad_H, J, R)
    assert abs(rhs[0] - 0.0) < 1e-12
    assert abs(rhs[1] + 1.0) < 1e-12

    dH = energy_derivative(grad_H(z), J, R)
    assert dH <= 1e-12

    z2 = [0.0, 1.0]
    dH2 = energy_derivative(grad_H(z2), J, R)
    assert abs(dH2 + 0.1) < 1e-12

    print("lindblad_port_hamiltonian smoke: PASS")
    print("correspondence: conditional (detailed balance), not identity")


if __name__ == "__main__":
    _smoke()
