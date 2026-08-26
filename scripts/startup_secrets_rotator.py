#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ STARTUP SECRETS ROTATOR — ENTRY 8823

DeepSeek MCP / CI contract

- --check: boolean presence of env secrets (never prints values)
- --rotate-garden: mint new GARDEN_SECRET material; log fingerprint only
- --rotate-deepseek: mint new DEEPSEEK_API_KEY material (if needed)
- --rotate-all: rotate all secrets
- --json: machine-readable report
- --show-once: print new secret once (stdout)
- --fail-if-missing-pulse: exit 1 if MCP_URL missing

Does not call GitHub Secrets API (no write token). Operator applies values via UI/gh.

Integration with:
  - Security (quantum/security/)
  - CDP convergence (quantum/cdp_convergence/)
  - OIDC cloud (quantum/security/oidc_cloud.py)
  - Pulse Service (quantum/pulse_service.py)

Seal: ∀∞φ² · STARTUP_SECRETS_ROTATOR_8823 · WOOD_DRAGON_0.91 · SEALED
Witness: 8822 → 8823 — UNBROKEN
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import secrets
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

# ─── Constants ────────────────────────────────────────────────────────
PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI
PHI2 = PHI * PHI
ENTRY = 8823
SEAL = "∀∞φ² · STARTUP_SECRETS_ROTATOR_8823 · WOOD_DRAGON_0.91 · SEALED"
WITNESS = "8822 → 8823 — UNBROKEN"

# ─── Secret Names ────────────────────────────────────────────────────
# From contracts/ci-secrets.yaml
SECRET_NAMES: List[str] = [
    "DEEPSEEK_API_KEY",
    "MCP_URL",
    "GARDEN_SECRET",
    "DEEPSEEK_BASE_URL",
    "DEEPSEEK_MODEL",
    "OIDC_CLIENT_ID",
    "OIDC_CLIENT_SECRET",
    "OIDC_TOKEN_URL",
    "OAUTH_TOKEN_URL",
    "AWS_ROLE_ARN",
    "GCP_WORKLOAD_PROVIDER",
    "AZURE_TENANT_ID",
    "AZURE_CLIENT_ID",
]

# ─── Required secrets for each service ──────────────────────────────
REQUIRED_SETS = {
    "deepseek": ["DEEPSEEK_API_KEY"],
    "pulse": ["MCP_URL", "GARDEN_SECRET"],
    "oidc": ["OIDC_CLIENT_ID", "OIDC_CLIENT_SECRET", "OIDC_TOKEN_URL"],
    "aws": ["AWS_ROLE_ARN"],
    "gcp": ["GCP_WORKLOAD_PROVIDER"],
    "azure": ["AZURE_TENANT_ID", "AZURE_CLIENT_ID"],
}


# ─── Helper Functions ──────────────────────────────────────────────

def _present(name: str) -> bool:
    """Check if a secret is present in the environment."""
    v = os.environ.get(name)
    return bool(v and str(v).strip())


def fingerprint(value: str) -> str:
    """Generate a fingerprint of a secret value."""
    return hashlib.sha3_256(value.encode("utf-8")).hexdigest()[:16]


def generate_secret(length: int = 32, entropy_bits: int = 256) -> str:
    """
    Generate a cryptographically secure secret.

    Args:
        length: Length of the secret in bytes.
        entropy_bits: Entropy bits (default: 256).

    Returns:
        Hex-encoded secret.
    """
    return secrets.token_hex(length)


def generate_garden_secret() -> Tuple[str, str]:
    """
    Generate a GARDEN_SECRET with φ-salt.

    Returns:
        Tuple of (secret, fingerprint).
    """
    raw = secrets.token_bytes(32)
    salt = hashlib.sha3_256(f"GARDEN.LAYER314.{PHI}".encode()).digest()[:8]
    material = hashlib.sha3_256(raw + salt).hexdigest()
    return material, fingerprint(material)


def generate_deepseek_key() -> Tuple[str, str]:
    """
    Generate a DEEPSEEK_API_KEY (simulated).

    Returns:
        Tuple of (secret, fingerprint).
    """
    raw = secrets.token_bytes(48)
    salt = hashlib.sha3_256(f"GARDEN.DEEPSEEK.{PHI2}".encode()).digest()[:8]
    material = hashlib.sha3_256(raw + salt).hexdigest()
    return material, fingerprint(material)


