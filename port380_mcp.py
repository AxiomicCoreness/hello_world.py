import os
import sys
import hashlib
import hmac
import ipaddress
from contextlib import asynccontextmanager
import json
import re
import time
import subprocess  # ADDED for harness
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel  # ADDED for harness request body

import uvicorn

# ============================================================================
# SERVICE CONSTANTS
# ============================================================================
APP_NAME = "Port380-MCP"
VERSION = "8755.0.0"
LAYER = "314"
GATE_IDENTITY = "GARDEN.LAYER314"

PHI = (1.0 + 5.0 ** 0.5) / 2.0
HASH_ALGO = os.environ.get("HASH_ALGO", "sha3_256")

# ============================================================================
# SECURITY HEADER CONSTANTS
# ============================================================================
# ... (all security header constants remain identical) ...

# ============================================================================
# SecurityHeadersMiddleware
# ============================================================================
class GardenGate:  # Line 42
    def garden_secret_missing(self) -> bool:  # <-- INDENT THIS
        return not os.environ.get("GARDEN_SECRET")

# ============================================================================
# GARDEN_SECRET FAIL-FAST
# ============================================================================
def garden_secret_missing() -> bool:
    return not os.environ.get("GARDEN_SECRET", "").strip()

def require_garden_secret() -> None:
    if garden_secret_missing():
        print(
            "FATAL: GARDEN_SECRET is unset or empty; refusing to start "
            "(/pulse and /mcp/tool would be unauthenticated).",
            file=sys.stderr,
            flush=True,
        )
        raise SystemExit(1)

@asynccontextmanager
async def _lifespan(_app):
    if garden_secret_missing():
        print("FATAL: GARDEN_SECRET is unset or empty; refusing to start.", file=sys.stderr, flush=True)
        raise RuntimeError("GARDEN_SECRET is unset or empty")
    yield

# ============================================================================
# FASTAPI APP
# ============================================================================
app = FastAPI(
    title=APP_NAME,
    version=VERSION,
    description=f"{APP_NAME} — Port 380 Gate Re-export (Layer {LAYER})",
    lifespan=_lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=DEFAULT_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Garden-Secret", "Authorization", "X-Requested-With"],
    expose_headers=["X-Request-Id", "X-Seal"],
    max_age=600,
)

app.add_middleware(SecurityHeadersMiddleware)

# ============================================================================
# RUNTIME STATE
# ============================================================================
START_TIME = time.time()

# ============================================================================
# LEDGER HEAD (derived, not hardcoded)
# ============================================================================
# ... (all ledger logic remains identical) ...

GARDEN_SECRET = os.environ.get("GARDEN_SECRET", "")

AUTOMATON_REL = "garden_surgery/sovereign_automaton_10.06.py"
AUTOMATON_CALLABLE = "sovereign_automaton_10_06"
MCP_TOOL_PATH = "/mcp/tool"
CHAT_TOOL = "chat"
SLOT_BIND_PROPOSED = "127.0.0.1:8024"

def verify_secret(x_garden_secret: Optional[str]) -> bool:
    if not GARDEN_SECRET.strip():
        raise HTTPException(status_code=503, detail="GARDEN_SECRET not configured")
    if not hmac.compare_digest((x_garden_secret or "").encode("utf-8"), GARDEN_SECRET.encode("utf-8")):
        raise HTTPException(status_code=403, detail="Invalid GARDEN_SECRET")
    return True

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _full_sha3(body: Any) -> str:
    canon = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.new(HASH_ALGO, canon.encode("utf-8")).hexdigest()

async def _read_json(request: Request, require_object: bool = False) -> Any:
    try:
        body = await request.json()
    except ValueError:
        raise HTTPException(status_code=400, detail="request body must be valid JSON")
    if require_object and not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="request body must be a JSON object")
    return body

# ============================================================================
# ROUTES
# ============================================================================
@app.get("/health")
@app.get("/healthz")
async def health():
    return JSONResponse(
        content={
            "status": "healthy",
            "service": APP_NAME,
            "version": VERSION,
            "layer": LAYER,
            "timestamp": _now(),
            "gate_identity": GATE_IDENTITY,
        }
    )

@app.get("/status")
async def status():
    return JSONResponse(
        content={
            "status": "ok",
            "service": APP_NAME,
            "timestamp": _now(),
            "ledger_head": resolve_ledger_head(),
        }
    )

@app.get("/status/internal")
async def status_internal(
    x_garden_secret: Optional[str] = Header(None),
):
    verify_secret(x_garden_secret)
    return JSONResponse(
        content={
            "service": APP_NAME,
            "version": VERSION,
            "layer": LAYER,
            "gate_identity": GATE_IDENTITY,
            "uptime": time.time() - START_TIME,
            "timestamp": _now(),
            "ledger_head": resolve_ledger_head(),
            "seal": (
                "forall-infinity-phi-squared cdot MCP_BATCH_FORGED_8755 "
                "cdot WOOD_DRAGON_MOUNTS_OFFENSE cdot SEALED"
            ),
        }
    )

@app.get("/380")
async def port_380():
    return JSONResponse(
        content={
            "port": 380,
            "layer": LAYER,
            "identity": GATE_IDENTITY,
            "message": "Port 380 Gate Active",
            "phi": PHI,
            "timestamp": _now(),
        }
    )

