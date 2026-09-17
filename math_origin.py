#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
math_origin — ConvergenceWindow recomputed from n (Entry 8336 / analogue 8551).

Canonical (n=19):
  raw = n · ln φ
  modulus = π/φ  ≈ 1.9416110387 rad ≈ 111.246°  (window bound, NOT the phase)
  k = floor(raw / modulus) = 4
  u = raw − k·modulus ≈ 1.3765805213 rad ≈ 78.87°  (phase residue)
  L_19 = 9349, F_19 = 4181

Prose must not claim 26·ln φ or u = 111.246°. Those strings are not in the
hash preimage; if they ever become payload segments, re-seal.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple

PHI = (1.0 + math.sqrt(5.0)) / 2.0
LN_PHI = math.log(PHI)


def fibonacci(n: int) -> int:
    if n < 0:
        raise ValueError("n must be non-negative")
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def lucas(n: int) -> int:
    if n < 0:
        raise ValueError("n must be non-negative")
    a, b = 2, 1
    for _ in range(n):
        a, b = b, a + b
    return a


@dataclass(frozen=True)
class ConvergenceWindow:
    n: int
    L_n: int
    F_n: int
    raw: float
    modulus: float
    k: int
    u: float
    u_deg: float
    modulus_deg: float

    def payload_segment(self) -> str:
        """Canonical segment for hash preimage — derived, not asserted."""
        return (
            f"math_origin=Convergence_window("
            f"n={self.n};L={self.L_n};F={self.F_n};"
            f"u={self.u:.13f};k={self.k})"
        )


def convergence_window(n: int = 19) -> ConvergenceWindow:
    """Recompute L_n, F_n, u, k from n under x² − x − 1 = 0."""
    raw = n * LN_PHI
    modulus = math.pi / PHI
    k = int(math.floor(raw / modulus))
    u = raw - k * modulus
    return ConvergenceWindow(
        n=n,
        L_n=lucas(n),
        F_n=fibonacci(n),
        raw=raw,
        modulus=modulus,
        k=k,
        u=u,
        u_deg=math.degrees(u),
        modulus_deg=math.degrees(modulus),
    )


def verify_canonical_19(tol: float = 1e-9) -> Tuple[bool, ConvergenceWindow]:
    cw = convergence_window(19)
    ok = (
        cw.L_n == 9349
        and cw.F_n == 4181
        and cw.k == 4
        and abs(cw.u - 1.3765805212306) < 1e-10
        and abs(cw.modulus_deg - 111.246118) < 1e-4
    )
    return ok, cw


if __name__ == "__main__":
    ok, cw = verify_canonical_19()
    print(cw.payload_segment())
    print(f"u_deg={cw.u_deg:.6f} modulus_deg={cw.modulus_deg:.6f} ok={ok}")
