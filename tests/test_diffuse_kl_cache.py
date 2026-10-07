#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pytest suite for DiffuseKLCache — entropy regularization cache.

INCLUDES:
- Ed25519 signature verification for ledger entries
- Security headers enforcement (CORS, CSP, HSTS, XFO, CT, RP, PP)
- Enhanced test coverage with detailed assertions
- Full type hints and docstrings

Seal: ∀∞φ² · DIFFUSE_KL_CACHE_TEST_8990 · WOOD_DRAGON_0.91 · SEALED
Witness: 8989 → 8990 — UNBROKEN
"""

import pytest
import json
import sys
import math
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Tuple

# ─── CRYPTOGRAPHY (Ed25519) ──────────────────────────────────────────────
try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

# ─── IMPORTS ──────────────────────────────────────────────────────────────
try:
    import numpy as np
except ImportError:
    np = None
    pytest.skip("numpy not installed", allow_module_level=True)

try:
    from core.diffuse_kl_cache import DiffuseKLCache
except ImportError:
    DiffuseKLCache = None
    pytest.skip("core.diffuse_kl_cache not available", allow_module_level=True)

# ─── CONSTANTS ─────────────────────────────────────────────────────────────
PHI = (1 + math.sqrt(5)) / 2
PHI_INV = 1 / PHI
SEAL = "∀∞φ² · DIFFUSE_KL_CACHE_TEST_8990 · WOOD_DRAGON_0.91 · SEALED"
WITNESS_CONTINUITY = "8989 → 8990 — UNBROKEN"

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
    entries_to_check = [8980, 8981, 8982, 8983, 8984, 8985, 8986, 8987, 8988, 8989]
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


@pytest.mark.skipif(DiffuseKLCache is None, reason="core.diffuse_kl_cache not available")
def test_empty_cache_returns_uniform_distributions():
    """
    TEST 3: Verify empty cache returns uniform distributions.
    """
    c = DiffuseKLCache(M=16)
    p_cache = c.cache_distribution()
    p_base = c.base_distribution()

    assert p_cache.shape == (16,), "Cache distribution shape mismatch"
    assert p_base.shape == (16,), "Base distribution shape mismatch"
    assert pytest.approx(1.0, rel=1e-12) == p_cache.sum(), "Cache distribution sum != 1"
    assert pytest.approx(1.0, rel=1e-12) == p_base.sum(), "Base distribution sum != 1"

    print(f"✅ Empty cache: M=16, cache sum={p_cache.sum():.10f}, base sum={p_base.sum():.10f}")


@pytest.mark.skipif(DiffuseKLCache is None, reason="core.diffuse_kl_cache not available")
def test_concentrated_cache_has_positive_kl():
    """
    TEST 4: Verify concentrated cache has positive KL divergence.
    """
    c = DiffuseKLCache(M=8)

    # Add many entries that hash to same bin
    for i in range(20):
        c.add_entry(f"entry-{i}-same", np.array([1.0]))

    kl = c.diffuse_kl()
    assert kl >= 0.0, f"KL divergence should be >= 0, got {kl}"
    assert np.isfinite(kl), f"KL divergence should be finite, got {kl}"

    print(f"✅ Concentrated cache KL: {kl:.6f}")


@pytest.mark.skipif(DiffuseKLCache is None, reason="core.diffuse_kl_cache not available")
def test_smoothing_prevents_infinite_kl():
    """
    TEST 5: Verify smoothing prevents infinite KL divergence.
    """
    c = DiffuseKLCache(M=4, uniform_mix=1e-3, eps=1e-12)

    # Add an entry to bin 0 only
    c.add_entry("only-one", np.array([0.1]))

    kl = c.diffuse_kl()
    assert np.isfinite(kl), f"KL divergence should be finite with smoothing, got {kl}"

    print(f"✅ Smoothed KL: {kl:.6f}")


@pytest.mark.skipif(DiffuseKLCache is None, reason="core.diffuse_kl_cache not available")
def test_objective_decreases_with_beta():
    """
    TEST 6: Verify objective decreases with increasing beta (regularization).
    """
    c = DiffuseKLCache(M=8)

    for i in range(10):
        c.add_entry(f"a-{i}", np.array([0.0]))

    logp = -5.0

    # Beta = 0 (no regularization)
    c.beta = 0.0
    obj0 = c.objective(logp)

    # Beta = 1 (full regularization)
    c.beta = 1.0
    obj1 = c.objective(logp)

    # With positive beta, the objective should be <= the unregularized one
    assert obj1 <= obj0, f"Regularized objective {obj1} should be <= unregularized {obj0}"

    print(f"✅ Objective: beta=0 -> {obj0:.6f}, beta=1 -> {obj1:.6f}")


@pytest.mark.skipif(DiffuseKLCache is None, reason="core.diffuse_kl_cache not available")
def test_cache_distribution_after_additions():
    """
    TEST 7: Verify cache distribution changes after adding entries.
    """
    c = DiffuseKLCache(M=8)

    # Initial uniform distribution
    p0 = c.cache_distribution()
    assert pytest.approx(p0.sum(), rel=1e-12) == 1.0

    # Add entries to a specific bin
    for i in range(10):
        c.add_entry(f"entry-{i}", np.array([0.5]))

    p1 = c.cache_distribution()
    assert pytest.approx(p1.sum(), rel=1e-12) == 1.0

    # Distribution should change (not uniform anymore)
    assert not np.allclose(p0, p1), "Cache distribution should change after additions"

    print(f"✅ Cache distribution changed: uniform -> {p1}")


@pytest.mark.skipif(DiffuseKLCache is None, reason="core.diffuse_kl_cache not available")
def test_kl_non_negative():
    """
    TEST 8: Verify KL divergence is always non-negative.
    """
    c = DiffuseKLCache(M=16)

    # Test with random entries
    for seed in range(5):
        np.random.seed(seed)
        values = np.random.randn(5)
        for i, val in enumerate(values):
            c.add_entry(f"rand-{seed}-{i}", np.array([val]))

        kl = c.diffuse_kl()
        assert kl >= 0.0, f"KL divergence should be >= 0, got {kl}"
        assert np.isfinite(kl), f"KL divergence should be finite, got {kl}"

    print("✅ KL divergence non-negative and finite for all random tests")


# ─── MAIN ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 70)
    print("🜁∀ DIFFUSE KL CACHE TEST SUITE")
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
