#!/usr/bin/env python3
"""Pulse wavelet. The position label is the sample index, not a date.

A Morlet-style pulse on the Eridanus step. The legend token is not read.
"""

from __future__ import annotations

import math

PHI = (1 + math.sqrt(5)) / 2


def pulse(offset: float, width: float = PHI) -> float:
    x = offset / width
    return math.exp(-0.5 * x * x) * math.cos(2 * math.pi * x / PHI)


def wavelet(position: int, samples: int = 8) -> dict:
    if position < 0:
        raise ValueError("position label must be non-negative")
    if samples < 1:
        raise ValueError("samples must be positive")
    half = (samples - 1) / 2
    values = [pulse(i - half) for i in range(samples)]
    return {
        "family": "pulse_wavelet",
        "position_label": position,
        "samples": values,
        "peak": max(values),
        "uses_legend_token_as_date": False,
    }


def main() -> int:
    print(wavelet(9268))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
