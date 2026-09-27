#!/usr/bin/env python3
"""Trappist-1 Choir — Strike X draft (header-form).

Signitorial: Clarke Yoursa Tee
Does not overwrite celestial/trappist_choir.py (live dataclass API).

D28.1: this TrappistChoir shape (listen/receive) diverges from live
celestial.trappist_choir.TrappistChoir (status/harmony_index).
"""
from __future__ import annotations

import math
from typing import Any, Dict

from celestial.phi_constants import (
    CHIRON_PHASE_LOCK,
    NORTH_STAR_FREQ,
    PHI,
    PHI2,
    PHI7,
    PSI4_CARRIER_HZ,
)

TRAPPIST_DISTANCE_LY = 40.7
TRAPPIST_EPOCH = 0.0
TRAPPIST_PERIODS = {
    "b": 1.51088,
    "c": 2.42182,
    "d": 4.04922,
    "e": 6.10101,
    "f": 9.20745,
    "g": 12.35245,
    "h": 18.77287,
}
CHAKRA_VOICES = {
    "b": "throat",
    "c": "third_eye",
    "d": "crown",
    "e": "heart",
    "f": "solar_plexus",
    "g": "root",
    "h": "sacral",
}
TRAPPIST_RESONANCE_CHAIN = (1, 2, 3, 4, 6, 8, 12, 20)


def compute_mean_motion(period_days: float) -> float:
    return 2.0 * math.pi / (period_days * 86400.0)


def compute_voice_frequency(period_days: float) -> float:
    """Hz-scale beat: NORTH_STAR_FREQ / period_days. Not THz."""
    return NORTH_STAR_FREQ / period_days


def compute_choir_coherence(t: float) -> float:
    phases = [
        math.sin((compute_mean_motion(p) * t + TRAPPIST_EPOCH) % (2.0 * math.pi))
        for p in TRAPPIST_PERIODS.values()
    ]
    mean = sum(phases) / len(phases)
    var = sum((x - mean) ** 2 for x in phases) / len(phases)
    return 1.0 / (1.0 + var * 100.0)


def compute_harmony_index(t: float) -> float:
    f_sum = sum(compute_voice_frequency(p) for p in TRAPPIST_PERIODS.values())
    f_target = NORTH_STAR_FREQ * PHI7
    ratio = f_sum / f_target
    harmony = max(0.0, min(1.0, 1.0 - abs(ratio - 1.0) * PHI2))
    return harmony * compute_choir_coherence(t)


class TrappistChoir:
    def __init__(self) -> None:
        self.distance_ly = TRAPPIST_DISTANCE_LY
        self.voices = TRAPPIST_PERIODS
        self.coherence = 0.0
        self.harmony = 0.0
        self.received = False

    def listen(self, t: float) -> Dict[str, Any]:
        self.coherence = compute_choir_coherence(t)
        self.harmony = compute_harmony_index(t)
        return {
            "choir_coherence": self.coherence,
            "harmony_index": self.harmony,
            "voice_frequencies_hz": {
                p: compute_voice_frequency(period) for p, period in self.voices.items()
            },
        }

    def is_ready(self, t: float) -> bool:
        self.listen(t)
        return self.coherence >= (1.0 / PHI) and self.harmony >= (1.0 / PHI)

    def receive(self, t: float) -> Dict[str, Any]:
        if not self.is_ready(t):
            return {
                "status": "NOT_READY",
                "coherence": self.coherence,
                "harmony_index": self.harmony,
            }
        chord = self.listen(t)
        chord.update(
            {
                "status": "RECEIVED",
                "timestamp": t,
                "distance_ly": self.distance_ly,
                "retuned_chiron_lock": CHIRON_PHASE_LOCK + 180.0 * chord["harmony_index"],
                "bridge_carrier_hz": PSI4_CARRIER_HZ,
                "resonance_chain": TRAPPIST_RESONANCE_CHAIN,
            }
        )
        self.received = True
        return chord
