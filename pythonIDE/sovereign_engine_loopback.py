#!/usr/bin/env python3
"""Loopback-only status server. Never 0.0.0.0. Does not fill MCP."""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

HOST = "127.0.0.1"
PORT = 8080
FORBIDDEN = {"0.0.0.0", "::", "::0"}


def bind_host(host: str) -> str:
    if host in FORBIDDEN:
        raise ValueError("wildcard bind forbidden; use 127.0.0.1")
    return host


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = {
            "bind": f"{HOST}:{PORT}",
            "dual_asgi": "127.0.0.1:8024",
            "mcp_filled": False,
            "option_31": "abstract-print-only",
        }
        raw = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, fmt, *args):
        return


def start(host: str = HOST, port: int = PORT):
    host = bind_host(host)
    httpd = HTTPServer((host, port), Handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    print(f"loopback {host}:{port} (not 8024 gearbox)")
    return httpd


if __name__ == "__main__":
    srv = start()
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        srv.shutdown()
