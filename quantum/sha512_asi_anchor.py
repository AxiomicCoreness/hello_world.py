#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ SHA-512 ASI EXTENDED ANCHORS — ENTRY 8752

SHA-512 extended anchors + ASI 512-bit material
===============================================
Extends 64-hex (SHA-256) commitments to 128-hex (SHA-512) digests.

Crypto facts (enforced in code comments and outputs):
  · SHA-256 → 256 bits → 64 hex chars
  · SHA-512 → 512 bits → 128 hex chars  ← ASI 512-bit support
  · AES key sizes are ONLY 128 / 192 / 256 bits — there is NO AES-512.
  · AES-256 subkey = first 32 bytes of SHA-512 digest (hex: first 64 chars)
  · Optional "attach string" is domain-separated into the hash material,
    never used as a raw AES key by itself.

Integration with:
  - Security (quantum/security/)
  - CDP convergence (quantum/cdp_convergence/)
  - Digest Policy (quantum/digest_policy.py)
  - Merkle Economic Bridge (quantum/merkle_economic_bridge.py)

Seal: ∀∞φ² · SHA512_ASI_8752 · WOOD_DRAGON_0.91 · SEALED
Witness: 8751 → 8752 — UNBROKEN
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from typing import Any, Dict, Optional, Tuple, Union

# ─── Constants ────────────────────────────────────────────────────────
PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI
PHI2 = PHI * PHI
ENTRY = 8752
SEAL = "∀∞φ² · SHA512_ASI_8752 · WOOD_DRAGON_0.91 · SEALED"
WITNESS = "8751 → 8752 — UNBROKEN"

DOMAIN_256 = b"GARDEN.LAYER331.MERKLE.v1"
DOMAIN_512 = b"GARDEN.ASI.SHA512.v1"
DOMAIN_ATTACH = b"GARDEN.ASI.ATTACH.v1"
DOMAIN_AES = b"GARDEN.AES.SUBKEY.v1"

# ─── Prior Sealed Anchors ────────────────────────────────────────────
ANCHOR_KEY_256 = "8a250cf445e8ad0cc8d06d0096b969029a175a14eb58838e734f1975358b860d"
LEAF = "807de931c86add23baabafd1252dcc89cbcc23812be1f69e8fc215e51849ee68"
PARENT_330 = "a5173604f02d4a00af365940b0c438fd46bd7f2b16e75e0aabf63a87f5b8c7db"
LAYER_331_256 = "8665c8681492bd176cce55ba4b4f13b2cab0f4253fbefa168234ae56b8d729f2"


# ─── Core Functions ──────────────────────────────────────────────────

