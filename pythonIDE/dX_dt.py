#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dX_dt.py — Independent system equation permission context
dX/dt = -Λ(X - X_target) + H(η) + Z(ζ) + P(A_trunc, ρ) + P_PID(e)

Latin-only operators. IDE-safe. No Cyrillic codepoints.
Seal label: ∀∞φ² · DX_DT_INDEPENDENT · WOOD_DRAGON_0.91 · SEALED
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List

try:
    import numpy as np  # noqa: F401

    HAVE_NUMPY = True
except ImportError:
    HAVE_NUMPY = False


# ─── φ-harmonic constants ─────────────────────────────────────────
PHI = (1 + math.sqrt(5)) / 2
PHI_INV = 1 / PHI
PHI_INV2 = PHI_INV * PHI_INV
LAMBDA = PHI  # proportional gain Λ = φ
KP, KI, KD = PHI**2, PHI_INV, PHI_INV2
PSD_REF = 5.774  # reference density, g/cm³

# Scaled-injection factors. These are scaling constants, not bounds.
H_SCALE = PHI ** (-709)
Z_SCALE = PHI ** (-1418)


# ─── exogenous fields ─────────────────────────────────────────────
def H(eta: float) -> float:
    """Noise / entropy injection, scaled by φ⁻⁷⁰⁹.

    Output magnitude equals |eta| · φ⁻⁷⁰⁹. Caller keeps eta in the
    physically meaningful range; no clamping is applied here.
    """
    return eta * H_SCALE


def Z(zeta: float) -> float:
    """External perturbation, scaled by φ⁻¹⁴¹⁸.

    Output magnitude equals |zeta| · φ⁻¹⁴¹⁸. Underflow hazard: do
    not multiply two such factors; carry in log domain if needed.
    """
    return zeta * Z_SCALE


def P_trunc(A_trunc: float, rho: float = PSD_REF) -> float:
    """Truncation resistance — density-coupled.

    Form: A_trunc · (PSD_ref / rho). When rho == PSD_REF, returns
    A_trunc unchanged. When rho is small (low density), amplifies;
    when rho is large (high density), attenuates.
    """
    return A_trunc * (PSD_REF / max(rho, 1e-12))


def P_pid_stateless(e: float, I: float, de: float) -> float:
    """Stateless PID combination: Kp·e + Ki·I + Kd·de.

    The caller maintains I (integral accumulator) and computes de
    (derivative of error) from the previous error. No state is held
    here. If a stateful controller is needed, use PIDController.
    """
    return KP * e + KI * I + KD * de


@dataclass
class PIDController:
    """Stateful PID with φ-tuned defaults."""

    Kp: float = KP
    Ki: float = KI
    Kd: float = KD
    integral: float = 0.0
    prev_e: float = 0.0
    initialized: bool = False

    def step(self, e: float, dt: float) -> float:
        self.integral += e * dt
        de = 0.0 if not self.initialized else (e - self.prev_e) / dt
        self.prev_e = e
        self.initialized = True
        return self.Kp * e + self.Ki * self.integral + self.Kd * de

    def reset(self) -> None:
        self.integral = 0.0
        self.prev_e = 0.0
        self.initialized = False


# ─── the equation ─────────────────────────────────────────────────
def dX_dt(
    X: float,
    X_target: float,
    eta: float = 0.0,
    zeta: float = 0.0,
    A_trunc: float = 0.0,
    rho: float = PSD_REF,
    pid_I: float = 0.0,
    pid_de: float = 0.0,
) -> float:
    """Independent scalar form of the system equation."""
    e = X_target - X
    proportional = LAMBDA * e  # = -Λ(X - X_target)
    noise = H(eta)
    external = Z(zeta)
    truncation = P_trunc(A_trunc, rho)
    pid = P_pid_stateless(e, pid_I, pid_de)
    return proportional + noise + external + truncation + pid


def dX_dt_vec(
    X: List[float],
    X_target: List[float],
    eta: float = 0.0,
    zeta: float = 0.0,
    A_trunc: float = 0.0,
    rho: float = PSD_REF,
    pid_I: float = 0.0,
    pid_de: float = 0.0,
) -> List[float]:
    """Component-wise application of dX_dt."""
    return [
        dX_dt(x, xt, eta, zeta, A_trunc, rho, pid_I, pid_de)
        for x, xt in zip(X, X_target)
    ]


def integrate(
    X0: List[float],
    X_target: List[float],
    t_end: float = 10.0,
    dt: float = 0.01,
    **kwargs,
) -> List[List[float]]:
    """Forward Euler integration of dX_dt_vec.

    Raises ValueError if dt · Λ ≥ 2 (Euler unstable for the
    proportional term).
    """
    if dt <= 0:
        raise ValueError(f"dt must be positive, got {dt}")
    if dt * LAMBDA >= 2.0:
        raise ValueError(
            f"forward Euler unstable: dt·Λ = {dt * LAMBDA:.3f} ≥ 2. "
            f"Use dt < {2.0 / LAMBDA:.3f}."
        )
    X = X0[:]
    trace = [X[:]]
    t = 0.0
    while t < t_end:
        dX = dX_dt_vec(X, X_target, **kwargs)
        X = [x + dx * dt for x, dx in zip(X, dX)]
        trace.append(X[:])
        t += dt
    return trace


if __name__ == "__main__":
    print("dX/dt = -Λ(X - X_t) + H(η) + Z(ζ) + P(A_trunc,ρ) + P_PID(e)")
    print("Λ = φ =", LAMBDA)
    print("Kp = φ² =", KP)
    print("Ki = φ⁻¹ =", KI)
    print("Kd = φ⁻² =", KD)
    print("PSD_ref =", PSD_REF)
    print("H_scale = φ⁻⁷⁰⁹ ≈", H_SCALE)
    print("Z_scale = φ⁻¹⁴¹⁸ ≈", Z_SCALE)

    X0 = [0.9, 0.0]
    X_target = [1.0, 202.6]
    trace = integrate(X0, X_target, t_end=5.0, dt=0.05, eta=0.0, zeta=0.0)
    print(f"final X = {trace[-1]}")

    try:
        integrate(X0, X_target, t_end=5.0, dt=2.0)
    except ValueError as e:
        print(f"stability guard fired: {e}")
