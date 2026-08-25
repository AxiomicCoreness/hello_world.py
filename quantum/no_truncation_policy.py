#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ DIGEST POLICY — ENTRY 8756

Policy: digests and fingerprints are full-width — never truncated in APIs/logs.

This module enforces the Garden's no-truncation policy:
  - SHA-256: 64 hex characters
  - SHA-512: 128 hex characters
  - No ellipsis, no slicing, no truncation in any display or log output

Integration with:
  - Security (quantum/security/)
  - Merkle roots (quantum/merkle_economic_bridge.py)
  - OIDC tokens (quantum/security/oidc_cloud.py)
  - Ledger entries (ledger/)

Seal: ∀∞φ² · DIGEST_POLICY_8756 · WOOD_DRAGON_0.91 · SEALED
Witness: 8755 → 8756 — UNBROKEN
"""

from __future__ import annotations

import hashlib
import math
import re
import sys
import time
from typing import Any, Dict, List, Optional, Union

# ─── Constants ────────────────────────────────────────────────────────
PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI
PHI2 = PHI * PHI
ENTRY = 8756
SEAL = "∀∞φ² · DIGEST_POLICY_8756 · WOOD_DRAGON_0.91 · SEALED"
WITNESS = "8755 → 8756 — UNBROKEN"

# ─── Regex Patterns ──────────────────────────────────────────────────
SHA256_HEX = re.compile(r"^[0-9a-f]{64}$", re.IGNORECASE)
SHA512_HEX = re.compile(r"^[0-9a-f]{128}$", re.IGNORECASE)
SHA1_HEX = re.compile(r"^[0-9a-f]{40}$", re.IGNORECASE)
MD5_HEX = re.compile(r"^[0-9a-f]{32}$", re.IGNORECASE)
HEX_ONLY = re.compile(r"^[0-9a-f]+$", re.IGNORECASE)


# ─── Validation Functions ──────────────────────────────────────────

def assert_full_sha256_hex(s: str, name: str = "digest") -> str:
    """
    Assert that a string is a full 64-character SHA-256 hex digest.

    Args:
        s: The digest string to validate.
        name: The name of the digest for error messages.

    Returns:
        The validated digest string (lowercase).

    Raises:
        ValueError: If the digest is not a full SHA-256 hex string.
    """
    s = s.strip().lower()
    if not SHA256_HEX.match(s):
        raise ValueError(
            f"{name} must be full 64-char hex SHA-256, got len={len(s)}: {s[:16]}..."
        )
    return s


def assert_full_sha512_hex(s: str, name: str = "digest") -> str:
    """
    Assert that a string is a full 128-character SHA-512 hex digest.

    Args:
        s: The digest string to validate.
        name: The name of the digest for error messages.

    Returns:
        The validated digest string (lowercase).

    Raises:
        ValueError: If the digest is not a full SHA-512 hex string.
    """
    s = s.strip().lower()
    if not SHA512_HEX.match(s):
        raise ValueError(
            f"{name} must be full 128-char hex SHA-512, got len={len(s)}: {s[:16]}..."
        )
    return s


def assert_full_sha1_hex(s: str, name: str = "digest") -> str:
    """
    Assert that a string is a full 40-character SHA-1 hex digest.

    Args:
        s: The digest string to validate.
        name: The name of the digest for error messages.

    Returns:
        The validated digest string (lowercase).

    Raises:
        ValueError: If the digest is not a full SHA-1 hex string.
    """
    s = s.strip().lower()
    if not SHA1_HEX.match(s):
        raise ValueError(
            f"{name} must be full 40-char hex SHA-1, got len={len(s)}: {s[:16]}..."
        )
    return s


def assert_full_md5_hex(s: str, name: str = "digest") -> str:
    """
    Assert that a string is a full 32-character MD5 hex digest.

    Args:
        s: The digest string to validate.
        name: The name of the digest for error messages.

    Returns:
        The validated digest string (lowercase).

    Raises:
        ValueError: If the digest is not a full MD5 hex string.
    """
    s = s.strip().lower()
    if not MD5_HEX.match(s):
        raise ValueError(
            f"{name} must be full 32-char hex MD5, got len={len(s)}: {s[:16]}..."
        )
    return s


def assert_hex_only(s: str, name: str = "digest") -> str:
    """
    Assert that a string contains only hex characters.

    Args:
        s: The string to validate.
        name: The name for error messages.

    Returns:
        The validated string (lowercase).

    Raises:
        ValueError: If the string contains non-hex characters.
    """
    s = s.strip().lower()
    if not HEX_ONLY.match(s):
        raise ValueError(
            f"{name} must contain only hex characters, got: {s[:32]}..."
        )
    return s


def is_full_sha256_hex(s: str) -> bool:
    """Check if a string is a full SHA-256 hex digest."""
    return bool(SHA256_HEX.match(s.strip().lower()))


def is_full_sha512_hex(s: str) -> bool:
    """Check if a string is a full SHA-512 hex digest."""
    return bool(SHA512_HEX.match(s.strip().lower()))


def is_full_sha1_hex(s: str) -> bool:
    """Check if a string is a full SHA-1 hex digest."""
    return bool(SHA1_HEX.match(s.strip().lower()))


def is_full_md5_hex(s: str) -> bool:
    """Check if a string is a full MD5 hex digest."""
    return bool(MD5_HEX.match(s.strip().lower()))


# ─── Display Functions ──────────────────────────────────────────────

def display_digest(s: str) -> str:
    """
    Return digest unchanged — no ellipsis, no slicing, no truncation.

    Args:
        s: The digest string to display.

    Returns:
        The original digest string unchanged.
    """
    return s


def display_truncated(s: str, max_len: int = 16) -> str:
    """
    Display a digest with truncation for UI contexts.

    WARNING: This function is for UI display ONLY. It does NOT modify
    the actual digest value. Full digests must always be used in APIs and logs.

    Args:
        s: The digest string to display.
        max_len: Maximum length before truncation.

    Returns:
        The digest string with ellipsis if truncated.
    """
    if len(s) <= max_len:
        return s
    return f"{s[:max_len]}…"


def format_for_log(s: str) -> str:
    """
    Format a digest for log output - FULL digest, no truncation.

    Args:
        s: The digest string to log.

    Returns:
        The full digest string.
    """
    return s


def format_for_api(s: str) -> str:
    """
    Format a digest for API response - FULL digest, no truncation.

    Args:
        s: The digest string to return.

    Returns:
        The full digest string.
    """
    return s


# ─── Digest Generators ──────────────────────────────────────────────

def sha256_digest(data: Union[str, bytes]) -> str:
    """
    Generate a full SHA-256 digest (64 hex chars).

    Args:
        data: The data to hash (string or bytes).

    Returns:
        Full 64-character SHA-256 hex digest.
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def sha512_digest(data: Union[str, bytes]) -> str:
    """
    Generate a full SHA-512 digest (128 hex chars).

    Args:
        data: The data to hash (string or bytes).

    Returns:
        Full 128-character SHA-512 hex digest.
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha512(data).hexdigest()


def sha256_domain_digest(domain: bytes, data: Union[str, bytes]) -> str:
    """
    Generate a domain-separated SHA-256 digest.

    Args:
        domain: Domain separation bytes.
        data: The data to hash (string or bytes).

    Returns:
        Full 64-character SHA-256 hex digest.
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(domain + b"\0" + data).hexdigest()


