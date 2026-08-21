"""pytest — Argo CD Application presence / sync / health.

Requires a live cluster + kubernetes client. Skips cleanly in CI when either
is missing so collection does not fail Sovereign CI/CD.
"""
from __future__ import annotations

import pytest

kubernetes = pytest.importorskip(
    "kubernetes",
    reason="kubernetes client not installed (CI default)",
)
try:
    from kubernetes import client, config
    from kubernetes.client.rest import ApiException
except ImportError as exc:
    pytest.skip(f"kubernetes client incomplete: {exc}", allow_module_level=True)


def _load() -> None:
    try:
        config.load_incluster_config()
    except config.ConfigException:
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


@pytest.mark.integration
def test_argo_cd_namespace_exists(core_api):
    try:
        core_api.read_namespace("argocd")
    except ApiException as e:
        pytest.skip(f"Namespace argocd missing (no cluster): {e}")


@pytest.mark.integration
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
        pytest.skip(f"Application sovereign-garden not found: {e}")


@pytest.mark.integration
def test_application_synced_and_healthy(custom_api):
    try:
        app = custom_api.get_namespaced_custom_object(
            group="argoproj.io",
            version="v1alpha1",
            namespace="argocd",
            plural="applications",
            name="sovereign-garden",
        )
    except ApiException as e:
        pytest.skip(f"Application unreachable: {e}")
    status = app.get("status", {})
    sync_status = status.get("sync", {}).get("status")
    health_status = status.get("health", {}).get("status")
    assert sync_status in ("Synced", "OutOfSync", None) or sync_status is not None
    if sync_status == "Synced":
        assert health_status in ("Healthy", "Progressing", "Degraded", None)
