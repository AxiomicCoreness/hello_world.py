"""Consumer Axiom: Spec B.

C₀: ⊘ = D / R

  Rate C = Demand D divided by Root scale R.
  Identity: R.scale = 1 → C.value = D.value
  R.scale = 0 → ZeroRootError at division time (construction allowed).

Invariant (default #1):
  C · O = D · S
  with O = S · R  (product-completion of stream and root).
  Hence C·O = (D/R)·(S·R) = D·S.

Negatives allowed. domain is informational only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

AXIOM_TEXT = "Rate stems from demand over root"
VALENCE = "CONSUMING_POSITIVE_PROVEN"
IDENTITY_SCALE = 1.0


class ZeroRootError(ZeroDivisionError):
    """Raised when dividing by Root with scale == 0."""


@dataclass(frozen=True)
class Demand:
    """Demand magnitude D."""

    value: float
    domain: str = ""  # informational only


@dataclass(frozen=True)
class Root:
    """Root scale R. scale=0 is constructible; fails at ⊘."""

    scale: float
    domain: str = ""


@dataclass(frozen=True)
class Rate:
    """Rate C = D ⊘ R."""

    value: float
    domain: str = ""


@dataclass(frozen=True)
class Stream:
    """Stream intensity S (lineage factor)."""

    intensity: float = 1.0


@dataclass(frozen=True)
class Output:
    """Output O = S · R."""

    value: float


def axiom_c0(demand: Demand, root: Root) -> Rate:
    """C₀: Rate = Demand ⊘ Root.

    Raises ZeroRootError if root.scale == 0.
    Identity: root.scale == 1 → rate.value == demand.value.
    """
    if root.scale == 0.0:
        raise ZeroRootError("C0: division by zero root (R.scale == 0)")
    domain = demand.domain or root.domain
    return Rate(value=demand.value / root.scale, domain=domain)


def output_from(stream: Stream, root: Root) -> Output:
    """O = S · R (product-completion used by the invariant)."""
    return Output(value=stream.intensity * root.scale)


def invariant_holds(
    demand: Demand,
    root: Root,
    stream: Stream,
    *,
    tol: float = 1e-12,
) -> bool:
    """Check C · O == D · S (when R ≠ 0)."""
    rate = axiom_c0(demand, root)
    out = output_from(stream, root)
    left = rate.value * out.value
    right = demand.value * stream.intensity
    return abs(left - right) <= tol
