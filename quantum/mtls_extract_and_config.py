#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ UNIFIED mTLS CONFIG — ENTRY 8759 + ROTATION SUPPORT (8861)

- get_ssl_context(): server mTLS with dual-CA (ca-bundle) during rotation overlap
- verify_client_cert(): require client cert (or soft-open when MTLS_SOFT=1)
- Integrates with scripts/mtls_cert_rotate.sh live/ layout

Integration with:
  - mtls_cert_lifecycle (Entry 8861)
  - Security (quantum/security/)
  - CDP convergence (quantum/cdp_convergence/)

Env:
  SERVER_CERT  default /certs/server.crt
  SERVER_KEY   default /certs/server.key
  CA_CERT      default /certs/ca.crt  (prefers sibling ca-bundle.crt if present)
  MTLS_SOFT    if "1"/"true", missing client cert → allow (dev/Render without proxy)
  MTLS_CERT_DIR optional root for status
  MTLS_DEBUG   if "1"/"true", enable debug logging

Seal: ∀∞φ² · MCP_MTLS_ROTATE · WOOD_DRAGON_GATE · SEALED
Witness: 8860 → 8861 → 8759 — UNBROKEN
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import os
import re
import ssl
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

# ─── Constants ────────────────────────────────────────────────────────
PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI
PHI2 = PHI * PHI
ENTRY_8759 = 8759
ENTRY_8861 = 8861
SEAL_8759 = "∀∞φ² · MCP_MTLS_ROTATE · WOOD_DRAGON_GATE · SEALED"
SEAL_8861 = "∀∞φ² · MTLS_LIFECYCLE · WOOD_DRAGON_0.91 · SEALED"
WITNESS = "8860 → 8861 → 8759 — UNBROKEN"

# ─── Environment ──────────────────────────────────────────────────────
SERVER_CERT = os.environ.get("SERVER_CERT", "/certs/server.crt")
SERVER_KEY = os.environ.get("SERVER_KEY", "/certs/server.key")
CA_CERT = os.environ.get("CA_CERT", "/certs/ca.crt")
MTLS_CERT_DIR = os.environ.get("MTLS_CERT_DIR", "./certs")
MTLS_DEBUG = os.environ.get("MTLS_DEBUG", "").lower() in ("1", "true", "yes", "on")

# ─── Logging ──────────────────────────────────────────────────────────
logger = logging.getLogger("mtls_config")
if MTLS_DEBUG:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)


def _soft_mode() -> bool:
    """Check if soft mode is enabled (development mode)."""
    return os.environ.get("MTLS_SOFT", "").lower() in ("1", "true", "yes", "on")


def _resolve_ca(ca_cert: str) -> str:
    """Prefer ca-bundle.crt next to CA for dual-trust during rotation."""
    p = Path(ca_cert)
    bundle = p.parent / "ca-bundle.crt"
    if bundle.is_file():
        logger.debug(f"Using CA bundle: {bundle}")
        return str(bundle)

    # Check live directory for rotation
    live_bundle = p.parent / "live" / "ca-bundle.crt"
    if live_bundle.is_file():
        logger.debug(f"Using live CA bundle: {live_bundle}")
        return str(live_bundle)

    return ca_cert


def _resolve_cert_path(cert_path: str) -> str:
    """Resolve certificate path with live/current fallback."""
    path = Path(cert_path)
    if path.is_file():
        return str(path)

    # Check live directory
    live_path = path.parent / "live" / path.name
    if live_path.is_file():
        return str(live_path)

    # Check current directory
    current_path = path.parent / "current" / path.name
    if current_path.is_file():
        return str(current_path)

    return str(path)


# ─── SSL Context ──────────────────────────────────────────────────────

def get_ssl_context(
    server_cert: Optional[str] = None,
    server_key: Optional[str] = None,
    ca_cert: Optional[str] = None,
    require_client: bool = True,
    cert_dir: Optional[str] = None,
) -> ssl.SSLContext:
    """
    Create SSL context for mTLS server side (uvicorn / hypercorn).

    Args:
        server_cert: Path to server certificate.
        server_key: Path to server private key.
        ca_cert: Path to CA certificate.
        require_client: Whether to require client certificates.
        cert_dir: Certificate directory (for auto-discovery).

    Returns:
        SSL context.

    Raises:
        FileNotFoundError: If server certificate or key is missing.
    """
    # Resolve server cert and key
    server_cert = server_cert or SERVER_CERT
    server_key = server_key or SERVER_KEY
    ca_cert = ca_cert or CA_CERT

    # Resolve with live/current fallback
    server_cert = _resolve_cert_path(server_cert)
    server_key = _resolve_cert_path(server_key)
    ca_cert = _resolve_ca(ca_cert)

    logger.debug(f"Server cert: {server_cert}")
    logger.debug(f"Server key: {server_key}")
    logger.debug(f"CA cert: {ca_cert}")

    # Check for cert files
    if not os.path.exists(server_cert):
        raise FileNotFoundError(
            f"Server certificate not found: {server_cert}. "
            "Set SERVER_CERT or run scripts/mtls_cert_rotate.sh"
        )
    if not os.path.exists(server_key):
        raise FileNotFoundError(
            f"Server key not found: {server_key}. "
            "Set SERVER_KEY or run scripts/mtls_cert_rotate.sh"
        )

    ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

    # Load cert chain
    ctx.load_cert_chain(server_cert, server_key)

    # Load CA
    if os.path.exists(ca_cert):
        ctx.load_verify_locations(ca_cert)
        logger.debug(f"Loaded CA: {ca_cert}")
    else:
        ctx.load_default_certs()
        logger.debug("Loaded default CA certificates")

    # Set verify mode
    if require_client and not _soft_mode():
        ctx.verify_mode = ssl.CERT_REQUIRED
    else:
        ctx.verify_mode = ssl.CERT_OPTIONAL
        if _soft_mode():
            logger.info("mTLS running in SOFT mode (client cert optional)")

    # Set minimum TLS version
    try:
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    except AttributeError:
        # Older Python versions
        ctx.options |= ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1

    return ctx


