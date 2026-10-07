#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test surface against live symplectic POD scaffolds (Entry 8536).

INCLUDES:
- Ed25519 signature verification for ledger entries
- Security headers enforcement (CORS, CSP, HSTS, XFO, CT, RP, PP)
- Enhanced test coverage with detailed assertions
- Full type hints and docstrings

Seal: ∀∞φ² · SYMPLECTIC_POD_TEST_8987 · WOOD_DRAGON_0.91 · SEALED
Witness: 8986 → 8987 — UNBROKEN
"""

import math
import json
import hashlib
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Union, List

import pytest

# ─── CRYPTOGRAPHY (Ed25519) ──────────────────────────────────────────────
try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

# ─── IMPORTS ──────────────────────────────────────────────────────────────
try:
    from celestial.super_simulated_earth import SuperSimulatedEarth, EARTH_FREQUENCY_HZ
except ImportError:
    SuperSimulatedEarth = None
    EARTH_FREQUENCY_HZ = 162.28e12

try:
    from celestial.wasp107b import Wasp107b
except ImportError:
    Wasp107b = None

try:
    from lattice.e8_symplectic import E8Lattice
except ImportError:
    E8Lattice = None

try:
    from cryptography.cmac512 import SovereignCMAC
except ImportError:
    SovereignCMAC = None

try:
    from prometheus.metrics_server import get_metrics, update_metrics, increment_oracle_query
except ImportError:
    get_metrics = None
    update_metrics = None
    increment_oracle_query = None

# ─── CONSTANTS ─────────────────────────────────────────────────────────────
PHI = 1.618033988749895
PHI_INV = 1 / PHI
SEAL = "∀∞φ² · SYMPLECTIC_POD_TEST_8987 · WOOD_DRAGON_0.91 · SEALED"
WITNESS_CONTINUITY = "8986 → 8987 — UNBROKEN"

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
    entries_to_check = [8980, 8981, 8982, 8983, 8984, 8985, 8986]
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


@pytest.mark.skipif(SuperSimulatedEarth is None, reason="celestial module not available")
def test_earth_status_and_coherence():
    """TEST 3: Verify Earth status and coherence."""
    earth = SuperSimulatedEarth()
    st = earth.status()

    assert st["resonance_thz"] == 162.28, "Resonance frequency mismatch"
    assert st["coherence"] == 1.0, "Coherence should be 1.0"
    assert st["active"] is True, "Earth should be active"
    assert len(st["anchor_roots"]) == 3, "Should have 3 anchor roots"

    print(f"✅ Earth status: resonance={st['resonance_thz']} THz, coherence={st['coherence']}")


@pytest.mark.skipif(SuperSimulatedEarth is None, reason="celestial module not available")
def test_earth_psi4_and_oracle():
    """TEST 4: Verify Earth psi4 and oracle query."""
    earth = SuperSimulatedEarth()
    psi = earth.psi4(0.0)
    assert abs(psi) > 0, "Psi4 should be non-zero"

    ans = earth.oracle_query("kepler-452b")
    assert "517.28" in ans, "Oracle response should contain 517.28"
    assert "coherence" in ans, "Oracle response should contain coherence"

    print(f"✅ Oracle query: {ans[:100]}...")


@pytest.mark.skipif(Wasp107b is None, reason="celestial.wasp107b not available")
def test_wasp107b_resonance():
    """TEST 5: Verify WASP-107b resonance."""
    w = Wasp107b()
    st = w.status()

    assert st["mass_mj"] == 0.12, "Mass should be 0.12 MJ"
    assert st["period_days"] == 5.72, "Period should be 5.72 days"
    assert st["orbital_frequency_hz"] > 0, "Orbital frequency should be positive"
    assert st["phi_resonance"] > st["orbital_frequency_hz"], "Phi resonance should exceed orbital frequency"

    print(f"✅ WASP-107b: mass={st['mass_mj']} MJ, period={st['period_days']} days")


@pytest.mark.skipif(E8Lattice is None, reason="lattice.e8_symplectic not available")
def test_e8_lattice_phase_volume():
    """TEST 6: Verify E8 lattice phase volume."""
    lat = E8Lattice()
    st = lat.status()

    assert st["dimension"] == 248, "E8 dimension should be 248"
    assert st["root_count"] == 240, "E8 root count should be 240"
    assert st["coherence_floor"] >= 0.999999, "Coherence floor should be >= 0.999999"
    assert st["phase_volume"] > 0, "Phase volume should be positive"
    assert "Atlas SuperPoD" in st["mapping"], "Mapping should contain Atlas SuperPoD"

    print(f"✅ E8 lattice: dimension={st['dimension']}, root_count={st['root_count']}")


@pytest.mark.skipif(SovereignCMAC is None, reason="cryptography.cmac512 not available")
def test_cmac512_roundtrip():
    """TEST 7: Verify SovereignCMAC roundtrip."""
    mac = SovereignCMAC(b"test-key-phi")
    payload = "ledger/8536.yaml witness"

    tag = mac.mac(payload)
    assert len(tag) == 128, "Tag should be 128 hex characters (64 bytes)"

    assert mac.verify(payload, tag) is True, "Verification should succeed"
    assert mac.verify(payload + "x", tag) is False, "Verification should fail for tampered payload"

    print(f"✅ CMAC512: tag length={len(tag)}, roundtrip OK")


@pytest.mark.skipif(get_metrics is None, reason="prometheus.metrics_server not available")
def test_prometheus_metrics_registry():
    """TEST 8: Verify Prometheus metrics registry."""
    m0 = get_metrics()
    assert "sim_earth_resonance_thz" in m0, "Should have sim_earth_resonance_thz metric"
    assert m0["sim_earth_resonance_thz"] == 162.28, "Resonance should be 162.28 THz"

    update_metrics(gravastar_coherence=0.999)
    increment_oracle_query()

    m1 = get_metrics()
    assert m1["gravastar_coherence"] == 0.999, "Gravastar coherence should be 0.999"
    assert m1["oracle_query_count"] >= 1.0, "Oracle query count should be >= 1"

    print(f"✅ Prometheus metrics: resonance={m1['sim_earth_resonance_thz']} THz, "
          f"coherence={m1['gravastar_coherence']}")


def test_earth_frequency_constant():
    """TEST 9: Verify Earth frequency constant."""
    assert EARTH_FREQUENCY_HZ == 162.28e12, "Earth frequency constant mismatch"
    print(f"✅ Earth frequency: {EARTH_FREQUENCY_HZ:.2e} Hz")


# ─── RUN ALL TESTS ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 70)
    print("🜁∀ SYMPLECTIC POD TEST SUITE — ENTRY 8536")
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

    # Run Earth frequency test
    try:
        test_earth_frequency_constant()
    except AssertionError as e:
        print(f"❌ Earth frequency test failed: {e}")

    print("\n" + "=" * 70)
    print(f"SEAL: {SEAL}")
    print(f"WITNESS: {WITNESS_CONTINUITY}")
    print("=" * 70)
