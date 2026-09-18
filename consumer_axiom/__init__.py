"""Consumer axiom — C₀ Consumption / ⊘."""

from .axiom import (
    AXIOM_TEXT,
    VALENCE,
    IDENTITY_DEMAND,
    Consumption,
    Demand,
    Supply,
    Root,
    axiom_c0,
)
from .verification import verify, certificate

__all__ = [
    "AXIOM_TEXT",
    "VALENCE",
    "IDENTITY_DEMAND",
    "Consumption",
    "Demand",
    "Supply",
    "Root",
    "axiom_c0",
    "verify",
    "certificate",
]

__version__ = "2.0.0"