# ─── Client Certificate Verification ─────────────────────────────────

def verify_client_cert(request: Any) -> Dict[str, Any]:
    """
    Extract / require client certificate.

    Args:
        request: FastAPI request object.

    Returns:
        Dictionary with client certificate information.

    Raises:
        HTTPException: If client certificate is required and missing.
    """
    client_cert = None

    # Try to get from request.client
    try:
        client_cert = getattr(request.client, "cert", None)
        if client_cert:
            logger.debug("Client cert from request.client.cert")
    except Exception as e:
        logger.debug(f"Could not get client.cert: {e}")

    # Try from scope
    if not client_cert and hasattr(request, "scope"):
        client_cert = request.scope.get("client_cert")
        if not client_cert:
            client_cert = request.scope.get("ssl_client_cert")
        if client_cert:
            logger.debug("Client cert from request.scope")

    # Try from headers (for proxies)
    if not client_cert and hasattr(request, "headers"):
        for header in ("x-client-cert", "x-forwarded-client-cert", "ssl-client-subject", "ssl-client-cert"):
            if request.headers.get(header):
                client_cert = {
                    "header": header,
                    "value": request.headers.get(header),
                    "source": "header",
                }
                logger.debug(f"Client cert from header: {header}")
                break

    # Try from state (if set by middleware)
    if not client_cert and hasattr(request, "state"):
        client_cert = getattr(request.state, "client_cert", None)
        if client_cert:
            logger.debug("Client cert from request.state")

    # If no client cert found
    if not client_cert:
        if _soft_mode():
            logger.info("MTLS_SOFT=1: allowing request without client cert")
            return {"soft": True, "verified": False, "mode": "soft"}
        try:
            from fastapi import HTTPException
        except ImportError:
            HTTPException = Exception  # type: ignore
        raise HTTPException(status_code=403, detail="mTLS client certificate required")

    # Normalise response
    if isinstance(client_cert, dict):
        client_cert["verified"] = True
        client_cert["mode"] = "hard" if not _soft_mode() else "soft"
        return client_cert
    return {"raw": str(client_cert), "verified": True, "mode": "hard" if not _soft_mode() else "soft"}


# ─── Status ──────────────────────────────────────────────────────────

def mtls_status(cert_dir: str = MTLS_CERT_DIR) -> Dict[str, Any]:
    """
    Get mTLS status including certificate lifecycle.

    Args:
        cert_dir: Certificate directory.

    Returns:
        Dictionary with mTLS status.
    """
    status = {
        "entry_8759": ENTRY_8759,
        "entry_8861": ENTRY_8861,
        "seal_8759": SEAL_8759,
        "seal_8861": SEAL_8861,
        "witness": WITNESS,
        "soft_mode": _soft_mode(),
        "server_cert": SERVER_CERT,
        "server_key": SERVER_KEY,
        "ca_cert": CA_CERT,
        "resolved_ca": _resolve_ca(CA_CERT),
        "cert_dir": cert_dir,
        "timestamp": time.time(),
        "phi": PHI,
        "phi_inv": PHI_INV,
        "phi2": PHI2,
    }

    # Include certificate lifecycle status
    try:
        from quantum.mtls_cert_lifecycle import status_report
        status["lifecycle"] = status_report(cert_dir)
    except ImportError:
        try:
            from mtls_cert_lifecycle import status_report
            status["lifecycle"] = status_report(cert_dir)
        except ImportError:
            status["lifecycle"] = {"error": "mtls_cert_lifecycle module not available"}

    return status


# ─── Extraction ──────────────────────────────────────────────────────

def find_file(root: Path, filename: str) -> Optional[Path]:
    """Find a file recursively in the given root."""
    for p in root.rglob(filename):
        if "certs" not in p.parts and ".git" not in p.parts:
            return p
    return None


def extract_env_vars(content: str) -> Dict[str, str]:
    """Extract environment variables from Python code."""
    pattern = r'(SERVER_CERT|SERVER_KEY|CA_CERT)\s*=\s*os\.environ\.get\(["\']([^"\']+)["\']'
    env_vars: Dict[str, str] = {}
    for match in re.finditer(pattern, content):
        env_vars[match.group(1)] = match.group(2)
    return env_vars


