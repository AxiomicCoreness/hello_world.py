#!/usr/bin/env python3
"""Timesecret — temporal nonce locked to domain-separated Merkle layer."""
from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone

DOMAIN = b"GARDEN.TIMESECRET.v1"

def mint_timesecret(parent_root: str, layer: int = 329) -> dict:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = {"layer": layer, "parent_root": parent_root, "timestamp": ts}
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    nonce = hashlib.sha256(DOMAIN + b"\0" + body).hexdigest()
    assert len(nonce) == 64
    return {"nonce": nonce, "timestamp": ts, "layer": layer, "parent_root": parent_root}

if __name__ == "__main__":
    r = mint_timesecret("c5c7646295eec7c88fb00aa6a3f384afdc04c679e6abb31954c8d0cd54fba3dc")
    print(r["nonce"])
