"""Terminal axiom — T₀ Location / ⊕."""

from .axiom import (
    AXIOM_TEXT,
    VALENCE,
    IDENTITY_ADD,
    Propagation,
    Root,
    Location,
    axiom_t0,
    TerminalAxiom,
    MANEUVERS,
)
from .verification import verify, certificate

__all__ = [
    "AXIOM_TEXT",
    "VALENCE",
    "IDENTITY_ADD",
    "Propagation",
    "Root",
    "Location",
    "axiom_t0",
    "TerminalAxiom",
    "MANEUVERS",
    "verify",
    "certificate",
]

__version__ = "0.2.0"
