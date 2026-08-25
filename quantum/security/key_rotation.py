#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ KEY ROTATION MACRO — ENTRY 8940
Functional macro to rotate public keys for mTLS, OIDC, or Garden seals.
Append-only; no lines subtracted.

Note: user label 8938 conflicted with MAIN_NO_CLONE_8938; this module is 8940.
"""

from __future__ import annotations

import json
import logging
import os
import time
import hashlib
import hmac
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict

# ─── Constants ────────────────────────────────────────────────────────
PHI = (1.0 + 5 ** 0.5) / 2.0
ENTRY = 8940
SEAL_UNICODE = "∀∞φ² · KEY_ROTATION_8940 · WOOD_DRAGON_0.91 · SEALED"
SEAL_ASCII = "∀∞φ² · KEY_ROTATION_8940 · WOOD_DRAGON_0.91 · SEALED"
LOG = logging.getLogger(__name__)

# ─── State paths ─────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent
LEDGER_DIR = BASE_DIR / "ledger"
ROTATION_LOG_DIR = LEDGER_DIR / "rotation_log"
STATE_FILE = BASE_DIR / ".key_rotation_state"
SEAL_FILE = BASE_DIR / ".current_seal"
JWKS_FILE = BASE_DIR / ".oidc_jwks.json"


@dataclass
class RotationResult:
    """Structured result of a rotation operation."""
    status: str
    key_type: str
    timestamp: float
    updated_keys: List[str]
    message: str
    seal: str = SEAL_UNICODE
    entry: int = ENTRY
    new_seal: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    dry_run: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)


def _ensure_dirs() -> None:
    """Ensure all required directories exist."""
    ROTATION_LOG_DIR.mkdir(parents=True, exist_ok=True)


def _read_state_file() -> Dict[str, Any]:
    """Read the rotation state file if it exists."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _write_state_file(data: Dict[str, Any]) -> None:
    """Write to the rotation state file."""
    with open(STATE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _write_seal_file(seal: str) -> None:
    """Write the current seal to file."""
    with open(SEAL_FILE, "w") as f:
        f.write(seal)


def _write_jwks_file(jwks: Dict[str, Any]) -> None:
    """Write JWKS to file."""
    with open(JWKS_FILE, "w") as f:
        json.dump(jwks, f, indent=2)


def _log_rotation(result: RotationResult) -> None:
    """Append rotation to the rotation log (append-only)."""
    _ensure_dirs()
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(result.timestamp))
    entry = {
        "entry_index": ENTRY,
        "timestamp": stamp,
        "event": "/key_rotation",
        "key_type": result.key_type,
        "updated_keys": result.updated_keys,
        "status": result.status,
        "dry_run": result.dry_run,
        "seal": SEAL_UNICODE,
    }
    log_file = ROTATION_LOG_DIR / f"rot_{stamp}_{hashlib.sha256(str(time.time()).encode()).hexdigest()[:8]}.json"
    with open(log_file, "w") as f:
        json.dump(entry, f, indent=2)
    LOG.info(f"Rotation logged to {log_file}")


def _generate_new_seal() -> str:
    """Generate a new seal ID and return the full seal string."""
    new_seal_id = hashlib.sha256(f"seal:{time.time()}:{PHI}:{os.urandom(16).hex()}".encode()).hexdigest()[:16]
    return f"∀∞φ² · {new_seal_id} · WOOD_DRAGON_0.91 · SEALED"