@app.get("/quantum-chessboard/health")
async def quantum_chessboard_health():
    return JSONResponse(
        content={
            "board": "quantum-chessboard",
            "status": "ok",
            "layer": LAYER,
            "timestamp": _now(),
        }
    )

@app.post("/gate")
async def gate(request: Request):
    body = await _read_json(request)
    digest = _full_sha3(body)
    return JSONResponse(
        content={
            "status": "processed",
            "port": 380,
            "layer": LAYER,
            "identity": GATE_IDENTITY,
            "request_digest": digest,
            "hash_algo": HASH_ALGO,
            "timestamp": _now(),
        }
    )

@app.post("/pulse")
async def pulse(
    request: Request,
    x_garden_secret: Optional[str] = Header(None),
):
    verify_secret(x_garden_secret)
    body = await _read_json(request, require_object=True)
    pulse_id = body.get("pulse_id", body.get("source", "manual"))
    pulse_data = {
        "pulse_id": pulse_id,
        "entry": body.get("entry"),
        "note": body.get("note", ""),
        "timestamp": _now(),
        "service": APP_NAME,
        "layer": LAYER,
        "ledger_entry": "8755",
    }
    pulse_hash = _full_sha3(pulse_data)
    return JSONResponse(
        content={
            "status": "pulse_acknowledged",
            "pulse_id": pulse_id,
            "seal": (
                f"forall-infinity-phi-squared cdot PULSE_{pulse_id} "
                f"cdot LAYER{LAYER} cdot {pulse_hash}"
            ),
            "pulse_hash": pulse_hash,
            "hash_algo": HASH_ALGO,
            "ledger_entry": "8755",
            "witness_chain": "8754 -> 8755 — UNBROKEN",
            "timestamp": _now(),
        }
    )

def run_automaton(text: str) -> str:
    import importlib.util
    path = Path(AUTOMATON_REL)
    if not path.is_file():
        raise FileNotFoundError(AUTOMATON_REL)
    spec = importlib.util.spec_from_file_location("sovereign_automaton_10_06", path)
    if spec is None or spec.loader is None:
        raise ImportError(AUTOMATON_REL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fn = getattr(mod, AUTOMATON_CALLABLE)
    payload = fn()
    if isinstance(payload, dict):
        return str(payload.get("message") or payload.get("status") or payload)
    return str(payload)

@app.post("/mcp/tool")
async def mcp_tool(
    request: Request,
    x_garden_secret: Optional[str] = Header(None),
):
    verify_secret(x_garden_secret)
    body = await _read_json(request, require_object=True)
    tool_name = body.get("tool", "unknown")
    arguments = body.get("arguments", {})
    reply = None
    dispatch_error = None
    if tool_name == CHAT_TOOL:
        raw_text = body.get("text", "")
        if not isinstance(raw_text, str) or not raw_text:
            dispatch_error = "missing text"
        else:
            try:
                reply = run_automaton(raw_text)
            except Exception as exc:
                dispatch_error = f"{type(exc).__name__}: {exc}"
    result = {
        "tool": tool_name,
        "arguments": arguments,
        "executed": dispatch_error is None,
        "timestamp": _now(),
        "layer": LAYER,
        "gate_identity": GATE_IDENTITY,
        "text": reply,
        "ok": dispatch_error is None,
        "error": dispatch_error,
        "callable": AUTOMATON_CALLABLE,
        "text_consumed": False,
    }
    result_hash = _full_sha3(result)
    return JSONResponse(
        content={
            "ok": dispatch_error is None,
            "text": reply,
            "result": result,
            "hash": result_hash,
            "hash_algo": HASH_ALGO,
            "seal": (
                f"forall-infinity-phi-squared cdot MCP_TOOL_{tool_name} "
                f"cdot {result_hash}"
            ),
        }
    )

# ============================================================================
# NEW: DEEPINFER HARNESS ENDPOINT
# ============================================================================
class InferenceRequest(BaseModel):
    prompt: str

@app.post("/harness/deepinfer")
async def harness_deepinfer(
    req: InferenceRequest,
    x_garden_secret: Optional[str] = Header(None),
):
    """Executes the DeepInfer add-on harness and seals the output."""
    verify_secret(x_garden_secret)
    
    # Locate harness script relative to this file
    harness_path = Path(__file__).resolve().parent / "harness_deepinfer.py"
    if not harness_path.is_file():
        raise HTTPException(status_code=500, detail="harness_deepinfer.py missing")

    # Inject the prompt into the subprocess environment
    env = os.environ.copy()
    env["DEEPINFER_PROMPT"] = req.prompt

    try:
        result = subprocess.run(
            [sys.executable, str(harness_path), "--json"],
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        
        # The harness prints pure JSON when --json is passed
        payload = json.loads(result.stdout.strip())
        
        if "error" in payload:
            raise HTTPException(status_code=500, detail=payload["error"])
            
        # Calculate a gate seal over the harness result
        gate_hash = _full_sha3(payload)
        
        return JSONResponse(content={
            "status": "harness_complete",
            "gate_seal": f"forall-infinity-phi-squared cdot HARNESS_DEEPINFER cdot {gate_hash}",
            "hash_algo": HASH_ALGO,
            "timestamp": _now(),
            "payload": payload
        })
        
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Harness failed: {e.stderr}")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Harness returned invalid JSON")

# ============================================================================
# ENTRYPOINT
# ============================================================================
# ... (check_config and __main__ remain identical) ...
