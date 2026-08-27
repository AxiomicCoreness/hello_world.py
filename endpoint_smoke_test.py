#!/usr/bin/env python3
"""
endpoint_smoke_test.py
======================
Smoke test for fastapi_flywheel_gearbox.py

Usage:
  python endpoint_smoke_test.py [--base-url http://127.0.0.1:8024]
"""

import sys
import json
import argparse
import urllib.request
import urllib.error

NORTH_STAR_FREQ = 71.975
FROZEN_PID_ERROR = 0.000350
NULL_BAN_SIGMA = 12
EXPECTED_FIRING_DEG = 111.246

EXPECTED_HEALTH = {
    "status": "OK",
    "north_star": NORTH_STAR_FREQ,
}

EXPECTED_STATUS = {
    "coherence": 1.0,
    "entropy": 0.0,
    "workload": 0.0,
    "null_ban_sigma": NULL_BAN_SIGMA,
    "pid_error": FROZEN_PID_ERROR,
    "firing_phase_deg": EXPECTED_FIRING_DEG,
}


def validate_health(payload: dict) -> bool:
    return payload.get("status") == EXPECTED_HEALTH["status"] and abs(
        payload.get("north_star", 0) - EXPECTED_HEALTH["north_star"]
    ) < 1e-6


def validate_learner_hash(payload: dict) -> bool:
    digest = payload.get("learner_hash")
    return isinstance(digest, str) and len(digest) == 64 and all(
        c in "0123456789abcdef" for c in digest
    )


def validate_status(payload: dict) -> bool:
    for key, expected in EXPECTED_STATUS.items():
        actual = payload.get(key)
        if isinstance(expected, float):
            if abs(actual - expected) > 1e-6:
                return False
        elif actual != expected:
            return False
    return True


def fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=5) as resp:
        return json.loads(resp.read().decode("utf-8"))


def run_check(name: str, url: str, validator) -> bool:
    try:
        payload = fetch_json(url)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        print(f"FAIL {name}: request failed - {e}")
        return False
    if not validator(payload):
        print(f"FAIL {name}: validation failed - got {payload}")
        return False
    print(f"PASS {name}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8024")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    checks = [
        ("health", f"{base}/health", validate_health),
        ("learner/hash", f"{base}/learner/hash?text=sovereign", validate_learner_hash),
        ("sovereign/status", f"{base}/sovereign/status", validate_status),
    ]
    all_pass = True
    for name, url, validator in checks:
        if not run_check(name, url, validator):
            all_pass = False
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
