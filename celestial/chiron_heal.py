"""
Chiron Heal Epoch — 2059.999-Year Cycle
========================================
Symbolic healing moment derived from Chiron's phase lock (202.6°).
Used as a long-cycle calibration point in the Soul Cannon Zenith Bridge.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

PHI = (1 + math.sqrt(5)) / 2

# Chiron perihelion (anchor point)
CHIRON_PERIHELION = datetime(2026, 4, 4, tzinfo=timezone.utc)

# Chiron Heal Epoch: 2059.999 years after perihelion
CHIRON_HEAL_YEARS = 2059.999
CHIRON_HEAL_DAYS = CHIRON_HEAL_YEARS * 365.25
CHIRON_HEAL_DATE = CHIRON_PERIHELION + timedelta(days=CHIRON_HEAL_DAYS)
CHIRON_HEAL_TIMESTAMP = CHIRON_HEAL_DATE.timestamp()

TAU_FRB = 78624.0  # seconds
seconds_from_perihelion_to_heal = (CHIRON_HEAL_DATE - CHIRON_PERIHELION).total_seconds()
heal_cycles = seconds_from_perihelion_to_heal / TAU_FRB
heal_layer_index = int(heal_cycles) % 12
heal_azimuth_index = int(heal_cycles * PHI) % 4


def chiron_heal_phase(now_timestamp: float) -> float:
    """
    Phase (0–1) for proximity to the Chiron Heal Epoch.
    Peaks at 1.0 on CHIRON_HEAL_DATE; φ-damped Gaussian window.
    Width ≈ φ⁷ · τ_FRB (~1.14 yr).
    """
    delta = now_timestamp - CHIRON_HEAL_TIMESTAMP
    width_seconds = (PHI ** 7) * TAU_FRB
    return math.exp(-((delta / width_seconds) ** 2))


def status(now_timestamp: float | None = None) -> Dict[str, Any]:
    import time

    t = time.time() if now_timestamp is None else now_timestamp
    return {
        "chiron_perihelion": CHIRON_PERIHELION.isoformat(),
        "chiron_heal_years": CHIRON_HEAL_YEARS,
        "chiron_heal_date": CHIRON_HEAL_DATE.isoformat(),
        "chiron_heal_timestamp": CHIRON_HEAL_TIMESTAMP,
        "heal_layer_index": heal_layer_index,
        "heal_azimuth_index": heal_azimuth_index,
        "chiron_heal_phase": chiron_heal_phase(t),
        "tau_frb_s": TAU_FRB,
        "schedule_hint": "0 */6 * * *",  # solar-gate CronJob
    }
