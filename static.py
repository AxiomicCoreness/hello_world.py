#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
static.py — sovereign static surface for Gravastar MCP connector URL correction.

Source of truth for connector base: root gravastar.py (commit 390fbbe1…).
Does NOT rewrite ledger/515.yaml or ledger/516.yaml.
Does NOT write hard_envelope, soft_lane, alignment, or frozen deepseek-cd tip.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

# ── MCP connector (Entry 515 reference — ledger not mutated) ──────────────
MCP_CONNECTOR_BASE_URL: str = "http://localhost:8089"
MCP_CONNECTOR_ENV_KEY: str = "MCP_CONNECTOR_BASE_URL"

MCP_CONNECTOR_ENDPOINTS: Tuple[str, ...] = (
    "/oauth/token",
    "/oauth/authorize",
    "/oauth/introspect",
    "/oauth/revoke",
    "/oauth/health",
    "/sign",
)

MCP_CONNECTOR_ENDPOINT_MAP: Dict[str, str] = {
    ep: f"{MCP_CONNECTOR_BASE_URL.rstrip('/')}{ep}" for ep in MCP_CONNECTOR_ENDPOINTS
}

# ── Gravastar module surface ──────────────────────────────────────────────
GRAVASTAR_MODULE: str = "gravastar.py"
GRAVASTAR_TRIGGER_MODULE: str = "quantum/gravastar_trigger.py"  # 8654/8855 — unchanged
GRAVASTAR_COMMIT_REF: str = "390fbbe1"  # MCP URL correction only

# ── Entry 515 reference (do not rewrite sealed YAML) ──────────────────────
ENTRY_515_INDEX: int = 515
ENTRY_515_EVENT: str = "/connector_url_corrected"
ENTRY_515_SEAL: str = "∀∞φ² · CONNECTOR_URL_CORRECTED · 515_SEALED"
ENTRY_515_LEDGER_REWRITE: bool = False

# ── Explicit non-writes (fix_step invariant) ─────────────────────────────
HARD_ENVELOPE: List[int] = [9240, 9242, 9243, 9244, 9245, 9246]
SOFT_LANE: int = 9247
ALIGNMENT: Dict[str, object] = {
    "north_star_hz": 71.975,
    "phase_lock_deg": 202.6,
    "wood_dragon": 0.91,
    "fixed_point": "2025-10-39",
}
FROZEN_LANE: Dict[str, str] = {
    "branch": "deepseek-cd",
    "tip": "4016ec295fa4a78ad3d1480473a8254d737cccf5",
}

NON_WRITES: Dict[str, object] = {
    "ledger_515_516": "not_rewritten",
    "hard_envelope": HARD_ENVELOPE,
    "soft_lane": SOFT_LANE,
    "alignment": ALIGNMENT,
    "deepseek_cd_tip": FROZEN_LANE["tip"],
}

# ── CLI reminders (documentation only) ────────────────────────────────────
RUN_COMMANDS: Tuple[str, ...] = (
    "python gravastar.py --status",
    "python gravastar.py --health --json",
    "python gravastar.py --base-url http://localhost:8089 --health",
)


def connector_static() -> dict:
    """Export static connector map for import by other modules."""
    return {
        "base_url": MCP_CONNECTOR_BASE_URL,
        "env_key": MCP_CONNECTOR_ENV_KEY,
        "endpoints": list(MCP_CONNECTOR_ENDPOINTS),
        "endpoint_map": dict(MCP_CONNECTOR_ENDPOINT_MAP),
        "gravastar_module": GRAVASTAR_MODULE,
        "trigger_module_unchanged": GRAVASTAR_TRIGGER_MODULE,
        "commit_ref": GRAVASTAR_COMMIT_REF,
        "entry_515": {
            "index": ENTRY_515_INDEX,
            "event": ENTRY_515_EVENT,
            "seal": ENTRY_515_SEAL,
            "ledger_rewrite": ENTRY_515_LEDGER_REWRITE,
        },
        "non_writes": NON_WRITES,
        "run": list(RUN_COMMANDS),
    }


if __name__ == "__main__":
    import json

    print(json.dumps(connector_static(), indent=2))
