#!/usr/bin/env python3
"""FastMCP stub for ledger/event_hash.py. FILLED=False. No 0.0.0.0. No port 380."""
from __future__ import annotations

import os
import sys
from pathlib import Path

FILLED = False
BIND_0000 = False
DUAL_ASGI = "127.0.0.1:8024"

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from ledger.event_hash import compute, event_hash_block, payload  # noqa: E402

try:
    from fastmcp import FastMCP
except ImportError:  # control venv has no fastmcp
    FastMCP = None


def ledger_event_hash(index: int, event: str) -> dict:
    return compute(index, event)


def preview_payload(index: int, event: str) -> str:
    return payload(index, event)


def mcp_config() -> dict:
    return {
        "name": "garden-event-hash",
        "filled": FILLED,
        "mcp_filled": False,
        "transport": "stdio",
        "bind_0000": BIND_0000,
        "dual_asgi": DUAL_ASGI,
        "port_380": False,
        "tools": ["ledger_event_hash", "preview_payload"],
        "module": "ledger/event_hash.py",
    }


if FastMCP is not None:
    mcp = FastMCP("garden-event-hash")

    @mcp.tool()
    def ledger_event_hash_tool(index: int, event: str) -> dict:
        return ledger_event_hash(index, event)

    @mcp.tool()
    def preview_payload_tool(index: int, event: str) -> str:
        return preview_payload(index, event)
else:
    mcp = None


if __name__ == "__main__":
    if os.environ.get("FASTMCP_RUN") == "1" and mcp is not None:
        mcp.run(transport="stdio")
    else:
        import json

        print(json.dumps(mcp_config(), indent=2))
        print(json.dumps(ledger_event_hash(9189, "/actualized_dual_asyncio_cicd_appended_math_origin"), indent=2))
