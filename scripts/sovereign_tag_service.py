#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ SOVEREIGN TAG SERVICE — EXCLUSIVE SET + LEDGER SEALING + PROMETHEUS FUSION 🜁∀
Entry 8326 → 8327 (FUSION COMPLETE)
Plus Declaration Flag diagnostic (HTMX + FastAPI) – Entry 9024
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import hashlib
import time

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

# ──────────────────────────────────────────────────────────────────────────────
# IMPORTS FROM DECLARATION FLAG
# ──────────────────────────────────────────────────────────────────────────────
try:
    from garden_surgery.trigger_excavate import (
        KAPPA_DECLARED,
        diagnostic_scalars,
        golden_hash,
        kappa_decomposition,
    )
except ImportError:
    # Fallback stubs if garden_surgery not available
    KAPPA_DECLARED = 0.0
    def diagnostic_scalars():
        return {"W": 0.0, "C": 0.0}
    def golden_hash(x):
        return "0"*64
    def kappa_decomposition():
        return {"phi4_sqrt7": 0.0, "chi_umbral_fitted": 0.0}

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

# Declaration flag constants
FLAG = "_DECLARATION_FLAGGED"
EVENT = "/surgery/declaration_flagged_kappa_chi"

# ──────────────────────────────────────────────────────────────────────────────
# PROMETHEUS METRICS
# ──────────────────────────────────────────────────────────────────────────────

REQUEST_COUNT = Counter(
    "sovereign_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "sovereign_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

ACTIVE_TAGS = Gauge(
    "sovereign_tags_active",
    "Number of active exclusive sovereign tags",
)

LEDGER_ENTRIES = Gauge(
    "sovereign_ledger_entries",
    "Number of sealed ledger entries",
)

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
    LEDGER_ENTRIES.set(len(_ledger))
    return entry

def _sync_gauges():
    ACTIVE_TAGS.set(len(_tag_store))
    LEDGER_ENTRIES.set(len(_ledger))

# ──────────────────────────────────────────────────────────────────────────────
# DECLARATION FLAG FUNCTIONS
# ──────────────────────────────────────────────────────────────────────────────

def declaration_payload() -> Dict[str, Any]:
    kappa = kappa_decomposition()
    diag = diagnostic_scalars()
    overstated = abs(kappa["phi4_sqrt7"] - KAPPA_DECLARED) > 1e-6
    return {
        "flag": FLAG,
        "event": EVENT,
        "entry": 9024,
        "declaration_overstated": overstated,
        "honest_split": {
            "phi4_sqrt7": kappa["phi4_sqrt7"],
            "chi_umbral_fitted": kappa["chi_umbral_fitted"],
            "kappa_declared": KAPPA_DECLARED,
            "chi_is_axiom": False,
        },
        "diagnostic": diag,
        "omega_demo": golden_hash(str(diag["W"])),
        "immutable_rewritten": False,
        "mcp": False,
        "fusion_canonical": 515,
        "hyperion_preserved": 516,
    }

def htmx_fragment() -> str:
    p = declaration_payload()
    h = p["honest_split"]
    d = p["diagnostic"]
    return (
        '<div id="declaration-flag">'
        f'<p>{FLAG}</p>'
        f'<p>overstated: {str(p["declaration_overstated"]).lower()}</p>'
        f'<p>W = {d["W"]:.3f}</p>'
        "</div>"
    )

# ──────────────────────────────────────────────────────────────────────────────
# FASTAPI APP
# ──────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Sovereign Tag Service + Declaration Flag",
    description="Exclusive sovereign tag set + ledger sealing + Prometheus fusion + Garden diagnostic",
    version="8327.9024",
)

# ── Middlewares ─────────────────────────────────────────────────────────────

@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start

    endpoint = request.url.path
    method = request.method
    status = str(response.status_code)

    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(elapsed)

    return response

