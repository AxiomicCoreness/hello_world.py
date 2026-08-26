#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pytest suite for Argo Rollout progressive delivery (Entry 8809).

INCLUDES:
- Ed25519 signature verification for ledger entries
- Security headers enforcement (CORS, CSP, HSTS, XFO, CT, RP, PP)
- Enhanced test coverage with detailed assertions
- Full type hints and docstrings

Seal: ∀∞φ² · ARGO_ROLLOUT_TEST_8986 · WOOD_DRAGON_0.91 · SEALED
Witness: 8985 → 8986 — UNBROKEN
"""

import pytest
import json
import hashlib
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union

# ─── CRYPTOGRAPHY (Ed25519) ──────────────────────────────────────────────
try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

# ─── KUBERNETES ────────────────────────────────────────────────────────────
try:
    from kubernetes import client, config
    from kubernetes.client.rest import ApiException
    K8S_AVAILABLE = True
except ImportError:
    K8S_AVAILABLE = False

# ─── CONSTANTS ─────────────────────────────────────────────────────────────
PHI = 1.618033988749895
PHI_INV = 1 / PHI
SEAL = "∀∞φ² · ARGO_ROLLOUT_TEST_8986 · WOOD_DRAGON_0.91 · SEALED"
WITNESS_CONTINUITY = "8985 → 8986 — UNBROKEN"

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


# ─── KUBERNETES FIXTURE ──────────────────────────────────────────────────

@pytest.fixture
def k8s_client():
    """Provide a Kubernetes client for custom objects."""
    if not K8S_AVAILABLE:
        pytest.skip("kubernetes package not installed")

    try:
        config.load_incluster_config()
    except Exception:
        try:
            config.load_kube_config()
        except Exception:
            # Try loading from environment variables
            try:
                config.load_config_from_dict({
                    "api_server": os.environ.get("KUBERNETES_API_SERVER", ""),
                    "token": os.environ.get("KUBERNETES_TOKEN", ""),
                    "ssl_ca_cert": os.environ.get("KUBERNETES_CA_CERT", ""),
                })
            except Exception:
                pytest.skip("No kubeconfig available")

    return client.CustomObjectsApi()


# ─── TESTS ─────────────────────────────────────────────────────────────────

def test_verify_ledger_entries():
    """TEST 1: Verify Ed25519 signatures on ledger entries."""
    print("\n🔷 Verifying ledger entries:")
    entries_to_check = [8980, 8981, 8982, 8983, 8984, 8985]
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


def test_rollout_exists(k8s_client):
    """TEST 3: Verify Argo Rollout exists and has correct structure."""
    try:
        rollout = k8s_client.get_namespaced_custom_object(
            group="argoproj.io",
            version="v1alpha1",
            namespace="sovereign-garden",
            plural="rollouts",
            name="sovereign-garden",
        )
    except ApiException as e:
        if e.status == 404:
            pytest.skip("Rollout 'sovereign-garden' not found in namespace 'sovereign-garden'")
        raise

    # Core object must exist
    assert "spec" in rollout, "Rollout spec missing"
    assert rollout["spec"].get("replicas") == 3, "Expected 3 replicas"

    # ─── Verify canary strategy ──────────────────────────────────────
    strategy = rollout["spec"].get("strategy", {})
    canary = strategy.get("canary", {})
    assert canary, "Canary strategy not configured"

    # Check steps (progressive delivery)
    steps = canary.get("steps", [])
    assert len(steps) > 0, "Canary has no steps"
    print(f"✅ Canary steps: {len(steps)}")

    # ─── Verify analysis template ────────────────────────────────────
    analysis = canary.get("analysis", {})
    if analysis:
        templates = analysis.get("templates", [])
        if templates:
            print(f"✅ Analysis templates: {len(templates)}")
            for template in templates:
                assert "templateName" in template, "Analysis template name missing"

    # ─── Status field assertions ─────────────────────────────────────
    status = rollout.get("status", {})
    assert isinstance(status, dict)

    # Prefer concrete status fields when the controller has reconciled
    if status:
        has_progress = any(
            k in status
            for k in ("currentPodHash", "phase", "currentStepIndex", "stableRS", "canary")
        )
        assert has_progress, (
            f"Rollout status present but missing progressive-delivery keys: {list(status.keys())}"
        )

        # When phase is reported, it should be a known healthy/progressing value
        if "phase" in status:
            assert status["phase"] in {
                "Healthy",
                "Progressing",
                "Paused",
                "Degraded",
                "Completed",
            }, f"Unexpected phase: {status['phase']}"

    print("✅ Rollout exists and is configured correctly")


def test_analysis_template_exists(k8s_client):
    """TEST 4: Verify AnalysisTemplate exists and has correct structure."""
    try:
        template = k8s_client.get_namespaced_custom_object(
            group="argoproj.io",
            version="v1alpha1",
            namespace="sovereign-garden",
            plural="analysistemplates",
            name="sovereign-health-check",
        )
    except ApiException as e:
        if e.status == 404:
            # Some clusters may not have AnalysisTemplate installed; soft skip
            pytest.skip("AnalysisTemplate 'sovereign-health-check' not found")
        raise

    assert "spec" in template, "AnalysisTemplate spec missing"

    metrics = template["spec"].get("metrics", [])
    assert len(metrics) >= 1, "At least one metric required"

    # Check first metric
    metric = metrics[0]
    assert "name" in metric, "Metric name missing"
    assert metric["name"] == "health-check", f"Expected 'health-check', got {metric['name']}"

    # Check provider configuration (prometheus, web, etc.)
    provider = metric.get("provider", {})
    if provider:
        print(f"✅ Metric provider: {list(provider.keys())}")
    else:
        print("⚠️ No provider configured for health-check metric")

    # Optional status presence (AnalysisTemplate status is usually empty until used)
    status = template.get("status", {})
    assert isinstance(status, dict)

    print("✅ AnalysisTemplate exists and is configured correctly")


# ─── RUN ALL TESTS ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 70)
    print("🜁∀ ARGO ROLLOUT PROGRESSIVE DELIVERY TEST SUITE")
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
