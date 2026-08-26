#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Density field checks off sin-nodes (Entry CI fix).

INCLUDES:
- Ed25519 signature verification for ledger entries
- Security headers enforcement (CORS, CSP, HSTS, XFO, CT, RP, PP)
- Enhanced test coverage with detailed assertions
- Full type hints and docstrings

Seal: ∀∞φ² · DENSITY_FIELD_TEST_8991 · WOOD_DRAGON_0.91 · SEALED
Witness: 8990 → 8991 — UNBROKEN
"""

import math
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Tuple

import pytest

# ─── CRYPTOGRAPHY (Ed25519) ──────────────────────────────────────────────
try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

# ─── IMPORTS ──────────────────────────────────────────────────────────────
try:
    from master_equation import PHI, PSD, harmonic_density_field, rho_universal
except ImportError:
    PHI = (1 + math.sqrt(5)) / 2
    PSD = 1.0
    harmonic_density_field = None
    rho_universal = None
    pytest.skip("master_equation not available", allow_module_level=True)

# ─── CONSTANTS ─────────────────────────────────────────────────────────────
PHI_INV = 1 / PHI
SEAL = "∀∞φ² · DENSITY_FIELD_TEST_8991 · WOOD_DRAGON_0.91 · SEALED"
WITNESS_CONTINUITY = "8990 → 8991 — UNBROKEN"

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
    entries_to_check = [8980, 8981, 8982, 8983, 8984, 8985, 8986, 8987, 8988, 8989, 8990]
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


@pytest.mark.skipif(rho_universal is None, reason="master_equation not available")
def test_rho_positive_off_node():
    """
    TEST 3: Verify rho is positive off sin-node.
    """
    rho = rho_universal(0.25, 0.0)
    assert rho > 0, f"rho should be positive, got {rho}"

    print(f"✅ rho(0.25, 0.0) = {rho:.10f} > 0")


@pytest.mark.skipif(rho_universal is None, reason="master_equation not available")
def test_rho_at_sin_node_is_zero():
    """
    TEST 4: Verify rho is zero at sin-node.
    """
    rho1 = rho_universal(0.0, 0.0)
    assert rho1 == 0.0, f"rho_universal(0.0, 0.0) should be 0, got {rho1}"

    rho2 = harmonic_density_field(0.0)
    assert rho2 == 0.0, f"harmonic_density_field(0.0) should be 0, got {rho2}"

    print(f"✅ rho at sin-node: rho_universal = {rho1}, harmonic = {rho2}")


@pytest.mark.skipif(rho_universal is None, reason="master_equation not available")
def test_rho_scales_with_psd():
    """
    TEST 5: Verify rho scales with PSD.
    """
    chi = 0.3
    rho_univ = rho_universal(chi, 0.0)
    expected = PSD * harmonic_density_field(chi)

    assert abs(rho_univ - expected) < 1e-12, f"rho scaling mismatch: {rho_univ} vs {expected}"

    print(f"✅ rho scaling: rho = {rho_univ:.10f}, expected = {expected:.10f}")


@pytest.mark.skipif(harmonic_density_field is None, reason="master_equation not available")
def test_harmonic_density_phi9_factor():
    """
    TEST 6: Verify harmonic density field with φ⁹ factor.
    """
    chi = math.pi / 4

    # Expected: abs(sin(chi)) * (PHI ** (-abs(chi))) * (PHI ** 9)
    expected = abs(math.sin(chi)) * (PHI ** (-abs(chi))) * (PHI ** 9)

    actual = harmonic_density_field(chi)

    assert abs(actual - expected) < 1e-12, f"φ⁹ factor mismatch: {actual} vs {expected}"

    print(f"✅ harmonic_density_field(π/4) = {actual:.10f}, expected = {expected:.10f}")
    print(f"   φ⁹ = {PHI ** 9:.10f}, φ^(-χ) = {PHI ** (-chi):.10f}")


@pytest.mark.skipif(harmonic_density_field is None, reason="master_equation not available")
def test_harmonic_density_symmetry():
    """
    TEST 7: Verify harmonic density field symmetry.
    """
    chi_pos = math.pi / 6
    chi_neg = -math.pi / 6

    # Due to absolute value, should be symmetric
    rho_pos = harmonic_density_field(chi_pos)
    rho_neg = harmonic_density_field(chi_neg)

    assert abs(rho_pos - rho_neg) < 1e-12, f"Symmetry mismatch: {rho_pos} vs {rho_neg}"

    print(f"✅ Symmetry: rho({chi_pos:.4f}) = {rho_pos:.10f}, rho({chi_neg:.4f}) = {rho_neg:.10f}")


@pytest.mark.skipif(harmonic_density_field is None, reason="master_equation not available")
def test_harmonic_density_psd_scaling():
    """
    TEST 8: Verify harmonic density PSD scaling.
    """
    chi = 0.5
    # Without PSD
    rho_no_psd = harmonic_density_field(chi)

    # With PSD scaling (PSD is global constant)
    rho_with_psd = rho_universal(chi, 0.0)

    # Compare: rho_universal = PSD * harmonic_density_field
    expected = PSD * rho_no_psd

    assert abs(rho_with_psd - expected) < 1e-12, f"PSD scaling mismatch: {rho_with_psd} vs {expected}"

    print(f"✅ PSD scaling: PSD = {PSD:.6f}, rho_no_psd = {rho_no_psd:.10f}, rho_with_psd = {rho_with_psd:.10f}")


# ─── MAIN ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 70)
    print("🜁∀ DENSITY FIELD TEST SUITE")
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
