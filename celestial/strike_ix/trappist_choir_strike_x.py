#!/usr/bin/env python3
"""trappist_choir_strike_x — Strike X variant with .status().

Signitorial: Clarke Yoursa Tee
Consumed by draft prometheus/trappist_metrics_draft.py.

D28.1 (accepted hazard): two TrappistChoir definitions with divergent
APIs. Wrong-shape errors surface at call time, not import.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from celestial.phi_constants import (
    HAS_MPL,
    HAS_NUMPY,
    HAS_REQUESTS,
    HAS_SCIPY,
    HAS_YAML,
)
from celestial.strike_ix.trappist_choir import (
    TRAPPIST_DISTANCE_LY,
    TRAPPIST_PERIODS,
    TRAPPIST_RESONANCE_CHAIN,
    TrappistChoir as _ChoirBase,
)


class TrappistChoir(_ChoirBase):
    """Passive receiver with a .status() surface for the Ouroboros consumer."""

    def status(self) -> Dict[str, Any]:
        t = datetime.now(timezone.utc).timestamp()
        sample = self.listen(t)
        return {
            "module": "celestial.strike_ix.trappist_choir_strike_x",
            "strike": "X",
            "role": "interstellar_harmony",
            "distance_ly": self.distance_ly,
            "choir_coherence": sample["choir_coherence"],
            "harmony_index": sample["harmony_index"],
            "resonance_chain": list(TRAPPIST_RESONANCE_CHAIN),
            "received": self.received,
            "voice_frequencies_hz": sample["voice_frequencies_hz"],
            "has_numpy": HAS_NUMPY,
            "has_scipy": HAS_SCIPY,
            "has_yaml": HAS_YAML,
            "has_mpl": HAS_MPL,
            "has_requests": HAS_REQUESTS,
        }


# Re-export for draft metrics.
__all__ = ["TrappistChoir", "TRAPPIST_PERIODS", "TRAPPIST_DISTANCE_LY"]