def extract_ssl_context(content: str) -> Optional[str]:
    """Extract SSL context creation code."""
    pattern = r'(ssl_context\s*=\s*ssl\.create_default_context.*?)(?=\n\s*def|\n\s*@|\n\s*class|\n\n|\Z)'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def extract_function(content: str, func_name: str) -> Optional[str]:
    """Extract a function definition from Python code."""
    pattern = rf'(def\s+{func_name}\s*\([\s\S]*?)(?=\n\s*def|\n\s*@|\n\s*class|\n\n|\Z)'
    match = re.search(pattern, content)
    if match:
        return match.group(1).strip()
    return None


def extract_and_output(output_format: str = "module") -> Dict[str, Any]:
    """
    Extract mTLS configuration from the codebase.

    Args:
        output_format: 'module' or 'json'.

    Returns:
        Dictionary with extracted data.
    """
    root = Path(__file__).resolve().parent
    port380_path = find_file(root.parent, "port380_mcp.py") or find_file(root, "endpoint.py")

    result = {
        "entry": ENTRY_8759,
        "seal": SEAL_8759,
        "witness": WITNESS,
        "found": port380_path is not None,
        "path": str(port380_path) if port380_path else None,
    }

    if port380_path:
        content = port380_path.read_text(encoding="utf-8")
        result["env_vars"] = extract_env_vars(content)
        result["ssl_context"] = extract_ssl_context(content)
        result["verify_client_cert"] = extract_function(content, "verify_client_cert")

    if output_format == "json":
        print(json.dumps(result, indent=2, default=str))
    else:
        print("# 🜁∀ mTLS extraction — Entry 8759")
        print("from quantum.mtls_extract_and_config import get_ssl_context, verify_client_cert")
        if result["found"]:
            print(f"# Found: {result['path']}")

    return result


# ─── CLI ──────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Unified mTLS extraction and config",
        epilog=f"Seal: {SEAL_8759}\nEntry: {ENTRY_8759}",
    )
    parser.add_argument("--format", choices=["module", "json"], default="module")
    parser.add_argument("--extract", action="store_true", help="Extract mTLS config")
    parser.add_argument("--status", action="store_true", help="Print cert lifecycle status")
    parser.add_argument("--dir", default=MTLS_CERT_DIR, help="Certificate directory")
    parser.add_argument("--check-integrations", action="store_true", help="Check integration status")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    if args.check_integrations:
        print("🜁∀ MTLS — Integration Status")
        print("=" * 40)
        try:
            from quantum.security import status
            print("  Security: ✅")
        except ImportError:
            print("  Security: ❌")
        try:
            from quantum.cdp_convergence import status
            print("  CDP: ✅")
        except ImportError:
            print("  CDP: ❌")
        try:
            from quantum.mtls_cert_lifecycle import status_report
            print("  Certificate Lifecycle: ✅")
        except ImportError:
            print("  Certificate Lifecycle: ❌")
        print(f"  Soft mode: {'✅' if _soft_mode() else '❌'}")
        return 0

    if args.status:
        try:
            from quantum.mtls_cert_lifecycle import status_report
            report = status_report(args.dir)
        except ImportError:
            from mtls_cert_lifecycle import status_report
            report = status_report(args.dir)

        if args.format == "json":
            print(json.dumps(report, indent=2, default=str))
        else:
            print("🜁∀ MTLS — Certificate Lifecycle Status")
            print("=" * 55)
            for name, cert in report.get("certs", {}).items():
                if cert.get("exists"):
                    days = cert.get("days_remaining")
                    days_s = f"{days:.1f} days" if isinstance(days, (int, float)) else "?"
                    print(f"  {name}: ✅ {days_s}")
                else:
                    print(f"  {name}: ❌ MISSING")
            for warning in report.get("warnings", []):
                print(f"  ⚠️ {warning}")
            print(f"  Rotate recommended: {'✅' if report.get('rotate_recommended') else '❌'}")
        return 0

    if args.extract:
        extract_and_output(args.format)
        return 0

    # Default: show help and status
    status = mtls_status(args.dir)
    if args.format == "json":
        print(json.dumps(status, indent=2, default=str))
    else:
        print("🌁∀ UNIFIED mTLS CONFIG — Entry 8759")
        print("=" * 55)
        print(f"  Soft mode: {'✅' if status['soft_mode'] else '❌'}")
        print(f"  Server cert: {status['server_cert']}")
        print(f"  Server key: {status['server_key']}")
        print(f"  CA cert: {status['ca_cert']}")
        print(f"  Resolved CA: {status['resolved_ca']}")
        if "lifecycle" in status:
            lifecycle = status["lifecycle"]
            print(f"  Lifecycle: {'✅' if 'error' not in lifecycle else '❌'}")
        print("=" * 55)
        print(f"  Seal 8759: {SEAL_8759}")
        print(f"  Seal 8861: {SEAL_8861}")
        print(f"  Witness: {WITNESS}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
