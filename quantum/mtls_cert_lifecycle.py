#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ mTLS CERTIFICATE LIFECYCLE — ENTRY 8861

Status, dual-CA, rotation readiness.

Features:
  - Certificate status reporting
  - Dual-CA support (root and intermediate)
  - Rotation readiness checking
  - SSL context building
  - Integration with security and CDP subsystems

Seal: ∀∞φ² · MTLS_LIFECYCLE · WOOD_DRAGON_0.91 · SEALED
Witness: 8860 → 8861 — UNBROKEN
"""

from __future__ import annotations

import argparse
import json
import math
import os
import ssl
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# ─── Constants ────────────────────────────────────────────────────────
PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI
PHI2 = PHI * PHI
ENTRY = 8861
SEAL = "∀∞φ² · MTLS_LIFECYCLE · WOOD_DRAGON_0.91 · SEALED"
WITNESS = "8860 → 8861 — UNBROKEN"

DEFAULT_CERT_DIR = os.environ.get("MTLS_CERT_DIR", "./certs")
DEFAULT_WARN_DAYS = 30
DEFAULT_ROTATE_DAYS = 14
DEFAULT_CRITICAL_DAYS = 7

# ─── Cryptography ─────────────────────────────────────────────────────
try:
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    HAVE_CRYPTO = True
except ImportError:
    HAVE_CRYPTO = False


# ─── Certificate Info ─────────────────────────────────────────────────

def load_cert_info(path: Path) -> Dict[str, Any]:
    """
    Load certificate information from a PEM file.

    Args:
        path: Path to the certificate file.

    Returns:
        Dictionary with certificate information.
    """
    if not path.is_file():
        return {"path": str(path), "exists": False}

    info: Dict[str, Any] = {"path": str(path), "exists": True}

    if HAVE_CRYPTO:
        try:
            cert = x509.load_pem_x509_certificate(path.read_bytes(), default_backend())
            nb = getattr(cert, "not_valid_before_utc", None)
            if nb is None:
                nb = cert.not_valid_before.replace(tzinfo=timezone.utc)
            na = getattr(cert, "not_valid_after_utc", None)
            if na is None:
                na = cert.not_valid_after.replace(tzinfo=timezone.utc)

            info["not_before"] = nb.isoformat()
            info["not_after"] = na.isoformat()
            info["subject"] = cert.subject.rfc4514_string()
            info["issuer"] = cert.issuer.rfc4514_string()
            info["serial_number"] = hex(cert.serial_number)
            info["version"] = cert.version.value
            info["days_remaining"] = (na - datetime.now(timezone.utc)).total_seconds() / 86400.0

            # Get signature algorithm
            info["signature_algorithm"] = cert.signature_algorithm_oid._name

            # Get extensions
            extensions = {}
            for ext in cert.extensions:
                extensions[ext.oid._name] = {
                    "critical": ext.critical,
                    "value": str(ext.value),
                }
            info["extensions"] = extensions

            return info
        except Exception as e:
            info["error"] = f"cryptography parse error: {e}"

    # Fallback to OpenSSL
    try:
        # Get end date
        end = subprocess.check_output(
            ["openssl", "x509", "-in", str(path), "-noout", "-enddate"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip().split("=", 1)[-1]
        info["not_after"] = end

        # Get subject
        subj = subprocess.check_output(
            ["openssl", "x509", "-in", str(path), "-noout", "-subject"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        info["subject"] = subj

        # Get issuer
        issuer = subprocess.check_output(
            ["openssl", "x509", "-in", str(path), "-noout", "-issuer"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        info["issuer"] = issuer

        # Get serial
        serial = subprocess.check_output(
            ["openssl", "x509", "-in", str(path), "-noout", "-serial"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        info["serial_number"] = serial

        # Parse end date
        try:
            dt = datetime.strptime(end, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
            info["days_remaining"] = (dt - datetime.now(timezone.utc)).total_seconds() / 86400.0
        except Exception:
            info["days_remaining"] = None
    except Exception as e:
        info["error"] = str(e)

    return info


def resolve_paths(cert_dir: str) -> Dict[str, Path]:
    """
    Resolve certificate paths with dual-CA support.

    Args:
        cert_dir: Base certificate directory.

    Returns:
        Dictionary of resolved paths.
    """
    root = Path(cert_dir)
    live = root / "live"
    current = root / "current"
    archive = root / "archive"

    def pick(name: str) -> Path:
        a = live / name
        if a.is_file():
            return a
        c = current / name
        if c.is_file():
            return c
        return a  # Return live path even if not exists

    return {
        "root": root,
        "live": live,
        "current": current,
        "archive": archive,
        "ca": pick("ca.crt"),
        "ca_key": pick("ca.key"),
        "ca_bundle": live / "ca-bundle.crt",
        "intermediate_ca": pick("intermediate.crt"),
        "server_crt": pick("server.crt"),
        "server_key": pick("server.key"),
        "client_crt": pick("client.crt"),
        "client_key": pick("client.key"),
    }


# ─── Status Report ───────────────────────────────────────────────────

def status_report(cert_dir: str = DEFAULT_CERT_DIR) -> Dict[str, Any]:
    """
    Generate a comprehensive certificate status report.

    Args:
        cert_dir: Certificate directory.

    Returns:
        Dictionary with status report.
    """
    paths = resolve_paths(cert_dir)

    report: Dict[str, Any] = {
        "entry": ENTRY,
        "seal": SEAL,
        "witness": WITNESS,
        "cert_dir": cert_dir,
        "have_cryptography": HAVE_CRYPTO,
        "certs": {},
        "rotate_recommended": False,
        "critical": False,
        "warnings": [],
        "errors": [],
        "timestamp": time.time(),
        "phi": PHI,
        "phi_inv": PHI_INV,
        "phi2": PHI2,
    }

    # Load all certificates
    cert_names = ["ca", "ca_bundle", "intermediate_ca", "server_crt", "client_crt"]
    for name in cert_names:
        report["certs"][name] = load_cert_info(paths[name])

    # Check for missing certificates
    for name in ["server_crt", "client_crt", "ca"]:
        if not report["certs"].get(name, {}).get("exists", False):
            report["errors"].append(f"{name} certificate missing")

    # Check expiry
    for name in ["server_crt", "client_crt", "ca", "intermediate_ca"]:
        cert_info = report["certs"].get(name)
        if not cert_info or not cert_info.get("exists"):
            continue

        days = cert_info.get("days_remaining")
        if days is None:
            continue

        if days < DEFAULT_CRITICAL_DAYS:
            report["critical"] = True
            report["warnings"].append(
                f"{name} expires in {days:.1f}d (< {DEFAULT_CRITICAL_DAYS} days) — CRITICAL!"
            )
        elif days < DEFAULT_ROTATE_DAYS:
            report["rotate_recommended"] = True
            report["warnings"].append(
                f"{name} expires in {days:.1f}d (< {DEFAULT_ROTATE_DAYS} days) — rotation recommended"
            )
        elif days < DEFAULT_WARN_DAYS:
            report["warnings"].append(
                f"{name} expires in {days:.1f}d (warn threshold {DEFAULT_WARN_DAYS} days)"
            )

    # Check dual-CA setup
    ca_exists = report["certs"]["ca"].get("exists", False)
    intermediate_exists = report["certs"]["intermediate_ca"].get("exists", False)
    if ca_exists and intermediate_exists:
        report["dual_ca"] = True
    elif ca_exists:
        report["dual_ca"] = False
        report["warnings"].append("Single CA detected (intermediate CA missing)")
    else:
        report["dual_ca"] = False

    return report


# ─── SSL Context ──────────────────────────────────────────────────────

def build_ssl_context(
    server_cert: Optional[str] = None,
    server_key: Optional[str] = None,
    ca_cert: Optional[str] = None,
    require_client: bool = True,
    cert_dir: Optional[str] = None,
) -> ssl.SSLContext:
    """
    Build an SSL context for mTLS.

    Args:
        server_cert: Path to server certificate.
        server_key: Path to server private key.
        ca_cert: Path to CA certificate.
        require_client: Whether to require client certificates.
        cert_dir: Certificate directory (for auto-discovery).

    Returns:
        SSL context.
    """
    # Resolve paths
    if cert_dir is not None:
        paths = resolve_paths(cert_dir)
        server_cert = server_cert or str(paths["server_crt"])
        server_key = server_key or str(paths["server_key"])
        ca_cert = ca_cert or str(paths["ca"])

    server_cert = server_cert or os.environ.get("SERVER_CERT", "/certs/server.crt")
    server_key = server_key or os.environ.get("SERVER_KEY", "/certs/server.key")
    ca_cert = ca_cert or os.environ.get("CA_CERT", "/certs/ca.crt")

    # Try CA bundle
    bundle = Path(ca_cert).parent / "ca-bundle.crt"
    if bundle.is_file():
        ca_cert = str(bundle)

    ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

    # Check for cert files
    if not (os.path.exists(server_cert) and os.path.exists(server_key)):
        raise FileNotFoundError(f"Missing SERVER_CERT/KEY: {server_cert} {server_key}")

    ctx.load_cert_chain(server_cert, server_key)

    if os.path.exists(ca_cert):
        ctx.load_verify_locations(ca_cert)
    else:
        ctx.load_default_certs()

    ctx.verify_mode = ssl.CERT_REQUIRED if require_client else ssl.CERT_OPTIONAL

    # Set minimum TLS version
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2

    return ctx


# ─── Rotation Readiness ─────────────────────────────────────────────

def rotation_readiness(cert_dir: str = DEFAULT_CERT_DIR) -> Dict[str, Any]:
    """
    Check if certificates are ready for rotation.

    Args:
        cert_dir: Certificate directory.

    Returns:
        Dictionary with rotation readiness status.
    """
    report = status_report(cert_dir)

    readiness = {
        "entry": ENTRY,
        "seal": SEAL,
        "cert_dir": cert_dir,
        "ready": False,
        "reasons": [],
        "certificates": {},
    }

    # Check each certificate
    for name in ["server_crt", "client_crt", "ca"]:
        cert_info = report["certs"].get(name, {})
        if not cert_info.get("exists"):
            readiness["reasons"].append(f"{name} missing")
            readiness["certificates"][name] = {"status": "missing"}
            continue

        days = cert_info.get("days_remaining")
        if days is None:
            readiness["reasons"].append(f"{name} expiry unknown")
            readiness["certificates"][name] = {"status": "unknown"}
            continue

        if days < DEFAULT_ROTATE_DAYS:
            readiness["ready"] = True
            readiness["certificates"][name] = {
                "status": "ready",
                "days_remaining": days,
            }
        else:
            readiness["certificates"][name] = {
                "status": "valid",
                "days_remaining": days,
            }

    # Check for critical expiry
    if report.get("critical", False):
        readiness["ready"] = True
        readiness["reasons"].append("Critical expiry detected — rotation required")

    return readiness


# ─── Security Integration ────────────────────────────────────────────

def mtls_security_status() -> Dict[str, Any]:
    """Get security status for the mTLS lifecycle."""
    try:
        from quantum.security import status as security_status
        return {
            "security": security_status(),
            "entry": ENTRY,
            "seal": SEAL,
            "timestamp": time.time(),
        }
    except ImportError:
        return {
            "security": None,
            "note": "Security module not available",
            "entry": ENTRY,
            "seal": SEAL,
        }


# ─── CDP Integration ─────────────────────────────────────────────────

def mtls_cdp_status() -> Dict[str, Any]:
    """Get CDP status for the mTLS lifecycle."""
    try:
        from quantum.cdp_convergence import status as cdp_status
        return {
            "cdp": cdp_status(),
            "entry": ENTRY,
            "seal": SEAL,
            "timestamp": time.time(),
        }
    except ImportError:
        return {
            "cdp": None,
            "note": "CDP module not available",
            "entry": ENTRY,
            "seal": SEAL,
        }


# ─── CLI ──────────────────────────────────────────────────────────────

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="mTLS certificate lifecycle status",
        epilog=f"Seal: {SEAL}\nEntry: {ENTRY}",
    )
    parser.add_argument("--dir", default=DEFAULT_CERT_DIR, help="Certificate directory")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--check-rotate", action="store_true", help="Check rotation readiness")
    parser.add_argument("--check-critical", action="store_true", help="Check critical expiry")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--check-integrations", action="store_true", help="Check integration status")
    args = parser.parse_args(argv)

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
        print(f"  Cryptography: {'✅' if HAVE_CRYPTO else '❌'}")
        return 0

    if args.check_rotate:
        report = rotation_readiness(args.dir)
        if args.json:
            print(json.dumps(report, indent=2, default=str))
        else:
            print("🜁∀ MTLS — Rotation Readiness")
            print("=" * 55)
            print(f"  Ready: {'✅' if report['ready'] else '❌'}")
            for reason in report["reasons"]:
                print(f"    ⚠️ {reason}")
            for name, status in report["certificates"].items():
                status_str = status.get("status", "unknown")
                days = status.get("days_remaining")
                if days is not None:
                    print(f"  {name}: {status_str} ({days:.1f} days)")
                else:
                    print(f"  {name}: {status_str}")
        return 0

    if args.check_critical:
        report = status_report(args.dir)
        if args.json:
            print(json.dumps({"critical": report.get("critical", False), "warnings": report.get("warnings", [])}, indent=2))
        else:
            print("🜁∀ MTLS — Critical Check")
            print("=" * 55)
            print(f"  Critical: {'✅' if report.get('critical') else '❌'}")
            for w in report.get("warnings", []):
                if "CRITICAL" in w:
                    print(f"    ⚠️ {w}")
        return 2 if report.get("critical") else 0

    report = status_report(args.dir)

    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        print("🜁∀ MTLS CERTIFICATE LIFECYCLE — Entry 8861")
        print("=" * 55)
        print(f"  Cert Dir: {report['cert_dir']}")
        print(f"  Cryptography: {'✅' if report['have_cryptography'] else '❌'}")
        print(f"  Dual-CA: {'✅' if report.get('dual_ca') else '❌'}")
        print("  Certificates:")
        for name, cert_info in report["certs"].items():
            if not cert_info.get("exists"):
                print(f"    {name}: ❌ MISSING")
                continue
            days = cert_info.get("days_remaining")
            days_s = f"{days:.1f} days" if isinstance(days, (int, float)) else "?"
            subject = cert_info.get("subject", "?")
            print(f"    {name}: ✅ {days_s} | {subject[:40]}...")

        if report["warnings"]:
            print("  Warnings:")
            for w in report["warnings"]:
                print(f"    ⚠️ {w}")

        if report["errors"]:
            print("  Errors:")
            for e in report["errors"]:
                print(f"    ❌ {e}")

        print(f"  Rotate Recommended: {'✅' if report['rotate_recommended'] else '❌'}")
        print(f"  Critical: {'✅' if report.get('critical') else '❌'}")
        print("=" * 55)
        print(f"  Seal: {report['seal']}")
        print(f"  Entry: {report['entry']}")
        print(f"  Witness: {report['witness']}")

    if args.check_rotate and report["rotate_recommended"]:
        return 2
    if args.check_critical and report.get("critical"):
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
