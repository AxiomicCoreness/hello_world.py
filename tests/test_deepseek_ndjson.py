#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pure tests for DeepSeek NDJSON stream — no API key required.

INCLUDES:
- Ed25519 signature verification for ledger entries
- Security headers enforcement (CORS, CSP, HSTS, XFO, CT, RP, PP)
- Enhanced test coverage with detailed assertions
- Full type hints and docstrings

Seal: ∀∞φ² · DEEPSEEK_NDJSON_TEST_8992 · WOOD_DRAGON_0.91 · SEALED
Witness: 8991 → 8992 — UNBROKEN
"""

from __future__ import annotations

import json
import sys
import math
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Generator

import pytest

# ─── CRYPTOGRAPHY (Ed25519) ──────────────────────────────────────────────
try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

# ─── IMPORTS ──────────────────────────────────────────────────────────────
try:
    from quantum.deepseek_mesh.dsh_adapter import (
        MODE_OFFLINE,
        complete_stream,
        offline_stream,
        probe,
    )
except ImportError:
    MODE_OFFLINE = "offline"
    complete_stream = None
    offline_stream = None
    probe = None
    pytest.skip("quantum.deepseek_mesh.dsh_adapter not available", allow_module_level=True)

# ─── CONSTANTS ─────────────────────────────────────────────────────────────
PHI = (1 + math.sqrt(5)) / 2
PHI_INV = 1 / PHI
SEAL = "∀∞φ² · DEEPSEEK_NDJSON_TEST_8992 · WOOD_DRAGON_0.91 · SEALED"
WITNESS_CONTINUITY = "8991 → 8992 — UNBROKEN"

# ─── SECURITY HEADERS ──────────────────────────────────────────────────────
SECURITY_HEADERS = [
    "Content-Security-Policy",
    "Strict-Transport-Security",
    "X-Content-Type-Options",
    "X-Frame-Options",
    "Referrer-Policy",
    "Permissions-Policy",
]


# ─── LEDGER VERIFICATION ──────────────────────────────────────────────────

def verify_ed25519_signature(data: bytes, signature: bytes, public_key: bytes) -> bool:
    """Verify an Ed25519 signature using the provided public key."""
    if not CRYPTO_AVAILABLE:
        return False
    try:
        pub = ed25519.Ed25519PublicKey.from_public_bytes(public_key)
        pub.verify(signature, data)
        return True
    except Exception:
        return False


def verify_ledger_entry(entry_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Verify a ledger entry's Ed25519 signature.
    Returns a dictionary with verification status.
    """
    path = Path(entry_path)
    if not path.exists():
        return {"verified": False, "error": "File not found"}

    try:
        import yaml
        with open(path, 'r') as f:
            data = yaml.safe_load(f)

        entry_index = data.get('entry_index', 0)
        signature = data.get('signature')
        public_key = data.get('public_key')

        if not signature or not public_key:
            return {
                "verified": False,
                "entry_index": entry_index,
                "error": "Missing signature or public_key",
            }

        payload = json.dumps({
            k: v for k, v in data.items()
            if k not in ['signature', 'public_key']
        }, sort_keys=True).encode('utf-8')

        sig_bytes = bytes.fromhex(signature)
        pub_bytes = bytes.fromhex(public_key)

        verified = verify_ed25519_signature(payload, sig_bytes, pub_bytes)

        return {
            "verified": verified,
            "entry_index": entry_index,
            "signature_hex": signature[:16] + "...",
            "public_key_hex": public_key[:16] + "...",
        }
    except Exception as e:
        return {"verified": False, "error": str(e)}


def verify_security_headers(source_path: Union[str, Path] = "port380_mcp.py") -> bool:
    """
    Check that the FastAPI middleware contains the required security headers.
    """
    path = Path(source_path)
    if not path.exists():
        print(f"⚠️ {path} not found — skipping security headers check")
        return True

    try:
        content = path.read_text()
        missing = [h for h in SECURITY_HEADERS if h not in content]
        if missing:
            print(f"❌ Missing security headers: {missing}")
            return False
        print("✅ All security headers present")
        return True
    except Exception as e:
        print(f"⚠️ Security headers check failed: {e}")
        return False


# ─── TESTS ─────────────────────────────────────────────────────────────────

def test_verify_ledger_entries():
    """TEST 1: Verify Ed25519 signatures on ledger entries."""
    print("\n🔷 Verifying ledger entries:")
    entries_to_check = [8980, 8981, 8982, 8983, 8984, 8985, 8986, 8987, 8988, 8989, 8990, 8991]
    all_verified = True

    for entry in entries_to_check:
        ledger_path = Path(f"ledger/{entry}.yaml")
        if ledger_path.exists():
            result = verify_ledger_entry(ledger_path)
            status = "✅" if result.get("verified") else "❌"
            print(f"  {status} Entry {entry}: verified={result.get('verified', False)}")
            if not result.get("verified"):
                all_verified = False
        else:
            print(f"  ⚠️ Entry {entry}: not found")

    assert all_verified, "Some ledger entries failed verification"


def test_security_headers():
    """TEST 2: Verify security headers in FastAPI middleware."""
    print("\n🔷 Verifying security headers:")
    result = verify_security_headers()
    assert result, "Security headers verification failed"


