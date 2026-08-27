"""Environment awareness — presence only. Never echo secret values."""

from __future__ import annotations

import os
from dataclasses import dataclass, asdict, field
from typing import Dict, List

# Names only. Values are never copied into reports.
ONLINE_KEYS = (
    "DEEPSEEK_API_KEY",
    "MCP_URL",
    "GARDEN_SECRET",
    "MCP_CONNECTOR_URL",
)
OPTIONAL_KEYS = (
    "DEEPSEEK_BASE_URL",
    "DEEPSEEK_MODEL",
    "PORT380_HOST",
    "PORT380_PORT",
)

# Offline CI must be able to pass without any ONLINE_KEYS set.
OFFLINE_OK_WITHOUT = ONLINE_KEYS


@dataclass
class EnvReport:
    present: Dict[str, bool]
    offline_viable: bool
    notes: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict:
        d = asdict(self)
        d["ok"] = True  # presence probe never hard-fails; surfaces do
        return d


def _present(name: str) -> bool:
    val = os.environ.get(name)
    return bool(val) and val.strip() not in {"", "your_secret_here", "your_key"}


def probe_environment() -> EnvReport:
    present = {k: _present(k) for k in (*ONLINE_KEYS, *OPTIONAL_KEYS)}
    notes = []
    if not present["DEEPSEEK_API_KEY"]:
        notes.append("offline DeepSeek mode expected")
    if not present["GARDEN_SECRET"]:
        notes.append("Port 380 /pulse auth will soft-warn")
    if not present["MCP_URL"] and not present["MCP_CONNECTOR_URL"]:
        notes.append("MCP pulse URL unset — gate tests must skip live HTTP")
    offline_viable = True  # by contract: missing keys do not block offline
    return EnvReport(present=present, offline_viable=offline_viable, notes=notes)
