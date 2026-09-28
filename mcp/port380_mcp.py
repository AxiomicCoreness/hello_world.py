#!/usr/bin/env python3
# mcp/port380_mcp.py
#
# MCP gate — loopback-first surface.
# Wildcard bind is opt-in and refused by default.
#
# Env (same names in CI and runtime):
#   MCP_BIND_HOST        default 127.0.0.1  (wildcard refused unless opted in)
#   MCP_ALLOW_WILDCARD   default 0          (1/true/yes/on permits 0.0.0.0 or ::)
#   MCP_PORT             default 380        (legacy PORT fallback only if MCP_PORT unset)
#   MCP_NAMESPACE        default sovereign-garden
# Empty-string MCP_PORT / MCP_BIND_HOST is rejected (not treated as default).
#
# --check-config JSON contract (stdout, exit 0 on success):
#   {"host": "127.0.0.1", "port": 380, "namespace": "sovereign-garden",
#    "bind_host": "127.0.0.1",
#    "url": "http://127.0.0.1:380/healthz",
#    "surface": ["/healthz"],
#    "legacy_out_of_surface": ["/health", "/pulse"],
#    "legacy_404_hard": false,
#    "wildcard_allowed": false,
#    "ok": true}
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

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 380
DEFAULT_NAMESPACE = "sovereign-garden"
WILDCARD_HOSTS = ("0.0.0.0", "::", "[::]", "*")


def _env_flag(env: Mapping[str, str], name: str, default: bool = False) -> bool:
    raw = env.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def parse_bind_env(
    environ: Optional[Mapping[str, str]] = None,
) -> Tuple[str, int, str, bool]:
    """Re-runnable bind parse. Used by --check-config and serve."""
    env: Mapping[str, str] = environ if environ is not None else os.environ

    # --- namespace ---
    if "MCP_NAMESPACE" in env:
        ns = env["MCP_NAMESPACE"]
        if ns == "":
            raise ValueError("MCP_NAMESPACE is empty string")
        namespace = ns
    else:
        namespace = DEFAULT_NAMESPACE

    # --- port ---
    if "MCP_PORT" in env:
        raw = env["MCP_PORT"]
        if raw == "":
            raise ValueError("MCP_PORT is empty string")
        port = int(raw)
    elif "PORT" in env and env["PORT"] != "":
        port = int(env["PORT"])
    else:
        port = DEFAULT_PORT
    if not (1 <= port <= 65535):
        raise ValueError(f"port out of range: {port}")

    # --- host ---
    if "MCP_BIND_HOST" in env:
        host = env["MCP_BIND_HOST"]
        if host == "":
            raise ValueError("MCP_BIND_HOST is empty string")
    else:
        host = DEFAULT_HOST

    wildcard_allowed = _env_flag(env, "MCP_ALLOW_WILDCARD", default=False)
    if host in WILDCARD_HOSTS and not wildcard_allowed:
        raise ValueError(
            f"wildcard bind refused: host={host!r} "
            f"(set MCP_ALLOW_WILDCARD=1 to opt in)"
        )

    return host, port, namespace, wildcard_allowed


# Module-scope for handler responses only. Import does not touch sys.argv.
try:
    BIND_HOST, PORT, NAMESPACE, WILDCARD_ALLOWED = parse_bind_env()
except ValueError:
    BIND_HOST, PORT, NAMESPACE, WILDCARD_ALLOWED = (
        DEFAULT_HOST, DEFAULT_PORT, DEFAULT_NAMESPACE, False,
    )


def bind_plan(environ: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
    """Always re-parses env. Superset of the prior CI contract.

    Required keys: bind, port, url, surface, namespace, legacy_404_hard, ok.
    Stable aliases: host == bind_host == bind.
    New key: wildcard_allowed.
    """
    host, port, namespace, wildcard_allowed = parse_bind_env(environ)
    env: Mapping[str, str] = environ if environ is not None else os.environ
    legacy_404_hard = _env_flag(env, "MCP_LEGACY_404_HARD", default=False)
    return {
        "ok": True,
        "bind": host,
        "host": host,
        "bind_host": host,
        "port": port,
        "namespace": namespace,
        "url": f"http://{host}:{port}/healthz",
        "surface": ["/healthz"],
        "legacy_out_of_surface": ["/health", "/pulse"],
        "legacy_404_hard": legacy_404_hard,
        "wildcard_allowed": wildcard_allowed,
    }


class MCPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/healthz":
            body = (
                b'{"ok": true, "namespace": "'
                + NAMESPACE.encode()
                + b'", "port": '
                + str(PORT).encode()
                + b'", "wildcard_allowed": '
                + (b"true" if WILDCARD_ALLOWED else b"false")
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
        print(json.dumps(plan, sort_keys=True))
        return 0

    try:
        host, port, namespace, wildcard_allowed = parse_bind_env()
    except ValueError as e:
        print(f"[mcp] bad env: {e}", file=sys.stderr)
        return 1

    global BIND_HOST, PORT, NAMESPACE, WILDCARD_ALLOWED
    BIND_HOST, PORT, NAMESPACE, WILDCARD_ALLOWED = (
        host, port, namespace, wildcard_allowed,
    )

    if host in WILDCARD_HOSTS:
        print(f"[mcp] WARNING: wildcard bind active host={host} "
              f"(explicit opt-in via MCP_ALLOW_WILDCARD=1)", flush=True)

    print(f"[mcp] binding {host}:{port} namespace={namespace}", flush=True)
    HTTPServer((host, port), MCPHandler).serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
