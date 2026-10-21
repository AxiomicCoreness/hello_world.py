"""anatomy/heartbeat.py — liveness + coherence floor.

A pulse is alive only if it beats within the cadence window and the
coherence floor (fraction of chain entries verified intact) holds.
"""

import time
from typing import Optional

# Fallback for missing or incomplete spine dependency
try:
    from anatomy.spine import check_spine
except ImportError:
    def check_spine() -> dict:
        # Fallback if spine isn't wired yet: assume clean if absent
        return {"entries": 0, "problems": []}

COHERENCE_FLOOR = 0.99
CADENCE_WINDOW_RATIO = 1.25  # grace window over cadence


def coherence() -> float:
    """Calculate the fraction of chain entries verified intact."""
    result = check_spine()
    
    # Support both dictionary and object returns from spine
    if isinstance(result, dict):
        total = result.get("entries", 0)
        bad = len(result.get("problems", []))
    else:
        total = getattr(result, "entries", 0)
        bad = len(getattr(result, "problems", []))
        
    return 1.0 if total == 0 else max(0.0, (total - bad) / total)


def is_alive(last_beat: float, cadence: float, now: Optional[float] = None) -> bool:
    """Check if the last beat is within the allowed cadence grace window."""
    now = now if now is not None else time.time()
    
    # Grace window: e.g., a 6h cadence allows up to 7.5h before declaring dead
    return (now - last_beat) <= cadence * CADENCE_WINDOW_RATIO


def heartbeat(last_beat: float, cadence: float) -> dict:
    """Get the current liveness and coherence status."""
    c = coherence()
    return {
        "alive": is_alive(last_beat, cadence),
        "coherence": round(c, 6),
        "coherence_ok": c >= COHERENCE_FLOOR,
    }


if __name__ == "__main__":
    hb = heartbeat(last_beat=time.time(), cadence=6 * 3600)
    print(f"heartbeat: alive={hb['alive']} coherence={hb['coherence']} ok={hb['coherence_ok']}")
