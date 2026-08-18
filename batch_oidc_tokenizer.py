#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch OIDC tokenizer server helpers.

Issues and verifies opaque batch tokens bound to the sovereign OIDC secret
policy: Phase-3 ephemeral digests are **full 64-char SHA-256** (never truncated).

Works offline without a live IdP — suitable for Garden agent JSONL / Grafana labels.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any, Dict, Iterable, List, Optional


def resolve_secret() -> str:
    try:
        from sovereign_engine import get_oidc_secret

        return get_oidc_secret()
    except Exception:
        import math
        import os

        env = os.environ.get("OIDC_CLIENT_SECRET", "")
        if env and len(env) > 10:
            return env
        phi = (1 + math.sqrt(5)) / 2
        seed = f"VENOMSUITE_EPHEMERAL_{int(time.time() / 3600)}_{phi}"
        return hashlib.sha256(seed.encode()).hexdigest()  # full 64


def mint_token(subject: str, claims: Optional[Dict[str, Any]] = None, ttl_s: int = 3600) -> Dict[str, Any]:
    secret = resolve_secret()
    assert len(secret) >= 32, "OIDC secret too short — refuse truncated digests"
    now = int(time.time())
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + int(ttl_s),
        "claims": claims or {},
        "secret_len": len(secret),
    }
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    sig = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()  # full 64
    return {"token": f"{body}.{sig}", "sig": sig, "secret_len": len(secret), "payload": payload}


def verify_token(token: str) -> Dict[str, Any]:
    secret = resolve_secret()
    try:
        body, sig = token.rsplit(".", 1)
    except ValueError:
        return {"ok": False, "error": "malformed"}
    expect = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expect):
        return {"ok": False, "error": "bad_signature", "secret_len": len(secret)}
    payload = json.loads(body)
    if int(time.time()) > int(payload.get("exp", 0)):
        return {"ok": False, "error": "expired", "payload": payload}
    return {"ok": True, "payload": payload, "secret_len": len(secret), "sig_len": len(sig)}


def batch_mint(subjects: Iterable[str], ttl_s: int = 3600) -> List[Dict[str, Any]]:
    return [mint_token(s, ttl_s=ttl_s) for s in subjects]


def main() -> None:
    tokens = batch_mint(["orchestrator", "clarke_yoursa_tee_worker", "grafana"])
    for t in tokens:
        v = verify_token(t["token"])
        print(t["payload"]["sub"], "secret_len=", t["secret_len"], "sig_len=", len(t["sig"]), "verify=", v["ok"])


if __name__ == "__main__":
    main()
