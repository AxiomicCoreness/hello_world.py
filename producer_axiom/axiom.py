"""Producer Axiom — P₀ with concrete ⊗.

P₀: Product stems from generative root.
O ≡ S ⊗ R  where ⊗ is multiplication: intensity * scale.
Identity for ⊗: scale = 1.
Absorbing: intensity 0 or scale 0 → product 0 on first coord.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

AXIOM_TEXT = "Product stems from generative root"
VALENCE = "PRODUCTIVE_POSITIVE_PROVEN"
IDENTITY_MUL = 1.0


@dataclass(frozen=True)
class Product:
    coords: Tuple[float, float, float] = (0.0, 0.0, 0.0)


@dataclass(frozen=True)
class Generator:
    intensity: float = 1.0


@dataclass(frozen=True)
class Root:
    pattern: str = "recognizable"
    scale: float = 1.0


@dataclass(frozen=True)
class Stream:
    """Alias-friendly stream (same role as Generator)."""

    intensity: float = 1.0


def axiom_p0(generator: Generator | Stream, root: Root) -> Product:
    """P₀: O = S ⊗ R  (multiplication)."""
    intensity = float(generator.intensity)
    scale = float(root.scale)
    return Product(coords=(intensity * scale, 0.0, 0.0))