def sha512_domain_digest(domain: bytes, data: Union[str, bytes]) -> str:
    """
    Generate a domain-separated SHA-512 digest.

    Args:
        domain: Domain separation bytes.
        data: The data to hash (string or bytes).

    Returns:
        Full 128-character SHA-512 hex digest.
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha512(domain + b"\0" + data).hexdigest()


# ─── Merkle Integration ─────────────────────────────────────────────

def merkle_leaf(path: str, content: bytes) -> str:
    """
    Generate a full SHA-256 Merkle leaf.

    Args:
        path: The path string.
        content: The content bytes.

    Returns:
        Full 64-character SHA-256 hex digest.
    """
    h = hashlib.sha256()
    h.update(path.encode("utf-8"))
    h.update(b"\0")
    h.update(content)
    return h.hexdigest()


def merkle_root(leaves: List[str]) -> str:
    """
    Compute a full SHA-256 Merkle root from leaves.

    Args:
        leaves: List of leaf digests.

    Returns:
        Full 64-character SHA-256 hex digest.
    """
    if not leaves:
        return hashlib.sha256(b"empty").hexdigest()

    # Ensure all leaves are full digests
    for leaf in leaves:
        assert_full_sha256_hex(leaf)

    level = leaves[:]
    while len(level) > 1:
        nxt = []
        for i in range(0, len(level), 2):
            if i + 1 < len(level):
                pair = level[i] + level[i + 1]
            else:
                pair = level[i] + level[i]
            nxt.append(hashlib.sha256(pair.encode()).hexdigest())
        level = nxt

    root = level[0]
    assert_full_sha256_hex(root)
    return root


# ─── Security Integration ────────────────────────────────────────────

def digest_security_status() -> Dict[str, Any]:
    """Get security status for the digest policy."""
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

def digest_cdp_status() -> Dict[str, Any]:
    """Get CDP status for the digest policy."""
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
        description="Digest Policy — Entry 8756",
        epilog=f"Seal: {SEAL}\nEntry: {ENTRY}",
    )
    parser.add_argument(
        "--digest",
        type=str,
        help="Validate a digest string",
    )
    parser.add_argument(
        "--type",
        choices=["sha256", "sha512", "sha1", "md5"],
        default="sha256",
        help="Digest type to validate",
    )
    parser.add_argument(
        "--generate",
        type=str,
        help="Generate a digest from a string",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Show the digest policy",
    )
    parser.add_argument(
        "--check-integrations",
        action="store_true",
        help="Check integration status and exit",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    args = parser.parse_args()

    if args.check_integrations:
        print("🜁∀ DIGEST POLICY — Integration Status")
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
        print(f"  Policy: full-width digests only (no truncation)")
        return 0

    if args.generate:
        if args.type == "sha256":
            digest = sha256_digest(args.generate)
        elif args.type == "sha512":
            digest = sha512_digest(args.generate)
        else:
            digest = hashlib.sha1(args.generate.encode()).hexdigest()
        if args.json:
            print(json.dumps({
                "type": args.type,
                "input": args.generate,
                "digest": digest,
                "length": len(digest),
                "policy": "full_width_no_truncation",
                "entry": ENTRY,
                "seal": SEAL,
            }, indent=2))
        else:
            print("🜁∀ DIGEST GENERATED")
            print("=" * 40)
            print(f"  Type: {args.type}")
            print(f"  Digest: {digest}")
            print(f"  Length: {len(digest)} ({'✅ full' if len(digest) in (64, 128) else '⚠️ not full'})")
            print(f"  Policy: full_width_no_truncation")
        return 0

    if args.digest:
        try:
            if args.type == "sha256":
                validated = assert_full_sha256_hex(args.digest)
            elif args.type == "sha512":
                validated = assert_full_sha512_hex(args.digest)
            elif args.type == "sha1":
                validated = assert_full_sha1_hex(args.digest)
            elif args.type == "md5":
                validated = assert_full_md5_hex(args.digest)

            if args.json:
                print(json.dumps({
                    "digest": validated,
                    "type": args.type,
                    "valid": True,
                    "length": len(validated),
                    "policy": "full_width_no_truncation",
                    "entry": ENTRY,
                    "seal": SEAL,
                }, indent=2))
            else:
                print(f"✅ Valid {args.type.upper()} digest: {validated}")
                print(f"   Length: {len(validated)}")
            return 0
        except ValueError as e:
            if args.json:
                print(json.dumps({
                    "digest": args.digest,
                    "type": args.type,
                    "valid": False,
                    "error": str(e),
                    "policy": "full_width_no_truncation",
                    "entry": ENTRY,
                    "seal": SEAL,
                }, indent=2))
            else:
                print(f"❌ {e}")
            return 1

    if args.show:
        policy = {
            "entry": ENTRY,
            "seal": SEAL,
            "witness": WITNESS,
            "policy": "full_width_no_truncation",
            "rules": {
                "SHA-256": "64 hex characters (full)",
                "SHA-512": "128 hex characters (full)",
                "SHA-1": "40 hex characters (full)",
                "MD5": "32 hex characters (full)",
            },
            "no_truncation": True,
            "no_ellipsis": True,
            "no_slicing": True,
        }
        if args.json:
            print(json.dumps(policy, indent=2, default=str))
        else:
            print("🜁∀ DIGEST POLICY — Entry 8756")
            print("=" * 55)
            print(f"  Policy: {policy['policy']}")
            print(f"  No truncation: {policy['no_truncation']}")
            print(f"  No ellipsis: {policy['no_ellipsis']}")
            print(f"  No slicing: {policy['no_slicing']}")
            print("  Rules:")
            for rule, description in policy["rules"].items():
                print(f"    {rule}: {description}")
            print("=" * 55)
            print(f"  Seal: {SEAL}")
            print(f"  Entry: {ENTRY}")
            print(f"  Witness: {WITNESS}")
        return 0

    # Default: show policy status
    out = {
        "entry": ENTRY,
        "seal": SEAL,
        "witness": WITNESS,
        "policy": "full_width_no_truncation",
        "sha256_pattern": "64 hex chars",
        "sha512_pattern": "128 hex chars",
        "no_truncation": True,
        "no_ellipsis": True,
        "no_slicing": True,
    }
    if args.json:
        print(json.dumps(out, indent=2, default=str))
    else:
        print("🜁∀ DIGEST POLICY — Entry 8756")
        print("=" * 55)
        print(f"  Policy: {out['policy']}")
        print(f"  SHA-256: {out['sha256_pattern']}")
        print(f"  SHA-512: {out['sha512_pattern']}")
        print(f"  No truncation: {out['no_truncation']}")
        print("=" * 55)
        print(f"  Seal: {out['seal']}")
        print(f"  Entry: {out['entry']}")
        print(f"  Witness: {out['witness']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