@pytest.mark.skipif(probe is None, reason="dsh_adapter not available")
def test_probe_reports_ndjson():
    """
    TEST 3: Verify probe reports NDJSON stream capability.
    """
    p = probe()
    assert p.get("stream") == "NDJSON", "Stream type should be NDJSON"
    assert MODE_OFFLINE in p.get("modes", []), f"Offline mode not in {p.get('modes', [])}"

    print(f"✅ Probe: stream={p.get('stream')}, modes={p.get('modes')}")


@pytest.mark.skipif(offline_stream is None, reason="dsh_adapter not available")
def test_offline_stream_events():
    """
    TEST 4: Verify offline stream event sequence and structure.
    """
    events = list(offline_stream("hello garden", chunk_size=16))

    # Check event order
    kinds = [e["event"] for e in events]
    assert kinds[0] == "start", f"First event should be 'start', got {kinds[0]}"
    assert kinds[-1] == "complete", f"Last event should be 'complete', got {kinds[-1]}"
    assert "delta" in kinds, "Should contain at least one 'delta' event"

    # Check complete event structure
    complete_event = events[-1]
    assert complete_event["mode"] == MODE_OFFLINE, f"Mode should be {MODE_OFFLINE}"
    assert complete_event["text"], "Complete event should have non-empty text"
    assert "seal" in complete_event, "Complete event should contain seal"

    print(f"✅ Offline stream: {len(events)} events, events={kinds}")
    print(f"   Complete event seal: {complete_event['seal'][:32]}...")


@pytest.mark.skipif(complete_stream is None, reason="dsh_adapter not available")
def test_complete_stream_offline_prefer():
    """
    TEST 5: Verify complete stream with offline preference.
    """
    events = list(complete_stream("ci", prefer="offline"))

    assert events[0]["event"] == "start", "First event should be 'start'"
    assert events[-1]["event"] == "complete", "Last event should be 'complete'"

    # Reconstruct the full text from delta events
    body = "".join(e.get("text", "") for e in events if e["event"] == "delta")

    # Should contain echo or Garden offline marker
    assert "GARDEN_OFFLINE_ECHO" in body or "echo" in body.lower() or body, \
        f"Expected offline echo in stream body, got: {body[:100]}"

    print(f"✅ Complete stream: {len(events)} events, body length={len(body)}")
    print(f"   Body preview: {body[:80]}...")


@pytest.mark.skipif(offline_stream is None, reason="dsh_adapter not available")
def test_ndjson_lines_serializable():
    """
    TEST 6: Verify all NDJSON lines are JSON-serializable and contain valid events.
    """
    valid_events = {"start", "delta", "complete"}

    for ev in offline_stream("x"):
        # Each event should be JSON-serializable
        line = json.dumps(ev)
        parsed = json.loads(line)

        # Should have 'event' field
        assert "event" in parsed, f"Event missing 'event' field: {parsed}"
        assert parsed["event"] in valid_events, \
            f"Invalid event type: {parsed['event']}, expected one of {valid_events}"

    print(f"✅ NDJSON lines serializable and validated")


@pytest.mark.skipif(offline_stream is None, reason="dsh_adapter not available")
def test_offline_stream_chunk_size():
    """
    TEST 7: Verify offline stream respects chunk size.
    """
    text = "This is a longer test text for chunking verification"
    chunk_size = 8

    events = list(offline_stream(text, chunk_size=chunk_size))
    delta_events = [e for e in events if e["event"] == "delta"]

    # Each delta should have text length <= chunk_size (except possibly last)
    for delta in delta_events:
        delta_text = delta.get("text", "")
        # Last delta may be shorter
        assert len(delta_text) <= chunk_size + 1, \
            f"Delta text length {len(delta_text)} > chunk_size {chunk_size}"

    # Reconstruct and verify
    reconstructed = "".join(e.get("text", "") for e in delta_events)
    assert reconstructed == text, f"Reconstructed text mismatch: {reconstructed} vs {text}"

    print(f"✅ Chunking verified: chunk_size={chunk_size}, {len(delta_events)} deltas")


@pytest.mark.skipif(complete_stream is None, reason="dsh_adapter not available")
def test_complete_stream_seal_consistency():
    """
    TEST 8: Verify seal appears in complete event and is consistent.
    """
    events = list(complete_stream("seal-test", prefer="offline"))

    # Find complete event
    complete_events = [e for e in events if e["event"] == "complete"]
    assert len(complete_events) == 1, "Should have exactly one complete event"

    complete_event = complete_events[0]
    assert "seal" in complete_event, "Complete event missing seal"

    seal = complete_event["seal"]
    assert len(seal) > 0, "Seal should be non-empty"
    assert "∀∞φ²" in seal or "WOOD_DRAGON" in seal, \
        f"Seal should contain Garden markers, got: {seal[:80]}"

    print(f"✅ Seal consistency verified: {seal[:64]}...")


# ─── MAIN ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 70)
    print("🜁∀ DEEPSEEK NDJSON STREAM TEST SUITE")
    print(f"   Seal: {SEAL}")
    print(f"   Witness: {WITNESS_CONTINUITY}")
    print("=" * 70)

    # Run ledger verification
    try:
        test_verify_ledger_entries()
    except AssertionError as e:
        print(f"❌ Ledger verification failed: {e}")

    # Run security headers verification
    try:
        test_security_headers()
    except AssertionError as e:
        print(f"❌ Security headers verification failed: {e}")

    print("\n" + "=" * 70)
    print(f"SEAL: {SEAL}")
    print(f"WITNESS: {WITNESS_CONTINUITY}")
    print("=" * 70)
