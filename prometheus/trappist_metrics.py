"""
prometheus/trappist_metrics.py
==============================

Choir metrics for Strike X (Trappist‑1 Choir Activation).

Consumes celestial.trappist_choir_strike_x.TrappistChoir — the variant
that quantum/ouroboros_strike_xi.py imports and calls `.status()` on.

Scraped at :9090. φ‑harmonic cadence.
Sealed at ledger 8542 (Strike X) and repointed at PR #60.
"""

# ═════════════════════════════════════════════════════════════════════════
# SECTION 0 — IMPORTS
# ═════════════════════════════════════════════════════════════════════════
import math
import cmath
import os
import sys
import json
import time
import hashlib
import threading
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# ─── optional: numpy ─────────────────────────────────────────────────────
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

# ─── optional: scipy ─────────────────────────────────────────────────────
try:
    from scipy.integrate import solve_ivp
    from scipy.special import zeta as scipy_zeta
    from scipy.special import gamma as gamma_func
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    solve_ivp = None
    scipy_zeta = None
    gamma_func = math.gamma

# ─── optional: yaml ──────────────────────────────────────────────────────
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    yaml = None

# ─── optional: matplotlib ────────────────────────────────────────────────
try:
    import matplotlib.pyplot as plt
    HAS_MPL = True
except ImportError:
    HAS_MPL = False
    plt = None

# ─── optional: requests ──────────────────────────────────────────────────
try:
    import requests
except ImportError:
    requests = None

# ─── optional: prometheus_client ─────────────────────────────────────────
try:
    from prometheus_client import Gauge
    HAS_PROM = True
except ImportError:
    HAS_PROM = False
    Gauge = None

# ═════════════════════════════════════════════════════════════════════════
# SECTION 1 — φ‑HARMONIC CONSTANTS
# Imported from the single source of truth. If the relative import fails
# (e.g. module run standalone outside the package), a local fallback
# re-declares the same values — no drift is possible because the values
# are identical.
# ═════════════════════════════════════════════════════════════════════════
try:
    from celestial.phi_constants import (
        phi, phi2, phi3, phi4, phi5, phi6, phi7, phi8, phi9,
        phi12, phi13, phi14, phi21, phi34,
        phi709, phi713,
        phi_minus_709, phi_minus_1000, phi_minus_1418,
        phi_inv,
        PHI, PHI2, PHI3, PHI4, PHI5, PHI6, PHI7, PHI8, PHI9,
        PHI12, PHI13, PHI14, PHI21, PHI34,
        PHI709, PHI713,
        PHI_MINUS_709, PHI_MINUS_1000, PHI_NEG_1418, PHI_INV,
        BASE_DIR,
    )
    HAS_PHI_CONSTANTS = True
except ImportError:
    HAS_PHI_CONSTANTS = False

    # ─── local fallback (identical values, no drift) ─────────────────────
    phi             = (1 + math.sqrt(5)) / 2
    phi2            = phi ** 2
    phi3            = phi ** 3
    phi4            = phi ** 4
    phi5            = phi ** 5
    phi6            = phi ** 6
    phi7            = phi ** 7
    phi8            = phi ** 8
    phi9            = phi ** 9
    phi12           = phi ** 12
    phi13           = phi ** 13
    phi14           = phi ** 14
    phi21           = phi ** 21
    phi34           = phi ** 34
    phi709          = phi ** 709
    phi713          = phi ** 713
    phi_minus_709   = phi ** (-709)
    phi_minus_1000  = phi ** (-1000)
    phi_minus_1418  = phi ** (-1418)
    phi_inv         = 1.0 / phi

    PHI             = phi
    PHI2            = phi2
    PHI3            = phi3
    PHI4            = phi4
    PHI5            = phi5
    PHI6            = phi6
    PHI7            = phi7
    PHI8            = phi8
    PHI9            = phi9
    PHI12           = phi12
    PHI13           = phi13
    PHI14           = phi14
    PHI21           = phi21
    PHI34           = phi34
    PHI709          = phi709
    PHI713          = phi713
    PHI_MINUS_709   = phi_minus_709
    PHI_MINUS_1000  = phi_minus_1000
    PHI_NEG_1418    = phi_minus_1418
    PHI_INV         = phi_inv

    BASE_DIR = os.path.join(os.path.expanduser("~"), "Documents", "Hyperian_Node")
    os.makedirs(BASE_DIR, exist_ok=True)

