#!/usr/bin/env python3
# mcp/port380_mcp.py
#
# MCP gate — pod-internal surface. Wildcard bind is intentional.
# Dependent artifact of sovereign-stack-ci / sovereignty-python-package.
#
# Env precedence (CI and prod use the same names — no PORT-only divergence):
#   MCP_BIND_HOST  default 0.0.0.0   (wildcard by design; override to narrow)
#   MCP_PORT       default 380       (legacy PORT accepted only as fallback)
#   MCP_NAMESPACE  default sovereign-garden
#
# North Star loopback (127.0.0.1:8024) governs ASGI only (app_main, flywheel).
# This gate is the mesh-reachable surface: 0.0.0.0:$MCP_PORT by default.
#
# CLI:
#   python mcp/port380_mcp.py              # serve
#   python mcp/port380_mcp.py --check-config  # print bind plan, exit 0 (no socket)

from __future__ import annotations

import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- bind config: MCP_* first, same keys in CI and runtime ---------------
NAMESPACE = os.environ.get("MCP_NAMESPACE", "sovereign-garden")
# Prefer MCP_PORT; fall back to PORT only if MCP_PORT unset (compat).
PORT = int(os.environ["MCP_PORT"] if "MCP_PORT" in os.environ else os.environ.get("PORT", "380"))
BIND_HOST = os.environ.get("MCP_BIND_HOST", "0.0.0.0")  # wildcard by design


def bind_plan() -> dict:
    return {
        "bind_host": BIND_HOST,
        "port": PORT,
        "namespace": NAMESPACE,
        "url": f"http://{BIND_HOST}:{PORT}/healthz",
        "surface": ["/healthz"],
        "legacy_out_of_surface": ["/health", "/pulse"],
    }


class MCPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/healthz":
            body = (
                b'{"ok": true, "namespace": "'
                + NAMESPACE.encode()
                + b'", "port": '
                + str(PORT).encode()
                + b"}"
            )
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


def main() -> int:
    if "--check-config" in sys.argv:
        import json

        print(json.dumps(bind_plan(), indent=2))
        return 0

    plan = bind_plan()
    print(
        f"[mcp] binding {plan['bind_host']}:{plan['port']} "
        f"namespace={plan['namespace']}",
        flush=True,
    )
    HTTPServer((BIND_HOST, PORT), MCPHandler).serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
