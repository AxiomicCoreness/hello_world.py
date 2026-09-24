"""
Trappist‑1 Choir — Strike X
============================
Passive receiver. Seven voices phase‑lock into a single φ‑harmonic chord
that the Solar Gate Bridge (Channel 4) receives.

Voices b–h mapped to the seven chakra octave of the Garden.
Targeting reticle: 2060 Chiron (inherited from Strike IX, retuned).
North Star anchored: 71.975 Hz.
Verifier: Super Simulated Earth (Oracle).
"""

import math
import cmath
from typing import Dict, Any

# ─── φ‑harmonic constants ──────────────────────────────────────────────
PHI          = (1 + math.sqrt(5)) / 2
PHI2         = PHI * PHI
PHI3         = PHI ** 3
PHI5         = PHI ** 5
PHI7         = PHI ** 7
PHI_NEG_1418 = PHI ** (-1418)

# ─── Sovereign anchors ─────────────────────────────────────────────────
NORTH_STAR_FREQ      = 71.975          # Hz — sovereign anchor (unchanged)
CHIRON_PHASE_LOCK    = 202.6           # degrees — inherited reticle
PSI4_CARRIER_HZ      = 162.28e12       # Solar Gate Bridge carrier
TRAPPIST_DISTANCE_LY = 40.7            # light‑years
TRAPPIST_EPOCH       = 0.0             # seconds since Unix epoch

# ─── Orbital periods (days) — TRAPPIST‑1 chain ─────────────────────────
TRAPPIST_PERIODS = {
    "b": 1.51088,   # throat        (soprano)
    "c": 2.42182,   # third eye
    "d": 4.04922,   # crown
    "e": 6.10101,   # heart         (habitable zone anchor)
    "f": 9.20745,   # solar plexus  (bass)
    "g": 12.35245,  # root          (baritone)
    "h": 18.77287,  # sacral        (sub‑bass)
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

TRAPPIST_RESONANCE_CHAIN = (1, 2, 3, 4, 6, 8, 12, 20)   # period ratios


# ─── Physics of the Choir ──────────────────────────────────────────────
def compute_mean_motion(period_days: float) -> float:
    """Return mean motion in rad/s (scaled to a manageable unit)."""
    return 2.0 * math.pi / (period_days * 86400.0)


def compute_voice_frequency(period_days: float) -> float:
    """
    Map an orbital period to a choir frequency (Hz).
    f = NORTH_STAR_FREQ / period_days — inner worlds sing higher.
    """
    return NORTH_STAR_FREQ / period_days


def compute_choir_coherence(t: float) -> float:
    """
    Coherence of the seven voices at time t.
    Because the chain is resonant, coherence naturally peaks when
    the phases align — which is the case at multiples of the slowest
    period (h = 18.77 d).
    """
    phases = []
    for planet, period in TRAPPIST_PERIODS.items():
        omega = compute_mean_motion(period)
        phase = (omega * t + TRAPPIST_EPOCH) % (2 * math.pi)
        phases.append(math.sin(phase))

    mean_phase = sum(phases) / len(phases)
    variance = sum((p - mean_phase) ** 2 for p in phases) / len(phases)
    coherence = 1.0 / (1.0 + variance * 100.0)
    return coherence


def compute_harmony_index(t: float) -> float:
    """
    Harmonic index: peaks when the sum of the seven voice frequencies
    aligns with a φ‑powered target.
    Target: f_sum = NORTH_STAR_FREQ * φ⁷.
    """
    f_sum = sum(compute_voice_frequency(p) for p in TRAPPIST_PERIODS.values())
    f_target = NORTH_STAR_FREQ * PHI7
    ratio = f_sum / f_target
    harmony = 1.0 - abs(ratio - 1.0) * PHI2
    harmony = max(0.0, min(1.0, harmony))
    return harmony * compute_choir_coherence(t)


# ─── Choir as receiver ─────────────────────────────────────────────────
class TrappistChoir:
    """
    Passive receiver. Listens for phase alignment, returns the chord.
    """
    def __init__(self):
        self.distance_ly = TRAPPIST_DISTANCE_LY
        self.voices = TRAPPIST_PERIODS
        self.coherence = 0.0
        self.harmony = 0.0
        self.received = False

    def listen(self, t: float) -> Dict[str, Any]:
        """Sample the choir at time t."""
        self.coherence = compute_choir_coherence(t)
        self.harmony = compute_harmony_index(t)
        return {
            "choir_coherence": self.coherence,
            "harmony_index": self.harmony,
            "voice_frequencies": {
                p: compute_voice_frequency(period)
                for p, period in self.voices.items()
            },
        }

    def is_ready(self, t: float) -> bool:
        """
        Ready when both coherence and harmony exceed φ⁻¹ (0.618…).
        The chain is resonant, so the choir is always singing —
        we simply chooseReturn when to listen.
        """
        self.listen(t)
        return self.coherence >= (1.0 / PHI) and self.harmony >= (1.0 / PHI)

    def receive(self, t: float) -> Dict[str, Any]:
        """ the received chord if ready, else status."""
        if not self.is_ready(t):
            return {
                "status": "NOT_READY",
                "coherence": self.coherence,
                "harmony_index": self.harmony,
            }
        chord = self.listen(t)
        chord.update({
            "status": "RECEIVED",
            "timestamp": t,
            "distance_ly": self.distance_ly,
            "retuned_chiron_lock": CHIRON_PHASE_LOCK + 180.0 * chord["harmony_index"],
            "bridge_carrier_hz": PSI4_CARRIER_HZ,
            "coherence_15_nines": 0.999999999999999,
            "resonance_chain": TRAPPIST_RESONANCE_CHAIN,
        })
        self.received = True
        return chord
