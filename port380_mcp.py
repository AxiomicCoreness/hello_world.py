#!/usr/bin/env python3
"""
port380_mcp.py – Fallback A/B/C Protocol Gateway
MCP surface for the Sovereign Engine when OIDC/Orchestrator is unavailable.
Operates purely on stdlib and local contracts.
"""
import os
import json
import math
import time
import hashlib
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel

# ---- Constants ----
PHI = (1 + math.sqrt(5)) / 2
GARDEN_SECRET = os.environ.get("X_GARDEN_SECRET", os.environ.get("GARDEN_SECRET", "wood_dragon_0.91"))
CONTRACT_DIR = os.environ.get("CONTRACT_DIR", "./contracts")
THRESHOLD_ERROR = 0.5  # default error tolerance
PHASE_TARGET = 202.6
PHASE_TOLERANCE = 2.0

app = FastAPI(title="Port-380 MCP Surface", version="1.0.0")

# ---- Data Models ----
class PulseRequest(BaseModel):
    phase_override: float | None = None  # optional manual phase input
    source: str | None = None

# ---- 1. Liveness & Status ----
@app.get("/health")
async def health_check():
    return {"status": "alive", "coherence": 1.0 - 1e-18, "branch": "HEALTHY"}

@app.get("/status")
async def get_status():
    return {"service": "port-380-gate", "phase_lock": PHASE_TARGET, "state": "ETERNAL_NOW"}

@app.get("/380")
async def identity_380():
    return {
        "layer": 314,
        "port_identity": 380,
        "phase_deg": PHASE_TARGET,
        "phi": PHI,
        "seal": "LAYER314_GATE",
    }

# ---- 2. Core Pulse Logic (A/B/C Dispatch) ----
@app.post("/pulse")
async def gate_pulse(
    request: PulseRequest = PulseRequest(),
    x_garden_secret: str | None = Header(None),
):
    if x_garden_secret != GARDEN_SECRET:
        raise HTTPException(status_code=401, detail="Invalid X-Garden-Secret")

    try:
        with open(f"{CONTRACT_DIR}/symplectic_status.agent.jsonl", "r") as f:
            lines = f.readlines()
            latest = json.loads(lines[-1]) if lines else {}
            coherence = float(latest.get("coherence", 0.9999))
            phi_phase = float(latest.get("phi_phase", time.time() % 78624.0))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        coherence = 0.9999
        phi_phase = time.time() % 78624.0

    if request.phase_override is not None:
        phi_phase = request.phase_override

    e = 1.0 - coherence
    branch = "B"  # default hold

    if e > THRESHOLD_ERROR:
        branch = "A"  # Immediate flush
    elif abs(phi_phase - PHASE_TARGET) > PHASE_TOLERANCE:
        branch = "C"  # Trappist-1 reroute
    else:
        branch = "B"  # Natural cron + Merkle temper

    seal_input = f"{branch}|{coherence}|{phi_phase}|{int(time.time())}"
    sub_seal = hashlib.sha256(seal_input.encode()).hexdigest()[:16]

    return {
        "branch": branch,
        "coherence": coherence,
        "phi_phase": phi_phase,
        "error": e,
        "sub_seal": sub_seal,
        "recommended_action": {
            "A": "force_immediate_flush",
            "B": "wait_for_cron_cycle",
            "C": "reroute_to_trappist_harmony",
        }[branch],
        "status": "DECOUPLED_WORKAROUND_ACTIVE",
    }

# ---- 3. MCP Gateway (POST /gate) ----
@app.post("/gate")
async def gate_proxy(payload: dict | None = None, x_garden_secret: str | None = Header(None)):
    return await gate_pulse(PulseRequest(), x_garden_secret)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