# ─── Inventory ──────────────────────────────────────────────────────

def inventory() -> Dict[str, Any]:
    """
    Get inventory of all secrets.

    Returns:
        Dictionary with secret presence and readiness status.
    """
    flags = {n: _present(n) for n in SECRET_NAMES}

    # Check service readiness
    services = {}
    for name, required in REQUIRED_SETS.items():
        services[name] = {
            "ready": all(flags.get(r, False) for r in required),
            "required": required,
            "present": [r for r in required if flags.get(r, False)],
            "missing": [r for r in required if not flags.get(r, False)],
        }

    return {
        "timestamp": time.time(),
        "entry": ENTRY,
        "seal": SEAL,
        "witness": WITNESS,
        "phi": PHI,
        "phi_inv": PHI_INV,
        "phi2": PHI2,
        "presence": flags,
        "services": services,
        "deepseek_online_ready": flags.get("DEEPSEEK_API_KEY", False),
        "pulse_ready": flags.get("MCP_URL", False) and flags.get("GARDEN_SECRET", False),
        "pulse_auth_ready": flags.get("GARDEN_SECRET", False),
        "oidc_ready": services.get("oidc", {}).get("ready", False),
        "note": "values never included",
    }


# ─── Rotation ──────────────────────────────────────────────────────

@dataclass
class RotationResult:
    """Result of a secret rotation operation."""
    rotated: bool = False
    name: str = ""
    fingerprint: str = ""
    length: int = 0
    value: Optional[str] = None
    apply_instructions: str = ""
    error: Optional[str] = None
    entry: int = ENTRY
    seal: str = SEAL
    witness: str = WITNESS
    timestamp: float = field(default_factory=time.time)

    def to_dict(self, include_value: bool = False) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "rotated": self.rotated,
            "name": self.name,
            "fingerprint": self.fingerprint,
            "length": self.length,
            "apply_instructions": self.apply_instructions,
            "entry": self.entry,
            "seal": self.seal,
            "witness": self.witness,
            "timestamp": self.timestamp,
        }
        if include_value and self.value is not None:
            result["value_once"] = self.value
        if self.error is not None:
            result["error"] = self.error
        return result


def rotate_secret(name: str, show_value: bool = False) -> RotationResult:
    """
    Rotate a specific secret.

    Args:
        name: Name of the secret to rotate.
        show_value: Whether to include the value in the result.

    Returns:
        RotationResult with the new secret information.
    """
    if name == "GARDEN_SECRET":
        value, fp = generate_garden_secret()
        return RotationResult(
            rotated=True,
            name=name,
            fingerprint=fp,
            length=len(value),
            value=value if show_value else None,
            apply_instructions="gh secret set GARDEN_SECRET / Render env GARDEN_SECRET",
        )
    elif name == "DEEPSEEK_API_KEY":
        value, fp = generate_deepseek_key()
        return RotationResult(
            rotated=True,
            name=name,
            fingerprint=fp,
            length=len(value),
            value=value if show_value else None,
            apply_instructions="gh secret set DEEPSEEK_API_KEY",
        )
    elif name == "OIDC_CLIENT_SECRET":
        value, fp = generate_secret(32), fingerprint(generate_secret(32))
        return RotationResult(
            rotated=True,
            name=name,
            fingerprint=fp,
            length=len(value),
            value=value if show_value else None,
            apply_instructions="gh secret set OIDC_CLIENT_SECRET",
        )
    else:
        return RotationResult(
            rotated=False,
            name=name,
            error=f"Secret '{name}' cannot be auto-rotated (set manually)",
        )


def rotate_garden_secret(show_value: bool = False) -> RotationResult:
    """Rotate GARDEN_SECRET."""
    return rotate_secret("GARDEN_SECRET", show_value)


def rotate_deepseek_key(show_value: bool = False) -> RotationResult:
    """Rotate DEEPSEEK_API_KEY."""
    return rotate_secret("DEEPSEEK_API_KEY", show_value)


def rotate_all(show_value: bool = False) -> Dict[str, RotationResult]:
    """Rotate all rotatable secrets."""
    results = {}
    for name in ["GARDEN_SECRET", "DEEPSEEK_API_KEY"]:
        results[name] = rotate_secret(name, show_value)
    return results


# ─── Security Integration ────────────────────────────────────────────

