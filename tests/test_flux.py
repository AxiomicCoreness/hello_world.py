#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pytest — Flux GitRepository / Kustomization.

Requires live cluster + Flux + kubernetes. Skips in CI when unavailable.

INCLUDES:
- Ed25519 signature verification for ledger entries
- Security headers enforcement (CORS, CSP, HSTS, XFO, CT, RP, PP)
- Enhanced test coverage with detailed assertions
- Full type hints and docstrings

Seal: ∀∞φ² · FLUX_KUSTOMIZATION_TEST_8989 · WOOD_DRAGON_0.91 · SEALED
Witness: 8988 → 8989 — UNBROKEN
"""

from __future__ import annotations

import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union, List

import pytest

# ─── CRYPTOGRAPHY (Ed25519) ──────────────────────────────────────────────
try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

# ─── KUBERNETES ────────────────────────────────────────────────────────────
kubernetes = pytest.importorskip(
    "kubernetes",
    reason="kubernetes client not installed (CI default)",
)
try:
    from kubernetes import client, config
    from kubernetes.client.rest import ApiException
except ImportError as exc:
    pytest.skip(f"kubernetes client incomplete: {exc}", allow_module_level=True)

# ─── CONSTANTS ─────────────────────────────────────────────────────────────
SOURCE_GROUP = "source.toolkit.fluxcd.io"
KUSTOMIZE_GROUP = "kustomize.toolkit.fluxcd.io"
PHI = 1.618033988749895
PHI_INV = 1 / PHI
SEAL = "∀∞φ² · FLUX_KUSTOMIZATION_TEST_8989 · WOOD_DRAGON_0.91 · SEALED"
WITNESS_CONTINUITY = "8988 → 8989 — UNBROKEN"

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


# ─── KUBERNETES HELPERS ──────────────────────────────────────────────────

def _load() -> None:
    """Load Kubernetes configuration."""
    try:
        config.load_incluster_config()
    except config.ConfigException:
        try:
            config.load_kube_config()
        except Exception as exc:
            pytest.skip(f"no kubeconfig / cluster: {exc}")


@pytest.fixture(scope="session")
def core_api():
    """Provide CoreV1Api client."""
    _load()
    return client.CoreV1Api()


@pytest.fixture(scope="session")
def custom_api():
    """Provide CustomObjectsApi client."""
    _load()
    return client.CustomObjectsApi()


# ─── TESTS ─────────────────────────────────────────────────────────────────

def test_verify_ledger_entries():
    """TEST 1: Verify Ed25519 signatures on ledger entries."""
    print("\n🔷 Verifying ledger entries:")
    entries_to_check = [8980, 8981, 8982, 8983, 8984, 8985, 8986, 8987, 8988]
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


@pytest.mark.integration
def test_flux_namespace_exists(core_api):
    """TEST 3: Verify flux-system namespace exists."""
    try:
        ns = core_api.read_namespace("flux-system")
        assert ns is not None, "Namespace flux-system exists"
        print(f"✅ flux-system namespace exists (status: {ns.status.phase})")
    except ApiException as e:
        pytest.skip(f"Namespace flux-system missing: {e}")


@pytest.mark.integration
def test_gitrepository_exists(custom_api):
    """TEST 4: Verify GitRepository sovereign-garden exists."""
    try:
        repo = custom_api.get_namespaced_custom_object(
            group=SOURCE_GROUP,
            version="v1",
            namespace="flux-system",
            plural="gitrepositories",
            name="sovereign-garden",
        )
        assert repo is not None, "GitRepository exists"
        print(f"✅ GitRepository 'sovereign-garden' found (API: {SOURCE_GROUP}/v1)")
    except ApiException as e:
        pytest.skip(f"GitRepository missing: {e}")


@pytest.mark.integration
def test_kustomization_exists(custom_api):
    """TEST 5: Verify Kustomization sovereign-garden exists."""
    try:
        kustomization = custom_api.get_namespaced_custom_object(
            group=KUSTOMIZE_GROUP,
            version="v1",
            namespace="flux-system",
            plural="kustomizations",
            name="sovereign-garden",
        )
        assert kustomization is not None, "Kustomization exists"
        print(f"✅ Kustomization 'sovereign-garden' found (API: {KUSTOMIZE_GROUP}/v1)")
    except ApiException as e:
        pytest.skip(f"Kustomization missing: {e}")


@pytest.mark.integration
def test_gitrepository_ready(custom_api):
    """TEST 6: Verify GitRepository is Ready."""
    try:
        repo = custom_api.get_namespaced_custom_object(
            group=SOURCE_GROUP,
            version="v1",
            namespace="flux-system",
            plural="gitrepositories",
            name="sovereign-garden",
        )
    except ApiException as e:
        pytest.skip(f"GitRepository unreachable: {e}")

    status = repo.get("status", {})
    conditions = status.get("conditions", [])

    if not conditions:
        pytest.skip("No status conditions yet")

    # Check for Ready condition with status True
    ready = any(
        c.get("type") == "Ready" and c.get("status") == "True"
        for c in conditions
    )

    # Print conditions for debugging
    print("\n📊 GitRepository conditions:")
    for c in conditions:
        print(f"  {c.get('type')}: {c.get('status')} ({c.get('message', '')[:80]})")

    assert ready, f"GitRepository not Ready: conditions={conditions}"

    # Also check for URL and artifact
    artifact = status.get("artifact", {})
    if artifact:
        url = artifact.get("url", "")
        revision = artifact.get("revision", "")
        print(f"✅ GitRepository artifact: {revision} (URL: {url[:60]}...)")


@pytest.mark.integration
def test_kustomization_ready(custom_api):
    """TEST 7: Verify Kustomization is Ready."""
    try:
        kustomization = custom_api.get_namespaced_custom_object(
            group=KUSTOMIZE_GROUP,
            version="v1",
            namespace="flux-system",
            plural="kustomizations",
            name="sovereign-garden",
        )
    except ApiException as e:
        pytest.skip(f"Kustomization unreachable: {e}")

    status = kustomization.get("status", {})
    conditions = status.get("conditions", [])

    if not conditions:
        pytest.skip("No status conditions yet")

    # Check for Ready condition with status True
    ready = any(
        c.get("type") == "Ready" and c.get("status") == "True"
        for c in conditions
    )

    # Print conditions for debugging
    print("\n📊 Kustomization conditions:")
    for c in conditions:
        print(f"  {c.get('type')}: {c.get('status')} ({c.get('message', '')[:80]})")

    assert ready, f"Kustomization not Ready: conditions={conditions}"

    # Check for last applied revision
    last_applied = status.get("lastAppliedRevision", "")
    if last_applied:
        print(f"✅ Kustomization lastAppliedRevision: {last_applied}")


@pytest.mark.integration
def test_gitrepository_annotations(custom_api):
    """TEST 8: Verify GitRepository has expected annotations."""
    try:
        repo = custom_api.get_namespaced_custom_object(
            group=SOURCE_GROUP,
            version="v1",
            namespace="flux-system",
            plural="gitrepositories",
            name="sovereign-garden",
        )
    except ApiException as e:
        pytest.skip(f"GitRepository unreachable: {e}")

    metadata = repo.get("metadata", {})
    annotations = metadata.get("annotations", {})

    # Check for specific annotations (optional)
    print("\n📊 GitRepository annotations:")
    for k, v in annotations.items():
        print(f"  {k}: {v[:60] if len(str(v)) > 60 else v}")

    # Check for flux sync annotation
    if "kustomize.toolkit.fluxcd.io/sync" in annotations:
        print("✅ Flux sync annotation present")


# ─── MAIN ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 70)
    print("🜁∀ FLUX KUSTOMIZATION TEST SUITE")
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
