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
# --check-config JSON contract (stdout, exit 0 on success):
#   {"host": "...", "port": 380, "namespace": "...",
#    "bind_host": "...",  # alias of host
#    "url": "http://host:port/healthz",
#    "surface": ["/healthz"],
#    "legacy_out_of_surface": ["/health", "/pulse"]}
#
# CLI (only under if __name__ == "__main__" — import never parses argv):
#   python mcp/port380_mcp.py
#   python mcp/port380_mcp.py --check-config

from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, Mapping, Optional, Tuple


def parse_bind_env(
    environ: Optional[Mapping[str, str]] = None,
) -> Tuple[str, int, str]:
    """Re-runnable bind parse. Used by --check-config and serve."""
    env: Mapping[str, str] = environ if environ is not None else os.environ

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
        port = int(raw)
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


# Module-scope for handler responses only. Import does not touch sys.argv.
try:
    BIND_HOST, PORT, NAMESPACE = parse_bind_env()
except ValueError:
    BIND_HOST, PORT, NAMESPACE = "0.0.0.0", 380, "sovereign-garden"


def bind_plan(environ: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
    """Always re-parses env. Superset CI contract (D34 fix, ledger 8983).

    Keys: ok, bind, host, port, namespace, bind_host, url, surface,
    legacy_out_of_surface, legacy_404_hard. The sovereign-stack CI step
    requires {bind, port, url, surface, namespace, legacy_404_hard, ok};
    host/bind_host remain stable aliases so older consumers keep working.
    """
    host, port, namespace = parse_bind_env(environ)
    env: Mapping[str, str] = environ if environ is not None else os.environ
    raw_legacy_404_hard = env.get("MCP_LEGACY_404_HARD", "0")
    legacy_404_hard = raw_legacy_404_hard.strip().lower() in ("1", "true", "yes", "on")
    return {
        "ok": True,
        "bind": host,
        "host": host,
        "port": port,
        "namespace": namespace,
        "bind_host": host,  # alias — same value as host and bind
        "url": f"http://{host}:{port}/healthz",
        "surface": ["/healthz"],
        "legacy_out_of_surface": ["/health", "/pulse"],
        "legacy_404_hard": legacy_404_hard,
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


def main(argv: Optional[list] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    if "--check-config" in argv:
        try:
            plan = bind_plan()  # explicit re-parse
        except ValueError as e:
            print(f"check-config FAIL: {e}", file=sys.stderr)
            return 1
        # Single JSON object on stdout — CI parses with json.load, no regex
        print(json.dumps(plan, sort_keys=True))
        return 0

    try:
        host, port, namespace = parse_bind_env()
    except ValueError as e:
        print(f"[mcp] bad env: {e}", file=sys.stderr)
        return 1

    global BIND_HOST, PORT, NAMESPACE
    BIND_HOST, PORT, NAMESPACE = host, port, namespace

    print(f"[mcp] binding {host}:{port} namespace={namespace}", flush=True)
    HTTPServer((host, port), MCPHandler).serve_forever()
    return 0


if __name__ == "__main__":
    # Import of this module never runs argv and never binds.
    sys.exit(main())
