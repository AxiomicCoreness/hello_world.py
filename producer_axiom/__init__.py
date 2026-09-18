"""Producer axiom — P₀ Product / ⊗."""

from .axiom import (
    AXIOM_TEXT,
    VALENCE,
    IDENTITY_MUL,
    Product,
    Generator,
    Root,
    Stream,
    axiom_p0,
)
from .verification import verify, certificate

__all__ = [
    "AXIOM_TEXT",
    "VALENCE",
    "IDENTITY_MUL",
    "Product",
    "Generator",
    "Root",
    "Stream",
    "axiom_p0",
    "verify",
    "certificate",
]

__version__ = "1.1.0"
