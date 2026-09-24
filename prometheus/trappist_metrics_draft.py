#!/usr/bin/env python3
"""prometheus/trappist_metrics_draft.py

Signitorial: Clarke Yoursa Tee
Does not overwrite prometheus/trappist_metrics.py.

Points at celestial.strike_ix.trappist_choir_strike_x.
Voice frequencies stay in Hz (D32: paste labelled Hz as THz).
"""
from __future__ import annotations

import time

from celestial.phi_constants import HAS_REQUESTS  # noqa: F401 — capability surface
from celestial.strike_ix.trappist_choir_strike_x import TrappistChoir

try:
    from prometheus_client import Gauge

    HAS_PROM = True
except ImportError:
    HAS_PROM = False
    Gauge = None  # type: ignore[assignment]

choir = TrappistChoir()

if HAS_PROM:
    trappist_choir_coherence = Gauge(
        "trappist_choir_coherence",
        "Overall coherence of the seven-voice Trappist-1 choir (0-1)",
    )
    trappist_harmony_index = Gauge(
        "trappist_harmony_index",
        "Harmony index: peaks when the choir aligns to a φ-chord (0-1)",
    )
    trappist_planet_frequency_hz = Gauge(
        "trappist_planet_frequency_hz",
        "Voice beat of each Trappist-1 planet (Hz) — NORTH_STAR_FREQ / period_days",
        ["planet"],
    )
    trappist_choir_distance_ly = Gauge(
        "trappist_choir_distance_ly",
        "Distance to Trappist-1 in light-years",
    )
    trappist_choir_distance_ly.set(40.7)
else:
    trappist_choir_coherence = None
    trappist_harmony_index = None
    trappist_planet_frequency_hz = None
    trappist_choir_distance_ly = None


def update_trappist_metrics() -> None:
    if not HAS_PROM:
        return
    t = time.time()
    sample = choir.listen(t)
    trappist_choir_coherence.set(sample["choir_coherence"])
    trappist_harmony_index.set(sample["harmony_index"])
    for planet, freq_hz in sample["voice_frequencies_hz"].items():
        trappist_planet_frequency_hz.labels(planet=planet).set(freq_hz)


try:
    from prometheus.metrics_server import register_update_hook

    register_update_hook(update_trappist_metrics)
except (ImportError, AttributeError):
    # D28.2: missing hook name is standalone mode, not a crash.
    pass
