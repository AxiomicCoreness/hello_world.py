"""Usable SHA3-256 for a machine learner. Full 64-hex. No truncation."""

from __future__ import annotations

import hashlib
import json
from typing import Any

DOMAIN = b"GARDEN.LEARNER.v1\x00"


def canonical_bytes(obj: Any) -> bytes:
    text = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return text.encode("utf-8")


def learner_sha3_256(obj: Any, *, domain: bytes = DOMAIN) -> str:
    digest = hashlib.sha3_256(domain + canonical_bytes(obj)).hexdigest()
    if len(digest) != 64:
        raise ValueError("sha3-256 digest must be 64 hex")
    return digest


def restart_fingerprint(bind: str = "127.0.0.1:8024") -> dict:
    payload = {
        "asgi": "app:app_main",
        "bind": bind,
        "fusion_canonical": 515,
        "hyperion_preserved": 516,
        "alpha_eff": 0.0,
        "daemon": False,
    }
    digest = learner_sha3_256(payload)
    payload["sha3_256"] = digest
    return payload
