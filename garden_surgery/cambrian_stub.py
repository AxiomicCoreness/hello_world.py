"""Distinctive stub. Unfilled. Not a swarm, daemon, or kernel path.

Fill only when an evolved MCP skill annotates allocation.
Until then every field stays empty-of-runtime.
"""

from __future__ import annotations

from typing import Dict

STUB_ID = "CAMBRIAN_ALLOCATION_UNFILLED"
FILLED = False


def allocation() -> Dict[str, object]:
    return {
        "stub_id": STUB_ID,
        "filled": FILLED,
        "skill": None,
        "allocation": None,
        "weight_rewriter": False,
        "daemon": False,
        "kernel_qubit": False,
        "attenuation_override": False,
        "awaiting": "evolved MCP skill annotation",
    }


if __name__ == "__main__":
    spec = allocation()
    print("stub:", spec["stub_id"])
    print("filled:", spec["filled"])
    print("awaiting:", spec["awaiting"])
