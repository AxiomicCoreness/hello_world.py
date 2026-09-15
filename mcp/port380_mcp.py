#!/usr/bin/env python3
# mcp/port380_mcp.py
#
# MCP gate — pod-internal surface. Wildcard bind is intentional.
#
# Env (same names in CI and runtime):
#   MCP_BIND_HOST  default 0.0.0.0
#   MCP_PORT       default 380 (legacy PORT fallback only if MCP_PORT unset)
#   MCP_NAMESPACE  default sovereign-garden
# Empty-string MCP_PORT / MCP_BIND_HOST is rejected (not treated as default).
#
# CLI (only under if __name__ == "__main__" — import never parses argv):
#   python mcp/port380_mcp.py
#   python mcp/port380_mcp.py --check-config

from __future__ import annotations

import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Tuple


def parse_bind_env(
    environ: dict | None = None,
) -> Tuple[str, int, str]:
    """Re-runnable bind parse. Used at import *and* by --check-config."""
    env = environ if environ is not None else os.environ

    if "MCP_NAMESPACE" in env:
        ns = env["MCP_NAMESPACE"]
        if ns == "":
            raise ValueError("MCP_NAMESPACE is empty string")
        namespace = ns
    else:
        namespace = "sovereign-garden"

    if "MCP_PORT" in env:
        raw = env["MCP_PORT"]
        if raw == "":
            raise ValueError("MCP_PORT is empty string")
        port = int(raw)  # ValueError on garbage e.g. abc
    elif "PORT" in env and env["PORT"] != "":
        port = int(env["PORT"])
    else:
        port = 380

    if not (1 <= port <= 65535):
        raise ValueError(f"port out of range: {port}")

    if "MCP_BIND_HOST" in env:
        host = env["MCP_BIND_HOST"]
        if host == "":
            raise ValueError("MCP_BIND_HOST is empty string")
    else:
        host = "0.0.0.0"

    return host, port, namespace


# Module-scope defaults for handlers / import-time inspection.
# Import does not touch sys.argv. Serve path re-validates via parse_bind_env.
try:
    BIND_HOST, PORT, NAMESPACE = parse_bind_env()
except ValueError:
    # Defer hard fail to main/check-config so import of a misconfigured
    # process still allows --help-style discovery; serve will re-raise.
    BIND_HOST, PORT, NAMESPACE = "0.0.0.0", 380, "sovereign-garden"
    _IMPORT_PARSE_ERROR = True
else:
    _IMPORT_PARSE_ERROR = False


def bind_plan(environ: dict | None = None) -> dict:
    """Always re-parses — does not trust stale module-scope alone."""
    host, port, namespace = parse_bind_env(environ)
    return {
        "bind_host": host,
        "port": port,
        "namespace": namespace,
        "url": f"http://{host}:{port}/healthz",
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


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    if "--check-config" in argv:
        import json

        # Explicit re-parse of current os.environ — never trust only import-time.
        try:
            plan = bind_plan()
        except ValueError as e:
            print(f"check-config FAIL: {e}", file=sys.stderr)
            return 1
        print(json.dumps(plan, indent=2))
        return 0

    try:
        host, port, namespace = parse_bind_env()
    except ValueError as e:
        print(f"[mcp] bad env: {e}", file=sys.stderr)
        return 1

    # Keep handler constants in sync with re-parsed values
    global BIND_HOST, PORT, NAMESPACE
    BIND_HOST, PORT, NAMESPACE = host, port, namespace

    print(
        f"[mcp] binding {host}:{port} namespace={namespace}",
        flush=True,
    )
    HTTPServer((host, port), MCPHandler).serve_forever()
    return 0


if __name__ == "__main__":
    # Guard: import mcp.port380_mcp never runs argv / never binds.
    sys.exit(main())
