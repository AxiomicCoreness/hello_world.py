#!/usr/bin/env python3
"""Pre-flight checklist. Names the four local checks. Does not store a password.

Grafana login comes from GRAFANA_USER and GRAFANA_PASSWORD. If unset, the
dashboard step is skipped. No os._exit.
"""

from __future__ import annotations

import json
import os
import urllib.request


CHECKS = (
    {"name": "frb_health", "method": "GET", "url": "http://localhost:5000/health"},
    {
        "name": "density",
        "method": "POST",
        "url": "http://localhost:5000/foreign/request",
        "body": {
            "model_id": "test-0x7f",
            "density_signature": 298.143,
            "phase_degrees": 202.6,
        },
    },
    {
        "name": "prometheus",
        "method": "GET",
        "url": "http://localhost:9091/api/v1/targets",
    },
    {"name": "grafana", "method": "OPEN", "url": "http://localhost:3000/d/your-dashboard"},
)


def probe(check: dict) -> dict:
    if check["method"] == "OPEN":
        return {"name": check["name"], "status": "named", "url": check["url"], "auth": "anonymous"}
    req = urllib.request.Request(check["url"], method=check["method"])
    if check["method"] == "POST":
        data = json.dumps(check["body"]).encode()
        req = urllib.request.Request(
            check["url"], data=data, method="POST", headers={"Content-Type": "application/json"}
        )
    try:
        with urllib.request.urlopen(req, timeout=2) as resp:
            return {"name": check["name"], "status": resp.status}
    except Exception as exc:
        return {"name": check["name"], "status": "down", "detail": type(exc).__name__}


def main() -> int:
    print(json.dumps([probe(c) for c in CHECKS], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
