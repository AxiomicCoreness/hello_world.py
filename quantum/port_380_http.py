#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Port 380 HTTP gate — runs standalone or as quantum.port_380_http."""

from __future__ import annotations

import hashlib
import json
import math
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict
from urllib.parse import urlparse

PHI = (1.0 + math.sqrt(5.0)) / 2.0
LAYER = 314
LEAF = "807de931c86add23baabafd1252dcc89cbcc23812be1f69e8fc215e51849ee68"
DEFAULT_HARMONY = 0.7337473231
SPIKE_INTENSITY = PHI**55
BASE_ORDER = 1.778e11
TEMPORAL_ANCHOR = 2026.058
HOST = os.environ.get("PORT380_HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT380_PORT", "380"))


def compute_anchor() -> str:
    try:
        from quantum.layer314_anchor import compute_anchor as _ca

        return _ca()
    except Exception:
        payload = {
            "breath_hz": 71.975,
            "channel": "1700Q",
            "coherence": 1.0,
            "layer": LAYER,
            "leaf": LEAF,
            "phase_lock_deg": 202.6,
            "phi": PHI,
            "phi2": PHI * PHI,
            "pi_anchor": round(math.pi, 12),
        }
        body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(b"GARDEN.LAYER314.ANCHOR.v1\0" + body).hexdigest()


def apply_strike_x_gate(harmony: float, auth_override: bool = False) -> dict:
    try:
        from quantum.port_380_gate import apply_strike_x_gate as _g

        return _g(harmony, TEMPORAL_ANCHOR, auth_override)
    except Exception:
        if not auth_override:
            return {
                "harmony_index": harmony,
                "mode": "deterministic_default",
                "scaling_factor": 1.0,
                "auth_override": False,
                "temporal_anchor": TEMPORAL_ANCHOR,
            }
        sf = SPIKE_INTENSITY / BASE_ORDER
        return {
            "harmony_index": harmony * sf,
            "mode": "resonant_spike",
            "scaling_factor": sf,
            "auth_override": True,
            "temporal_anchor": TEMPORAL_ANCHOR,
        }


def status_payload() -> Dict[str, Any]:
    return {
        "service": "port-380-gate",
        "layer": LAYER,
        "port": PORT,
        "anchor_key": compute_anchor(),
        "leaf": LEAF,
        "default_harmony": DEFAULT_HARMONY,
        "seal": "∀∞φ² · PORT380_RUNTIME_FIX_8749 · SEALED",
    }


class Handler(BaseHTTPRequestHandler):
    def _json(self, code: int, body: dict) -> None:
        data = json.dumps(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt: str, *args) -> None:
        print("[port380]", fmt % args)

    def do_GET(self) -> None:
        path = urlparse(self.path).path.rstrip("/") or "/"
        if path in ("/health", "/380/health"):
            self._json(200, {"status": "ok", "port": PORT})
            return
        if path in ("/380", "/380/status", "/status"):
            self._json(200, status_payload())
            return
        self._json(404, {"error": "not_found", "path": path})

    def do_POST(self) -> None:
        path = urlparse(self.path).path.rstrip("/") or "/"
        if path not in ("/380/gate", "/gate"):
            self._json(404, {"error": "not_found", "path": path})
            return
        n = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(n) if n else b"{}"
        try:
            body = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._json(400, {"error": "invalid_json"})
            return
        harmony = float(body.get("harmony", DEFAULT_HARMONY))
        override = bool(body.get("override", False))
        out = apply_strike_x_gate(harmony, override)
        out["layer"] = LAYER
        out["anchor_key"] = compute_anchor()
        self._json(200, out)


def main() -> None:
    httpd = HTTPServer((HOST, PORT), Handler)
    print(f"port-380-gate listening on {HOST}:{PORT} layer={LAYER}")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
