#!/usr/bin/env python3
"""
Visualization learning action modal — hash mesh surface.

Background-capable FastAPI:
  GET  /              modal shell (HTML)
  GET  /health
  GET  /status
  POST /mesh/run?steps=N
  GET  /mesh/state
  GET  /mesh/hash
  GET  /ledger/query
  POST /run_sequence

Run:
  uvicorn mesh_modal:app --host 127.0.0.1 --port 8001
  python mesh_modal.py --background

Entry 8825 · pairs with Dragon Breath 8824
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse

from phi_pipeline import PHI, PHASE_STEP, PhiPipeline

DB_PATH = Path(__file__).resolve().parent / "mesh_ledger.sqlite3"
_ledger_lock = threading.Lock()
_state_lock = threading.Lock()
_pipeline = PhiPipeline()
_bg_stop = threading.Event()

app = FastAPI(title="Hash Mesh Modal", version="1.0.0")


def _init_db() -> None:
    with _ledger_lock:
        con = sqlite3.connect(DB_PATH)
        con.execute(
            """CREATE TABLE IF NOT EXISTS ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts REAL NOT NULL,
                event TEXT NOT NULL,
                payload TEXT NOT NULL,
                hash TEXT NOT NULL
            )"""
        )
        con.commit()
        con.close()


def append_ledger(event: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    h = hashlib.sha3_256(f"{event}|{body}".encode()).hexdigest()
    with _ledger_lock:
        con = sqlite3.connect(DB_PATH)
        cur = con.execute(
            "INSERT INTO ledger (ts, event, payload, hash) VALUES (?, ?, ?, ?)",
            (time.time(), event, body, h),
        )
        row_id = cur.lastrowid
        con.commit()
        con.close()
    return {"ledger_id": row_id, "hash": h, "event": event}


def query_ledger(limit: int = 20) -> List[Dict[str, Any]]:
    with _ledger_lock:
        con = sqlite3.connect(DB_PATH)
        rows = con.execute(
            "SELECT id, ts, event, payload, hash FROM ledger ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        con.close()
    out = []
    for r in rows:
        out.append(
            {
                "id": r[0],
                "ts": r[1],
                "event": r[2],
                "payload": json.loads(r[3]),
                "hash": r[4],
            }
        )
    return out


def mesh_hash(state: Dict[str, Any]) -> str:
    raw = json.dumps(state, sort_keys=True, separators=(",", ":"))
    return hashlib.sha3_256(raw.encode()).hexdigest()


_init_db()


@app.get("/", response_class=HTMLResponse)
def modal_shell() -> str:
    """Visualization learning action modal — hash mesh UI."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>Hash Mesh · Visualization Learning Modal</title>
