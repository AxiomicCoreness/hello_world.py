"""Consumer Axiom: strict form.

C₀: ∃! C ∈ ℝ⁺ ∣ C ≡ D ⊘ R

Where:
  C = Consumption (satisfied residual, non-negative)
  D = Demand (required amount)
  R = Root / supply (available amount)
  ⊘ = saturating subtraction: max(D - R, 0)

R = 0 → C = D (feature).
This is a clamp operation, not a field operation.
No division, no ZeroRootError, no field identities.
"""

from __future__ import annotations

from dataclasses import dataclass

AXIOM_TEXT = "Consumption stems from saturating demand over root"
VALENCE = "SATURATING_POSITIVE_PROVEN"
IDENTITY_DEMAND = float("inf")


@dataclass(frozen=True)
class Consumption:
    amount: float

    def __le__(self, other: "Consumption") -> bool:
        return self.amount <= other.amount


@dataclass(frozen=True)
class Demand:
    amount: float


@dataclass(frozen=True)
class Supply:
    """Available root/supply amount."""

    amount: float


@dataclass(frozen=True)
class Root:
    """Alias for supply-as-root (scale == amount)."""

    scale: float
    pattern: str = ""

    def as_supply(self) -> Supply:
        return Supply(amount=self.scale)


def axiom_c0(demand: Demand, supply: Supply | Root) -> Consumption:
    """C₀: C = max(D - R, 0). Never raises on R = 0."""
    if isinstance(supply, Root):
        r = float(supply.scale)
    else:
        r = float(supply.amount)
    d = float(demand.amount)
    raw = d - r
    if raw != raw:  # NaN guard
        return Consumption(amount=0.0)
    return Consumption(amount=max(raw, 0.0))
