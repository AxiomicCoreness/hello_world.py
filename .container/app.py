#!/usr/bin/env python3
"""Stdlib HTTP service. No FastAPI, no uvicorn, no third-party deps.

Endpoints:
  GET  /healthz          liveness, unauthenticated
  POST /oidc_handover    workflow handover, GARDEN_SECRET
  POST /restart          request respawn via exit code 75
  POST /380/restart      alias of /restart

Auth: X-Garden-Secret header OR {"token": "..."} body.
Restart: child exits 75; supervisor sees 75 and respawns.
TLS: enabled only when TLS_CERT, TLS_KEY, TLS_CA are all set.
"""
from __future__ import annotations

import json
import os
import signal
import ssl
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional

RESTART_EXIT_CODE = 75
RESTART_DELAY_S = 0.75
HEADER_NAME = "X-Garden-Secret"

_state: Dict[str, bool] = {"restart_requested": False}


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    return os.environ.get(name, default)


def _trigger_restart() -> None:
    _state["restart_requested"] = True
    os.kill(os.getpid(), signal.SIGTERM)


class Handler(BaseHTTPRequestHandler):
    server_version = "SovereignContainer/0.1"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("%s - - %s\n" % (self.address_string(), fmt % args))

    def _secret(self) -> str:
        return getattr(self.server, "garden_secret", "") or ""

    def _authorized(self, body: Dict[str, Any]) -> bool:
        secret = self._secret()
        if not secret:
            return False
        supplied = self.headers.get(HEADER_NAME) or body.get("token") or ""
        return supplied == secret

    def _read_body(self) -> Dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return {}
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return {}
        return parsed if isinstance(parsed, dict) else {}

    def _send(self, status: int, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/healthz":
            self._send(200, {"ok": True})
            return
        self._send(404, {"ok": False, "error": "not found"})

    def do_POST(self) -> None:
        body = self._read_body()
        if self.path == "/oidc_handover":
            if not self._authorized(body):
                self._send(401, {"ok": False, "error": "invalid or missing garden secret"})
                return
            self._send(200, {"ok": True, "mode": "oidc_handover"})
            return
        if self.path in ("/restart", "/380/restart"):
            if not self._authorized(body):
                self._send(401, {"ok": False, "error": "invalid or missing garden secret"})
                return
            self._send(200, {
                "ok": True,
                "restart": "scheduled",
                "delay_s": RESTART_DELAY_S,
                "reason": body.get("reason"),
            })
            threading.Timer(RESTART_DELAY_S, _trigger_restart).start()
            return
        self._send(404, {"ok": False, "error": "not found"})


def _build_server(host: str, port: int) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), Handler)
    server.garden_secret = _env("GARDEN_SECRET", "") or ""
    return server


def _wrap_tls(server: ThreadingHTTPServer) -> bool:
    cert = _env("TLS_CERT")
    key = _env("TLS_KEY")
    ca = _env("TLS_CA")
    if not (cert and key and ca):
        return False
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(certfile=cert, keyfile=key)
    ctx.load_verify_locations(cafile=ca)
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.check_hostname = False
    server.socket = ctx.wrap_socket(server.socket, server_side=True)
    return True


def main() -> int:
    host = _env("HOST", "0.0.0.0") or "0.0.0.0"
    port = int(_env("PORT", "380") or "380")

    server = _build_server(host, port)

    tls_on = _wrap_tls(server)
    sys.stderr.write("tls: %s\n" % ("required" if tls_on else "disabled"))
    if not getattr(server, "garden_secret", ""):
        sys.stderr.write("warn: GARDEN_SECRET unset; protected endpoints return 401\n")

    def _on_signal(signum: int, frame: Any) -> None:
        threading.Thread(target=server.shutdown, daemon=True).start()

    signal.signal(signal.SIGTERM, _on_signal)
    signal.signal(signal.SIGINT, _on_signal)

    try:
        server.serve_forever()
    finally:
        server.server_close()

    return RESTART_EXIT_CODE if _state["restart_requested"] else 0


if __name__ == "__main__":
    sys.exit(main())
