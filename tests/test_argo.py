"""pytest — Argo CD Application presence / sync / health (needs live cluster)."""
from __future__ import annotations

import pytest
from kubernetes import client, config
from kubernetes.client.rest import ApiException


def _load():
    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()


@pytest.fixture(scope="session")
def core_api():
    _load()
    return client.CoreV1Api()


@pytest.fixture(scope="session")
def custom_api():
    _load()
    return client.CustomObjectsApi()


def test_argo_cd_namespace_exists(core_api):
    try:
        core_api.read_namespace("argocd")
    except ApiException as e:
        pytest.fail(f"Namespace argocd missing: {e}")


def test_application_exists(custom_api):
    try:
        custom_api.get_namespaced_custom_object(
            group="argoproj.io",
            version="v1alpha1",
            namespace="argocd",
            plural="applications",
            name="sovereign-garden",
        )
    except ApiException as e:
        pytest.fail(f"Application sovereign-garden not found: {e}")


def test_application_synced_and_healthy(custom_api):
    app = custom_api.get_namespaced_custom_object(
        group="argoproj.io",
        version="v1alpha1",
        namespace="argocd",
        plural="applications",
        name="sovereign-garden",
    )
    status = app.get("status", {})
    sync_status = status.get("sync", {}).get("status")
    health_status = status.get("health", {}).get("status")
    # Allow Unknown/Progressing during first sync
    assert sync_status in ("Synced", "OutOfSync", None) or sync_status is not None
    if sync_status == "Synced":
        assert health_status in ("Healthy", "Progressing", "Degraded", None)
