"""
fiduciary_node_rewards.py

Reward distribution across N_NODES agents using tier-quantized
golden-ratio decay. The golden ratio is a design convention,
not a physical constant.

Fixes relative to the previous version:
  - rank is the TIER index, not the node id
  - total_pool() is computed, not asserted against a hard-coded number
  - verify_reward_pool() returns (ok, computed) and only compares to an
    expectation you actually supply

Note on constants:
  Q_INVARIANT * PHI ** -3 == 1/4 exactly.  (2+sqrt(5))/4 * (sqrt(5)-2) = 1/4.
  Do not "simplify" Q_INVARIANT; the tier-3 contribution depends on it.
"""

from __future__ import annotations

import math

PHI = (1.0 + math.sqrt(5.0)) / 2.0
Q_INVARIANT = (2.0 + math.sqrt(5.0)) / 4.0   # ~1.0590169943749475

N_NODES = 144_008

# (upper bound inclusive, tier index). Tier 1 is the highest weight.
TIERS: tuple[tuple[int, int], ...] = (
    (7, 1),
    (49, 2),
    (343, 3),
    (2401, 4),
    (16807, 5),
    (117649, 6),
    (144008, 7),
)


def tier_of(node_id: int) -> int:
    if node_id < 1 or node_id > N_NODES:
        raise ValueError(f"node_id out of range: {node_id}")
    for upper, tier in TIERS:
        if node_id <= upper:
            return tier
    raise AssertionError("unreachable")


def nodes_in_tier(tier: int) -> int:
    upper = next(u for u, t in TIERS if t == tier)
    lower = next((u for u, t in TIERS if t == tier - 1), 0)
    return upper - lower


def calculate_node_reward(node_id: int, q: float = Q_INVARIANT, c: float = 1.0) -> float:
    """R_n = q * phi^{-tier(node_id)} * c_n"""
    return q * PHI ** (-tier_of(node_id)) * c


def total_pool(q: float = Q_INVARIANT) -> float:
    """Sum of all node rewards. Computed, not declared."""
    return sum(
        nodes_in_tier(t) * q * PHI ** (-t)
        for _, t in TIERS
    )


def verify_reward_pool(expected: float | None = None,
                       tol: float = 1e-6) -> tuple[bool, float]:
    """
    Returns (ok, computed_total).

    If `expected` is None, ok is always True and you get the computed total
    for inspection. If `expected` is provided, ok reports whether the
    computed total matches within tol.
    """
    computed = total_pool()
    if expected is None:
        return (True, computed)
    return (abs(computed - expected) <= tol, computed)


if __name__ == "__main__":
    ok, total = verify_reward_pool()
    print(f"total_pool = {total:.10f}   (ok={ok})")
    for _, t in TIERS:
        n = nodes_in_tier(t)
        w = PHI ** (-t)
        print(f"  tier {t}: {n:>7} nodes  phi^-{t} = {w:.10f}  "
              f"tier total = {n * Q_INVARIANT * w:.4f}")
