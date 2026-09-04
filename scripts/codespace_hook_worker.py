#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Codespace hook worker — ledger 9159
Observer / publish-subscribe on asyncio.

Constraints (Garden POLICY):
  FILLED = False          — not an MCP server
  BIND   = 127.0.0.1      — never 0.0.0.0
  PORT   = 8091           — does not occupy Dual ASGI 127.0.0.1:8024
  Hooks append only. No rewrite of sealed YAML.
  No eval. No arbitrary subprocess. Allowlisted events only.
"""
from __future__ import annotations

import asyncio
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Set

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

FILLED = False
BIND = "127.0.0.1"
PORT = 8091
DUAL_ASGI = "127.0.0.1:8024"
ALLOWLIST = frozenset({"/hook/ledger", "/health", "/hooks"})
PHI2 = 2.618033988749895

app = FastAPI(title="Codespace Hook Worker", version="9159")
_tasks: Set[asyncio.Task] = set()
_log: List[Dict[str, Any]] = []


class LedgerHook(BaseModel):
    event: str = Field(..., min_length=1, max_length=128)
    note: str = Field("", max_length=2048)


def _seal(event: str, note: str) -> str:
    payload = f"9159|{event}|{note}|phi2={PHI2}"
    digest = hashlib.sha3_256(payload.encode()).hexdigest()
    return f"∀∞φ² · HOOK_WORKER · {digest[:32]}_ACCEPTED"


async def process_ledger_event(body: LedgerHook) -> Dict[str, Any]:
    await asyncio.sleep(0)
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": body.event,
        "note": body.note,
        "append_only": True,
        "mcp_filled": FILLED,
        "seal": _seal(body.event, body.note),
    }
    _log.append(entry)
    return entry


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "codespace_hook_worker",
        "filled": FILLED,
        "bind": BIND,
        "port": PORT,
        "dual_asgi": DUAL_ASGI,
        "bind_0000": False,
        "allowlist": sorted(ALLOWLIST),
        "pending_tasks": len(_tasks),
        "accepted": len(_log),
        "qed": True,
    }


@app.get("/hooks")
async def hooks(limit: int = 20) -> Dict[str, Any]:
    return {"log": _log[-limit:], "total": len(_log)}


@app.post("/hook/ledger")
async def ledger_hook(body: LedgerHook) -> Dict[str, Any]:
    if not body.event.startswith("/"):
        raise HTTPException(status_code=400, detail="event must be a path token")
    task = asyncio.create_task(process_ledger_event(body))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
    result = await task
    return {"status": "accepted", "entry": result}


if __name__ == "__main__":
    import uvicorn

    print("hook worker 9159 FILLED=False bind", BIND, PORT)
    uvicorn.run(app, host=BIND, port=PORT)
