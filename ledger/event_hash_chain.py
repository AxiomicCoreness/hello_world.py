"""Untruncated SHA3-256 witness chain.

witness_prefix (16 hex) is a label only. Integrity is the full 64-hex SHA3-256.
SHA3-256 does not degrade at 10^6 entries. Collision work is ~2^128.
"""
from __future__ import annotations

import hashlib
from typing import Optional

DOMAIN = b"GARDEN.EVENT.v1"
HEX_LEN = 64  # 256 bits, untruncated
PREFIX_LEN = 16  # label only — not integrity


def sha3_256_hex(payload: bytes) -> str:
    digest = hashlib.sha3_256(payload).hexdigest()
    if len(digest) != HEX_LEN:
        raise ValueError("truncated digest rejected")
    return digest


def event_digest(index: str, event: str, phi2: str, theta: str, prev_hex: Optional[str] = None) -> str:
    body = f"{index}|{event}|phi2={phi2}|delta=b^2-4ac|theta={theta}"
    if prev_hex:
        if len(prev_hex) != HEX_LEN:
            raise ValueError("prev hash must be untruncated 64 hex")
        body = f"{index}|{event}|prev={prev_hex}|phi2={phi2}|delta=b^2-4ac|theta={theta}"
    return sha3_256_hex(DOMAIN + b"\x00" + body.encode("utf-8"))


def prefix_label(full_hex: str) -> str:
    """Display slice only. Never use as the stored witness."""
    return full_hex[:PREFIX_LEN]
