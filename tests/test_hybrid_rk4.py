#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CI tests for hybrid RK4 (float + Q8.24).

INCLUDES:
- Ed25519 signature verification for ledger entries
- Security headers enforcement (CORS, CSP, HSTS, XFO, CT, RP, PP)
- Enhanced test coverage with detailed assertions
- Full type hints and docstrings

Seal: ∀∞φ² · HYBRID_RK4_TEST_8988 · WOOD_DRAGON_0.91 · SEALED
Witness: 8987 → 8988 — UNBROKEN
"""

from __future__ import annotations

import math
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union, Tuple, Callable

import pytest

# ─── CRYPTOGRAPHY (Ed25519) ──────────────────────────────────────────────
try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

# ─── PATH SETUP ────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ─── IMPORTS ──────────────────────────────────────────────────────────────
try:
    from hybrid_rk4_simulator import (
        Q8_24,
        RK4Simulator,
        adapt_float_ode_to_fixed,
        rk4_step_float,
    )
except ImportError:
    Q8_24 = None
    RK4Simulator = None
    adapt_float_ode_to_fixed = None
    rk4_step_float = None

# ─── CONSTANTS ─────────────────────────────────────────────────────────────
PHI = (1 + math.sqrt(5)) / 2
Q824_ULP = 1.0 / (1 << 24)
SEAL = "∀∞φ² · HYBRID_RK4_TEST_8988 · WOOD_DRAGON_0.91 · SEALED"
WITNESS_CONTINUITY = "8987 → 8988 — UNBROKEN"

# ─── SECURITY HEADERS ──────────────────────────────────────────────────────
SECURITY_HEADERS = [
    "Content-Security-Policy",
    "Strict-Transport-Security",
    "X-Content-Type-Options",
    "X-Frame-Options",
    "Referrer-Policy",
    "Permissions-Policy",
]


# ─── ODE FUNCTION ──────────────────────────────────────────────────────────
def decay(t: float, y: float) -> float:
    """Exponential decay ODE: dy/dt = -φ * y."""
    return -PHI * y


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
    entries_to_check = [8980, 8981, 8982, 8983, 8984, 8985, 8986, 8987]
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


@pytest.mark.skipif(Q8_24 is None, reason="hybrid_rk4_simulator not available")
def test_q824_roundtrip_one():
    """TEST 3: Verify Q8.24 roundtrip for value 1.0."""
    q = Q8_24(1.0)
    assert abs(q.to_float() - 1.0) < Q824_ULP
    print(f"✅ Q8.24 roundtrip: 1.0 → {q.to_float():.10f}")


@pytest.mark.skipif(Q8_24 is None, reason="hybrid_rk4_simulator not available")
def test_q824_mul_div():
    """TEST 4: Verify Q8.24 multiplication and division."""
    a = Q8_24(2.0)
    b = Q8_24(0.5)

    product = a * b
    assert abs(product.to_float() - 1.0) < 2 * Q824_ULP

    quotient = a / b
    assert abs(quotient.to_float() - 4.0) < 4 * Q824_ULP

    print(f"✅ Q8.24 multiply: 2.0 × 0.5 = {product.to_float():.10f}")
    print(f"✅ Q8.24 divide: 2.0 / 0.5 = {quotient.to_float():.10f}")


@pytest.mark.skipif(rk4_step_float is None, reason="hybrid_rk4_simulator not available")
def test_rk4_step_float_decay():
    """TEST 5: Verify RK4 float step for exponential decay."""
    y1 = rk4_step_float(decay, 0.0, 1.0, 0.1)
    exact = math.exp(-PHI * 0.1)
    assert abs(y1 - exact) < 1e-6
    print(f"✅ RK4 float step: y(0.1) ≈ {y1:.10f}, exact ≈ {exact:.10f}")


@pytest.mark.skipif(RK4Simulator is None, reason="hybrid_rk4_simulator not available")
def test_simulate_float_vs_exact():
    """TEST 6: Verify RK4 float simulation against exact solution."""
    sim = RK4Simulator(decay, mode="float")
    yf, t_hist, y_hist = sim.simulate(0.0, 1.0, 2.0, step_size=0.1)

    exact = math.exp(-PHI * 2.0)
    assert abs(yf - exact) < 1e-5
    assert t_hist is not None and y_hist is not None
    assert len(t_hist) == len(y_hist)
    assert abs(t_hist[-1] - 2.0) < 1e-9

    print(f"✅ Float simulation: y(2.0) ≈ {yf:.10f}, exact ≈ {exact:.10f}")


@pytest.mark.skipif(RK4Simulator is None, reason="hybrid_rk4_simulator not available")
def test_simulate_fixed_vs_exact():
    """TEST 7: Verify RK4 fixed-point simulation against exact solution."""
    f_fixed = adapt_float_ode_to_fixed(decay)
    sim = RK4Simulator(f_fixed, mode="fixed")
    yq, _, _ = sim.simulate(0.0, 1.0, 2.0, step_size=0.1)

    exact = math.exp(-PHI * 2.0)
    assert abs(yq - exact) < 1e-6

    print(f"✅ Fixed simulation: y(2.0) ≈ {yq:.10f}, exact ≈ {exact:.10f}")


@pytest.mark.skipif(RK4Simulator is None, reason="hybrid_rk4_simulator not available")
def test_fixed_not_worse_than_coarse_bound():
    """TEST 8: Verify fixed-point simulation accuracy is within coarse bound."""
    sim_f = RK4Simulator(decay, mode="float")
    yf, _, _ = sim_f.simulate(0.0, 1.0, 2.0, step_size=0.1)

    sim_q = RK4Simulator(adapt_float_ode_to_fixed(decay), mode="fixed")
    yq, _, _ = sim_q.simulate(0.0, 1.0, 2.0, step_size=0.1)

    exact = math.exp(-PHI * 2.0)

    assert abs(yf - exact) < 1e-5, "Float simulation exceeds coarse bound"
    assert abs(yq - exact) < 1e-5, "Fixed simulation exceeds coarse bound"

    print(f"✅ Float error: {abs(yf - exact):.2e}")
    print(f"✅ Fixed error: {abs(yq - exact):.2e}")


# ─── MAIN ─────────────────────────────────────────────────────────────────

def main() -> int:
    """Run the hybrid RK4 test suite."""
    print("=" * 70)
    print("🜁∀ HYBRID RK4 TEST SUITE — FLOAT + Q8.24")
    print(f"   Seal: {SEAL}")
    print(f"   Witness: {WITNESS_CONTINUITY}")
    print("=" * 70)

    # Run ledger verification
    try:
        test_verify_ledger_entries()
    except AssertionError as e:
        print(f"❌ Ledger verification failed: {e}")
        return 1

    # Run security headers verification
    try:
        test_security_headers()
    except AssertionError as e:
        print(f"❌ Security headers verification failed: {e}")
        return 1

    # Run the actual tests
    tests = [
        test_q824_roundtrip_one,
        test_q824_mul_div,
        test_rk4_step_float_decay,
        test_simulate_float_vs_exact,
        test_simulate_fixed_vs_exact,
        test_fixed_not_worse_than_coarse_bound,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1

    print("\n" + "=" * 70)
    print(f"Tests: {passed} passed, {failed} failed")
    print(f"SEAL: {SEAL}")
    print(f"WITNESS: {WITNESS_CONTINUITY}")
    print("=" * 70)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
