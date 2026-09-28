"""anatomy/breath.py — cadence, 6h default, jitter bound.

Cadence governor for scheduled pulses. Default period 6h.
Jitter is bounded so the schedule stays auditable.
"""

import random

DEFAULT_CADENCE_SECONDS = 6 * 3600  # 6h
JITTER_BOUND_RATIO = 0.05          # ±5% max


def next_interval(base: int = DEFAULT_CADENCE_SECONDS, jitter_ratio: float = JITTER_BOUND_RATIO) -> int:
    """Bounded-jitter interval around the cadence. Deterministic bounds, never exceeding the ratio."""
    if not 0 <= jitter_ratio <= 1:
        raise ValueError("jitter_ratio out of bounds")
    span = int(base * jitter_ratio)
    return base + random.randint(-span, span)


def cron_for(base: int = DEFAULT_CADENCE_SECONDS) -> str:
    """Canonical cron for the base cadence (6h default -> '0 */6 * * *')."""
    hours = base // 3600
    if base % 3600 or not 1 <= hours <= 23:
        raise ValueError("cadence must be whole hours, 1-23")
    return f"0 */{hours} * * *"


if __name__ == "__main__":
    print(f"breath: cadence {DEFAULT_CADENCE_SECONDS}s, cron '{cron_for()}', jitter ±{int(JITTER_BOUND_RATIO*100)}%")
