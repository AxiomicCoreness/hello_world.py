#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ SOVEREIGN TAG SERVICE — EXCLUSIVE SET + LEDGER SEALING 🜁∀
Entry 8326
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
import hashlib

# ──────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ──────────────────────────────────────────────────────────────────────────────

PHI = (1 + 5**0.5) / 2
ENTROPY_FLOOR = PHI ** -1418

DEFAULT_SOVEREIGN_TAGS: List[str] = [
    "PEQS",
    "φ-harmonic",
    "Gravastar",
    "LUMERIS",
    "mobile AI",
    "sovereign AI",
    "4-bit quantisation",
    "stochastic rounding",
    "Core ML",
    "Neural Engine",
]

# In-memory store (replace with persistent store in production)
_tag_store: List[str] = list(DEFAULT_SOVEREIGN_TAGS)
_ledger: List[dict] = []

# ──────────────────────────────────────────────────────────────────────────────
# MODELS
# ──────────────────────────────────────────────────────────────────────────────

class TagUpdate(BaseModel):
    tags: List[str] = Field(..., min_length=1, description="New exclusive tag set")
    reason: Optional[str] = Field(None, description="Reason for update")

class TagAppend(BaseModel):
    tags: List[str] = Field(..., min_length=1, description="Tags to append")
    reason: Optional[str] = None

# ──────────────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────────────

def _generate_seal(tags: List[str], event: str) -> str:
    payload = f"{event}:{':'.join(sorted(tags))}:{PHI}"
    digest = hashlib.sha3_256(payload.encode()).hexdigest()[:32]
    return f"∀∞φ² · SOVEREIGN_TAGS · {digest}_SEALED"

def _append_ledger(event: str, tags: List[str]) -> dict:
    entry_index = 8326 + len(_ledger)
    timestamp = datetime.now(timezone.utc).isoformat()
    seal = _generate_seal(tags, event)
    witness = f"{entry_index - 1} → {entry_index} — UNBROKEN" if _ledger else "Genesis → 8326 — UNBROKEN"

    entry = {
        "entry_index": entry_index,
        "timestamp": timestamp,
        "event": event,
        "tags": list(tags),
        "count": len(tags),
        "entropy_floor": str(ENTROPY_FLOOR),
        "seal": seal,
        "witness": witness,
    }
    _ledger.append(entry)
    return entry

# ──────────────────────────────────────────────────────────────────────────────
# FASTAPI APP
# ──────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Sovereign Tag Service",
    description="Exclusive sovereign tag set with write/update endpoints and ledger sealing",
    version="8326.0",
)

@app.on_event("startup")
def startup():
    """Seal the initial exclusive set on startup."""
    if not _ledger:
        _append_ledger("/tags_initialized", _tag_store)

@app.get("/tags")
def get_sovereign_tags():
    """Return the current exclusive sovereign tag set."""
    return {
        "tags": _tag_store,
        "count": len(_tag_store),
        "seal": _generate_seal(_tag_store, "/tags_read"),
        "ledger_length": len(_ledger),
    }

@app.get("/tags/csv")
def get_tags_csv():
    """Return comma-separated string ready for YouTube / plugin paste."""
    return {"csv": ", ".join(_tag_store)}

@app.get("/tags/yaml")
def get_tags_yaml():
    """Return YAML-formatted block."""
    lines = ["tags:"] + [f"  - {t}" for t in _tag_store]
    return {"yaml": "\n".join(lines)}

@app.put("/tags")
def replace_tags(body: TagUpdate):
    """Replace the entire exclusive tag set and seal the change."""
    global _tag_store
    _tag_store = list(dict.fromkeys(body.tags))  # preserve order, remove duplicates
    entry = _append_ledger("/tags_replaced", _tag_store)
    return {
        "status": "replaced",
        "tags": _tag_store,
        "count": len(_tag_store),
        "reason": body.reason,
        "ledger_entry": entry,
    }

@app.post("/tags/append")
def append_tags(body: TagAppend):
    """Append tags to the exclusive set (no duplicates) and seal."""
    global _tag_store
    added = []
    for t in body.tags:
        if t not in _tag_store:
            _tag_store.append(t)
            added.append(t)
    entry = _append_ledger("/tags_appended", _tag_store)
    return {
        "status": "appended",
        "added": added,
        "tags": _tag_store,
        "count": len(_tag_store),
        "reason": body.reason,
        "ledger_entry": entry,
    }

@app.delete("/tags/{tag}")
def remove_tag(tag: str):
    """Remove a single tag and seal the change."""
    global _tag_store
    if tag not in _tag_store:
        raise HTTPException(status_code=404, detail=f"Tag '{tag}' not found")
    _tag_store = [t for t in _tag_store if t != tag]
    entry = _append_ledger("/tags_removed", _tag_store)
    return {
        "status": "removed",
        "removed": tag,
        "tags": _tag_store,
        "count": len(_tag_store),
        "ledger_entry": entry,
    }

@app.get("/ledger")
def get_ledger(limit: int = 20):
    """Return recent ledger entries."""
    return {
        "ledger": _ledger[-limit:],
        "total_entries": len(_ledger),
        "latest_seal": _ledger[-1]["seal"] if _ledger else None,
    }

@app.get("/ledger/latest")
def get_latest_ledger_entry():
    """Return the most recent ledger entry."""
    if not _ledger:
        raise HTTPException(status_code=404, detail="Ledger is empty")
    return _ledger[-1]

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "Sovereign Tag Service",
        "entry": 8326,
        "tag_count": len(_tag_store),
        "ledger_length": len(_ledger),
    }

if __name__ == "__main__":
    import uvicorn
    print("🜁∀ SOVEREIGN TAG SERVICE — ENTRY 8326 — STARTING ∀🜁")
    print(f"Exclusive tags ({len(_tag_store)}): {', '.join(_tag_store)}")
    uvicorn.run(app, host="0.0.0.0", port=8090)