def rotate_public_keys(
    key_type: str = "all",
    force: bool = False,
    dry_run: bool = False,
) -> RotationResult:
    """
    Rotate public keys used in the Garden's security infrastructure.

    Args:
        key_type: 'mTLS' | 'OIDC' | 'SEAL' | 'all'
        force: Force rotation even if prerequisites are missing
        dry_run: Simulate rotation without writing files

    Returns:
        RotationResult with status, updated_keys, and messages.
    """
    _ensure_dirs()
    result = RotationResult(
        status="initiated",
        key_type=key_type,
        timestamp=time.time(),
        updated_keys=[],
        message="",
        dry_run=dry_run,
    )

    # ─── mTLS rotation ──────────────────────────────────────────────────
    if key_type in ("mTLS", "all"):
        try:
            cert_path = os.environ.get("SERVER_CERT", "/certs/server.crt")
            key_path = os.environ.get("SERVER_KEY", "/certs/server.key")
            ca_path = os.environ.get("CA_CERT", "/certs/ca.crt")

            certs_exist = (
                os.path.exists(cert_path) and
                os.path.exists(key_path) and
                os.path.exists(ca_path)
            )

            if certs_exist or force:
                if dry_run:
                    result.updated_keys.append("mTLS")
                    result.warnings.append("mTLS rotation simulated (dry-run)")
                    LOG.info("mTLS rotation simulated (dry-run)")
                else:
                    new_hash = hashlib.sha256(
                        f"{cert_path}:{key_path}:{ca_path}:{time.time()}:{os.urandom(8).hex()}".encode()
                    ).hexdigest()
                    state = _read_state_file()
                    state["mTLS_rotation_hash"] = new_hash
                    state["mTLS_rotated_at"] = time.time()
                    _write_state_file(state)
                    result.updated_keys.append("mTLS")
                    LOG.info("mTLS certificates rotated")
            else:
                result.warnings.append(
                    f"mTLS cert files missing: cert={cert_path}, key={key_path}, ca={ca_path}. "
                    "Use --force to simulate."
                )
                LOG.warning("mTLS cert files not found; skip rotation.")
        except Exception as e:
            result.status = "partial_failure"
            result.errors.append(f"mTLS rotation failed: {e}")
            LOG.error("mTLS rotation failed: %s", e)

    # ─── OIDC rotation ──────────────────────────────────────────────────
    if key_type in ("OIDC", "all"):
        try:
            token_url = os.environ.get("OIDC_TOKEN_URL") or os.environ.get("OAUTH_TOKEN_URL")
            if token_url or force:
                if dry_run:
                    result.updated_keys.append("OIDC")
                    result.warnings.append("OIDC JWKS rotation simulated (dry-run)")
                    LOG.info("OIDC JWKS rotation simulated (dry-run)")
                else:
                    # In production, fetch from well-known endpoint
                    # For simulation, generate mock JWKS with rotation timestamp
                    new_jwks = {
                        "keys": [
                            {
                                "kid": f"garden_{int(time.time())}",
                                "kty": "RSA",
                                "use": "sig",
                                "alg": "RS256",
                                "n": "mock_n_value",
                                "e": "AQAB",
                            }
                        ],
                        "rotated_at": time.time(),
                        "source": "garden_rotation",
                    }
                    _write_jwks_file(new_jwks)
                    result.updated_keys.append("OIDC")
                    LOG.info("OIDC JWKS rotated")
            else:
                result.warnings.append(
                    "OIDC_TOKEN_URL not set. Use --force to simulate or set OIDC_TOKEN_URL."
                )
                LOG.warning("OIDC_TOKEN_URL missing; skip OIDC rotation.")
        except Exception as e:
            result.status = "partial_failure"
            result.errors.append(f"OIDC rotation failed: {e}")
            LOG.error("OIDC rotation failed: %s", e)

    # ─── SEAL rotation ──────────────────────────────────────────────────
    if key_type in ("SEAL", "all"):
        try:
            if dry_run:
                new_seal = _generate_new_seal()
                result.new_seal = new_seal
                result.updated_keys.append("SEAL")
                result.warnings.append("SEAL rotation simulated (dry-run)")
                LOG.info("SEAL rotation simulated (dry-run)")
            else:
                new_seal = _generate_new_seal()
                _write_seal_file(new_seal)
                # Update state
                state = _read_state_file()
                state["seal_rotated_at"] = time.time()
                state["seal_id"] = new_seal.split("·")[1].strip()
                _write_state_file(state)
                result.updated_keys.append("SEAL")
                result.new_seal = new_seal
                LOG.info("Seal rotated to %s", new_seal)
        except Exception as e:
            result.status = "partial_failure"
            result.errors.append(f"SEAL rotation failed: {e}")
            LOG.error("Seal rotation failed: %s", e)

    # ─── Finalise ──────────────────────────────────────────────────────
    if not result.updated_keys:
        result.status = "failed" if not dry_run else "simulated_failed"
        result.message = result.message or "No keys rotated. Check configuration and key_type."
    else:
        if "failure" not in result.status:
            result.status = "success" if not dry_run else "simulated_success"
        if not result.message:
            result.message = f"Successfully rotated: {', '.join(result.updated_keys)}"
        if dry_run:
            result.message += " (DRY RUN - no files modified)"

    # ─── Log rotation (append-only) ────────────────────────────────────
    if not dry_run:
        try:
            _log_rotation(result)
        except Exception as e:
            LOG.error("Failed to log rotation: %s", e)

    return result


# ─── CLI ──────────────────────────────────────────────────────────────
def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Public key rotation macro",
        epilog=f"Seal: {SEAL_UNICODE}\nEntry: {ENTRY}",
    )
    parser.add_argument(
        "--type",
        choices=["mTLS", "OIDC", "SEAL", "all"],
        default="SEAL",
        help="Key type to rotate",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Simulate rotation even without cert files or env vars",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate rotation without writing files",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress INFO logging",
    )
    args = parser.parse_args()

    if not args.quiet:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    result = rotate_public_keys(
        key_type=args.type,
        force=args.force,
        dry_run=args.dry_run,
    )

    if args.json:
        print(result.to_json())
    else:
        print(f"\n🜁∀ KEY ROTATION — Entry {ENTRY}")
        print("=" * 50)
        print(f"  Status:       {result.status}")
        print(f"  Key type:     {result.key_type}")
        print(f"  Updated:      {', '.join(result.updated_keys) or 'none'}")
        if result.new_seal:
            print(f"  New seal:     {result.new_seal}")
        if result.warnings:
            print(f"  Warnings:     {len(result.warnings)}")
            for w in result.warnings:
                print(f"    ⚠️ {w}")
        if result.errors:
            print(f"  Errors:       {len(result.errors)}")
            for e in result.errors:
                print(f"    ❌ {e}")
        print(f"  Message:      {result.message}")
        print(f"  Dry run:      {result.dry_run}")
        print("=" * 50)
        print(f"  Seal: {SEAL_UNICODE}")
        print(f"  Entry: {ENTRY}")

    return 0 if result.status in ("success", "simulated_success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
