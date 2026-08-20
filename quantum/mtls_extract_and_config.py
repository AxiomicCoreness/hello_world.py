#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌁∀ Unified mTLS config — Entry 8759 + rotation support (8861)

- get_ssl_context(): server mTLS with dual-CA (ca-bundle) during rotation overlap
- verify_client_cert(): require client cert (or soft-open when MTLS_SOFT=1)
- Integrates with scripts/mtls_cert_rotate.sh live/ layout

Env:
  SERVER_CERT  default /certs/server.crt
  SERVER_KEY   default /certs/server.key
  CA_CERT      default /certs/ca.crt  (prefers sibling ca-bundle.crt if present)
  MTLS_SOFT    if "1"/"true", missing client cert → allow (dev/Render without proxy)
  MTLS_CERT_DIR optional root for status

Seal: ∀∞φ² · MCP_MTLS_ROTATE · WOOD_DRAGON_GATE · SEALED
"""

from __future__ import annotations

import argparse
import json
import os
import re
import ssl
import sys
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from fastapi import HTTPException, Request
except ImportError:  # pragma: no cover
    HTTPException = Exception  # type: ignore
    Request = object  # type: ignore

SERVER_CERT = os.environ.get("SERVER_CERT", "/certs/server.crt")
SERVER_KEY = os.environ.get("SERVER_KEY", "/certs/server.key")
CA_CERT = os.environ.get("CA_CERT", "/certs/ca.crt")


def _soft_mode() -> bool:
    return os.environ.get("MTLS_SOFT", "").lower() in ("1", "true", "yes", "on")


def _resolve_ca(ca_cert: str) -> str:
    """Prefer ca-bundle.crt next to CA for dual-trust during rotation."""
    p = Path(ca_cert)
    bundle = p.parent / "ca-bundle.crt"
    if bundle.is_file():
        return str(bundle)
    return ca_cert


def get_ssl_context(
    server_cert: Optional[str] = None,
    server_key: Optional[str] = None,
    ca_cert: Optional[str] = None,
    require_client: bool = True,
) -> ssl.SSLContext:
    """Create SSL context for mTLS server side (uvicorn / hypercorn)."""
    server_cert = server_cert or SERVER_CERT
    server_key = server_key or SERVER_KEY
    ca_cert = _resolve_ca(ca_cert or CA_CERT)

    ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    if not os.path.exists(server_cert) or not os.path.exists(server_key):
        raise FileNotFoundError(
            "Server certificate or key not found. "
            "Set SERVER_CERT and SERVER_KEY (or run scripts/mtls_cert_rotate.sh)."
        )
    ctx.load_cert_chain(server_cert, server_key)
    if os.path.exists(ca_cert):
        ctx.load_verify_locations(ca_cert)
    else:
        ctx.load_default_certs()
    if require_client and not _soft_mode():
        ctx.verify_mode = ssl.CERT_REQUIRED
    else:
        ctx.verify_mode = ssl.CERT_OPTIONAL
    return ctx


def verify_client_cert(request: Request) -> dict:
    """
    Extract / require client certificate.
    Behind TLS-terminating proxy, set MTLS_SOFT=1 or inject client DN via headers.
    """
    client_cert = None
    try:
        client_cert = getattr(request.client, "cert", None)
    except Exception:
        pass
    if not client_cert and hasattr(request, "scope"):
        client_cert = request.scope.get("client_cert") or request.scope.get("ssl_client_cert")

    if not client_cert and hasattr(request, "headers"):
        for h in ("x-client-cert", "x-forwarded-client-cert", "ssl-client-subject"):
            if request.headers.get(h):
                client_cert = {"header": h, "value": request.headers.get(h)}
                break

    if not client_cert:
        if _soft_mode():
            return {"soft": True, "verified": False}
        raise HTTPException(status_code=403, detail="mTLS client certificate required")
    return client_cert if isinstance(client_cert, dict) else {"raw": str(client_cert)}


def find_file(root: Path, filename: str) -> Optional[Path]:
    for p in root.rglob(filename):
        if "certs" not in p.parts and ".git" not in p.parts:
            return p
    return None


def extract_env_vars(content: str) -> Dict[str, str]:
    pattern = r'(SERVER_CERT|SERVER_KEY|CA_CERT)\s*=\s*os\.environ\.get\(["\']([^"\']+)["\']'
    env_vars: Dict[str, str] = {}
    for match in re.finditer(pattern, content):
        env_vars[match.group(1)] = match.group(2)
    return env_vars


def extract_and_output(output_format: str = "module") -> None:
    root = Path(__file__).resolve().parent
    port380_path = find_file(root.parent, "port380_mcp.py") or find_file(root, "endpoint.py")
    if not port380_path:
        print("\u274c port380_mcp.py / endpoint.py not found.")
        sys.exit(1)
    content = port380_path.read_text(encoding="utf-8")
    if output_format == "json":
        data = {"env_vars": extract_env_vars(content), "path": str(port380_path)}
        print(json.dumps(data, indent=2))
    else:
        print("from quantum.mtls_extract_and_config import get_ssl_context, verify_client_cert")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Unified mTLS extraction and config")
    parser.add_argument("--format", choices=["module", "json"], default="module")
    parser.add_argument("--extract", action="store_true")
    parser.add_argument("--status", action="store_true", help="Print cert lifecycle status")
    args = parser.parse_args()
    if args.status:
        try:
            from quantum.mtls_cert_lifecycle import status_report
            print(json.dumps(status_report(), indent=2, default=str))
        except ImportError:
            from mtls_cert_lifecycle import status_report  # type: ignore
            print(json.dumps(status_report(), indent=2, default=str))
    elif args.extract:
        extract_and_output(args.format)
    else:
        print("🌁∀ Unified mTLS Config — rotation-aware")
        print("  get_ssl_context() \u00b7 verify_client_cert() \u00b7 MTLS_SOFT dual-CA")
        print("  Run: python -m quantum.mtls_cert_lifecycle --dir ./certs")
        print("  Rotate: bash scripts/mtls_cert_rotate.sh")
