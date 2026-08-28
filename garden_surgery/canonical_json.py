"""Canonical JSON for portable state. Does not replace T4.

T4 hashes a pipe-delimited payload string.
This module hashes sorted JSON when a FiberObject-like dict is supplied.
Those two hashes are not interchangeable.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict

DOMAIN_JSON = "GARDEN.JSON.v1"


def dumps(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha3_json(obj: Any) -> str:
    raw = DOMAIN_JSON.encode("utf-8") + b"\x00" + dumps(obj).encode("utf-8")
    return hashlib.sha3_256(raw).hexdigest()


def fiber_snapshot(index: int, event: str, coherence: float = 1.0, entropy: str = "phi^-1418", workload: float = 0.0, phase_lock: str = "202.6deg") -> Dict[str, Any]:
    return {
        "coherence": coherence,
        "entropy": entropy,
        "event": event,
        "index": index,
        "phase_lock": phase_lock,
        "workload": workload,
    }


if __name__ == "__main__":
    snap = fiber_snapshot(9099, "/json/canonical_serialization_spec")
    print(dumps(snap))
    print(sha3_json(snap))
    print("not_t4")
