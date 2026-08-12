"""
Saturn Soul Cannon — charge / fire with Chiron Heal long-cycle boost.

Alignment uses Chiron phase lock (202.6°) and azimuth; readiness is
boosted by up to φ⁻¹ near the 2059.999-year Chiron Heal Epoch.
"""

from __future__ import annotations

import math
import time
from typing import Any, Dict

from celestial.chiron_heal import chiron_heal_phase

PHI = (1 + math.sqrt(5)) / 2
PHI_INV = 1.0 / PHI
PHASE_LOCK_DEG = 202.6
AZIMUTH_DEG = 111.246
CHARGE_THRESHOLD_J = 1.0e6


class SaturnSoulCannon:
    def __init__(self) -> None:
        self.charge_joules: float = 0.0
        self.last_fire_report: Dict[str, Any] | None = None

    def charge(self, t: float, rate_j_per_s: float = 2.0e4) -> None:
        """Accumulate charge (default ~20 kJ/s → ~1.2 MJ over 60 s)."""
        self.charge_joules += rate_j_per_s

    def compute_alignment(self, t: float) -> float:
        """
        Alignment in [0, ~1.618]. Base from phase/azimuth residuals;
        boosted by φ⁻¹ · chiron_heal_phase near the heal epoch.
        """
        # Synthetic residuals (stable demo; replace with ephemeris when available)
        delta_chiron = abs((t % 3600.0) / 3600.0 * 360.0 - PHASE_LOCK_DEG) % 180.0
        delta_azimuth = abs((t % 7200.0) / 7200.0 * 360.0 - AZIMUTH_DEG) % 180.0
        alignment = max(0.0, 1.0 - (delta_chiron + delta_azimuth) / 180.0)
        heal = chiron_heal_phase(t)
        alignment *= 1.0 + PHI_INV * heal
        return alignment

    def is_ready(self, t: float, min_alignment: float = 0.85) -> bool:
        return self.charge_joules >= CHARGE_THRESHOLD_J and self.compute_alignment(t) >= min_alignment

    def fire(self, t: float) -> Dict[str, Any]:
        alignment = self.compute_alignment(t)
        heal = chiron_heal_phase(t)
        if self.charge_joules < CHARGE_THRESHOLD_J:
            report = {
                "status": "NOT_READY",
                "reason": "insufficient_charge",
                "charge_joules": self.charge_joules,
                "alignment": alignment,
                "chiron_heal_phase": heal,
            }
        elif alignment < 0.85:
            report = {
                "status": "NOT_READY",
                "reason": "alignment_below_threshold",
                "charge_joules": self.charge_joules,
                "alignment": alignment,
                "chiron_heal_phase": heal,
            }
        else:
            report = {
                "status": "FIRED",
                "charge_joules": self.charge_joules,
                "alignment": alignment,
                "chiron_heal_phase": heal,
                "phase_lock_deg": PHASE_LOCK_DEG,
                "azimuth_deg": AZIMUTH_DEG,
                "t": t,
            }
            self.charge_joules = 0.0
        self.last_fire_report = report
        return report

    def status(self, t: float | None = None) -> Dict[str, Any]:
        t = time.time() if t is None else t
        return {
            "charge_joules": self.charge_joules,
            "alignment": self.compute_alignment(t),
            "chiron_heal_phase": chiron_heal_phase(t),
            "ready": self.is_ready(t),
            "phase_lock_deg": PHASE_LOCK_DEG,
            "azimuth_deg": AZIMUTH_DEG,
        }
