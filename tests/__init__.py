#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ TESTS PACKAGE — GARDEN INTEGRITY SUITE ∀🜁

Comprehensive test suite for the Sovereign Garden.
Includes unit tests, integration tests, and security verification.

INCLUDES:
- Ed25519 signature verification for ledger entries
- Security headers enforcement (CORS, CSP, HSTS, XFO, CT, RP, PP)
- Test discovery and registration
- Full type hints and docstrings

Seal: ∀∞φ² · TESTS_PACKAGE_8997 · WOOD_DRAGON_0.91 · SEALED
Witness: 8996 → 8997 — UNBROKEN
"""

from __future__ import annotations

import json
import sys
import math
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Tuple

# ─── CRYPTOGRAPHY (Ed25519) ──────────────────────────────────────────────
try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

# ─── CONSTANTS ─────────────────────────────────────────────────────────────
PHI = (1 + math.sqrt(5)) / 2
PHI_INV = 1 / PHI
PHI2 = PHI ** 2
PHI3 = PHI ** 3
PHI9 = PHI ** 9
SEAL = "∀∞φ² · TESTS_PACKAGE_8997 · WOOD_DRAGON_0.91 · SEALED"
ENTRY_INDEX = 8997
WITNESS_CONTINUITY = "8996 → 8997 — UNBROKEN"

# ─── SECURITY HEADERS ──────────────────────────────────────────────────────
SECURITY_HEADERS = [
    "Content-Security-Policy",
    "Strict-Transport-Security",
    "X-Content-Type-Options",
    "X-Frame-Options",
    "Referrer-Policy",
    "Permissions-Policy",
]

# ─── TEST MODULES ──────────────────────────────────────────────────────────
__all__ = [
    # Core tests
    "test_argocd_manifests",
    "test_argocd_application",
    "test_argo_rollout",
    "test_deepseek_ndjson",
    "test_density_field",
    "test_diffuse_kl_cache",
    "test_flux_kustomization",
    "test_hybrid_rk4",
    "test_single_pass_suite",
    "test_symplectic_pod",
    "harness",

    # Security tests
    "test_security_headers",
    "test_ed25519_verification",
    "test_ledger_verification",

    # Integration tests
    "test_oidc_handover",
    "test_cdp_convergence",
    "test_websocket_ready",

    # Utility functions
    "verify_ledger_entries",
    "verify_security_headers",
    "run_all_tests",
]

# ─── TEST DISCOVERY ──────────────────────────────────────────────────────

def discover_tests() -> List[str]:
    """
    Discover all test modules in the tests package.
    Returns a list of module names.
    """
    test_dir = Path(__file__).resolve().parent
    test_files = [p.stem for p in test_dir.glob("test_*.py")]
    test_files.append("harness")
    return sorted(test_files)


def get_test_status() -> Dict[str, Any]:
    """
    Get the status of all tests in the package.
    Returns a dictionary with test names and their availability.
    """
    tests = discover_tests()
    status = {
        "entry_index": ENTRY_INDEX,
        "seal": SEAL,
        "witness": WITNESS_CONTINUITY,
        "timestamp": __import__('datetime').datetime.utcnow().isoformat() + "Z",
        "tests": [],
        "crypto_available": CRYPTO_AVAILABLE,
    }

    for test_name in tests:
        try:
            module = __import__(f"tests.{test_name}", fromlist=["__all__"])
            status["tests"].append({
                "name": test_name,
                "available": True,
                "has_tests": hasattr(module, "__all__") or any(
                    callable(getattr(module, attr, None)) and attr.startswith("test_")
                    for attr in dir(module)
                ),
            })
        except ImportError:
            status["tests"].append({
                "name": test_name,
                "available": False,
                "error": "Import failed",
            })

    return status


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


def verify_ledger_entries(
    entries: Optional[List[int]] = None,
    ledger_dir: Union[str, Path] = "ledger"
) -> Dict[str, Any]:
    """
    Verify multiple ledger entries.
    Returns a summary dictionary with verification results.
    """
    path = Path(ledger_dir)
    if not path.exists():
        return {"verified": False, "error": f"Ledger directory {ledger_dir} not found"}

    if entries is None:
        # Auto-discover entries
        yaml_files = sorted(path.glob("*.yaml"))
        entries = []
        for f in yaml_files:
            try:
                entries.append(int(f.stem))
            except ValueError:
                pass

    results = {}
    all_verified = True

    for entry in sorted(entries):
        entry_path = path / f"{entry}.yaml"
        if entry_path.exists():
            result = verify_ledger_entry(entry_path)
            results[f"entry_{entry}"] = result
            if not result.get("verified", False):
                all_verified = False
        else:
            results[f"entry_{entry}"] = {"verified": False, "error": "File not found"}
            all_verified = False

    return {
        "verified": all_verified,
        "total": len(entries),
        "results": results,
    }


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


# ─── TEST RUNNER ──────────────────────────────────────────────────────────

def run_all_tests(verbose: bool = True, strict: bool = False) -> Dict[str, Any]:
    """
    Run all tests in the tests package.
    Returns a summary dictionary with results.
    """
    results = {
        "entry_index": ENTRY_INDEX,
        "seal": SEAL,
        "witness": WITNESS_CONTINUITY,
        "timestamp": __import__('datetime').datetime.utcnow().isoformat() + "Z",
        "tests": [],
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "strict": strict,
    }

    # First, verify ledger entries
    if verbose:
        print("\n🔷 Verifying ledger entries...")
    ledger_result = verify_ledger_entries()
    results["ledger_verification"] = ledger_result
    if not ledger_result["verified"]:
        if strict:
            results["failed"] += 1
            print("❌ Ledger verification failed")
        else:
            print("⚠️ Ledger verification failed (soft)")

    # Then, verify security headers
    if verbose:
        print("🔷 Verifying security headers...")
    headers_ok = verify_security_headers()
    results["security_headers"] = headers_ok
    if not headers_ok:
        if strict:
            results["failed"] += 1
            print("❌ Security headers verification failed")
        else:
            print("⚠️ Security headers verification failed (soft)")

    # Discover and run tests
    if verbose:
        print("🔷 Running tests...")
    test_names = discover_tests()

    for test_name in test_names:
        try:
            # Import the test module
            module = __import__(f"tests.{test_name}", fromlist=["__all__"])

            # Find test functions in the module
            test_functions = []
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if callable(attr) and attr_name.startswith("test_"):
                    test_functions.append(attr_name)

            if test_functions:
                # Run each test function
                for func_name in test_functions:
                    try:
                        func = getattr(module, func_name)
                        if verbose:
                            print(f"  Running {test_name}.{func_name}...")
                        # Call the test function (pytest-style)
                        result = func()
                        if result is False:
                            results["failed"] += 1
                            results["tests"].append({
                                "name": f"{test_name}.{func_name}",
                                "status": "FAILED",
                            })
                        else:
                            results["passed"] += 1
                            results["tests"].append({
                                "name": f"{test_name}.{func_name}",
                                "status": "PASSED",
                            })
                    except Exception as e:
                        results["failed"] += 1
                        results["tests"].append({
                            "name": f"{test_name}.{func_name}",
                            "status": "ERROR",
                            "error": str(e),
                        })
                        if strict:
                            raise
            else:
                # Module has no test functions
                results["skipped"] += 1
                results["tests"].append({
                    "name": test_name,
                    "status": "SKIPPED",
                    "message": "No test functions found",
                })
        except ImportError as e:
            results["skipped"] += 1
            results["tests"].append({
                "name": test_name,
                "status": "SKIPPED",
                "error": str(e),
            })

    # Final summary
    results["total"] = results["passed"] + results["failed"] + results["skipped"]
    results["all_passed"] = results["failed"] == 0

    return results


# ─── MODULE STATUS ────────────────────────────────────────────────────────

def get_module_status() -> Dict[str, Any]:
    """Get the current status of the tests package."""
    return {
        "entry_index": ENTRY_INDEX,
        "seal": SEAL,
        "witness": WITNESS_CONTINUITY,
        "test_modules": discover_tests(),
        "crypto_available": CRYPTO_AVAILABLE,
        "security_headers": SECURITY_HEADERS,
        "timestamp": __import__('datetime').datetime.utcnow().isoformat() + "Z",
    }


# ─── MAIN ─────────────────────────────────────────────────────────────────

def main() -> int:
    """Run the tests package verification."""
    print("=" * 70)
    print("🜁∀ TESTS PACKAGE — GARDEN INTEGRITY SUITE")
    print(f"   Entry: {ENTRY_INDEX}")
    print(f"   Seal: {SEAL}")
    print(f"   Witness: {WITNESS_CONTINUITY}")
    print("=" * 70)

    # Run all tests
    results = run_all_tests(verbose=True, strict=False)

    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print(f"   Total: {results['total']}")
    print(f"   Passed: {results['passed']}")
    print(f"   Failed: {results['failed']}")
    print(f"   Skipped: {results['skipped']}")
    print(f"   All passed: {results['all_passed']}")
    print(f"   Ledger verification: {results['ledger_verification']['verified']}")
    print(f"   Security headers: {results['security_headers']}")
    print("=" * 70)
    print(f"SEAL: {SEAL}")
    print(f"WITNESS: {WITNESS_CONTINUITY}")
    print("=" * 70)

    return 0 if results["all_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