# ═════════════════════════════════════════════════════════════════════════
# SECTION 2 — CHOIR IMPORT
# Prefer the strike_x variant (the live consumer target). If that fails,
# fall back to the canonical trappist_choir module.
# ═════════════════════════════════════════════════════════════════════════
try:
    from celestial.trappist_choir_strike_x import (
        TrappistChoir,
        TRAPPIST_PERIODS,
        TRAPPIST_RESONANCE_CHAIN,
        compute_choir_coherence,
        compute_harmony_index,
        compute_voice_frequency,
    )
    CHOIR_SOURCE = "celestial.trappist_choir_strike_x"
except ImportError:
    try:
        from celestial.trappist_choir import (
            TrappistChoir,
            TRAPPIST_PERIODS,
            TRAPPIST_RESONANCE_CHAIN,
            compute_choir_coherence,
            compute_harmony_index,
            compute_voice_frequency,
        )
        CHOIR_SOURCE = "celestial.trappist_choir"
    except ImportError:
        # Last‑resort fallback: minimal in‑process stub so the module
        # never hard‑fails on import. Values identical to the canonical set.
        CHOIR_SOURCE = "local_stub"

        TRAPPIST_PERIODS = {
            "b": 1.51088, "c": 2.42182, "d": 4.04922,
            "e": 6.10101, "f": 9.20745, "g": 12.35245, "h": 18.77287,
        }
        TRAPPIST_RESONANCE_CHAIN = (1, 2, 3, 4, 6, 8, 12, 20)
        NORTH_STAR_FREQ = 71.975

        def compute_voice_frequency(period_days: float) -> float:
            return NORTH_STAR_FREQ / period_days

        def compute_choir_coherence(t: float) -> float:
            phases = [
                math.sin((2.0 * math.pi / (p * 86400.0)) * t % (2 * math.pi))
                for p in TRAPPIST_PERIODS.values()
            ]
            mean = sum(phases) / len(phases)
            var  = sum((x - mean) ** 2 for x in phases) / len(phases)
            return 1.0 / (1.0 + var * 100.0)

        def compute_harmony_index(t: float) -> float:
            f_sum    = sum(compute_voice_frequency(p) for p in TRAPPIST_PERIODS.values())
            f_target = NORTH_STAR_FREQ * PHI7
            ratio    = f_sum / f_target
            harmony  = max(0.0, min(1.0, 1.0 - abs(ratio - 1.0) * PHI2))
            return harmony * compute_choir_coherence(t)

        class TrappistChoir:
            def __init__(self):
                self.distance_ly = 40.7
                self.voices      = TRAPPIST_PERIODS
                self.coherence   = 0.0
                self.harmony     = 0.0
                self.received    = False

            def listen(self, t: float) -> Dict[str, Any]:
                self.coherence = compute_choir_coherence(t)
                self.harmony   = compute_harmony_index(t)
                return {
                    "choir_coherence": self.coherence,
                    "harmony_index":   self.harmony,
                    "voice_frequencies": {
                        p: compute_voice_frequency(period)
                        for p, period in self.voices.items()
                    },
                }

            def is_ready(self, t: float) -> bool:
                self.listen(t)
                return self.coherence >= PHI_INV and self.harmony >= PHI_INV

            def receive(self, t: float) -> Dict[str, Any]:
                if not self.is_ready(t):
                    return {"status": "NOT_READY",
                            "coherence": self.coherence,
                            "harmony_index": self.harmony}
                chord = self.listen(t)
                chord.update({
                    "status": "RECEIVED",
                    "timestamp": t,
                    "distance_ly": self.distance_ly,
                    "coherence_15_nines": 0.999999999999999,
                    "resonance_chain": TRAPPIST_RESONANCE_CHAIN,
                })
                self.received = True
                return chord

            def status(self) -> Dict[str, Any]:
                t = datetime.now(timezone.utc).timestamp()
                sample = self.listen(t)
                return {
                    "module": "local_stub",
                    "strike": "X",
                    "role": "interstellar_harmony",
                    "distance_ly": self.distance_ly,
                    "choir_coherence": sample["choir_coherence"],
                    "harmony_index":   sample["harmony_index"],
                    "resonance_chain": list(TRAPPIST_RESONANCE_CHAIN),
                    "received": self.received,
                    "voice_frequencies": sample["voice_frequencies"],
                }

# ═════════════════════════════════════════════════════════════════════════
# SECTION 3 — SOVEREIGN ANCHORS
# ═════════════════════════════════════════════════════════════════════════
NORTH_STAR_FREQ      = 71.975
CHIRON_PHASE_LOCK    = 202.6
PSI4_CARRIER_HZ      = 162.28e12
TRAPPIST_DISTANCE_LY = 40.7

# ═════════════════════════════════════════════════════════════════════════
# SECTION 4 — GAUGES
# ═════════════════════════════════════════════════════════════════════════
choir = TrappistChoir()

