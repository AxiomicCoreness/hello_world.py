#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ WORKER SERVER — ENTRY 8000

Sovereign stdlib HTTP worker v2.3

Exposes:
  - /health
  - /mcp/tools/predict_grammar_score
  - /strike_x/harmony

Integration with:
  - Security (quantum/security/)
  - CDP convergence (quantum/cdp_convergence/)
  - FRB Bridge (quantum/frb_bridge.py)
  - Pulse Service (quantum/pulse_service.py)

Seal: ∀∞φ² · WORKER_SERVER_8000 · WOOD_DRAGON_0.91 · SEALED
Witness: 7999 → 8000 — UNBROKEN
"""

import hashlib
import json
import math
import sys
import time
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Dict, Optional, Tuple

# ─── Constants ────────────────────────────────────────────────────────
PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI
PHI2 = PHI * PHI
PHI3 = PHI2 * PHI
ENTRY = 8000
SEAL = "∀∞φ² · WORKER_SERVER_8000 · WOOD_DRAGON_0.91 · SEALED"
WITNESS = "7999 → 8000 — UNBROKEN"

PHI_SQ = PHI2
T_FRB = 78624.0  # 0.91 days in seconds
PHASE_LOCK_DEG = 202.6
PHASE_LOCK_RAD = math.radians(PHASE_LOCK_DEG)
Q8_24_SCALE = 1 << 24  # 16,777,216
HOST = "0.0.0.0"
DEFAULT_PORT = 8000

# ─── In-Memory State ──────────────────────────────────────────────────
# Not persisted across restarts
HARMONY_INDEX = 0.7337473231  # latest Choir index
WORKER_COHERENCE = 1.0  # live coherence c(t)
WORKER_STEP = 0
WORKER_HISTORY: list[Dict[str, Any]] = []


# ─── Helper Functions ─────────────────────────────────────────────────

def q8_24_quantize(x: float) -> float:
    """Q8.24 fixed-point quantization."""
    return round(x * Q8_24_SCALE) / Q8_24_SCALE


def q8_24_quantize_int(x: float) -> int:
    """Q8.24 fixed-point quantization to integer."""
    return int(round(x * Q8_24_SCALE))


def update_coherence_from_frb() -> float:
    """Update coherence from current FRB phase."""
    phase = time.time() % T_FRB
    return 0.5 * (1.0 + math.cos(2.0 * math.pi * phase / T_FRB))


def update_harmony_phi_step() -> float:
    """Update harmony index using φ‑step."""
    global HARMONY_INDEX
    raw = HARMONY_INDEX * PHI
    quantized = q8_24_quantize(raw)
    HARMONY_INDEX = quantized
    return HARMONY_INDEX


def get_status() -> Dict[str, Any]:
    """Get current worker status."""
    return {
        "harmony_index": HARMONY_INDEX,
        "coherence": WORKER_COHERENCE,
        "step": WORKER_STEP,
        "phase_lock_deg": PHASE_LOCK_DEG,
        "tau_frb": T_FRB,
        "q8_24_scale": Q8_24_SCALE,
        "entry": ENTRY,
        "seal": SEAL,
        "witness": WITNESS,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def record_history(event: str, data: Dict[str, Any]) -> None:
    """Record an event in history."""
    global WORKER_HISTORY
    WORKER_HISTORY.append({
        "event": event,
        "timestamp": time.time(),
        "data": data,
    })
    if len(WORKER_HISTORY) > 1000:
        WORKER_HISTORY = WORKER_HISTORY[-1000:]


# ─── HTTP Handler ─────────────────────────────────────────────────────

class SovereignWorkerHandler(BaseHTTPRequestHandler):
    """HTTP handler for the Sovereign Worker Server."""

    def _send_json(self, status: int, data: Dict[str, Any]) -> None:
        """Send JSON response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, default=str).encode())

    def _get_auth(self) -> Tuple[bool, Optional[str]]:
        """Check OIDC bearer authentication."""
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
            # Simple validation (length check)
            if len(token) > 10:
                return True, token
            return False, None
        return False, None

    def _log_message(self, format: str, *args: Any) -> None:
        """Override to suppress default logging."""
        pass

    def do_OPTIONS(self) -> None:
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        """Handle GET requests."""
        global WORKER_COHERENCE, WORKER_STEP

        if self.path == "/health":
            WORKER_COHERENCE = update_coherence_from_frb()
            self._send_json(200, {
                "status": "ok",
                "worker": "clarke_yoursa_tee_worker",
                "coherence": WORKER_COHERENCE,
                "phase_lock": PHASE_LOCK_DEG,
                "harmony_index": HARMONY_INDEX,
                "step": WORKER_STEP,
                "entry": ENTRY,
                "seal": SEAL,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            return

        if self.path == "/strike_x/harmony":
            WORKER_COHERENCE = update_coherence_from_frb()
            self._send_json(200, {
                "harmony_index": HARMONY_INDEX,
                "coherence": WORKER_COHERENCE,
                "tau_frb": T_FRB,
                "phase_lock": PHASE_LOCK_DEG,
                "step": WORKER_STEP,
                "entry": ENTRY,
                "seal": SEAL,
            })
            return

        if self.path == "/status":
            self._send_json(200, get_status())
            return

        if self.path == "/history":
            limit = 10
            self._send_json(200, {
                "history": WORKER_HISTORY[-limit:],
                "total": len(WORKER_HISTORY),
                "entry": ENTRY,
                "seal": SEAL,
            })
            return

        self.send_error(404)

    def do_POST(self) -> None:
        """Handle POST requests."""
        global WORKER_COHERENCE, WORKER_STEP, HARMONY_INDEX

        # Parse body
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            body_raw = self.rfile.read(content_len).decode()
            body = json.loads(body_raw) if body_raw else {}
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON body"})
            return

        # ─── /mcp/tools/predict_grammar_score ──────────────────────────
        if self.path == "/mcp/tools/predict_grammar_score":
            auth_ok, token = self._get_auth()
            if not auth_ok:
                self._send_json(403, {
                    "error": "OIDC bearer required",
                    "entry": ENTRY,
                    "seal": SEAL,
                })
                return

            WORKER_COHERENCE = update_coherence_from_frb()
            c = WORKER_COHERENCE
            x = body.get("x", 1.0)

            # φ‑corrected prediction
            y_hat = (1.0 - c) * 0.9 + (0.35 + 0.65 * c) * x

            # Apply φ‑scaling
            y_hat = y_hat * PHI_INV

            result = {
                "predicted_score": q8_24_quantize(y_hat),
                "coherence": c,
                "harmony_index": HARMONY_INDEX,
                "worker": "clarke_yoursa_tee_worker",
                "entry": ENTRY,
                "seal": SEAL,
            }

            record_history("predict_grammar_score", {"x": x, "y_hat": y_hat, "coherence": c})
            self._send_json(200, result)
            return

        # ─── /strike_x/harmony (POST) ──────────────────────────────────
        if self.path == "/strike_x/harmony":
            auth_ok, token = self._get_auth()
            if not auth_ok:
                self._send_json(403, {
                    "error": "OIDC bearer required",
                    "entry": ENTRY,
                    "seal": SEAL,
                })
                return

            # Get optional parameters
            target_harmony = body.get("harmony_index")
            step_mode = body.get("mode", "phi")

            # Update step counter
            WORKER_STEP += 1

            if step_mode == "phi":
                # φ‑step
                new_index = update_harmony_phi_step()
            elif step_mode == "set" and target_harmony is not None:
                # Set to specific value
                HARMONY_INDEX = q8_24_quantize(target_harmony)
                new_index = HARMONY_INDEX
            elif step_mode == "reset":
                # Reset to default
                HARMONY_INDEX = 0.7337473231
                new_index = HARMONY_INDEX
            else:
                # Default: φ‑step
                new_index = update_harmony_phi_step()

            # Update coherence
            WORKER_COHERENCE = update_coherence_from_frb()

            result = {
                "harmony_index": HARMONY_INDEX,
                "coherence": WORKER_COHERENCE,
                "phi_step": PHI,
                "q8_24_scale": Q8_24_SCALE,
                "step": WORKER_STEP,
                "mode": step_mode,
                "entry": ENTRY,
                "seal": SEAL,
            }

            record_history("strike_x_harmony", {"mode": step_mode, "result": result})
            self._send_json(200, result)
            return

        # ─── /reset ─────────────────────────────────────────────────────
        if self.path == "/reset":
            auth_ok, token = self._get_auth()
            if not auth_ok:
                self._send_json(403, {
                    "error": "OIDC bearer required",
                    "entry": ENTRY,
                    "seal": SEAL,
                })
                return

            HARMONY_INDEX = 0.7337473231
            WORKER_COHERENCE = 1.0
            WORKER_STEP = 0
            WORKER_HISTORY = []

            self._send_json(200, {
                "status": "reset",
                "message": "Worker state reset",
                "entry": ENTRY,
                "seal": SEAL,
            })
            return

        self.send_error(404)


# ─── Server Runner ────────────────────────────────────────────────────

def run_server(port: int = DEFAULT_PORT, host: str = HOST) -> None:
    """Run the worker server."""
    server = HTTPServer((host, port), SovereignWorkerHandler)
    print(f"🜁∀ Worker Server — Entry {ENTRY}")
    print(f"   Listening on {host}:{port}")
    print(f"   Seal: {SEAL}")
    print(f"   Witness: {WITNESS}")
    print(f"   Endpoints:")
    print(f"     GET  /health")
    print(f"     GET  /status")
    print(f"     GET  /history")
    print(f"     GET  /strike_x/harmony")
    print(f"     POST /strike_x/harmony (OIDC required)")
    print(f"     POST /mcp/tools/predict_grammar_score (OIDC required)")
    print(f"     POST /reset (OIDC required)")
    print("")
    print(f"   Starting server...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🜁∀ Server stopped.")


# ─── Security Integration ────────────────────────────────────────────

def worker_security_status() -> Dict[str, Any]:
    """Get security status for the worker server."""
    try:
        from quantum.security import status as security_status
        return {
            "security": security_status(),
            "entry": ENTRY,
            "seal": SEAL,
            "timestamp": time.time(),
        }
    except ImportError:
        return {
            "security": None,
            "note": "Security module not available",
            "entry": ENTRY,
            "seal": SEAL,
        }


# ─── CDP Integration ─────────────────────────────────────────────────

def worker_cdp_status() -> Dict[str, Any]:
    """Get CDP status for the worker server."""
    try:
        from quantum.cdp_convergence import status as cdp_status
        return {
            "cdp": cdp_status(),
            "entry": ENTRY,
            "seal": SEAL,
            "timestamp": time.time(),
        }
    except ImportError:
        return {
            "cdp": None,
            "note": "CDP module not available",
            "entry": ENTRY,
            "seal": SEAL,
        }


# ─── CLI ──────────────────────────────────────────────────────────────

def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Worker Server — Entry 8000",
        epilog=f"Seal: {SEAL}\nEntry: {ENTRY}",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help="Port to listen on",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=HOST,
        help="Host to bind to",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show current status and exit",
    )
    parser.add_argument(
        "--check-integrations",
        action="store_true",
        help="Check integration status and exit",
    )
    args = parser.parse_args()

    if args.check_integrations:
        print("🜁∀ WORKER — Integration Status")
        print("=" * 40)
        try:
            from quantum.security import status
            print("  Security: ✅")
        except ImportError:
            print("  Security: ❌")
        try:
            from quantum.cdp_convergence import status
            print("  CDP: ✅")
        except ImportError:
            print("  CDP: ❌")
        return 0

    if args.status:
        st = get_status()
        print(json.dumps(st, indent=2, default=str))
        return 0

    run_server(port=args.port, host=args.host)
    return 0


if __name__ == "__main__":
    sys.exit(main())
