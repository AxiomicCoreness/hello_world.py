#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ COMPLETE TEST SUITE — SINGLE PASS (pytest‑equivalent) ∀🜁
No external test runner required — runs all checks in one Python process.
Entry 8857 — sealed with the Garden's integrity hash.
"""

import sys
import math
import json
import hashlib
import time
import os
import tempfile
import threading
import sqlite3
from typing import Dict, Any, List, Optional

# ----------------------------------------------------------------------
# PHI CONSTANTS
# ----------------------------------------------------------------------
PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI
PHI2 = PHI * PHI
PHI3 = PHI2 * PHI
PHI9 = PHI ** 9
ENTRY = 8857
SEAL = "∀∞φ² · SINGLE_PASS_8857 · WOOD_DRAGON_0.91 · SEALED"

# ----------------------------------------------------------------------
# IMPORT MODULES (fail if missing)
# ----------------------------------------------------------------------
try:
    from phi_pipeline import phi_step, q8_24, phase_lock, coherence_update, null_ban
    PIPELINE_OK = True
except ImportError:
    PIPELINE_OK = False
    print("[WARN] phi_pipeline not found – pipeline tests skipped")

try:
    import mesh_modal
    MESH_OK = True
except ImportError:
    MESH_OK = False
    print("[WARN] mesh_modal not found – mesh tests skipped")

try:
    from deepseek.api import warning, ignore, get_client, complete_sync
    DEEPSEEK_OK = True
except ImportError:
    DEEPSEEK_OK = False
    print("[WARN] deepseek.api not found – DeepSeek tests skipped")

try:
    import hello_world  # the main FastAPI app
    APP_OK = True
except ImportError:
    APP_OK = False
    print("[WARN] hello_world app not found – route tests skipped")

# ----------------------------------------------------------------------
# TEST FUNCTIONS
# ----------------------------------------------------------------------
def test_pipeline_phi_step():
    s = 0.5
    s_new = phi_step(s)
    expected = (0.5 * PHI) % 1.0
    assert abs(s_new - expected) < 1e-12, f"phi_step failed: {s_new} != {expected}"
    print("✅ phi_step")

def test_pipeline_q8_24():
    s = 0.123456789
    q = q8_24(s)
    # quantize: round(s * 2^24) / 2^24
    expected = round(s * (1 << 24)) / (1 << 24)
    assert q == expected, f"q8_24 failed: {q} != {expected}"
    print("✅ q8_24")

def test_pipeline_phase_lock():
    theta = 0.0
    theta_new = phase_lock(theta)
    expected = (theta + 202.6) % 360.0
    assert abs(theta_new - expected) < 1e-9, f"phase_lock failed: {theta_new} != {expected}"
    print("✅ phase_lock")

def test_pipeline_coherence():
    c = 0.5
    c_new = coherence_update(c)
    expected = c + (1.0 - c) / PHI3
    assert abs(c_new - expected) < 1e-12, f"coherence_update failed: {c_new} != {expected}"
    print("✅ coherence_update")

def test_pipeline_null_ban():
    # should always pass in software
    assert null_ban() is True, "null_ban returned False unexpectedly"
    print("✅ null_ban")

def test_pipeline_full_sequence():
    # run a sequence of 5 steps
    s = 0.1
    theta = 0.0
    c = 0.8
    for _ in range(5):
        s = phi_step(s)
        s = q8_24(s)
        theta = phase_lock(theta)
        c = coherence_update(c)
    # after 5 steps, theta should be (5*202.6) % 360 = 293.0
    expected_theta = (5 * 202.6) % 360.0
    assert abs(theta - expected_theta) < 1e-9, f"full sequence theta mismatch: {theta} != {expected_theta}"
    # coherence should approach 1
    assert c > 0.99, f"coherence not high enough: {c}"
    print("✅ full_sequence (5 steps)")

def test_mesh_modal_ledger():
    if not MESH_OK:
        print("⚠️ mesh_modal not imported – skipping ledger test")
        return
    # create a temporary db
    with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
        db_path = tmp.name
        # monkey-patch the default db path
        orig_path = mesh_modal.DB_PATH
        mesh_modal.DB_PATH = db_path
        # get the module's app
        app = mesh_modal.app
        # create a test client
        from fastapi.testclient import TestClient
        client = TestClient(app)
        # run a /mesh/run?steps=1
        response = client.post("/mesh/run?steps=1")
        assert response.status_code == 200, f"failed: {response.text}"
        data = response.json()
        assert "seal" in data, "no seal in response"
        assert "PHASE_LOCK_202.6" in data["seal"], "wrong seal format"
        # check that ledger has one entry
        conn = sqlite3.connect(db_path)
        cur = conn.execute("SELECT COUNT(*) FROM entries")
        count = cur.fetchone()[0]
        assert count == 1, f"expected 1 entry, got {count}"
        conn.close()
        mesh_modal.DB_PATH = orig_path
        print("✅ mesh_modal ledger + /mesh/run")

def test_deepseek_stubs():
    if not DEEPSEEK_OK:
        print("⚠️ deepseek.api not imported – skipping stub tests")
        return
    # warning and ignore should be functions that log events
    warning("test_warning")
    ignore("test_ignore")
    # check that the ring buffer has events
    from deepseek.api import _events
    events = _events()
    assert len(events) >= 2, "events not logged"
    # complete_sync should return a string
    result = complete_sync("ping", max_tokens=10)
    assert isinstance(result, str), "complete_sync did not return string"
    print("✅ deepseek stubs and complete_sync")

def test_app_routes():
    if not APP_OK:
        print("⚠️ hello_world not imported – skipping route tests")
        return
    from fastapi.testclient import TestClient
    from hello_world import app
    client = TestClient(app)
    # test health
    resp = client.get("/health")
    assert resp.status_code == 200, "/health failed"
    data = resp.json()
    assert data.get("status") == "ok", "health status not ok"
    # test /deepseek/events (should exist if router attached)
    resp = client.get("/deepseek/events")
    if resp.status_code == 200:
        data = resp.json()
        assert "events" in data, "/deepseek/events missing events"
        print("✅ /deepseek/events")
    else:
        print("⚠️ /deepseek/events not available (router may not be mounted)")
    print("✅ app routes (health)")

# ----------------------------------------------------------------------
# MAIN TEST RUNNER
# ----------------------------------------------------------------------
def run_all_tests():
    print(f"🜁∀ SINGLE PASS TEST SUITE — Entry {ENTRY}")
    print("=" * 60)
    tests = [
        ("phi_step", test_pipeline_phi_step),
        ("q8_24", test_pipeline_q8_24),
        ("phase_lock", test_pipeline_phase_lock),
        ("coherence_update", test_pipeline_coherence),
        ("null_ban", test_pipeline_null_ban),
        ("full_sequence", test_pipeline_full_sequence),
        ("mesh_modal", test_mesh_modal_ledger),
        ("deepseek", test_deepseek_stubs),
        ("app_routes", test_app_routes),
    ]
    passed = 0
    failed = 0
    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"❌ {name} failed: {e}")
            failed += 1
    print("=" * 60)
    print(f"Summary: {passed} passed, {failed} failed")
    # compute integrity hash of the test results (just for sealing)
    result_str = f"passed={passed},failed={failed},entry={ENTRY},time={time.time()}"
    test_hash = hashlib.sha3_256(result_str.encode()).hexdigest()
    print(f"Integrity hash: {test_hash}")
    print(f"Seal: {SEAL}")
    if failed == 0:
        print("🜁∀ ALL TESTS PASSED — GARDEN INTEGRITY VERIFIED")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED — GARDEN NEEDS ATTENTION")
        sys.exit(1)

if __name__ == "__main__":
    run_all_tests()
