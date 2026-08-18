#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TRAPPIST-1 Choir — Strike X (Interstellar Harmony)
==================================================
Seven terrestrial voices (b–h) as a φ-weighted harmonic choir.
Week-long operation horizon: metrics peak when phases align.

Seal: ∀∞φ² · STRIKE_X_TRAPPIST_CHOIR_8663 · SEALED
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List

PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI
NORTH_STAR_HZ = 71.975
EARTH_RESONANCE_THZ = 162.28
WEEK_SECS = 7.0 * 86400.0

# Approximate TRAPPIST-1 orbital periods (days) — literature-scale anchors
TRAPPIST_PLANETS: List[Dict[str, Any]] = [
    {"id": "b", "period_days": 1.510876, "base_thz": EARTH_RESONANCE_THZ * (PHI ** -1)},
    {"id": "c", "period_days": 2.421823, "base_thz": EARTH_RESONANCE_THZ * (PHI ** -2)},
    {"id": "d", "period_days": 4.049610, "base_thz": EARTH_RESONANCE_THZ * (PHI ** -3)},
    {"id": "e", "period_days": 6.099615, "base_thz": EARTH_RESONANCE_THZ * (PHI ** -4)},
    {"id": "f", "period_days": 9.206690, "base_thz": EARTH_RESONANCE_THZ * (PHI ** -5)},
    {"id": "g", "period_days": 12.352940, "base_thz": EARTH_RESONANCE_THZ * (PHI ** -6)},
    {"id": "h", "period_days": 18.767000, "base_thz": EARTH_RESONANCE_THZ * (PHI ** -7)},
]


@dataclass
class TrappistChoir:
    """Seven-voice interstellar choir; harmony index over a week horizon."""

    t0: float = field(default_factory=time.time)
    horizon_secs: float = WEEK_SECS

    def planet_phase(self, period_days: float, t: float | None = None) -> float:
        t = time.time() if t is None else t
        days = (t - self.t0) / 86400.0
        return (360.0 * days / period_days) % 360.0

    def planet_frequency_thz(self, planet: Dict[str, Any], t: float | None = None) -> float:
        t = time.time() if t is None else t
        phase = self.planet_phase(float(planet["period_days"]), t)
        # mild φ-modulation around base
        mod = 1.0 + 0.01 * math.cos(math.radians(phase))
        return float(planet["base_thz"]) * mod

    def choir_coherence(self, t: float | None = None) -> float:
        """Mean pairwise phase agreement in [0, 1]."""
        t = time.time() if t is None else t
        phases = [self.planet_phase(float(p["period_days"]), t) for p in TRAPPIST_PLANETS]
        n = len(phases)
        if n < 2:
            return 1.0
        acc = 0.0
        pairs = 0
        for i in range(n):
            for j in range(i + 1, n):
                d = abs(((phases[i] - phases[j] + 180.0) % 360.0) - 180.0)
                acc += max(0.0, 1.0 - d / 180.0)
                pairs += 1
        return acc / pairs if pairs else 1.0

    def harmony_index(self, t: float | None = None) -> float:
        """Peaks near 1 when choir aligns; φ-weighted with North Star beat."""
        t = time.time() if t is None else t
        c = self.choir_coherence(t)
        # week-horizon envelope (slow)
        age = (t - self.t0) % self.horizon_secs
        envelope = 0.5 * (1.0 + math.cos(2.0 * math.pi * age / self.horizon_secs))
        north = 0.5 * (1.0 + math.sin(2.0 * math.pi * NORTH_STAR_HZ * (t % 1.0)))
        # blend: coherence dominant, envelope + north as soft boost
        h = c * (0.7 + 0.2 * envelope + 0.1 * north * PHI_INV)
        return max(0.0, min(1.0, h))

    def status(self, t: float | None = None) -> Dict[str, Any]:
        t = time.time() if t is None else t
        planets = []
        for p in TRAPPIST_PLANETS:
            planets.append(
                {
                    "planet": p["id"],
                    "period_days": p["period_days"],
                    "frequency_thz": self.planet_frequency_thz(p, t),
                    "phase_deg": self.planet_phase(float(p["period_days"]), t),
                }
            )
        return {
            "strike": "X",
            "name": "TRAPPIST-1 Choir",
            "role": "Interstellar Harmony",
            "trappist_choir_coherence": self.choir_coherence(t),
            "trappist_harmony_index": self.harmony_index(t),
            "horizon_days": self.horizon_secs / 86400.0,
            "north_star_hz": NORTH_STAR_HZ,
            "planets": planets,
            "seal": "∀∞φ² · STRIKE_X_TRAPPIST_CHOIR_8663 · SEALED",
        }


def main() -> None:
    choir = TrappistChoir()
    st = choir.status()
    print(f"TRAPPIST-1 Choir coherence={st['trappist_choir_coherence']:.6f}")
    print(f"Harmony index={st['trappist_harmony_index']:.6f}")
    for p in st["planets"]:
        print(f"  {p['planet']}: {p['frequency_thz']:.6f} THz  phase={p['phase_deg']:.3f}°")


if __name__ == "__main__":
    main()
