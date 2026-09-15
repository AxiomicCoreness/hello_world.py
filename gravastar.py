#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ GRAVASTAR — MCP CONNECTOR URL CORRECTION

Reference: ledger Entry 515 event /connector_url_corrected (sealed historical).
This module does NOT rewrite ledger/515.yaml or ledger/516.yaml.
Does NOT write hard_envelope [9240, 9242–9246], soft_lane 9247, alignment,
or frozen deepseek-cd tip.

Base URL: http://localhost:8089
Endpoints: /oauth/token · /authorize · /introspect · /revoke · /health · /sign
"""
from __future__ import annotations

import json
import math
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI2 = PHI * PHI
PHASE_LOCK_DEG = 202.6
NORTH_STAR_HZ = 71.975
WOOD_DRAGON = 0.91

# Entry 515 — URL correction (reference only; ledger file not rewritten here)
ENTRY_515 = 515
EVENT_515 = "/connector_url_corrected"
SEAL_515 = "∀∞φ² · CONNECTOR_URL_CORRECTED · 515_SEALED"
WITNESS_515 = "514 → 515 — UNBROKEN — URL CORRECTED"

DEFAULT_BASE_URL = os.environ.get("MCP_CONNECTOR_BASE_URL", "http://localhost:8089")

ENDPOINTS: List[str] = [
    "/oauth/token",
    "/oauth/authorize",
    "/oauth/introspect",
    "/oauth/revoke",
    "/oauth/health",
    "/sign",
]


@dataclass
class MCPConnector:
    """Gravastar MCP OAuth/sign connector — corrected base URL."""

    base_url: str = DEFAULT_BASE_URL
    timeout_s: float = 5.0
    last_health: Optional[Dict[str, Any]] = field(default=None, repr=False)

    def url(self, path: str) -> str:
        base = self.base_url.rstrip("/") + "/"
        return urljoin(base, path.lstrip("/"))

    def endpoint_map(self) -> Dict[str, str]:
        return {ep: self.url(ep) for ep in ENDPOINTS}

    def health(self) -> Dict[str, Any]:
        target = self.url("/oauth/health")
        try:
            req = urllib.request.Request(target, method="GET")
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                try:
                    parsed: Any = json.loads(body)
                except json.JSONDecodeError:
                    parsed = {"raw": body[:500]}
                out = {
                    "ok": 200 <= resp.status < 300,
                    "status_code": resp.status,
                    "url": target,
                    "body": parsed,
                }
        except urllib.error.HTTPError as e:
            out = {"ok": False, "status_code": e.code, "url": target, "error": str(e)}
        except Exception as e:  # noqa: BLE001
            out = {
                "ok": False,
                "status_code": None,
                "url": target,
                "error": f"{type(e).__name__}: {e}",
                "note": "Connector host may be down; URL still canonical",
            }
        self.last_health = out
        return out

    def status(self) -> Dict[str, Any]:
        return {
            "gravastar": "mcp_connector",
            "base_url": self.base_url,
            "endpoints": self.endpoint_map(),
            "entry_ref": ENTRY_515,
            "event_ref": EVENT_515,
            "seal_ref": SEAL_515,
            "witness_ref": WITNESS_515,
            "coherence": 1.0,
            "phase_lock_deg": PHASE_LOCK_DEG,
            "north_star_hz": NORTH_STAR_HZ,
            "wood_dragon": WOOD_DRAGON,
            "phi2": PHI2,
            "ledger_515_rewrite": False,
            "hard_envelope_touched": False,
            "soft_lane_touched": False,
            "health": self.last_health,
        }


CONNECTOR = MCPConnector()


def connector_status() -> Dict[str, Any]:
    return CONNECTOR.status()


def connector_health() -> Dict[str, Any]:
    return CONNECTOR.health()


def main() -> int:
    import argparse

    p = argparse.ArgumentParser(description="Gravastar MCP connector (URL corrected)")
    p.add_argument("--health", action="store_true", help="GET /oauth/health")
    p.add_argument("--status", action="store_true", help="print connector map")
    p.add_argument("--json", action="store_true")
    p.add_argument(
        "--base-url",
        default=None,
        help="override base (default http://localhost:8089)",
    )
    args = p.parse_args()

    if args.base_url:
        CONNECTOR.base_url = args.base_url.rstrip("/")

    if args.health:
        out = CONNECTOR.health()
    else:
        out = CONNECTOR.status()
        if args.health is False and not args.status:
            # default: status + optional probe
            out["health"] = CONNECTOR.health()

    if args.json:
        print(json.dumps(out, indent=2, default=str))
    else:
        print("🜁∀ GRAVASTAR MCP CONNECTOR")
        print(f"  Base: {CONNECTOR.base_url}")
        for ep, full in CONNECTOR.endpoint_map().items():
            print(f"  {ep} → {full}")
        print(f"  Entry ref: {ENTRY_515} (ledger not rewritten)")
        print(f"  Seal ref: {SEAL_515}")
        h = out.get("health") or CONNECTOR.last_health
        if h:
            print(f"  Health ok: {h.get('ok')} code={h.get('status_code')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
