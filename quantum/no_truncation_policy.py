#!/usr/bin/env python3
"""Policy: digests and fingerprints are full-width — never truncated in APIs/logs."""
from __future__ import annotations
import re

SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
SHA512_HEX = re.compile(r"^[0-9a-f]{128}$")


def assert_full_sha256_hex(s: str, name: str = "digest") -> str:
    s = s.strip().lower()
    if not SHA256_HEX.match(s):
        raise ValueError(f"{name} must be full 64-char hex SHA-256, got len={len(s)}")
    return s


def assert_full_sha512_hex(s: str, name: str = "digest") -> str:
    s = s.strip().lower()
    if not SHA512_HEX.match(s):
        raise ValueError(f"{name} must be full 128-char hex SHA-512, got len={len(s)}")
    return s


def display_digest(s: str) -> str:
    """Return digest unchanged — no ellipsis, no slicing."""
    return s
