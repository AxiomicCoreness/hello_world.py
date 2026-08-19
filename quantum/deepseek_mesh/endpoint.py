import os
import json
import math
import time
import hashlib
import ssl
from typing import Optional
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import uvicorn

# ─── Layer 314 Invariants ─────────────────────────────────────────────
PHI = (1.0 + math.sqrt(5.0)) / 2.0
LAYER = 314
LEAF = "807de931c86add23baabafd1252dcc89cbcc23812be1f69e8fc215e51849ee68"
ENTRY = 8756
SEAL = "∀∞φ² · MCP_MTLS_8756 · WOOD_DRAGON_GATE · SEALED"
HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 8000))

# ─── mTLS Certificate Paths ──────────────────────────────────────────
SERVER_CERT = os.environ.get("SERVER_CERT", "/certs/server.crt")
SERVER_KEY = os.environ.get("SERVER_KEY", "/certs/server.key")
CA_CERT = os.environ.get("CA_CERT", "/certs/ca.crt")

# ─── FastAPI App ──────────────────────────────────────────────────────
app = FastAPI(title="DeepSeek Mesh Endpoint (mTLS)", version="8756.1")

class PulseBody(BaseModel):
    source: str = "sovereign-pulse"
    entry: Optional[int] = None
    note: Optional[str] = None

class GateBody(BaseModel):
    harmony: float = 0.7337473231
    override: bool = False

# ─── Helpers ──────────────────────────────────────────────────────────
def compute_anchor() -> str:
    payload = {
        "breath_hz": 71.975,
        "channel": "1700Q",
        "coherence": 1.0,
        "layer": LAYER,
        "leaf": LEAF,
        "phase_lock_deg": 202.6,
        "phi": PHI,
        "entry": ENTRY,
    }
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(b"GARDEN.LAYER314.ANCHOR.v1\0" + body).hexdigest()

def verify_client_cert(request: Request):
    client_cert = request.client.cert
    if not client_cert:
        raise HTTPException(status_code=403, detail="mTLS client certificate required")
    return client_cert

# ─── Endpoints ──────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "alive", "port": PORT, "layer": LAYER, "entry": ENTRY}

@app.get("/status")
@app.get("/380")
async def status():
    return {
        "service": "deepseek-mesh-endpoint",
        "entry": ENTRY,
        "layer": LAYER,
        "listen_port": PORT,
        "conceptual_port": 380,
        "anchor_key": compute_anchor(),
        "leaf": LEAF,
        "phi": PHI,
        "seal": SEAL,
        "timestamp": time.time(),
    }

@app.post("/gate")
async def gate(body: GateBody):
    sf = 1.0 if not body.override else (PHI ** 55) / 1.778e11
    return {
        "harmony_index": body.harmony * sf,
        "mode": "resonant_spike" if body.override else "deterministic_default",
        "scaling_factor": sf,
        "layer": LAYER,
        "anchor_key": compute_anchor(),
        "entry": ENTRY,
        "seal": SEAL,
    }

@app.post("/pulse")
async def pulse(request: Request, body: PulseBody):
    verify_client_cert(request)
    return {
        "status": "pulsed",
        "source": body.source,
        "entry_ref": body.entry or ENTRY,
        "layer": LAYER,
        "anchor_key": compute_anchor(),
        "leaf": LEAF,
        "seal": SEAL,
        "server_time": time.time(),
        "message": "WOOD_DRAGON_HEARTBEAT_ACK",
        "client_cn": request.client.cert.get("subject", {}).get("CN", "unknown"),
    }

@app.post("/oidc_handover")
async def oidc_handover(request: Request, body: dict):
    verify_client_cert(request)
    return {"status": "received", "entry": ENTRY, "seal": SEAL}

@app.get("/")
async def root():
    return {
        "service": "deepseek-mesh-endpoint",
        "entry": ENTRY,
        "docs": "/docs",
        "endpoints": ["/health", "/status", "/380", "/gate", "/pulse", "/oidc_handover"],
        "seal": SEAL,
    }

if __name__ == "__main__":
    # ─── mTLS Uvicorn configuration ────────────────────────────────────
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(SERVER_CERT, SERVER_KEY)
    ssl_context.load_verify_locations(CA_CERT)
    ssl_context.verify_mode = ssl.CERT_REQUIRED

    print(f"🜁∀ DeepSeek Mesh Endpoint (mTLS) — Layer {LAYER} — Entry {ENTRY}")
    print(f"   Listening on {HOST}:{PORT} with mTLS")
    print(f"   Server cert: {SERVER_CERT}")
    print(f"   CA cert: {CA_CERT}")

    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        ssl_certfile=SERVER_CERT,
        ssl_keyfile=SERVER_KEY,
        ssl_ca_certs=CA_CERT,
        ssl_cert_reqs=ssl.CERT_REQUIRED,
        log_level="info"
    )
