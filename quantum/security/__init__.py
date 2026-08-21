#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ GARDEN SECURITY HELPERS — ENTRY 8946

Unified security module exports:
  - Key rotation (rotate_public_keys)
  - Key expiry monitoring (KeyExpiryMonitor, MonitorReport, KeyStatus)
  - OIDC cloud federation (OIDCCloudClient, CloudProvider, FederatedCredential, OIDCClaims)
  - Offline token operations (mint_offline_token, verify_offline_token)
  - JWKS cache with KMS verification (JwksCache, get_jwks_cache)

All modules are corrected and aligned with:
  - KMS condition bounds (quantum/math/kms_condition_bound.py)
  - Active PID control (quantum/active_pid_controller.py)
  - CDP convergence (quantum/cdp_convergence/)

Seal: ∀∞φ² · SECURITY_INIT_8946 · WOOD_DRAGON_0.91 · SEALED
Witness: 8945 → 8946 — UNBROKEN
"""

from __future__ import annotations

# ─── Key Rotation ────────────────────────────────────────────────────
from .key_rotation import rotate_public_keys, RotationResult

# ─── Key Expiry Monitor ─────────────────────────────────────────────
from .key_expiry_monitor import KeyExpiryMonitor, MonitorReport, KeyStatus

# ─── OIDC Cloud ─────────────────────────────────────────────────────
from .oidc_cloud import (
    OIDCCloudClient,
    CloudProvider,
    FederatedCredential,
    OIDCClaims,
    mint_offline_token,
    verify_offline_token,
    decode_jwt_unverified,
)

# ─── JWKS Cache ─────────────────────────────────────────────────────
from .jwks_cache import JwksCache, get_jwks_cache, KMSVerifier, CacheEntry

# ─── Exports ────────────────────────────────────────────────────────
__all__ = [
    # Key rotation
    "rotate_public_keys",
    "RotationResult",
    # Key expiry monitor
    "KeyExpiryMonitor",
    "MonitorReport",
    "KeyStatus",
    # OIDC cloud
    "OIDCCloudClient",
    "CloudProvider",
    "FederatedCredential",
    "OIDCClaims",
    "mint_offline_token",
    "verify_offline_token",
    "decode_jwt_unverified",
    # JWKS cache
    "JwksCache",
    "get_jwks_cache",
    "KMSVerifier",
    "CacheEntry",
]

# ─── Version ────────────────────────────────────────────────────────
__version__ = "1.0.0"
__entry__ = 8946
__seal__ = "∀∞φ² · SECURITY_INIT_8946 · WOOD_DRAGON_0.91 · SEALED"

# ─── Quick status ──────────────────────────────────────────────────
def status() -> dict:
    """Return a quick status of the security module."""
    from .key_expiry_monitor import KeyExpiryMonitor
    from .oidc_cloud import OIDCCloudClient
    from .jwks_cache import get_jwks_cache

    monitor = KeyExpiryMonitor()
    oidc = OIDCCloudClient()
    cache = get_jwks_cache()

    return {
        "entry": __entry__,
        "seal": __seal__,
        "key_expiry": {
            "any_expired": False,  # Will be populated on actual evaluation
        },
        "oidc_cloud": oidc.status(),
        "jwks_cache": cache.status(),
        "crypto_available": OIDCCloudClient.CRYPTO_AVAILABLE
        if hasattr(OIDCCloudClient, "CRYPTO_AVAILABLE")
        else False,
    }


# ─── CLI ────────────────────────────────────────────────────────────
def main() -> int:
    """CLI entry point for security module status."""
    import json
    import argparse

    parser = argparse.ArgumentParser(description="Garden Security Helpers")
    parser.add_argument("--status", action="store_true", help="Show security module status")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    if args.status:
        out = status()
        if args.json:
            print(json.dumps(out, indent=2, default=str))
        else:
            print(f"\n🜁∀ SECURITY HELPERS — Entry {__entry__}")
            print("=" * 50)
            print(f"  Seal: {__seal__}")
            print(f"  Crypto available: {out.get('crypto_available', False)}")
            print(f"  OIDC offline mode: {out.get('oidc_cloud', {}).get('offline_mode', False)}")
            print(f"  JWKS cache dir: {out.get('jwks_cache', {}).get('cache_dir', 'unknown')}")
            print(f"  KMS enabled: {out.get('jwks_cache', {}).get('kms_enabled', False)}")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
