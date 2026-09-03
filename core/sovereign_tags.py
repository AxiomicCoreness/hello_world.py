#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ SOVEREIGN TAG SERVICE — EXCLUSIVE SET + LEDGER SEALING + PROMETHEUS FUSION 🜁∀
Entry 8326 → 8327 (FUSION COMPLETE)
"""

from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import List, Optional
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
# FASTAPI APP
# ──────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Sovereign Tag Service",
    description="Exclusive sovereign tag set + ledger sealing + Prometheus fusion",
    version="8327.0",
)

@app.get("/", response_class=HTMLResponse)
def dashboard():
        return """<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Sovereign Tag Service</title>
    <style>
        :root { color-scheme: dark; --ink: #eef4f0; --muted: #9aa9a1; --panel: #17221e; --line: #30443b; --accent: #d8f36b; --accent-ink: #14200f; --warn: #ffb86b; }
        * { box-sizing: border-box; }
        body { margin: 0; min-height: 100vh; background: radial-gradient(circle at 15% 0%, #294438 0, #101714 42%, #0b0f0d 100%); color: var(--ink); font: 16px/1.5 Georgia, "Times New Roman", serif; }
        main { width: min(1120px, calc(100% - 32px)); margin: 0 auto; padding: 48px 0 64px; }
        header { display: flex; justify-content: space-between; gap: 24px; align-items: end; border-bottom: 1px solid var(--line); padding-bottom: 28px; }
        h1 { margin: 0; font-size: clamp(2.2rem, 7vw, 5.5rem); line-height: .95; letter-spacing: 0; max-width: 680px; }
        .eyebrow { color: var(--accent); font: 700 .75rem/1.2 ui-monospace, SFMono-Regular, Menlo, monospace; letter-spacing: .08em; text-transform: uppercase; }
        .status { display: flex; align-items: center; gap: 8px; color: var(--muted); white-space: nowrap; }
        .dot { width: 10px; height: 10px; border-radius: 50%; background: var(--accent); box-shadow: 0 0 16px var(--accent); }
        .grid { display: grid; grid-template-columns: 1.3fr .7fr; gap: 18px; margin-top: 24px; }
        section { background: color-mix(in srgb, var(--panel) 88%, transparent); border: 1px solid var(--line); border-radius: 8px; padding: 24px; box-shadow: 0 16px 50px #0004; }
        h2 { margin: 0 0 18px; font-size: 1.15rem; font-weight: 400; }
        .tags { display: flex; flex-wrap: wrap; gap: 9px; min-height: 48px; }
        .tag { border: 1px solid #5b714a; border-radius: 999px; color: var(--accent); padding: 6px 11px; font: .82rem ui-monospace, SFMono-Regular, Menlo, monospace; }
        .stats { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
        .stat { border-top: 2px solid var(--accent); padding-top: 10px; }
        .value { display: block; font-size: 2rem; }
        .label { color: var(--muted); font: .72rem ui-monospace, SFMono-Regular, Menlo, monospace; text-transform: uppercase; }
        form { display: flex; gap: 8px; margin-top: 22px; }
        input { min-width: 0; flex: 1; border: 1px solid var(--line); border-radius: 4px; background: #0d1411; color: var(--ink); padding: 11px 12px; font: inherit; }
        button { border: 0; border-radius: 4px; background: var(--accent); color: var(--accent-ink); cursor: pointer; padding: 10px 15px; font: 700 .8rem ui-monospace, SFMono-Regular, Menlo, monospace; }
        button:hover { filter: brightness(1.1); }
        .ledger { display: grid; gap: 10px; max-height: 310px; overflow: auto; }
        .entry { border-left: 2px solid var(--warn); padding: 8px 0 8px 12px; }
        .entry strong { color: var(--accent); }
        .entry small { display: block; color: var(--muted); overflow-wrap: anywhere; }
        .links { display: flex; gap: 16px; margin-top: 20px; }
        a { color: var(--accent); }
        #message { color: var(--warn); min-height: 1.5em; margin: 12px 0 0; }
        @media (max-width: 720px) { main { padding-top: 28px; } header { display: block; } .status { margin-top: 18px; } .grid { grid-template-columns: 1fr; } section { padding: 18px; } }
    </style>
</head>
<body>
<main>
    <header><div><div class="eyebrow">Sovereign Tag Service / 8327</div><h1>Keep the signal coherent.</h1></div><div class="status"><span class="dot"></span><span id="health">Connecting</span></div></header>
    <div class="grid">
        <section><h2>Active tag set</h2><div id="tags" class="tags"></div><form id="add-form"><input id="new-tag" maxlength="256" placeholder="Add a tag" aria-label="New tag"><button>Add</button></form><div id="message" role="status"></div></section>
        <section><h2>System pulse</h2><div class="stats"><div class="stat"><span id="tag-count" class="value">--</span><span class="label">Active tags</span></div><div class="stat"><span id="ledger-count" class="value">--</span><span class="label">Ledger entries</span></div></div><div class="links"><a href="/metrics">Metrics</a><a href="/docs">API docs</a></div></section>
        <section style="grid-column: 1 / -1"><h2>Recent ledger</h2><div id="ledger" class="ledger"></div></section>
    </div>
</main>
<script>
const $ = (id) => document.getElementById(id);
async function refresh() {
    const [tags, health, ledger] = await Promise.all([fetch('/tags').then(r => r.json()), fetch('/health').then(r => r.json()), fetch('/ledger').then(r => r.json())]);
    $('health').textContent = health.status === 'ok' ? 'Operational' : 'Unavailable';
    $('tag-count').textContent = tags.count; $('ledger-count').textContent = ledger.total_entries;
    $('tags').innerHTML = tags.tags.map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join('');
    $('ledger').innerHTML = ledger.ledger.slice().reverse().map(entry => `<div class="entry"><strong>${entry.entry_index}</strong> ${escapeHtml(entry.event)}<small>${escapeHtml(entry.witness)} · ${escapeHtml(entry.seal)}</small></div>`).join('');
}
function escapeHtml(value) { return String(value).replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char])); }
async function addTag(event) { event.preventDefault(); const input = $('new-tag'); const tag = input.value.trim(); if (!tag) return; const response = await fetch('/tags/append', { method: 'POST', headers: {'content-type': 'application/json'}, body: JSON.stringify({tags: [tag]}) }); $('message').textContent = response.ok ? 'Tag set sealed.' : 'Unable to update tag set.'; if (response.ok) { input.value = ''; refresh(); } }
$('add-form').addEventListener('submit', addTag); refresh().catch(() => $('health').textContent = 'Unavailable');
</script>
</body>
</html>"""

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

# ── Tag endpoints ──────────────────────────────────────────────────────────

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
        "service": "Sovereign Tag Service",
        "entry": "8326 → 8327 (FUSION COMPLETE)",
        "tag_count": len(_tag_store),
        "ledger_length": len(_ledger),
        "metrics": "/metrics",
    }

if __name__ == "__main__":
    import uvicorn
    print("🜁∀ SOVEREIGN TAG SERVICE — ENTRY 8327 — FUSION COMPLETE ∀🜁")
    print(f"Exclusive tags ({len(_tag_store)}): {', '.join(_tag_store)}")
    print("Prometheus endpoint: GET /metrics")
    uvicorn.run(app, host="0.0.0.0", port=8090)