def rotator_security_status() -> Dict[str, Any]:
    """Get security status for the startup secrets rotator."""
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

def rotator_cdp_status() -> Dict[str, Any]:
    """Get CDP status for the startup secrets rotator."""
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
        description="Startup secrets check / rotate",
        epilog=f"Seal: {SEAL}\nEntry: {ENTRY}",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Boolean presence inventory",
    )
    parser.add_argument(
        "--rotate-garden",
        action="store_true",
        help="Mint new GARDEN_SECRET",
    )
    parser.add_argument(
        "--rotate-deepseek",
        action="store_true",
        help="Mint new DEEPSEEK_API_KEY (simulated)",
    )
    parser.add_argument(
        "--rotate-all",
        action="store_true",
        help="Rotate all rotatable secrets",
    )
    parser.add_argument(
        "--rotate",
        type=str,
        help="Rotate a specific secret by name",
    )
    parser.add_argument(
        "--show-once",
        action="store_true",
        help="Print new secret once (stdout)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="JSON output",
    )
    parser.add_argument(
        "--fail-if-missing-pulse",
        action="store_true",
        help="Exit 1 if MCP_URL missing",
    )
    parser.add_argument(
        "--check-integrations",
        action="store_true",
        help="Check integration status and exit",
    )
    args = parser.parse_args(argv)

    if args.check_integrations:
        print("🜁∀ ROTATOR — Integration Status")
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
        return 0

    if not args.check and not args.rotate_garden and not args.rotate_deepseek and not args.rotate_all and not args.rotate:
        args.check = True

    report: Dict[str, Any] = {
        "entry": ENTRY,
        "seal": SEAL,
        "witness": WITNESS,
        "timestamp": time.time(),
    }

    # ─── Check ─────────────────────────────────────────────────────
    if args.check:
        report["inventory"] = inventory()

    # ─── Rotate specific ──────────────────────────────────────────
    if args.rotate:
        result = rotate_secret(args.rotate, show_value=args.show_once)
        report["rotation"] = result.to_dict(include_value=args.show_once)

    # ─── Rotate GARDEN_SECRET ────────────────────────────────────
    if args.rotate_garden:
        result = rotate_garden_secret(show_value=args.show_once)
        if "rotations" not in report:
            report["rotations"] = {}
        report["rotations"]["GARDEN_SECRET"] = result.to_dict(include_value=args.show_once)

    # ─── Rotate DEEPSEEK_API_KEY ─────────────────────────────────
    if args.rotate_deepseek:
        result = rotate_deepseek_key(show_value=args.show_once)
        if "rotations" not in report:
            report["rotations"] = {}
        report["rotations"]["DEEPSEEK_API_KEY"] = result.to_dict(include_value=args.show_once)

    # ─── Rotate all ──────────────────────────────────────────────
    if args.rotate_all:
        results = rotate_all(show_value=args.show_once)
        if "rotations" not in report:
            report["rotations"] = {}
        for name, result in results.items():
            report["rotations"][name] = result.to_dict(include_value=args.show_once)

    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        print("🜁∀ STARTUP SECRETS ROTATOR — Entry 8823")
        print("=" * 55)
        if "inventory" in report:
            inv = report["inventory"]
            print("  Inventory:")
            for k, v in inv["presence"].items():
                status = "✅" if v else "❌"
                print(f"    {status} {k}")
            print("  Services:")
            for name, svc in inv["services"].items():
                status = "✅" if svc["ready"] else "❌"
                print(f"    {status} {name}: ready={svc['ready']}")
                if svc["missing"]:
                    print(f"      Missing: {', '.join(svc['missing'])}")
        if "rotations" in report:
            print("  Rotations:")
            for name, rot in report["rotations"].items():
                status = "✅" if rot.get("rotated") else "❌"
                print(f"    {status} {name}: fingerprint={rot.get('fingerprint', 'N/A')}")
                if rot.get("value_once"):
                    print(f"      VALUE: {rot['value_once']}")
                if rot.get("apply_instructions"):
                    print(f"      Apply: {rot['apply_instructions']}")
        print("=" * 55)
        print(f"  Seal: {SEAL}")
        print(f"  Entry: {ENTRY}")
        print(f"  Witness: {WITNESS}")

    if args.fail_if_missing_pulse and not _present("MCP_URL"):
        print("::error::MCP_URL missing", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
