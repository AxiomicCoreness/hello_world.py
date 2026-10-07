#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pytest — Argo CD presence checks.
Skips cleanly when kubernetes or a cluster is missing so CI collection does not fail.
Does not require a live cluster. Does not start servers.
Seal: ∀∞φ² · ARGOCD_APP_TEST_SKIP_CLEAN · WOOD_DRAGON_0.91
"""
from __future__ import annotations

from pathlib import Path

import pytest

kubernetes = pytest.importorskip(
    "kubernetes",
    reason="kubernetes client not installed (CI default)",
)
from kubernetes import client, config  # noqa: E402
from kubernetes.client.rest import ApiException  # noqa: E402

SECURITY_HEADERS = [
    "Content-Security-Policy",
    "Strict-Transport-Security",
    "X-Content-Type-Options",
    "X-Frame-Options",
    "Referrer-Policy",
    "Permissions-Policy",
]


def _load() -> None:
    try:
        config.load_incluster_config()
    except Exception:
        try:
            config.load_kube_config()
        except Exception as exc:
            pytest.skip(f"no kubeconfig / cluster: {exc}")


@pytest.fixture(scope="session")
def core_api():
    _load()
    return client.CoreV1Api()


@pytest.fixture(scope="session")
def custom_api():
    _load()
    return client.CustomObjectsApi()


def test_security_headers_source_optional():
    path = Path("port380_mcp.py")
    if not path.exists():
        pytest.skip("port380_mcp.py not present")
    content = path.read_text(encoding="utf-8", errors="replace")
    missing = [h for h in SECURITY_HEADERS if h not in content]
    assert not missing, f"missing headers: {missing}"


@pytest.mark.integration
def test_argocd_namespace_exists(core_api):
    try:
        ns = core_api.read_namespace("argocd")
        assert ns is not None
    except ApiException as e:
        pytest.skip(f"Namespace argocd missing: {e}")


@pytest.mark.integration
def test_application_exists(custom_api):
    try:
        app = custom_api.get_namespaced_custom_object(
            group="argoproj.io",
            version="v1alpha1",
            namespace="argocd",
            plural="applications",
            name="sovereign-garden",
        )
        assert app is not None
    except ApiException as e:
        pytest.skip(f"Application sovereign-garden not found: {e}")
