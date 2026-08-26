#!/usr/bin/env python3
"""Environment configuration for quantum/deepseek_mesh/terminal.py.

Reads process env (and optional .env). Never prints secret values.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict


def _load_dotenv() -> None:
    root = Path(__file__).resolve().parents[2]
    path = root / ".env"
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = val


def configure() -> Dict[str, Any]:
    _load_dotenv()
    host = os.getenv("PORT380_HOST", os.getenv("MESH_HOST", "127.0.0.1"))
    port = int(os.getenv("PORT380_PORT", os.getenv("MESH_PORT", "380")))
    mcp = os.getenv("MCP_CONNECTOR_URL", os.getenv("MCP_URL", f"http://{host}:{port}"))
    base_dir = os.getenv(
        "HYPERIAN_BASE_DIR",
        str(Path.home() / "Documents" / "Hyperian_Node"),
    )
    Path(base_dir).mkdir(parents=True, exist_ok=True)
    present = {
        "GARDEN_SECRET": bool(os.getenv("GARDEN_SECRET")),
        "DEEPSEEK_API_KEY": bool(os.getenv("DEEPSEEK_API_KEY")),
        "MCP_CONNECTOR_URL": bool(os.getenv("MCP_CONNECTOR_URL") or os.getenv("MCP_URL")),
    }
    os.environ.setdefault("HYPERIAN_BASE_DIR", base_dir)
    os.environ.setdefault("MCP_CONNECTOR_URL", mcp)
    return {
        "host": host,
        "port": port,
        "mcp_connector_url": mcp,
        "base_dir": base_dir,
        "oauth_offline": os.getenv("OAUTH_OFFLINE", "0"),
        "ci_mode": os.getenv("TERMINAL_CI", os.getenv("CI", "0")),
        "secrets_present": present,
    }
