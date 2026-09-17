"""Write hopper optimizer readout. No uvicorn. No 0.0.0.0. No ledger rewrite."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping


def resolve_out_dir() -> Path:
    env = os.environ.get("HOPPER_OUT")
    if env:
        p = Path(env)
        p.mkdir(parents=True, exist_ok=True)
        return p
    docker = Path("/app/ledger")
    if docker.is_dir() or os.environ.get("PYTHONPATH") == "/app":
        docker.mkdir(parents=True, exist_ok=True)
        if docker.is_dir():
            return docker
    local = Path("ledger")
    local.mkdir(parents=True, exist_ok=True)
    return local


def write_hopper_run(payload: Mapping[str, Any], filename: str = "hopper_run.json") -> Path:
    out = resolve_out_dir() / filename
    data = dict(payload)
    data.setdefault("mcp_filled", False)
    data.setdefault("bind_0000", False)
    data.setdefault("dual_asgi", "127.0.0.1:8024")
    out.write_text(json.dumps(data, indent=2))
    return out