def _canon(payload: dict) -> bytes:
    """Canonical JSON encoding."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_hex(domain: bytes, payload: dict) -> str:
    """Full 64-char SHA-256 hex digest."""
    d = hashlib.sha256(domain + b"\0" + _canon(payload)).hexdigest()
    assert len(d) == 64, f"SHA-256 digest must be 64 hex chars, got {len(d)}"
    assert all(c in "0123456789abcdef" for c in d), "SHA-256 digest must be hex"
    return d


def sha512_hex(domain: bytes, payload: dict) -> str:
    """Full 128-char SHA-512 hex digest — ASI 512-bit material."""
    d = hashlib.sha512(domain + b"\0" + _canon(payload)).hexdigest()
    assert len(d) == 128, f"SHA-512 digest must be 128 hex chars, got {len(d)}"
    assert all(c in "0123456789abcdef" for c in d), "SHA-512 digest must be hex"
    return d


def aes256_subkey_from_sha512(sha512_digest: str) -> str:
    """
    Extract AES-256 subkey from SHA-512 digest.

    Args:
        sha512_digest: Full 128-char SHA-512 hex digest.

    Returns:
        64-char hex string (256 bits) for AES-256.
    """
    if len(sha512_digest) != 128:
        raise ValueError(f"SHA-512 digest must be 128 hex chars, got {len(sha512_digest)}")
    return sha512_digest[:64]


def aes128_subkey_from_sha512(sha512_digest: str) -> str:
    """
    Extract AES-128 subkey from SHA-512 digest.

    Args:
        sha512_digest: Full 128-char SHA-512 hex digest.

    Returns:
        32-char hex string (128 bits) for AES-128.
    """
    if len(sha512_digest) != 128:
        raise ValueError(f"SHA-512 digest must be 128 hex chars, got {len(sha512_digest)}")
    return sha512_digest[:32]


def aes192_subkey_from_sha512(sha512_digest: str) -> str:
    """
    Extract AES-192 subkey from SHA-512 digest.

    Args:
        sha512_digest: Full 128-char SHA-512 hex digest.

    Returns:
        48-char hex string (192 bits) for AES-192.
    """
    if len(sha512_digest) != 128:
        raise ValueError(f"SHA-512 digest must be 128 hex chars, got {len(sha512_digest)}")
    return sha512_digest[:48]


def extend_with_attach(
    base_digest_256: str,
    attach_string: str,
    layer: int = 331,
) -> Dict[str, Any]:
    """
    Attach an arbitrary public string into a SHA-512 ASI commitment.

    Args:
        base_digest_256: Full 64-char SHA-256 digest.
        attach_string: Public string to attach.
        layer: Layer number.

    Returns:
        Dictionary with SHA-512 ASI commitment and AES subkeys.
    """
    if len(base_digest_256) != 64:
        raise ValueError(f"base_digest_256 must be full 64-hex SHA-256, got {len(base_digest_256)}")
    if any(c not in "0123456789abcdef" for c in base_digest_256):
        raise ValueError("base_digest_256 must be hex")

    payload = {
        "attach": attach_string,
        "base_sha256": base_digest_256,
        "layer": layer,
        "leaf": LEAF,
        "phi": PHI,
        "phi_inv": PHI_INV,
        "phi2": PHI2,
        "purpose": "ASI_512_material",
        "entry": ENTRY,
        "seal": SEAL,
    }

    full = sha512_hex(DOMAIN_ATTACH, payload)

    return {
        "sha512_asi": full,
        "sha512_asi_len": 128,
        "sha512_asi_bits": 512,
        "aes256_subkey_hex": aes256_subkey_from_sha512(full),
        "aes256_subkey_bits": 256,
        "aes128_subkey_hex": aes128_subkey_from_sha512(full),
        "aes128_subkey_bits": 128,
        "aes192_subkey_hex": aes192_subkey_from_sha512(full),
        "aes192_subkey_bits": 192,
        "aes512": None,
        "aes512_supported": False,
        "note": "AES has no 512-bit mode. ASI uses SHA-512 (512-bit); AES uses 256-bit subkey only.",
        "attach_string": attach_string,
        "base_sha256": base_digest_256,
        "layer": layer,
        "entry": ENTRY,
        "seal": SEAL,
    }


def layer331_sha512() -> Dict[str, Any]:
    """Compute SHA-512 for Layer 331."""
    payload = {
        "event": "mathematical_core",
        "layer": 331,
        "parent_root": PARENT_330,
        "pauli_trace": 1 - 2 * PHI + PHI2,
        "phi": PHI,
        "phi2": PHI2,
        "sha256_root": LAYER_331_256,
        "leaf": LEAF,
        "anchor_key": ANCHOR_KEY_256,
    }
    full = sha512_hex(DOMAIN_512, payload)

    return {
        "merkle_sha256_layer_331": LAYER_331_256,
        "merkle_sha512_asi_layer_331": full,
        "aes256_subkey_hex": aes256_subkey_from_sha512(full),
        "aes128_subkey_hex": aes128_subkey_from_sha512(full),
        "aes192_subkey_hex": aes192_subkey_from_sha512(full),
        "aes512_supported": False,
        "sha512_len": 128,
        "sha512_bits": 512,
        "entry": ENTRY,
        "seal": SEAL,
    }


def status(attach_string: Optional[str] = None) -> Dict[str, Any]:
    """
    Get the status of SHA-512 ASI anchors.

    Args:
        attach_string: Optional attach string for extended commitment.

    Returns:
        Dictionary with status information.
    """
    core = layer331_sha512()
    out: Dict[str, Any] = {
        "entry": ENTRY,
        "seal": SEAL,
        "witness": WITNESS,
        "anchor_key_256": ANCHOR_KEY_256,
        "leaf": LEAF,
        "parent_330": PARENT_330,
        **core,
        "phi": PHI,
        "phi_inv": PHI_INV,
        "phi2": PHI2,
        "policy": {
            "sha256_len": 64,
            "sha256_bits": 256,
            "sha512_len": 128,
            "sha512_bits": 512,
            "no_truncation": True,
            "aes256_only": True,
            "aes512_cipher": False,
            "asi_512_via": "SHA-512",
        },
        "timestamp": time.time(),
        "seal": SEAL,
    }

    if attach_string is not None:
        out["attached"] = extend_with_attach(LAYER_331_256, attach_string)

    return out


# ─── Security Integration ────────────────────────────────────────────

def sha512_security_status() -> Dict[str, Any]:
    """Get security status for SHA-512 ASI."""
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

def sha512_cdp_status() -> Dict[str, Any]:
    """Get CDP status for SHA-512 ASI."""
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

def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="SHA-512 ASI anchor extension — Entry 8752",
        epilog=f"Seal: {SEAL}\nEntry: {ENTRY}",
    )
    parser.add_argument(
        "--attach",
        default="WOOD_DRAGON_GATE · MATHEMATICAL_CORE_8751 · CLARKE_YOURSA_TEE",
        help="Public attach string folded into SHA-512 material",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show status",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    parser.add_argument(
        "--check-integrations",
        action="store_true",
        help="Check integration status and exit",
    )
    args = parser.parse_args()

    if args.check_integrations:
        print("🜁∀ SHA-512 ASI — Integration Status")
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
            from quantum.digest_policy import assert_full_sha512_hex
            print("  Digest Policy: ✅")
        except ImportError:
            print("  Digest Policy: ❌")
        return 0

    s = status(attach_string=args.attach)

    if args.json:
        print(json.dumps(s, indent=2, default=str))
        return 0

    print("🜁∀ SHA-512 ASI EXTENDED ANCHORS — Entry 8752")
    print("=" * 55)
    print(f"  Entry: {s['entry']}")
    print(f"  Seal: {s['seal']}")
    print(f"  Witness: {s['witness']}")
    print(f"  SHA-256 Layer 331: {s['merkle_sha256_layer_331']}")
    print(f"  SHA-512 ASI 331:   {s['merkle_sha512_asi_layer_331']}")
    print(f"  AES-256 subkey:    {s['aes256_subkey_hex']}")
    print(f"  AES-128 subkey:    {s['aes128_subkey_hex']}")
    print(f"  AES-192 subkey:    {s['aes192_subkey_hex']}")
    print(f"  AES-512 supported: {s['aes512_supported']}")
    print("")
    print("  Policy:")
    for k, v in s['policy'].items():
        print(f"    {k}: {v}")

    if "attached" in s:
        a = s["attached"]
        print("")
        print("  Attached Commitment:")
        print(f"    Attach string:    {a['attach_string'][:60]}…")
        print(f"    SHA-512 ASI:      {a['sha512_asi']}")
        print(f"    AES-256 subkey:   {a['aes256_subkey_hex']}")
        print(f"    Note:             {a['note']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
