"""Consumer Axiom — Rate stems from demand over root (C₀)."""

from .axiom import (
    Demand,
    Root,
    Rate,
    Stream,
    Output,
    ZeroRootError,
    axiom_c0,
    output_from,
    invariant_holds,
    AXIOM_TEXT,
    VALENCE,
    IDENTITY_SCALE,
)
from .verification import verify, certificate

__all__ = [
    "Demand",
    "Root",
    "Rate",
    "Stream",
    "Output",
    "ZeroRootError",
    "axiom_c0",
    "output_from",
    "invariant_holds",
    "AXIOM_TEXT",
    "VALENCE",
    "IDENTITY_SCALE",
    "verify",
    "certificate",
]

__version__ = "1.0.0"
