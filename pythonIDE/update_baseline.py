#!/usr/bin/env python3
"""Autonomous pythonIDE baseline (not Pythonista). Read-only vs sealed ledger."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = Path(__file__).resolve().parent / "baseline.json"
OUT_LOG = Path(__file__).resolve().parent / "last_fastmcp.log"

BIND_HOST = "127.0.0.1"
BIND_PORT = 8024
REFUSED = {"0.0.0.0", "::", "[::]"}


def probe_fastmcp() -> dict:
    log: list[str] = []
    result: dict = {
        "ok": True,
        "filled": False,
        "bind_host": BIND_HOST,
        "bind_port": BIND_PORT,
        "module": None,
        "errors": [],
    }
    try:
        sys.path.insert(0, str(ROOT))
        import fastMCP  # type: ignore

        result["module"] = getattr(fastMCP, "__file__", "fastMCP")
        filled = bool(getattr(fastMCP, "FILLED", False))
        result["filled"] = filled
        log.append(f"import fastMCP FILLED={filled}")
        if filled:
            result["ok"] = False
            result["errors"].append("MCP FILLED must stay False")
        try:
            from fastMCP.bind import BIND_HOST as H, BIND_PORT as P, REFUSED_HOSTS

            result["bind_host"] = H
            result["bind_port"] = int(P)
            log.append(f"bind {H}:{P} refused={sorted(REFUSED_HOSTS)}")
            if H in REFUSED or H == "0.0.0.0":
                result["ok"] = False
                result["errors"].append("wildcard bind refused")
            if int(P) != BIND_PORT:
                result["ok"] = False
                result["errors"].append("port must be 8024")
        except Exception as exc:
            log.append(f"bind submodule: {exc}")
    except Exception as exc:
        result["ok"] = False
        result["errors"].append(f"fastMCP import: {exc}")
        log.append(str(exc))
    OUT_LOG.write_text("\n".join(log) + "\n", encoding="utf-8")
    return result


def main() -> int:
    probe = probe_fastmcp()
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "surface": "pythonIDE",
        "not": "pythonista",
        "dual_asgi": f"{BIND_HOST}:{BIND_PORT}",
        "mcp_filled": False,
        "fastmcp": probe,
        "ledger_rewrite": False,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if not probe["ok"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
