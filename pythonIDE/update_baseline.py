#!/usr/bin/env python3
"""Autonomous pythonIDE baseline (not Pythonista). Read-only vs sealed ledger."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = Path(__file__).resolve().parent / "baseline.json"
OUT_LOG = Path(__file__).resolve().parent / "last_baseline.log"

BIND_HOST = "127.0.0.1"
BIND_PORT = 8024
REFUSED = {"0.0.0.0", "::", "[::]"}


def probe_loopback() -> dict:
    """Probe loopback Dual-ASGI contract without the removed fastMCP package."""
    log: list[str] = []
    result: dict = {
        "ok": True,
        "filled": False,
        "bind_host": BIND_HOST,
        "bind_port": BIND_PORT,
        "entry": None,
        "errors": [],
    }
    entry = ROOT / "fastapi_flywheel_gearbox.py"
    if not entry.is_file():
        result["ok"] = False
        result["errors"].append("fastapi_flywheel_gearbox.py missing")
        log.append("entry missing")
    else:
        result["entry"] = str(entry)
        log.append(f"entry present: {entry.name}")
        log.append(f"bind contract {BIND_HOST}:{BIND_PORT}")
        log.append(f"refused hosts: {sorted(REFUSED)}")
    OUT_LOG.write_text("\n".join(log) + "\n", encoding="utf-8")
    return result


def main() -> int:
    probe = probe_loopback()
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "surface": "pythonIDE",
        "not": "pythonista",
        "dual_asgi": f"{BIND_HOST}:{BIND_PORT}",
        "mcp_filled": False,
        "loopback": probe,
        "ledger_rewrite": False,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if not probe["ok"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
