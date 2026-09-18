"""Producer Axiom — Product stems from generative root."""

from .axiom import (
    Product,
    Generator,
    Root,
    axiom_p0,
    VALENCE,
    AXIOM_TEXT,
    ProducedFact,
    GenerativeRoot,
)
from .verification import verify, certificate

__all__ = [
    "Product",
    "Generator",
    "Root",
    "axiom_p0",
    "VALENCE",
    "AXIOM_TEXT",
    "ProducedFact",
    "GenerativeRoot",
    "verify",
    "certificate",
]

__version__ = "1.0.0"
