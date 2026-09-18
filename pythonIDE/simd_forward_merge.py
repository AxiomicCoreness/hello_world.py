#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SIMD-style multi-lane forward merge for dX/dt states.

Honest scope:
  - "SIMD" here means *vectorized lane merge* (numpy broadcasting when
    available), not hand-written x86/ARM intrinsics.
  - On hosts without numpy, falls back to pure-Python zip loops.
  - Syncs a catalogue of parallel trajectories one Euler step at a time.

Usage:
  python -m pythonIDE.simd_forward_merge
  # or
  python pythonIDE/simd_forward_merge.py
"""
from __future__ import annotations

import math
from typing import List, Sequence, Tuple

try:
    import numpy as np

    HAVE_NUMPY = True
except ImportError:
    HAVE_NUMPY = False

# Prefer sibling dX_dt if importable
try:
    from dX_dt import LAMBDA, dX_dt_vec, integrate
except ImportError:
    try:
        from pythonIDE.dX_dt import LAMBDA, dX_dt_vec, integrate
    except ImportError:
        LAMBDA = (1 + math.sqrt(5)) / 2

        def dX_dt_vec(X, X_target, **kwargs):
            return [LAMBDA * (xt - x) for x, xt in zip(X, X_target)]

        def integrate(X0, X_target, t_end=1.0, dt=0.01, **kwargs):
            X = list(X0)
            t = 0.0
            while t < t_end:
                dX = dX_dt_vec(X, X_target, **kwargs)
                X = [x + dx * dt for x, dx in zip(X, dX)]
                t += dt
            return [X]


def merge_forward_lanes(
    states: Sequence[Sequence[float]],
    targets: Sequence[Sequence[float]],
    dt: float = 0.01,
) -> List[List[float]]:
    """One Euler step across N lanes in parallel.

    states[i] is the state vector of lane i; same length as targets[i].
    Returns new states after one forward step.
    """
    if not states:
        return []
    if len(states) != len(targets):
        raise ValueError("states and targets length mismatch")
    if dt <= 0:
        raise ValueError(f"dt must be positive, got {dt}")
    if dt * LAMBDA >= 2.0:
        raise ValueError(
            f"forward Euler unstable: dt·Λ = {dt * LAMBDA:.3f} ≥ 2"
        )

    if HAVE_NUMPY:
        # Stack lanes → (N, D); vectorized proportional step
        X = np.asarray(states, dtype=float)
        Xt = np.asarray(targets, dtype=float)
        if X.shape != Xt.shape:
            raise ValueError(f"shape mismatch {X.shape} vs {Xt.shape}")
        dX = LAMBDA * (Xt - X)
        X_next = X + dX * dt
        return X_next.tolist()

    # Pure-Python fallback (same math, scalar loops)
    out: List[List[float]] = []
    for X, Xt in zip(states, targets):
        dX = dX_dt_vec(list(X), list(Xt))
        out.append([x + dx * dt for x, dx in zip(X, dX)])
    return out


def sync_catalogue_merge(
    lanes: Sequence[Tuple[Sequence[float], Sequence[float]]],
    steps: int = 10,
    dt: float = 0.01,
) -> List[List[float]]:
    """Run `steps` SIMD-style merge forwards; return final states.

    lanes: sequence of (state0, target) pairs.
    """
    states = [list(s) for s, _ in lanes]
    targets = [list(t) for _, t in lanes]
    for _ in range(steps):
        states = merge_forward_lanes(states, targets, dt=dt)
    return states


def main() -> None:
    print("simd_forward_merge · HAVE_NUMPY =", HAVE_NUMPY)
    print("Λ =", LAMBDA)
    lanes = [
        ([0.9, 0.0], [1.0, 202.6]),
        ([0.5, 10.0], [1.0, 202.6]),
        ([0.0, 0.0], [1.0, 202.6]),
    ]
    final = sync_catalogue_merge(lanes, steps=50, dt=0.05)
    for i, s in enumerate(final):
        print(f"lane {i} final = {s}")


if __name__ == "__main__":
    main()
