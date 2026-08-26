#!/usr/bin/env python3
"""Bounded Wood-Dragon + Mistral dispatch sidecar.

Orders agentic terminal_ci.dispatch_main() against the Wood-Dragon cadence
(0.91 / 16.35 days) for GitHub workflow_dispatch. Does not import the
232KB wood_dragon_technique.py monolith. Does not fire Gravastar.
"""
from __future__ import annotations

import json
import math
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional

PHI = (1.0 + math.sqrt(5.0)) / 2.0
WOOD_DRAGON_DAYS = 0.91
DEEP_SPACE_DAYS = 16.35
EVENT = "/workflow_dispatch_wood_dragon_mistral"
ENTRY_INDEX = 9007
PHASE_LOCK_DEG = 202.6


def phase_in_cycle(period_days: float, now: Optional[datetime] = None) -> float:
    """Fractional phase [0, 1) of UTC epoch-days in the period."""
    now = now or datetime.now(timezone.utc)
    epoch_days = now.timestamp() / 86400.0
    return (epoch_days / float(period_days)) % 1.0


def cadence_report(now: Optional[datetime] = None) -> Dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    wd = phase_in_cycle(WOOD_DRAGON_DAYS, now)
    ds = phase_in_cycle(DEEP_SPACE_DAYS, now)
    return {
        "wood_dragon_days": WOOD_DRAGON_DAYS,
        "deep_space_days": DEEP_SPACE_DAYS,
        "phase_in_cycle_wood_dragon": wd,
        "phase_in_cycle_deep_space": ds,
        "gate": WOOD_DRAGON_DAYS,
        "phase_lock_deg": PHASE_LOCK_DEG,
        "phi": PHI,
        "utc": now.isoformat(),
        "near_mistral_window": wd < 0.10 or wd > 0.90,
    }


def mistral_presence() -> Dict[str, Any]:
    """Health presence only — never prints API key values."""
    present = {
        "MISTRAL_API_KEY": bool(os.getenv("MISTRAL_API_KEY")),
        "MISTRAL_API_URL": bool(os.getenv("MISTRAL_API_URL")),
    }
    try:
        from clients.mistral import MistralSovereignClient

        client = MistralSovereignClient(layer=7, agent_id="wood_dragon_mistral_9007")
        health = client.health_check()
        return {
            "import_ok": True,
            "secrets_present": present,
            "health": {
                "status": health.get("status"),
                "agent_id": health.get("agent_id"),
                "quantum_seal_present": bool(health.get("quantum_seal")),
            },
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "import_ok": False,
            "secrets_present": present,
            "health": {"status": "absent", "error": f"{type(exc).__name__}: {exc}"},
        }


def dispatch_main(event: str = EVENT) -> Dict[str, Any]:
    """Order agentic terminal_ci.dispatch_main next to wood-dragon timing."""
    from quantum.deepseek_mesh.env import configure
    from ledger.event_hash import event_hash_block
    from quantum.deepseek_mesh.terminal_ci import dispatch_main as terminal_dispatch_main

    env = configure()
    env["secrets_present"]["MISTRAL_API_KEY"] = bool(os.getenv("MISTRAL_API_KEY"))
    cadence = cadence_report()
    mistral = mistral_presence()
    block = event_hash_block(ENTRY_INDEX, event)
    terminal = terminal_dispatch_main(event=event)
    return {
        "ok": True,
        "entry_index": ENTRY_INDEX,
        "event": event,
        "call_site": (
            "quantum.wood_dragon_dispatch.dispatch_main "
            "→ terminal_ci.dispatch_main "
            "→ adjacent to terminal.main + wood_dragon_technique cadence"
        ),
        "env": env,
        "cadence": cadence,
        "mistral": mistral,
        "event_hash": block,
        "terminal_dispatch": terminal,
        "skipped_monolith": True,
        "skipped_gravastar": True,
        "ci": bool(os.getenv("CI") or os.getenv("TERMINAL_CI") or os.getenv("WOOD_DRAGON_CI")),
    }


def main() -> int:
    report = dispatch_main()
    print(json.dumps(report, indent=2, default=str))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
