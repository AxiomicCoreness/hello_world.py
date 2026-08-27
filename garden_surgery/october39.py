"""October 39 2025 is a legend token, not an ISO calendar date."""
from __future__ import annotations
import hashlib
TOKEN = "October 39 2025"
TOKEN_KIND = "english_legend"
ISO_DATE = False

def token_digest() -> str:
    return hashlib.sha3_256(b"GARDEN.SYMBOL.v1\x00" + TOKEN.encode("utf-8")).hexdigest()

def status():
    return {
        "token": TOKEN,
        "kind": TOKEN_KIND,
        "is_iso8601_date": ISO_DATE,
        "october_has_31_days": True,
        "digest_sha3_256": token_digest(),
        "fusion_canonical": 515,
        "hyperion_preserved": 516,
        "calendar_rewritten": False,
    }
