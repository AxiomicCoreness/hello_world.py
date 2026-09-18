"""Terminal axiom core.

T₀: Location stems from propagated root.
Valence: CLOSED_POSITIVE_PROVEN.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

AXIOM_TEXT = "Location stems from propagated root"
VALENCE = "CLOSED_POSITIVE_PROVEN"


@dataclass(frozen=True)
class TerminalAxiom:
    """Settled fact derived from definitive source."""

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
        }


# Pattern-completion (procrastination as incomplete pattern, not will-failure)
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
