#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mTLS certificate lifecycle — status, dual-CA, rotation readiness (Entry 8861)."""
from __future__ import annotations

import argparse
import json
import os
import ssl
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    HAVE_CRYPTO = True
except ImportError:
    HAVE_CRYPTO = False

DEFAULT_CERT_DIR = os.environ.get("MTLS_CERT_DIR", "./certs")
DEFAULT_WARN_DAYS = 30
DEFAULT_ROTATE_DAYS = 14
SEAL = "\u2200\u221e\u03c6\u00b2 \u00b7 MTLS_LIFECYCLE \u00b7 WOOD_DRAGON_0.91 \u00b7 SEALED"


def load_cert_info(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {"path": str(path), "exists": False}
    info: Dict[str, Any] = {"path": str(path), "exists": True}
    if HAVE_CRYPTO:
        cert = x509.load_pem_x509_certificate(path.read_bytes(), default_backend())
        nb = getattr(cert, "not_valid_before_utc", None) or cert.not_valid_before.replace(tzinfo=timezone.utc)
        na = getattr(cert, "not_valid_after_utc", None) or cert.not_valid_after.replace(tzinfo=timezone.utc)
        info["not_before"] = nb.isoformat()
        info["not_after"] = na.isoformat()
        info["subject"] = cert.subject.rfc4514_string()
        info["issuer"] = cert.issuer.rfc4514_string()
        info["days_remaining"] = (na - datetime.now(timezone.utc)).total_seconds() / 86400.0
        return info
    try:
        end = subprocess.check_output(["openssl", "x509", "-in", str(path), "-noout", "-enddate"], text=True).strip().split("=", 1)[-1]
        subj = subprocess.check_output(["openssl", "x509", "-in", str(path), "-noout", "-subject"], text=True).strip()
        info["not_after"] = end
        info["subject"] = subj
        try:
            dt = datetime.strptime(end, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
            info["days_remaining"] = (dt - datetime.now(timezone.utc)).total_seconds() / 86400.0
        except Exception:
            info["days_remaining"] = None
    except Exception as e:
        info["error"] = str(e)
    return info


def resolve_paths(cert_dir: str) -> Dict[str, Path]:
    root = Path(cert_dir)
    live = root / "live"
    current = root / "current"
    def pick(name: str) -> Path:
        a = live / name
        return a if a.is_file() else current / name
    return {
        "root": root,
        "ca": pick("ca.crt"),
        "ca_bundle": live / "ca-bundle.crt",
        "server_crt": pick("server.crt"),
        "server_key": pick("server.key"),
        "client_crt": pick("client.crt"),
    }


def status_report(cert_dir: str = DEFAULT_CERT_DIR) -> Dict[str, Any]:
    paths = resolve_paths(cert_dir)
    report: Dict[str, Any] = {
        "cert_dir": cert_dir,
        "have_cryptography": HAVE_CRYPTO,
        "certs": {},
        "rotate_recommended": False,
        "warnings": [],
        "seal": SEAL,
    }
    for name in ("ca", "ca_bundle", "server_crt", "client_crt"):
        report["certs"][name] = load_cert_info(paths[name])
    for name in ("server_crt", "client_crt", "ca"):
        days = (report["certs"].get(name) or {}).get("days_remaining")
        if days is None:
            continue
        if days < DEFAULT_ROTATE_DAYS:
            report["rotate_recommended"] = True
            report["warnings"].append(f"{name} expires in {days:.1f}d (< {DEFAULT_ROTATE_DAYS})")
        elif days < DEFAULT_WARN_DAYS:
            report["warnings"].append(f"{name} expires in {days:.1f}d (warn {DEFAULT_WARN_DAYS})")
    return report


def build_ssl_context(
    server_cert: Optional[str] = None,
    server_key: Optional[str] = None,
    ca_cert: Optional[str] = None,
    require_client: bool = True,
) -> ssl.SSLContext:
    server_cert = server_cert or os.environ.get("SERVER_CERT", "/certs/server.crt")
    server_key = server_key or os.environ.get("SERVER_KEY", "/certs/server.key")
    ca_cert = ca_cert or os.environ.get("CA_CERT", "/certs/ca.crt")
    bundle = Path(ca_cert).parent / "ca-bundle.crt"
    if bundle.is_file():
        ca_cert = str(bundle)
    ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    if not (os.path.exists(server_cert) and os.path.exists(server_key)):
        raise FileNotFoundError(f"Missing SERVER_CERT/KEY: {server_cert} {server_key}")
    ctx.load_cert_chain(server_cert, server_key)
    if os.path.exists(ca_cert):
        ctx.load_verify_locations(ca_cert)
    else:
        ctx.load_default_certs()
    ctx.verify_mode = ssl.CERT_REQUIRED if require_client else ssl.CERT_OPTIONAL
    return ctx


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="mTLS cert lifecycle status")
    parser.add_argument("--dir", default=DEFAULT_CERT_DIR)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--check-rotate", action="store_true")
    args = parser.parse_args(argv)
    report = status_report(args.dir)
    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        print("mTLS lifecycle status")
        print(f"  cert_dir: {report['cert_dir']}")
        for name, c in report["certs"].items():
            if not c.get("exists"):
                print(f"  {name}: MISSING")
                continue
            days = c.get("days_remaining")
            days_s = f"{days:.1f}d left" if isinstance(days, (int, float)) else "?"
            print(f"  {name}: {c.get('subject', '?')} | {days_s}")
        for w in report["warnings"]:
            print(f"  WARN: {w}")
        print(f"  rotate_recommended: {report['rotate_recommended']}")
        print(f"  seal: {report['seal']}")
    if args.check_rotate and report["rotate_recommended"]:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
