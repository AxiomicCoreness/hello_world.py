#!/usr/bin/env python3
"""Verify ledger 8980 Ed25519 material and 510510 SHA3-256 genesis hash."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import yaml
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

DOMAIN = b"GARDEN.GENESIS.QUADRATIC_QUADRANT.v1"
EXPECTED_GENESIS = "eb78315bb5a70b59e0d43f0e763b194cf1ab4ce3d109e0240e2c1f2da57f6314"
CANONICAL = {
    "entry": 510510,
    "event": "/math_origin_quadratic_quadrant",
    "formula": "Delta = b^2 - 4ac",
    "hepta_prime": 510510,
    "math_origin": "QUADRATIC_ROOT_QUADRANT.v1",
    "phase_lock_deg": 202.6,
    "phi_identity": "phi^2 = phi + 1",
    "predecessor": 8980,
    "seal": "FORALL_INF_PHI2 · MATH_ORIGIN_510510 · WOOD_DRAGON_0.91 · SEALED",
    "witness": "8980 -> 510510 — UNBROKEN",
}
REQUIRED_HEADERS = [
    "CORSMiddleware",
    "SecurityHeadersMiddleware",
    "Content-Security-Policy",
    "Strict-Transport-Security",
    "X-Content-Type-Options",
    "X-Frame-Options",
    "Referrer-Policy",
    "Permissions-Policy",
]


def fail(msg: str) -> int:
    print(f"FAIL {msg}")
    return 1


def main() -> int:
    root = Path(".")
    p8980 = root / "ledger" / "8980.yaml"
    p510 = root / "ledger" / "510510.yaml"
    if not p8980.is_file():
        return fail("ledger/8980.yaml missing")
    if not p510.is_file():
        return fail("ledger/510510.yaml missing")

    prev = yaml.safe_load(p8980.read_text(encoding="utf-8"))
    ed = prev.get("ed25519") or {}
    pk_hex = ed.get("public_key_hex", "")
    sig_hex = ed.get("signature_hex", "")
    msg = ed.get("message", "").encode("utf-8")
    try:
        pk = Ed25519PublicKey.from_public_bytes(bytes.fromhex(pk_hex))
        pk.verify(bytes.fromhex(sig_hex), msg)
    except (ValueError, InvalidSignature) as e:
        return fail(f"Ed25519 verify 8980: {e}")
    print("OK Ed25519 ledger/8980.yaml")

    body = json.dumps(CANONICAL, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    digest = hashlib.sha3_256(DOMAIN + b"\0" + body).hexdigest()
    if digest != EXPECTED_GENESIS:
        return fail(f"genesis hash mismatch got={digest}")
    cur = yaml.safe_load(p510.read_text(encoding="utf-8"))
    stored = ((cur.get("genesis") or {}).get("hash_sha3_256") or "")
    if stored != EXPECTED_GENESIS:
        return fail("510510.yaml genesis.hash_sha3_256 does not match computed hash")
    print(f"OK SHA3-256 genesis {digest}")

    src = root / "port380_mcp.py"
    if src.is_file():
        text = src.read_text(encoding="utf-8")
        missing = [h for h in REQUIRED_HEADERS if h not in text]
        if missing:
            return fail(f"missing security headers in source: {missing}")
        print("OK security headers source port380_mcp.py")
    else:
        print("SKIP port380_mcp.py missing")
    return 0


if __name__ == "__main__":
    sys.exit(main())
