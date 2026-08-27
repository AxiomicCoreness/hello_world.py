"""October 39, 2025 as code — syntactic literal, not datetime. Full 64-hex digests."""
from __future__ import annotations
import hashlib, json
from typing import Any, Dict

YEAR, MONTH, DAY = 2025, 10, 39
TOKEN = "October 39, 2025"
DOMAIN = b"GARDEN.SYMBOL.v1\x00"

class October39Literal:
    __slots__ = ("year", "month", "day", "token")
    def __init__(self) -> None:
        self.year, self.month, self.day, self.token = YEAR, MONTH, DAY, TOKEN
    def as_dict(self) -> Dict[str, Any]:
        return {"year": self.year, "month": self.month, "day": self.day, "token": self.token}
    def canonical_json(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    def sha256(self) -> str:
        d = hashlib.sha256(DOMAIN + self.canonical_json().encode("utf-8")).hexdigest()
        if len(d) != 64:
            raise ValueError("sha256 must be 64 hex characters")
        return d
    def sha3_256(self) -> str:
        d = hashlib.sha3_256(DOMAIN + self.canonical_json().encode("utf-8")).hexdigest()
        if len(d) != 64:
            raise ValueError("sha3-256 must be 64 hex characters")
        return d

LITERAL = October39Literal()

def token_digest() -> str:
    return LITERAL.sha3_256()

def status() -> Dict[str, Any]:
    return {
        "year": YEAR, "month": MONTH, "day": DAY, "token": TOKEN,
        "kind": "syntactic_literal", "is_iso8601_date": False, "constructs_datetime": False,
        "sha256": LITERAL.sha256(), "sha3_256": LITERAL.sha3_256(),
        "digest_hex_length": 64, "witness_hash_truncated": False,
        "fusion_canonical": 515, "hyperion_preserved": 516,
    }
