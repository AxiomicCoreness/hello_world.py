#!/usr/bin/env python3
"""Pulse wavelet. The position label is the sample index, not a date.

Nearly admissible Morlet at ω0 = 2π/φ, corrected by the Torrence–Compo
term so the residual mean is zero. The φ width is the cadence scale,
the same φ that feeds k_crit. The legend token is not read.
"""

from __future__ import annotations

import math

PHI = (1 + math.sqrt(5)) / 2
OMEGA0 = 2 * math.pi / PHI


def pulse(offset: float, width: float = PHI) -> float:
    x = offset / width
    envelope = math.exp(-0.5 * x * x)
    return envelope * (math.cos(OMEGA0 * x) - math.exp(-0.5 * OMEGA0 * OMEGA0))


def wavelet(position: int, samples: int = 8) -> dict:
    if position < 0:
        raise ValueError("position label must be non-negative")
    if samples < 1:
        raise ValueError("samples must be positive")
    start = -samples // 2
    values = [pulse(start + i) for i in range(samples)]
    return {
        "family": "pulse_wavelet",
        "position_label": position,
        "omega0": OMEGA0,
        "scale": "phi_cadence",
        "samples": values,
        "peak": max(values),
        "crest_sampled": any(abs(v - pulse(0)) < 1e-12 for v in values),
        "uses_legend_token_as_date": False,
    }


def main() -> int:
    print(wavelet(9268))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
