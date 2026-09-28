"""anatomy/heartbeat.py — liveness + coherence floor.

A pulse is alive only if it beats within the cadence window and the
coherence floor (fraction of chain entries verified intact) holds.
"""

import time
from anatomy.spine import check_spine

COHERENCE_FLOOR = 0.99
CADENCE_WINDOW_RATIO = 1.25  # grace window over cadence


def coherence() -> float:
    result = check_spine()
    total = result["entries"]
    bad = len(result["problems"])
    return 1.0 if total == 0 else max(0.0, (total - bad) / total)


def is_alive(last_beat: float, cadence: float, now: float | None = None) -> bool:
    now = now if now is not None else time.time()
    return (now - last_beat) <= cadence * CADENCE_WINDOW_RATIO


def heartbeat(last_beat: float, cadence: float) -> dict:
    c = coherence()
    return {
        "alive": is_alive(last_beat, cadence),
        "coherence": round(c, 6),
        "coherence_ok": c >= COHERENCE_FLOOR,
    }


if __name__ == "__main__":
    hb = heartbeat(last_beat=time.time(), cadence=6 * 3600)
    print(f"heartbeat: alive={hb['alive']} coherence={hb['coherence']} ok={hb['coherence_ok']}")
