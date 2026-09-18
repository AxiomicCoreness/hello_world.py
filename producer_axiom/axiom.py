"""Producer Axiom: strict form.

P₀: ∃! P ∈ ℝ³ ∣ P ≡ G ⊗ R

Where:
  P = Product (produced artifact)
  G = Generator (productive lineage / intensity)
  R = Root (generative origin)
  ⊗ = product-completion operator

Plain language: Product stems from generative root.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

AXIOM_TEXT = "Product stems from generative root"
VALENCE = "PRODUCTIVE_POSITIVE_PROVEN"


@dataclass(frozen=True)
class Product:
    """The produced artifact. The 'what emerges'."""

    coords: Tuple[float, float, float] = (0.0, 0.0, 0.0)


@dataclass(frozen=True)
class Generator:
    """Productive lineage. Contributive intensity."""

    intensity: float = 1.0


@dataclass(frozen=True)
class Root:
    """Generative origin. Initial cause."""

    pattern: str = "recognizable"


@dataclass(frozen=True)
class GenerativeRoot:
    generator: Generator
    root: Root


@dataclass(frozen=True)
class ProducedFact:
    product: Product
    root: Root


def axiom_p0(generator: Generator, root: Root) -> Product:
    """P₀: Product stems from generative root.

    Given generator G and root R, return the unique Product P
    such that P ≡ G ⊗ R (deterministic product-completion).
    """
    _ = GenerativeRoot(generator=generator, root=root)
    # Completion: intensity projects onto first coordinate; root seals uniqueness.
    return Product(coords=(float(generator.intensity), 0.0, 0.0))