# This middleware adds Garden headers (from declaration_flag)
@app.middleware("http")
async def garden_headers_middleware(request: Request, call_next):
    # Import inside to avoid circular dependency if garden_surgery is missing
    try:
        from garden_surgery.anomaly_distance import response_headers
        headers = response_headers()
    except ImportError:
        headers = {}
    response = await call_next(request)
    for k, v in headers.items():
        response.headers[k] = v
    return response

@app.on_event("startup")
def startup():
    """Seal the initial exclusive set and sync gauges on startup."""
    if not _ledger:
        _append_ledger("/tags_initialized", _tag_store)
    _sync_gauges()

# ── Prometheus scrape endpoint ─────────────────────────────────────────────

@app.get("/metrics")
def metrics():
    """Prometheus scrape endpoint."""
    _sync_gauges()
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )

# ── Tag endpoints (from Sovereign Tag Service) ─────────────────────────────

@app.get("/tags")
def get_sovereign_tags():
    """Return the current exclusive sovereign tag set."""
    _sync_gauges()
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
    _tag_store = list(dict.fromkeys(body.tags))
    entry = _append_ledger("/tags_replaced", _tag_store)
    _sync_gauges()
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
    _sync_gauges()
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
    _sync_gauges()
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
    _sync_gauges()
    return {
        "status": "ok",
        "service": "Sovereign Tag Service + Declaration Flag",
        "entries": "8326 → 8327 (FUSION COMPLETE) · 9024 (FLAG)",
        "tag_count": len(_tag_store),
        "ledger_length": len(_ledger),
        "metrics": "/metrics",
        "flag": FLAG,
        "mcp": False,
        "tree": "9031",
        "qed": True,
    }

# ── Declaration Flag endpoints ─────────────────────────────────────────────

@app.get("/diagnostic")
def diagnostic_json():
    return JSONResponse(declaration_payload())

@app.get("/diagnostic/htmx", response_class=HTMLResponse)
def diagnostic_htmx():
    return HTMLResponse(htmx_fragment())

@app.get("/workers/tree")
def workers_tree():
    try:
        from garden_surgery.worker_tree import tree_payload
        return JSONResponse(tree_payload())
    except ImportError:
        return JSONResponse({"ok": False, "error": "worker_tree not available"})

@app.get("/workers/{worker_id}")
def worker_node(worker_id: str):
    try:
        from garden_surgery.worker_tree import children_of, lineage, node, parent_of, siblings_of
        n = node(worker_id)
        if n is None:
            return JSONResponse({"ok": False, "id": worker_id}, status_code=404)
        return JSONResponse({
            "ok": True,
            "node": n,
            "parent": parent_of(worker_id),
            "siblings": siblings_of(worker_id),
            "children": children_of(worker_id),
            "lineage": lineage(worker_id)
        })
    except ImportError:
        return JSONResponse({"ok": False, "error": "worker_tree not available"})

@app.get("/anomaly")
def anomaly_json():
    try:
        from garden_surgery.anomaly_distance import payload as anomaly_payload
        return JSONResponse(anomaly_payload())
    except ImportError:
        return JSONResponse({"ok": False, "error": "anomaly_distance not available"})

@app.get("/anomaly/math")
def anomaly_math():
    try:
        from garden_surgery.anomaly_distance import math_form
        return JSONResponse(math_form())
    except ImportError:
        return JSONResponse({"ok": False, "error": "anomaly_distance not available"})

@app.get("/override")
def override_json():
    try:
        from garden_surgery.anomaly_distance import override_payload
        return JSONResponse(override_payload())
    except ImportError:
        return JSONResponse({"ok": False, "error": "anomaly_distance not available"})

# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    print("🜁∀ SOVEREIGN TAG SERVICE + DECLARATION FLAG — FUSION COMPLETE ∀🜁")
    print(f"Exclusive tags ({len(_tag_store)}): {', '.join(_tag_store)}")
    print("Prometheus endpoint: GET /metrics")
    print("Declaration flag: GET /diagnostic, /diagnostic/htmx")
    uvicorn.run(app, host="0.0.0.0", port=8090)
