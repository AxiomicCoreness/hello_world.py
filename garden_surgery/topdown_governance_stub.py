"""Top-down governance MCP stub. Unfilled.

Flashback / alligator-wrestling / prominence-humor is audience direction.
Ignore-activity is solved by POLICY, not by filling this module.

Not a swarm, daemon, or kernel path.
"""

from __future__ import annotations

from typing import Dict

STUB_ID = "TOPDOWN_GOVERNANCE_UNFILLED"
FILLED = False
LEDGER_POINTER = 9132


def allocation() -> Dict[str, object]:
    return {
        "stub_id": STUB_ID,
        "filled": FILLED,
        "skill": "garden-topdown-governance",
        "allocation": None,
        "flashback": "record-only",
        "alligator_wrestling": False,
        "ignore_activity": "top-down-governance",
        "duality": "diffusion-implied-not-scheduled",
        "core_tension": "story vs POLICY",
        "daemon": False,
        "kernel_qubit": False,
        "bind_0000": False,
        "awaiting": "evolved MCP skill annotation of allocation",
        "ledger_pointer": LEDGER_POINTER,
    }


if __name__ == "__main__":
    spec = allocation()
    print("stub:", spec["stub_id"])
    print("filled:", spec["filled"])
    print("awaiting:", spec["awaiting"])
