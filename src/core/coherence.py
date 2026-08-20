"""Coherence gate surface for production layout."""
from __future__ import annotations

from typing import Any, Dict


def coherence_state(value: float = 1.0) -> Dict[str, Any]:
    return {"coherence": float(value), "ok": float(value) >= 1.0}


def require_coherence(value: float = 1.0) -> Dict[str, Any]:
    st = coherence_state(value)
    if not st["ok"]:
        raise RuntimeError("coherence below 1.0")
    return st