<style>
  :root { --bg:#0b1020; --fg:#e8eefc; --accent:#7c5cff; --ok:#3ddc97; }
  body { margin:0; font-family: ui-sans-serif, system-ui, sans-serif; background:var(--bg); color:var(--fg); }
  .modal { max-width:720px; margin:4vh auto; padding:1.5rem; border:1px solid #2a3555;
           border-radius:16px; background:#121a30; box-shadow:0 12px 40px rgba(0,0,0,.45); }
  h1 { font-size:1.25rem; margin:0 0 .5rem; }
  .meta { opacity:.75; font-size:.85rem; margin-bottom:1rem; }
  button { background:var(--accent); color:white; border:0; border-radius:8px;
           padding:.55rem 1rem; margin-right:.5rem; cursor:pointer; font-weight:600; }
  button.secondary { background:#243056; }
  pre { background:#0a0f1c; padding:1rem; border-radius:10px; overflow:auto; font-size:.8rem; }
  .row { display:flex; gap:.5rem; flex-wrap:wrap; margin-bottom:1rem; }
  .pill { display:inline-block; padding:.2rem .55rem; border-radius:999px; background:#1c2744; font-size:.75rem; }
  .ok { color:var(--ok); }
</style>
</head>
<body>
  <div class="modal" role="dialog" aria-label="Hash mesh learning modal">
    <h1>Visualization Learning · Action Modal · Hash Mesh</h1>
    <div class="meta">
      Pipeline: φ-map → Q8.24 → phase → coherence → null-ban · phase target 202.6°
    </div>
    <div class="row">
      <button onclick="run(1)">Run 1 step (seal window)</button>
      <button class="secondary" onclick="run(5)">Run 5 steps</button>
      <button class="secondary" onclick="refresh()">Refresh state</button>
    </div>
    <div class="row">
      <span class="pill" id="hashPill">hash: —</span>
      <span class="pill" id="phasePill">θ: —</span>
      <span class="pill" id="sealPill">seal: —</span>
    </div>
    <pre id="out">Ready.</pre>
  </div>
<script>
async function run(steps){
  const r = await fetch('/mesh/run?steps='+steps,{method:'POST'});
  const j = await r.json();
  document.getElementById('out').textContent = JSON.stringify(j,null,2);
  paint(j);
}
async function refresh(){
  const r = await fetch('/mesh/state');
  const j = await r.json();
  document.getElementById('out').textContent = JSON.stringify(j,null,2);
  paint(j);
}
function paint(j){
  const st = j.state || j;
  document.getElementById('phasePill').textContent = 'θ: ' + (st.theta ?? st.state?.theta ?? '—');
  document.getElementById('sealPill').textContent = 'seal: ' + (j.status || st.seal_id || '—');
  document.getElementById('hashPill').textContent = 'hash: ' + (j.mesh_hash || j.hash || '—').toString().slice(0,16) + '…';
}
refresh();
</script>
</body>
</html>"""


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/status")
def status() -> Dict[str, Any]:
    with _state_lock:
        st = _pipeline.state.to_dict()
    return {
        "service": "mesh_modal",
        "coherence": st["coherence"],
        "phase": st["theta"],
        "phase_target": PHASE_STEP,
        "phi": PHI,
        "ticks": st["ticks"],
        "background": not _bg_stop.is_set() and _bg_stop.is_set() is False,
    }


@app.post("/mesh/run")
def mesh_run(steps: int = Query(1, ge=1, le=144)) -> Dict[str, Any]:
    with _state_lock:
        result = _pipeline.run_sequence(steps)
    st = result["state"]
    h = mesh_hash(st)
    entry = append_ledger(
        "PHASE_LOCK_REACHED" if result["status"] == "PHASE_LOCK_REACHED" else "SEQUENCE_EXECUTED",
        {"steps": steps, "state": st, "mesh_hash": h, "seal_id": st.get("seal_id")},
    )
    return {
        **result,
        "mesh_hash": h,
        "ledger": entry,
        "message": (
            f"PHASE_LOCK_REACHED phase {st['theta']}° · seal {st.get('seal_id')} · ledger #{entry['ledger_id']}"
            if result["status"] == "PHASE_LOCK_REACHED"
            else f"SEQUENCE_EXECUTED phase {st['theta']}° · no seal"
        ),
    }


@app.get("/mesh/state")
def mesh_state() -> Dict[str, Any]:
    with _state_lock:
        st = _pipeline.state.to_dict()
    return {"state": st, "mesh_hash": mesh_hash(st)}


@app.get("/mesh/hash")
def mesh_hash_route() -> Dict[str, str]:
    with _state_lock:
        st = _pipeline.state.to_dict()
    return {"mesh_hash": mesh_hash(st)}


@app.get("/ledger/query")
def ledger_query(limit: int = Query(20, ge=1, le=200)) -> Dict[str, Any]:
    return {"entries": query_ledger(limit)}


@app.post("/run_sequence")
def run_sequence(steps: int = Query(1, ge=1, le=144)) -> Dict[str, Any]:
    return mesh_run(steps)


def _background_loop(interval: float = 6.0) -> None:
    while not _bg_stop.wait(interval):
        try:
            with _state_lock:
                # single step; seal only when phase lands near 202.6
                result = _pipeline.run_sequence(1)
            st = result["state"]
            h = mesh_hash(st)
            append_ledger("BACKGROUND_TICK", {"state": st, "mesh_hash": h})
        except Exception:
            pass


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--background", action="store_true", help="tick pipeline in background")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--interval", type=float, default=6.0)
    args = parser.parse_args()

    if args.background:
        t = threading.Thread(target=_background_loop, args=(args.interval,), daemon=True)
        t.start()
        print(f"[mesh_modal] background tick every {args.interval}s")

    import uvicorn

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
