#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Port 380 HTTP gate — next dependency after Ingress /380
======================================================
stdlib HTTP server on :380 wrapping port_380_gate math.
GET  /health  /380  /380/status
POST /380/gate  JSON {harmony?, override?}

Seal: ∀∞φ² · PORT380_DEP_REWRITE_8747 · SEALED
"""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict
from urllib.parse import urlparse

from quantum.port_380_gate import DEFAULT_HARMONY, apply_strike_x_gate
from quantum.layer314_anchor import compute_anchor, LEAF, LAYER

HOST = os.environ.get("PORT380_HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT380_PORT", "380"))


def status_payload() -> Dict[str, Any]:
    return {
        "service": "port-380-gate",
        "layer": LAYER,
        "port": PORT,
        "anchor_key": compute_anchor(),
        "leaf": LEAF,
        "default_harmony": DEFAULT_HARMONY,
        "seal": "∀∞φ² · PORT380_DEP_REWRITE_8747 · SEALED",
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
        out = apply_strike_x_gate(harmony, auth_override=override)
        out["layer"] = LAYER
        out["anchor_key"] = compute_anchor()
        self._json(200, out)


def main() -> None:
    httpd = HTTPServer((HOST, PORT), Handler)
    print(f"port-380-gate listening on {HOST}:{PORT} layer={LAYER}")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
