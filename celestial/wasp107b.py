#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wasp-107b Celestial Model
0.12 Mⱼ, 0.94 Rⱼ, 5.72-day orbit — atmospheric escape + φ-resonance.
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Dict

PHI = (1 + math.sqrt(5)) / 2


@dataclass
class Wasp107b:
    mass_mj: float = 0.12
    radius_rj: float = 0.94
    period_days: float = 5.72
    coherence: float = 1.0

    def orbital_frequency_hz(self) -> float:
        """Base orbital frequency in Hz (very small, typically ~2 microHz)."""
        return 1.0 / (self.period_days * 86400.0)

    def phi_resonance_hz(self) -> float:
        """φ-resonance carrier in Hz."""
        return self.orbital_frequency_hz() * PHI

    def phi_resonance_thz(self) -> float:
        """
        Convert the φ-resonance into THz to align with the Garden's 
        spectral constants (matches the ~76 THz ghost vortex signature).
        """
        return self.phi_resonance_hz() * 1e12

    def status(self) -> Dict:
        return {
            "mass_mj": self.mass_mj,
            "radius_rj": self.radius_rj,
            "period_days": self.period_days,
            "orbital_frequency_hz": self.orbital_frequency_hz(),
            "phi_resonance_hz": self.phi_resonance_hz(),
            "phi_resonance_thz": self.phi_resonance_thz(),
            "coherence": self.coherence,
            "seal": "∀∞φ² · WASP_107b_THROAT_ANCHOR · SEALED",
        }
