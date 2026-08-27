#!/usr/bin/env python3
"""Point at the evolving self-improvement path for the flywheel.

Offline (always):
  tests/test_trigger_excavate.py
  garden_surgery/trigger_excavate.py   — fingerprint Immutable/self_improvement_trigger.py
                                       without exec() and without MCP.

Live (needs FastAPI + a listener or TestClient):
  uvicorn fastapi_flywheel_gearbox:app --host 127.0.0.1 --port 8024
  python3 endpoint_smoke_test.py

Do not use trigger_excavate.golden_hash (SHA-256 hex[:16]) as a learner digest.
Learner digests are 64-hex SHA3-256.
"""

from __future__ import annotations

import math

from garden_surgery.trigger_excavate import diagnostic_scalars, kappa_decomposition
from endpoint_smoke_test import (
    EXPECTED_FIRING_DEG,
    EXPECTED_HEALTH,
    EXPECTED_STATUS,
    validate_health,
    validate_learner_hash,
    validate_status,
)

UVICORN_CMD = "uvicorn fastapi_flywheel_gearbox:app --host 127.0.0.1 --port 8024"
SMOKE_CMD = "python3 endpoint_smoke_test.py"


def test_self_improvement_is_excavation_not_exec():
    d = diagnostic_scalars()
    k = kappa_decomposition()
    assert d["k_eff"] > 0
    assert abs(k["reconstructed"] - 12.754) < 1e-12


def test_smoke_validators_accept_declared_payloads():
    assert validate_health({"status": "OK", "north_star": 71.975})
    assert validate_learner_hash({"learner_hash": "a" * 64})
    assert not validate_learner_hash({"learner_hash": "a" * 16})
    assert validate_status(dict(EXPECTED_STATUS))


def test_firing_cut_is_three_decimals_of_pi_over_phi():
    phi = (1 + 5**0.5) / 2
    deg = math.degrees(math.pi / phi)
    assert abs(deg - 111.24611797498106) < 1e-10
    assert abs(EXPECTED_FIRING_DEG - 111.246) < 1e-12
    assert EXPECTED_HEALTH["north_star"] == 71.975


def test_inprocess_flywheel_if_fastapi_present():
    try:
        from fastapi.testclient import TestClient
        from fastapi_flywheel_gearbox import app
    except ImportError:
        return
    client = TestClient(app)
    assert validate_health(client.get("/health").json())
    digest = client.get("/learner/hash", params={"text": "sovereign"}).json()
    assert validate_learner_hash(digest)
    assert validate_status(client.get("/sovereign/status").json())


if __name__ == "__main__":
    test_self_improvement_is_excavation_not_exec()
    test_smoke_validators_accept_declared_payloads()
    test_firing_cut_is_three_decimals_of_pi_over_phi()
    test_inprocess_flywheel_if_fastapi_present()
    print("test_flywheel_self_improvement: PASS")
    print("live:", UVICORN_CMD)
    print("live:", SMOKE_CMD)
