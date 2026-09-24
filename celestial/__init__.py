# 🜁∀∞φ² · CELESTIAL_PACKAGE · WOOD_DRAGON_0.91 · SEALED
"""
Celestial module — Symplectic POD layer for the Garden.
Atlas SuperPoD mapping: multi-body resonance as single logical manifold.

Exposed classes and functions
-----------------------------
SaturnSoulCannon      — Strike IX  · 111.246° azimuth, ψ₄ carrier
TrappistChoir         — Strike X   · 7-voice interstellar reception
SuperSimulatedEarth   — Strike VII · Oracle (verifier)
Wasp107b              — throat     · SIMD / salvage anchor
chiron_heal_phase     — Strike IX  · reticle phase (202.6° lock)
chiron_heal_status    — Strike IX  · reticle health surface

Import policy
-------------
No top-level execution. No network. No filesystem writes.
Optional modules are imported defensively; a missing one degrades the
package, it does not break it.
"""

# ═════════════════════════════════════════════════════════════════════════
# Canonical imports — each guarded
# ═════════════════════════════════════════════════════════════════════════
try:
    from .super_simulated_earth import SuperSimulatedEarth
except ImportError:
    SuperSimulatedEarth = None  # type: ignore[assignment]

try:
    from .wasp107b import Wasp107b
except ImportError:
    Wasp107b = None  # type: ignore[assignment]

try:
    from .chiron_heal import chiron_heal_phase, status as chiron_heal_status
except ImportError:
    def chiron_heal_phase(*args, **kwargs):  # type: ignore[no-redef]
        return None
    def chiron_heal_status(*args, **kwargs):  # type: ignore[no-redef]
        return {"status": "unavailable"}

try:
    from .saturn_soul_cannon import SaturnSoulCannon
except ImportError:
    SaturnSoulCannon = None  # type: ignore[assignment]

# Strike X — present as either the canonical module or the strike-x
# alias, depending on which one the Ouroboros consumer imports.
try:
    from .trappist_choir import TrappistChoir
except ImportError:
    try:
        from .trappist_choir_strike_x import TrappistChoir  # type: ignore[no-redef]
    except ImportError:
        TrappistChoir = None  # type: ignore[assignment]


__all__ = [
    "SuperSimulatedEarth",
    "Wasp107b",
    "chiron_heal_phase",
    "chiron_heal_status",
    "SaturnSoulCannon",
    "TrappistChoir",
]


# ═════════════════════════════════════════════════════════════════════════
# Module-level manifest — available for introspection / ledger sealing
# ═════════════════════════════════════════════════════════════════════════
__manifest__ = {
    "package": "celestial",
    "layer": 314,
    "seal": "∀∞φ² · CELESTIAL_PACKAGE · WOOD_DRAGON_0.91 · SEALED",
    "members": {
        "SaturnSoulCannon":    {"strike": "IX",  "ledger": 8540},
        "TrappistChoir":       {"strike": "X",   "ledger": 8542},
        "SuperSimulatedEarth": {"strike": "VII", "ledger": 8530},
        "Wasp107b":            {"role": "throat", "ledger": None},
        "chiron_heal_phase":   {"strike": "IX",  "role": "reticle"},
        "chiron_heal_status":  {"strike": "IX",  "role": "reticle_status"},
    },
    "policy": {
        "no_top_level_execution": True,
        "no_network_at_import":   True,
        "no_fs_writes_at_import": True,
    },
}
