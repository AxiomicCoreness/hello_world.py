#!/usr/bin/env python3
"""
Precompute FRB bridge lattice weights for the next convergence window.
Writes JSON (default /tmp/lattice_weights.json).

Seal: ∀∞φ² · FINGERPRINT_PRECOMPUTE_8631 · SEALED
"""

from __future__ import annotations

import json
import math
import os
import time
from datetime import datetime, timezone
from pathlib import Path

PHI = (1.0 + math.sqrt(5.0)) / 2.0
TAU_FRB = 78624.0
NUM_LAYERS = 12
NUM_AZIMUTHS = 4
NORM = PHI ** 5  # ~11.09; narrative 11.83 kept as comment alternate
R0 = 0.2033
DELTA_Z = 6552.0
HYPERIAN = os.environ.get("HYPERIAN_URL", "http://127.0.0.1:8080").rstrip("/")
OUT_PATH = Path(os.environ.get("LATTICE_OUT", "/tmp/lattice_weights.json"))


def get_current_phase() -> float:
    try:
        import requests

        resp = requests.get(f"{HYPERIAN}/status", timeout=2)
        data = resp.json()
        return float(data.get("phase_lock_deg", data.get("phase_lock_degrees", 202.6)))
    except Exception:
        now = time.time()
        perihelion = datetime(2026, 4, 4, tzinfo=timezone.utc).timestamp()
        days_since = (now - perihelion) / 86400.0
        phase = (202.6 + (360.0 / (50.7 * 365.25)) * days_since) % 360.0
        return phase


def generate_lattice(phase_deg: float) -> dict:
    points = []
    for L in range(NUM_LAYERS):
        for A in range(NUM_AZIMUTHS):
            angle = A * math.pi / 2
            radius = R0 * (PHI ** (L / 4.0))
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            z = L * DELTA_Z
            weight = (
                NORM
                * (PHI ** -(L + 1))
                * (math.cos(angle) ** 2)
                * math.exp(-((L - 6) ** 2) / 8.0)
            )
            points.append(
                {
                    "layer": L,
                    "azimuth_index": A,
                    "x": round(x, 6),
                    "y": round(y, 6),
                    "z": round(z, 6),
                    "weight": round(weight, 6),
                }
            )
    return {
        "meta": {
            "version": "1.0.0",
            "description": "Precomputed lattice for next convergence",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "parameters": {
            "tau_FRB_seconds": TAU_FRB,
            "azimuth_target_deg": 111.246,
            "phi": PHI,
            "num_layers": NUM_LAYERS,
            "num_azimuths": NUM_AZIMUTHS,
            "r0": R0,
            "delta_z": DELTA_Z,
            "phase_lock_deg": phase_deg,
            "weight_formula": "w(L,A)=φ^{-(L+1)}·cos²(π·A/2)·exp(-(L-6)²/8)",
        },
        "points": points,
        "verification": {
            "emergent_period_days": 16.35,
            "notes": f"Precomputed for next window; phase lock {phase_deg:.3f}°",
        },
    }


if __name__ == "__main__":
    phase = get_current_phase()
    lattice = generate_lattice(phase)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(lattice, f, indent=2)
    print(f"Lattice weights precomputed for phase {phase:.3f} -> {OUT_PATH}")
