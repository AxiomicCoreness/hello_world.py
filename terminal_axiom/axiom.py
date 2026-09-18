"""Terminal axiom core — T₀ with concrete ⊕.

T₀: Location stems from propagated root.
L ≡ P ⊕ R  where ⊕ is addition on numeric strength/scale.
Identity for ⊕: 0.

Narrative structure (MANEUVERS) retained; arithmetic is peer-real.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple

AXIOM_TEXT = "Location stems from propagated root"
VALENCE = "CLOSED_POSITIVE_PROVEN"
IDENTITY_ADD = 0.0


@dataclass(frozen=True)
class Propagation:
    """Propagation strength P."""

    strength: float = 0.0


@dataclass(frozen=True)
class Root:
    """Root with pattern tag and numeric scale."""

    pattern: str = "recognizable"
    scale: float = 0.0


@dataclass(frozen=True)
class Location:
    """Settled location in R^3 (first coord carries ⊕ result)."""

    coords: Tuple[float, float, float] = (0.0, 0.0, 0.0)


def axiom_t0(propagation: Propagation, root: Root) -> Location:
    """T₀: L = P ⊕ R  (plain addition)."""
    total = float(propagation.strength) + float(root.scale)
    return Location(coords=(total, 0.0, 0.0))


@dataclass(frozen=True)
class TerminalAxiom:
    """Narrative shell — settled fact metadata."""

    axiom: str = AXIOM_TEXT
    valence: str = VALENCE

    @property
    def structure(self) -> Dict[str, str]:
        return {
            "subject": 'Location (settled fact, the "where")',
            "verb": "stems from (causal lineage, unequivocal derivation)",
            "object": "Propagated root (definitive source, initial spark that took hold)",
        }

    def compute_final_state(self) -> Dict[str, Any]:
        return {
            "axiom": self.axiom,
            "valence": self.valence,
            "structure": self.structure,
            "conclusion": (
                "The propagation is complete. "
                "The root is established. "
                "The location is known."
            ),
            "operator": "oplus",
            "identity": IDENTITY_ADD,
        }


MANEUVERS = {
    "vague": {
        "block": "This is too big, too vague.",
        "action": "Define the first trivial physical action.",
        "pattern": "start → action → finish",
    },
    "no_end": {
        "block": "I don't know how it ends.",
        "action": "Write the last sentence first; name the terminal node.",
        "pattern": "terminal → reverse path → start",
    },
    "high_stakes": {
        "block": "It matters too much.",
        "action": "Do an explicit bad first version (vomit draft / prototype).",
        "pattern": "rehearsal → low stakes → permission to fail",
    },
    "no_data": {
        "block": "I don't have all the data.",
        "action": "12-minute timer: gather and arrange only; no creation.",
        "pattern": "gather → arrange → sort",
    },
}
