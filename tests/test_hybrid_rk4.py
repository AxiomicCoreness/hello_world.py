#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CI tests for hybrid RK4 (float + Q8.24)."""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hybrid_rk4_simulator import (
    Q8_24,
    RK4Simulator,
    adapt_float_ode_to_fixed,
    rk4_step_float,
)

PHI = (1 + math.sqrt(5)) / 2
Q824_ULP = 1.0 / (1 << 24)


def decay(t: float, y: float) -> float:
    return -PHI * y


def test_q824_roundtrip_one():
    q = Q8_24(1.0)
    assert abs(q.to_float() - 1.0) < Q824_ULP


def test_q824_mul_div():
    a = Q8_24(2.0)
    b = Q8_24(0.5)
    assert abs((a * b).to_float() - 1.0) < 2 * Q824_ULP
    assert abs((a / b).to_float() - 4.0) < 4 * Q824_ULP


def test_rk4_step_float_decay():
    y1 = rk4_step_float(decay, 0.0, 1.0, 0.1)
    exact = math.exp(-PHI * 0.1)
    assert abs(y1 - exact) < 1e-6


def test_simulate_float_vs_exact():
    sim = RK4Simulator(decay, mode="float")
    yf, t_hist, y_hist = sim.simulate(0.0, 1.0, 2.0, step_size=0.1)
    exact = math.exp(-PHI * 2.0)
    assert abs(yf - exact) < 1e-5
    assert t_hist is not None and y_hist is not None
    assert len(t_hist) == len(y_hist)
    assert abs(t_hist[-1] - 2.0) < 1e-9


def test_simulate_fixed_vs_exact():
    f_fixed = adapt_float_ode_to_fixed(decay)
    sim = RK4Simulator(f_fixed, mode="fixed")
    yq, _, _ = sim.simulate(0.0, 1.0, 2.0, step_size=0.1)
    exact = math.exp(-PHI * 2.0)
    assert abs(yq - exact) < 1e-6


def test_fixed_not_worse_than_coarse_bound():
    sim_f = RK4Simulator(decay, mode="float")
    yf, _, _ = sim_f.simulate(0.0, 1.0, 2.0, step_size=0.1)
    sim_q = RK4Simulator(adapt_float_ode_to_fixed(decay), mode="fixed")
    yq, _, _ = sim_q.simulate(0.0, 1.0, 2.0, step_size=0.1)
    exact = math.exp(-PHI * 2.0)
    assert abs(yf - exact) < 1e-5
    assert abs(yq - exact) < 1e-5
