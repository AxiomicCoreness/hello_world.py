#!/usr/bin/env python3
# mcp/port380_mcp.py
#
# MCP gate — pod-internal surface. Wildcard bind is intentional.
# This file is the dependent artifact of .github/workflows/sovereignty-python-package.yml;
# its bind behavior is scoped policy, not a North Star violation.
#
# North Star loopback rule (127.0.0.1:8024) governs ASGI listeners only:
#   - app_main:app
#   - fastapi_flywheel_gearbox:app
# The MCP gate is the namespace-random-access surface and binds 0.0.0.0:$PORT by design.

import os
from http.server import HTTPServer, BaseHTTPRequestHandler

NAMESPACE = os.environ.get("MCP_NAMESPACE", "sovereign-garden")
PORT = int(os.environ.get("MCP_PORT", os.environ.get("PORT", "380")))
BIND_HOST = os.environ.get("MCP_BIND_HOST", "0.0.0.0")  # wildcard by design


class MCPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/healthz":
            body = b'{"ok": true, "namespace": "' + NAMESPACE.encode() + b'"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Security-Policy", "default-src 'none'")
            self.send_header("Strict-Transport-Security", "max-age=31536000")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Permissions-Policy", "interest-cohort=()")
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print(f"[mcp] binding {BIND_HOST}:{PORT} namespace={NAMESPACE}", flush=True)
    HTTPServer((BIND_HOST, PORT), MCPHandler).serve_forever()
