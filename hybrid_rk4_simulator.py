#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ HYBRID RK4 SIMULATOR – Q8.24 FIXED‑POINT & FLOAT
   Supports both fixed‑point (Q8.24) and standard floating‑point
   scalar ODE integration. Select mode = "fixed" or "float".

   Commander: Clarke Yoursa Tee Luminara Atlas LUMERIS 🜁∀
"""

from __future__ import annotations
import math
from typing import Callable, List, Tuple, Optional

# Q8.24 Fixed-Point Arithmetic
SCALE = 24
ONE = 1 << SCALE
HALF = 1 << (SCALE - 1)

class Q8_24:
    __slots__ = ('raw',)

    def __init__(self, value):
        if isinstance(value, Q8_24):
            self.raw = value.raw
        elif isinstance(value, int):
            self.raw = value << SCALE
        else:
            self.raw = int(value * ONE + (0.5 if value >= 0 else -0.5))

    def to_float(self):
        return self.raw / ONE

    def __add__(self, other):
        res = Q8_24.__new__(Q8_24)
        res.raw = self.raw + other.raw
        return res

    def __sub__(self, other):
        res = Q8_24.__new__(Q8_24)
        res.raw = self.raw - other.raw
        return res

    def __mul__(self, other):
        res = Q8_24.__new__(Q8_24)
        product = self.raw * other.raw
        if product >= 0:
            res.raw = (product + HALF) >> SCALE
        else:
            res.raw = (product - HALF) >> SCALE
        return res

    def __truediv__(self, other):
        numerator = self.raw << SCALE
        if other.raw == 0:
            raise ZeroDivisionError("Division by zero in Q8_24")
        if numerator >= 0:
            res_raw = (numerator + (other.raw >> 1)) // other.raw
        else:
            res_raw = (numerator - (other.raw >> 1)) // other.raw
        res = Q8_24.__new__(Q8_24)
        res.raw = int(res_raw)
        return res

    def __neg__(self):
        res = Q8_24.__new__(Q8_24)
        res.raw = -self.raw
        return res

    def __repr__(self):
        return f"Q8.24({self.to_float():.10f})"


def rk4_step_fixed(f, t, y, h):
    two = Q8_24(2)
    six = Q8_24(6)
    half = Q8_24(0.5)
    k1 = h * f(t, y)
    k2 = h * f(t + h * half, y + k1 * half)
    k3 = h * f(t + h * half, y + k2 * half)
    k4 = h * f(t + h, y + k3)
    increment = (k1 + k2 * two + k3 * two + k4) / six
    return y + increment


def rk4_step_float(f, t, y, h):
    k1 = h * f(t, y)
    k2 = h * f(t + 0.5 * h, y + 0.5 * k1)
    k3 = h * f(t + 0.5 * h, y + 0.5 * k2)
    k4 = h * f(t + h, y + k3)
    return y + (k1 + 2.0 * k2 + 2.0 * k3 + k4) / 6.0


class RK4Simulator:
    def __init__(self, f, mode="float"):
        self.f = f
        self.mode = mode
        self.t_hist = []
        self.y_hist = []

    def simulate(self, t0, y0, t_end, step_size=0.01, store_trajectory=True):
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
        final_y = self.y_hist[-1] if store_trajectory else y
        return final_y, (self.t_hist if store_trajectory else None), (self.y_hist if store_trajectory else None)


def adapt_float_ode_to_fixed(f_float):
    def f_fixed(t, y):
        val = f_float(t.to_float(), y.to_float())
        return Q8_24(val)
    return f_fixed


if __name__ == "__main__":
    phi = (1 + math.sqrt(5)) / 2

    def decay(t, y):
        return -phi * y

    print("=== RK4 Fixed-Point (Q8.24) vs Float ===")

    sim_float = RK4Simulator(decay, mode="float")
    yf, tf_hist, yf_hist = sim_float.simulate(0.0, 1.0, 2.0, step_size=0.1)
    print(f"[Float] y(2) = {yf:.10f}")

    f_fixed = adapt_float_ode_to_fixed(decay)
    sim_fixed = RK4Simulator(f_fixed, mode="fixed")
    yfix, tfix_hist, yfix_hist = sim_fixed.simulate(0.0, 1.0, 2.0, step_size=0.1)
    print(f"[Fixed] y(2) = {yfix:.10f}")

    exact = math.exp(-phi * 2)
    print(f"[Exact] y(2) = {exact:.10f}")

    print(f"Float error: {abs(yf - exact):.2e}")
    print(f"Fixed error: {abs(yfix - exact):.2e}")
    print("✅ Hybrid RK4 simulator ready.")