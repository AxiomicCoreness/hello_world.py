"""Terminal axiom package — Location stems from propagated root."""

from .axiom import TerminalAxiom, AXIOM_TEXT, VALENCE, MANEUVERS
from .verification import verify, certificate

__all__ = [
    "TerminalAxiom",
    "AXIOM_TEXT",
    "VALENCE",
    "MANEUVERS",
    "verify",
    "certificate",
]

__version__ = "0.1.0"