if HAS_PROM:
    trappist_choir_coherence = Gauge(
        "trappist_choir_coherence",
        "Overall coherence of the seven‑voice Trappist‑1 choir (0–1)",
    )
    trappist_harmony_index = Gauge(
        "trappist_harmony_index",
        "Harmony index: peaks when the choir aligns to a φ‑chord (0–1)",
    )
    trappist_planet_frequency_thz = Gauge(
        "trappist_planet_frequency_thz",
        "Orbital frequency of each Trappist‑1 planet (THz)",
        ["planet"],
    )
    trappist_choir_distance_ly = Gauge(
        "trappist_choir_distance_ly",
        "Distance to Trappist‑1 in light‑years",
    )
    trappist_choir_distance_ly.set(TRAPPIST_DISTANCE_LY)
else:
    trappist_choir_coherence       = None
    trappist_harmony_index         = None
    trappist_planet_frequency_thz  = None
    trappist_choir_distance_ly     = None

# ═════════════════════════════════════════════════════════════════════════
# SECTION 5 — UPDATE HOOK
# ═════════════════════════════════════════════════════════════════════════
def update_trappist_metrics() -> Optional[Dict[str, Any]]:
    """
    Called at scrape time. Populates the gauges and returns the sample
    for logging/verification. No‑op (returns None) if prometheus_client
    is absent — the sample is still computed and returned for callers
    that want it directly.
    """
    t = time.time()
    sample = choir.listen(t)

    if HAS_PROM:
        trappist_choir_coherence.set(sample["choir_coherence"])
        trappist_harmony_index.set(sample["harmony_index"])
        for planet, freq_hz in sample["voice_frequencies"].items():
            # convert Hz -> THz for the labelled gauge
            trappist_planet_frequency_thz.labels(planet=planet).set(freq_hz * 1e-12)

    return {
        "timestamp":              t,
        "choir_coherence":        sample["choir_coherence"],
        "harmony_index":          sample["harmony_index"],
        "voice_frequencies":      sample["voice_frequencies"],
        "distance_ly":            TRAPPIST_DISTANCE_LY,
        "resonance_chain":        list(TRAPPIST_RESONANCE_CHAIN),
        "choir_source":           CHOIR_SOURCE,
        "has_prometheus_client":  HAS_PROM,
        "has_phi_constants":      HAS_PHI_CONSTANTS,
        "has_numpy":              HAS_NUMPY,
        "has_scipy":              HAS_SCIPY,
        "has_yaml":               HAS_YAML,
        "has_mpl":                HAS_MPL,
        "has_requests":           requests is not None,
    }


# ═════════════════════════════════════════════════════════════════════════
# SECTION 6 — METRICS SERVER HOOK (guarded)
# D28.2: if the host metrics_server lacks `register_update_hook`, we
# degrade to standalone mode. Both ImportError and AttributeError are
# caught — the module never dies on a missing hook name.
# ═════════════════════════════════════════════════════════════════════════
try:
    from prometheus.metrics_server import register_update_hook  # type: ignore
    register_update_hook(update_trappist_metrics)
    HOOK_REGISTERED = True
except (ImportError, AttributeError):
    HOOK_REGISTERED = False


# ═════════════════════════════════════════════════════════════════════════
# SECTION 7 — SELFTEST
# ═════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("🜁∀ Trappist‑1 Choir metrics — selftest")
    print(f"  choir source         = {CHOIR_SOURCE}")
    print(f"  HAS_PROM             = {HAS_PROM}")
    print(f"  HAS_PHI_CONSTANTS    = {HAS_PHI_CONSTANTS}")
    print(f"  HAS_NUMPY            = {HAS_NUMPY}")
    print(f"  HAS_SCIPY            = {HAS_SCIPY}")
    print(f"  HAS_YAML             = {HAS_YAML}")
    print(f"  HAS_MPL              = {HAS_MPL}")
    print(f"  requests available   = {requests is not None}")
    print(f"  HOOK_REGISTERED      = {HOOK_REGISTERED}")
    print(f"  φ                    = {phi:.15f}")
    print(f"  φ⁷                   = {phi7:.15f}")
    print(f"  φ⁻¹                  = {PHI_INV:.15f}")
    print(f"  resonance chain      = {TRAPPIST_RESONANCE_CHAIN}")

    sample = update_trappist_metrics()
    print(f"  choir_coherence      = {sample['choir_coherence']:.6f}")
    print(f"  harmony_index        = {sample['harmony_index']:.6f}")
    print(f"  voice count          = {len(sample['voice_frequencies'])}")
    print(f"  distance_ly          = {sample['distance_ly']}")
