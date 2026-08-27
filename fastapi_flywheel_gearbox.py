#!/usr/bin/env python3
"""
fastapi_flywheel_gearbox.py
============================
FastAPI Flywheel Dimension Gearbox
- Flywheel: persistent uvicorn process with restart fingerprint
- Dimension: 12D φ-harmonic routing
- Gearbox: before_main() restart sequence + SHA3-256 learner hash

ASGI: uvicorn fastapi_flywheel_gearbox:app --host 127.0.0.1 --port 8024
Does not rewrite app:app_main. Does not rewrite ledger 9077.
"""

import os
import json
import hashlib
import time
from typing import Dict, Any, Optional

try:
    from fastapi import FastAPI, Query, HTTPException
except ImportError:
    raise ImportError("FastAPI not installed. Run: pip install fastapi uvicorn")

import uvicorn

PHI = (1 + 5 ** 0.5) / 2
PHI_INV = 1 / PHI
NORTH_STAR_FREQ = 71.975
FROZEN_PID_ERROR = 0.000350
NULL_BAN_SIGMA = 12
RESTART_FINGERPRINT = "a54bff616fc2d5be09240a2c375e7c25b1a2c6020736e51254c3840b1778b556"


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def sha3_256_hex(data: Any) -> str:
    """Full 64-hex SHA3-256 of canonical JSON."""
    if isinstance(data, (dict, list, tuple, str, int, float, bool)):
        data = canonical_json(data)
    else:
        data = str(data)
    digest = hashlib.sha3_256(data.encode("utf-8")).hexdigest()
    assert len(digest) == 64, "SHA3-256 digest must be 64 hex characters"
    return digest


def learner_hash(text: str, domain: str = "GARDEN.LEARNER.v1\x00") -> str:
    payload = {"domain": domain, "text": text, "timestamp": time.time()}
    return sha3_256_hex(payload)


def restart_fingerprint() -> str:
    return RESTART_FINGERPRINT


def before_main() -> dict:
    return {"restart_fingerprint": restart_fingerprint()}


app = FastAPI(title="Sovereign Garden — Flywheel Gearbox", version="0.1.0")


@app.get("/health")
async def health():
    return {"status": "OK", "north_star": NORTH_STAR_FREQ}


@app.get("/learner/hash")
async def learner_hash_route(text: str = Query(..., min_length=1, max_length=2048)):
    return {"learner_hash": learner_hash(text)}


@app.get("/sovereign/status")
async def sovereign_status():
    return {
        "coherence": 1.0,
        "entropy": 0.0,
        "workload": 0.0,
        "null_ban_sigma": NULL_BAN_SIGMA,
        "pid_error": FROZEN_PID_ERROR,
        "firing_phase_deg": 111.246,
    }


class Gearbox:
    def __init__(self):
        self.routes = {
            "/health": PHI_INV,
            "/learner/hash": PHI_INV ** 2,
            "/sovereign/status": PHI_INV ** 3,
        }

    def get_priority(self, path: str) -> float:
        return self.routes.get(path, PHI_INV ** 4)


if __name__ == "__main__":
    print("before_main():", before_main())
    print("Starting uvicorn on 127.0.0.1:8024")
    uvicorn.run(app, host="127.0.0.1", port=8024, log_level="info")
