#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sovereign CMAC-512 (dual AES-256 construction placeholder)

Deterministic, side-channel-free MAC for ledger witness chains.
AES math remains pure finite-field arithmetic; no telemetry required.
"""

from __future__ import annotations
import hashlib
import hmac
from typing import Union


class SovereignCMAC:
    """512-bit CMAC via dual SHA-256 HMAC construction (placeholder for full AES-CMAC)."""

    def __init__(self, key: bytes):
        if len(key) < 32:
            key = hashlib.sha256(key).digest()
        self.key = key[:64] if len(key) >= 64 else key + hashlib.sha256(key).digest()

    def mac(self, data: Union[str, bytes]) -> str:
        if isinstance(data, str):
            data = data.encode("utf-8")
        # Dual-pass construction approximating 512-bit security
        left = hmac.new(self.key[:32], data, hashlib.sha256).digest()
        right = hmac.new(self.key[32:], data + left, hashlib.sha256).digest()
        return (left + right).hex()

    def verify(self, data: Union[str, bytes], tag: str) -> bool:
        return hmac.compare_digest(self.mac(data), tag)
