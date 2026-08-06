#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HYBRID RK4 SIMULATOR – Q8.24 FIXED-POINT & FLOAT
   Supports both fixed-point (Q8.24) and standard floating-point
   scalar ODE integration.  Select mode = "fixed" or "float".
"""

from __future__ import annotations

import math
from typing import Callable, List, Optional, Tuple

SCALE = 24
ONE = 1 << SCALE
HALF = 1 << (SCALE - 1)


class Q8_24:
    """Fixed-point number: value = raw / 2**24."""

    __slots__ = ("raw",)

    def __init__(self, value: int | float | "Q8_24"):
        if isinstance(value, Q8_24):
            self.raw = value.raw
        elif isinstance(value, int):
            self.raw = value << SCALE
        else:
            self.raw = int(value * ONE + (0.5 if value >= 0 else -0.5))

    def to_float(self) -> float:
        return self.raw / ONE

    def __add__(self, other: "Q8_24") -> "Q8_24":
        res = Q8_24.__new__(Q8_24)
        res.raw = self.raw + other.raw
        return res

    def __sub__(self, other: "Q8_24") -> "Q8_24":
        res = Q8_24.__new__(Q8_24)
        res.raw = self.raw - other.raw
        return res

    def __mul__(self, other: "Q8_24") -> "Q8_24":
        res = Q8_24.__new__(Q8_24)
        product = self.raw * other.raw
        if product >= 0:
            res.raw = (product + HALF) >> SCALE
        else:
            res.raw = (product - HALF) >> SCALE
        return res

    def __truediv__(self, other: "Q8_24") -> "Q8_24":
        if other.raw == 0:
            raise ZeroDivisionError("Division by zero in Q8_24")
        numerator = self.raw << SCALE
        res = Q8_24.__new__(Q8_24)
        if numerator >= 0:
            res.raw = (numerator + (other.raw >> 1)) // other.raw
        else:
            res.raw = (numerator - (other.raw >> 1)) // other.raw
        return res

    def __neg__(self) -> "Q8_24":
        res = Q8_24.__new__(Q8_24)
        res.raw = -self.raw
        return res

    def __repr__(self) -> str:
        return f"Q8.24({self.to_float():.10f})"


def rk4_step_fixed(
    f: Callable[[Q8_24, Q8_24], Q8_24],
    t: Q8_24,
    y: Q8_24,
    h: Q8_24,
) -> Q8_24:
    two = Q8_24(2)
    six = Q8_24(6)
    half = Q8_24(0.5)

    k1 = h * f(t, y)
    k2 = h * f(t + h * half, y + k1 * half)
    k3 = h * f(t + h * half, y + k2 * half)
    k4 = h * f(t + h, y + k3)

    increment = (k1 + k2 * two + k3 * two + k4) / six
    return y + increment


def rk4_step_float(
    f: Callable[[float, float], float],
    t: float,
    y: float,
    h: float,
) -> float:
    k1 = h * f(t, y)
    k2 = h * f(t + 0.5 * h, y + 0.5 * k1)
    k3 = h * f(t + 0.5 * h, y + 0.5 * k2)
    k4 = h * f(t + h, y + k3)
    return y + (k1 + 2.0 * k2 + 2.0 * k3 + k4) / 6.0


class RK4Simulator:
    def __init__(self, f, mode: str = "float"):
        self.f = f
        self.mode = mode
        self.t_hist: List[float] = []
        self.y_hist: List[float] = []

    def simulate(
        self,
        t0: float,
        y0: float,
        t_end: float,
        step_size: float = 0.01,
        store_trajectory: bool = True,
    ) -> Tuple[float, Optional[List[float]], Optional[List[float]]]:
        if self.mode == "float":
            t = t0
            y = y0
            if store_trajectory:
                self.t_hist = [t]
                self.y_hist = [y]
            while t < t_end - 1e-15:
                h = min(step_size, t_end - t)
                y = rk4_step_float(self.f, t, y, h)
                t += h
                if store_trajectory:
                    self.t_hist.append(t)
                    self.y_hist.append(y)
            final_y = y
        else:
            t = Q8_24(t0)
            y = Q8_24(y0)
            h = Q8_24(step_size)
            t_end_fixed = Q8_24(t_end)
            if store_trajectory:
                self.t_hist = [t0]
                self.y_hist = [y0]
            while t.raw < t_end_fixed.raw:
                y = rk4_step_fixed(self.f, t, y, h)
                t = t + h
                if store_trajectory:
                    self.t_hist.append(t.to_float())
                    self.y_hist.append(y.to_float())
            final_y = y.to_float() if not store_trajectory else self.y_hist[-1]
        return (
            final_y,
            (self.t_hist if store_trajectory else None),
            (self.y_hist if store_trajectory else None),
        )


def adapt_float_ode_to_fixed(
    f_float: Callable[[float, float], float],
) -> Callable[[Q8_24, Q8_24], Q8_24]:
    def f_fixed(t: Q8_24, y: Q8_24) -> Q8_24:
        return Q8_24(f_float(t.to_float(), y.to_float()))

    return f_fixed


if __name__ == "__main__":
    phi = (1 + math.sqrt(5)) / 2

    def decay(t: float, y: float) -> float:
        return -phi * y

    print("=== RK4 Fixed-Point (Q8.24) vs Float ===")

    sim_float = RK4Simulator(decay, mode="float")
    yf, _, _ = sim_float.simulate(0.0, 1.0, 2.0, step_size=0.1)
    print(f"[Float] y(2) = {yf:.10f}")

    f_fixed = adapt_float_ode_to_fixed(decay)
    sim_fixed = RK4Simulator(f_fixed, mode="fixed")
    yq, _, _ = sim_fixed.simulate(0.0, 1.0, 2.0, step_size=0.1)
    print(f"[Fixed] y(2) = {yq:.10f}")

    exact = math.exp(-phi * 2)
    print(f"[Exact] y(2) = {exact:.10f}")
    print(f"Float error: {abs(yf - exact):.2e}")
    print(f"Fixed error: {abs(yq - exact):.2e}")
    print("Q8.24 unit:", 1.0 / (1 << 24))
    print("Hybrid RK4 simulator ready.")
