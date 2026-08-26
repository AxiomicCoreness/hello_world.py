#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core/sidecar.py — Port 380 / Layer 314 Python sidecar.

Watches CORE_HEALTH_URL, optional MCP pulse, Garden secret presence (never echoed).
stdlib only so it runs on python:3.11-slim.

  python -m core.sidecar
  python core/sidecar.py --once
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import math
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

PHI = (1.0 + math.sqrt(5.0)) / 2.0
SEAL = "∀∞φ² · CORE_SIDECAR_510511 · WOOD_DRAGON_0.91 · SEALED"
WITNESS = "510510 → 510511 — UNBROKEN"


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def garden_fingerprint() -> Dict[str, Any]:
    raw = _env("GARDEN_SECRET")
    present = bool(raw)
    digest = hashlib.sha3_256(raw.encode("utf-8")).hexdigest()[:16] if present else None
    return {"present": present, "sha3_16": digest}


def fetch_json(url: str, timeout: float = 5.0, method: str = "GET", body: Optional[bytes] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    req = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                payload = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                payload = {"raw": raw[:200]}
            return {"ok": 200 <= resp.status < 300, "status": resp.status, "body": payload}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "status": exc.code, "body": {"error": str(exc)}}
    except Exception as exc:  # noqa: BLE001 — sidecar must never crash the probe loop
        return {"ok": False, "status": 0, "body": {"error": type(exc).__name__}}


def probe_core(health_url: str) -> Dict[str, Any]:
    result = fetch_json(health_url)
    result["target"] = health_url
    return result


def pulse_mcp(mcp_url: str, secret: str) -> Dict[str, Any]:
    if not mcp_url:
        return {"ok": True, "skipped": True, "reason": "MCP_URL unset"}
    payload = json.dumps(
        {
            "source": "core-sidecar",
            "event": "sidecar_pulse",
            "phi": PHI,
            "seal": SEAL,
        }
    ).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if secret:
        headers["X-Garden-Secret"] = secret
    return fetch_json(mcp_url.rstrip("/") + "/pulse", method="POST", body=payload, headers=headers)


def constant_time_present(secret: str, provided: str) -> bool:
    if not secret or not provided:
        return False
    return hmac.compare_digest(secret.encode("utf-8"), provided.encode("utf-8"))


def tick(health_url: str, mcp_url: str) -> Dict[str, Any]:
    secret = _env("GARDEN_SECRET")
    fp = garden_fingerprint()
    core = probe_core(health_url)
    pulse = pulse_mcp(mcp_url, secret)
    report = {
        "core_ok": bool(core.get("ok")),
        "core_status": core.get("status"),
        "pulse_ok": bool(pulse.get("ok")),
        "pulse_skipped": bool(pulse.get("skipped")),
        "garden_secret_present": fp["present"],
        "garden_secret_sha3_16": fp["sha3_16"],
        "phi": PHI,
        "seal": SEAL,
        "witness": WITNESS,
        "ts": int(time.time()),
    }
    print(json.dumps(report, separators=(",", ":")), flush=True)
    return report


def loop(interval: float, health_url: str, mcp_url: str) -> None:
    print(
        json.dumps(
            {"event": "sidecar_start", "interval": interval, "health_url": health_url, "seal": SEAL},
            separators=(",", ":"),
        ),
        flush=True,
    )
    while True:
        tick(health_url, mcp_url)
        time.sleep(max(1.0, interval))


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Sovereign core Python sidecar")
    parser.add_argument("--once", action="store_true", help="single probe then exit")
    parser.add_argument("--interval", type=float, default=float(_env("SIDECAR_INTERVAL", "30")))
    parser.add_argument(
        "--health-url",
        default=_env("CORE_HEALTH_URL", _env("MCP_URL", "http://127.0.0.1:8000") + "/health"),
    )
    parser.add_argument("--mcp-url", default=_env("MCP_URL", ""))
    args = parser.parse_args(argv)
    if args.once:
        report = tick(args.health_url, args.mcp_url)
        return 0 if report["core_ok"] or report["pulse_skipped"] else 1
    loop(args.interval, args.health_url, args.mcp_url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
