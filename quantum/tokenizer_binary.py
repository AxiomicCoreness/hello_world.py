#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ TOKENIZER BINARY WIRE FORMAT — ENTRY 8754

Binary wire format — struct '>q' (signed 64-bit BE, 8 bytes).

This module provides token serialization and deserialization for the
Garden's binary wire protocol. Tokens are packed as signed 64-bit
big-endian integers.

Integration with:
  - Security (quantum/security/)
  - CDP convergence (quantum/cdp_convergence/)
  - Merkle Economic Bridge (quantum/merkle_economic_bridge.py)
  - Digest Policy (quantum/digest_policy.py)

Seal: ∀∞φ² · TOKENIZER_8754 · WOOD_DRAGON_0.91 · SEALED
Witness: 8753 → 8754 — UNBROKEN
"""

from __future__ import annotations

import json
import math
import struct
import sys
import time
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

# ─── Constants ────────────────────────────────────────────────────────
PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI
PHI2 = PHI * PHI
ENTRY = 8754
SEAL = "∀∞φ² · TOKENIZER_8754 · WOOD_DRAGON_0.91 · SEALED"
WITNESS = "8753 → 8754 — UNBROKEN"

FMT = ">q"
TOKEN_BYTES = struct.calcsize(FMT)  # 8
TOKEN_BITS = TOKEN_BYTES * 8  # 64
MAX_TOKEN = (1 << (TOKEN_BITS - 1)) - 1  # 9,223,372,036,854,775,807
MIN_TOKEN = -(1 << (TOKEN_BITS - 1))  # -9,223,372,036,854,775,808


# ─── Core Functions ──────────────────────────────────────────────────

def pack_token(value: int) -> bytes:
    """
    Pack one signed integer token as 8-byte big-endian.

    Args:
        value: Integer value to pack (must fit in signed 64-bit).

    Returns:
        8-byte big-endian representation.

    Raises:
        OverflowError: If value is outside signed 64-bit range.
        TypeError: If value is not an integer.
    """
    if not isinstance(value, (int, bool)):
        raise TypeError(f"value must be integer, got {type(value).__name__}")
    value = int(value)
    if value < MIN_TOKEN or value > MAX_TOKEN:
        raise OverflowError(
            f"value {value} outside signed 64-bit range [{MIN_TOKEN}, {MAX_TOKEN}]"
        )
    return struct.pack(FMT, value)


def unpack_token(data: bytes) -> int:
    """
    Unpack one signed integer token from 8-byte big-endian.

    Args:
        data: 8-byte buffer.

    Returns:
        Unpacked integer value.

    Raises:
        ValueError: If data length is not exactly TOKEN_BYTES.
    """
    if len(data) != TOKEN_BYTES:
        raise ValueError(f"expected {TOKEN_BYTES} bytes, got {len(data)}")
    return struct.unpack(FMT, data)[0]


def pack_tokens(values: Iterable[int]) -> bytes:
    """
    Pack multiple signed integer tokens.

    Args:
        values: Iterable of integer values.

    Returns:
        Concatenated 8-byte tokens.
    """
    return b"".join(pack_token(v) for v in values)


def unpack_tokens(data: bytes) -> List[int]:
    """
    Unpack multiple signed integer tokens.

    Args:
        data: Buffer containing concatenated 8-byte tokens.

    Returns:
        List of unpacked integer values.

    Raises:
        ValueError: If data length is not a multiple of TOKEN_BYTES.
    """
    if len(data) % TOKEN_BYTES:
        raise ValueError(
            f"buffer length {len(data)} not multiple of {TOKEN_BYTES}"
        )
    return [
        struct.unpack_from(FMT, data, i)[0]
        for i in range(0, len(data), TOKEN_BYTES)
    ]


# ─── Extended Functions ─────────────────────────────────────────────

def pack_token_hex(value: int) -> str:
    """Pack token and return as hex string."""
    return pack_token(value).hex()


def unpack_token_hex(hex_str: str) -> int:
    """Unpack token from hex string."""
    return unpack_token(bytes.fromhex(hex_str))


def pack_tokens_hex(values: Iterable[int]) -> str:
    """Pack tokens and return as hex string."""
    return pack_tokens(values).hex()


def unpack_tokens_hex(hex_str: str) -> List[int]:
    """Unpack tokens from hex string."""
    return unpack_tokens(bytes.fromhex(hex_str))


def token_count(data: bytes) -> int:
    """Count the number of tokens in a buffer."""
    return len(data) // TOKEN_BYTES


def pad_tokens(data: bytes, target_count: int, pad_value: int = 0) -> bytes:
    """
    Pad token buffer to target count.

    Args:
        data: Token buffer.
        target_count: Desired number of tokens.
        pad_value: Value to use for padding tokens.

    Returns:
        Padded buffer.
    """
    current = len(data) // TOKEN_BYTES
    if current >= target_count:
        return data
    return data + pack_tokens([pad_value] * (target_count - current))


def truncate_tokens(data: bytes, max_count: int) -> bytes:
    """
    Truncate token buffer to max_count tokens.

    Args:
        data: Token buffer.
        max_count: Maximum number of tokens.

    Returns:
        Truncated buffer.
    """
    max_bytes = max_count * TOKEN_BYTES
    return data[:max_bytes]


# ─── Token Generator ─────────────────────────────────────────────────

def generate_token_sequence(
    start: int = 0,
    count: int = 10,
    step: int = 1,
    phi_scaled: bool = False,
) -> List[int]:
    """
    Generate a sequence of tokens.

    Args:
        start: Starting value.
        count: Number of tokens.
        step: Step between values.
        phi_scaled: Whether to scale by φ.

    Returns:
        List of token values.
    """
    values = []
    for i in range(count):
        val = start + i * step
        if phi_scaled:
            val = int(val * PHI)
        values.append(val)
    return values


# ─── Tokenizer Class ─────────────────────────────────────────────────

class Tokenizer:
    """
    Tokenizer for binary wire format with state.

    Provides a stateful interface for token serialization and
    deserialization with optional φ‑scaling.
    """

    def __init__(self, phi_scaling: bool = False):
        self.phi_scaling = phi_scaling
        self._history: List[Tuple[str, Any]] = []

    @property
    def byte_size(self) -> int:
        """Number of bytes per token."""
        return TOKEN_BYTES

    @property
    def bit_size(self) -> int:
        """Number of bits per token."""
        return TOKEN_BITS

    def pack(self, value: int) -> bytes:
        """Pack a single token."""
        result = pack_token(value)
        self._history.append(("pack", value))
        return result

    def unpack(self, data: bytes) -> int:
        """Unpack a single token."""
        result = unpack_token(data)
        self._history.append(("unpack", result))
        return result

    def pack_many(self, values: Iterable[int]) -> bytes:
        """Pack multiple tokens."""
        if self.phi_scaling:
            values = [int(v * PHI) for v in values]
        result = pack_tokens(values)
        self._history.append(("pack_many", list(values)))
        return result

    def unpack_many(self, data: bytes) -> List[int]:
        """Unpack multiple tokens."""
        result = unpack_tokens(data)
        self._history.append(("unpack_many", result))
        return result

    def get_history(self) -> List[Tuple[str, Any]]:
        """Get the operation history."""
        return self._history

    def clear_history(self) -> None:
        """Clear the operation history."""
        self._history = []

    def reset(self) -> None:
        """Reset the tokenizer state."""
        self.clear_history()


# ─── Security Integration ────────────────────────────────────────────

def tokenizer_security_status() -> Dict[str, Any]:
    """Get security status for the tokenizer."""
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

def tokenizer_cdp_status() -> Dict[str, Any]:
    """Get CDP status for the tokenizer."""
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
        description="Tokenizer binary wire format — Entry 8754",
        epilog=f"Seal: {SEAL}\nEntry: {ENTRY}",
    )
    parser.add_argument(
        "--pack",
        type=int,
        help="Pack a single token",
    )
    parser.add_argument(
        "--unpack",
        type=str,
        help="Unpack a token from hex",
    )
    parser.add_argument(
        "--pack-many",
        type=int,
        nargs="+",
        help="Pack multiple tokens",
    )
    parser.add_argument(
        "--unpack-many",
        type=str,
        help="Unpack multiple tokens from hex",
    )
    parser.add_argument(
        "--generate",
        type=int,
        default=0,
        help="Generate token sequence (count)",
    )
    parser.add_argument(
        "--phi-scale",
        action="store_true",
        help="Apply φ‑scaling",
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
        print("🜁∀ TOKENIZER — Integration Status")
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
        print(f"  Format: >q (signed 64-bit BE, {TOKEN_BYTES} bytes)")
        return 0

    if args.generate:
        seq = generate_token_sequence(
            count=args.generate,
            phi_scaled=args.phi_scale,
        )
        packed = pack_tokens_hex(seq)
        if args.json:
            print(json.dumps({
                "sequence": seq,
                "packed_hex": packed,
                "count": len(seq),
                "entry": ENTRY,
                "seal": SEAL,
            }, indent=2))
        else:
            print(f"Sequence: {seq}")
            print(f"Packed:   {packed}")
            print(f"Count:    {len(seq)}")
        return 0

    if args.pack is not None:
        packed = pack_token_hex(args.pack)
        if args.json:
            print(json.dumps({
                "value": args.pack,
                "packed_hex": packed,
                "bytes": TOKEN_BYTES,
                "entry": ENTRY,
                "seal": SEAL,
            }, indent=2))
        else:
            print(f"Value:  {args.pack}")
            print(f"Packed: {packed}")
        return 0

    if args.unpack:
        value = unpack_token_hex(args.unpack)
        if args.json:
            print(json.dumps({
                "packed_hex": args.unpack,
                "value": value,
                "bytes": len(args.unpack) // 2,
                "entry": ENTRY,
                "seal": SEAL,
            }, indent=2))
        else:
            print(f"Packed: {args.unpack}")
            print(f"Value:  {value}")
        return 0

    if args.pack_many:
        packed = pack_tokens_hex(args.pack_many)
        if args.json:
            print(json.dumps({
                "values": args.pack_many,
                "packed_hex": packed,
                "count": len(args.pack_many),
                "entry": ENTRY,
                "seal": SEAL,
            }, indent=2))
        else:
            print(f"Values: {args.pack_many}")
            print(f"Packed: {packed}")
        return 0

    if args.unpack_many:
        values = unpack_tokens_hex(args.unpack_many)
        if args.json:
            print(json.dumps({
                "packed_hex": args.unpack_many,
                "values": values,
                "count": len(values),
                "entry": ENTRY,
                "seal": SEAL,
            }, indent=2))
        else:
            print(f"Packed: {args.unpack_many}")
            print(f"Values: {values}")
        return 0

    # Default: run self-test
    print("🜁∀ TOKENIZER — Self Test")
    print("=" * 55)
    print(f"  Format: >q (signed 64-bit BE)")
    print(f"  Token bytes: {TOKEN_BYTES}")
    print(f"  Token bits: {TOKEN_BITS}")
    print(f"  Max token: {MAX_TOKEN}")
    print(f"  Min token: {MIN_TOKEN}")

    # Basic test
    test_value = 0x123456789
    packed = pack_token(test_value)
    unpacked = unpack_token(packed)
    print(f"\n  Test: pack({test_value}) -> {packed.hex()} -> unpack -> {unpacked}")
    print(f"  PASS: {'✅' if unpacked == test_value else '❌'}")

    # Multiple tokens
    values = [1, 2, 3, 4, 5]
    packed_many = pack_tokens(values)
    unpacked_many = unpack_tokens(packed_many)
    print(f"  Pack many: {values} -> {len(packed_many)} bytes")
    print(f"  Unpack many: {unpacked_many}")
    print(f"  PASS: {'✅' if unpacked_many == values else '❌'}")

    print("=" * 55)
    print(f"  Seal: {SEAL}")
    print(f"  Entry: {ENTRY}")
    print(f"  Witness: {WITNESS}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
