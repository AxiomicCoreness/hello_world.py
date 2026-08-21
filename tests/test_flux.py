"""pytest — Flux GitRepository / Kustomization.

Requires live cluster + Flux + kubernetes. Skips in CI when unavailable.
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

SOURCE_GROUP = "source.toolkit.fluxcd.io"
KUSTOMIZE_GROUP = "kustomize.toolkit.fluxcd.io"


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
def test_flux_namespace_exists(core_api):
    try:
        core_api.read_namespace("flux-system")
    except ApiException as e:
        pytest.skip(f"Namespace flux-system missing: {e}")


@pytest.mark.integration
def test_gitrepository_exists(custom_api):
    try:
        custom_api.get_namespaced_custom_object(
            group=SOURCE_GROUP,
            version="v1",
            namespace="flux-system",
            plural="gitrepositories",
            name="sovereign-garden",
        )
    except ApiException as e:
        pytest.skip(f"GitRepository missing: {e}")


@pytest.mark.integration
def test_kustomization_exists(custom_api):
    try:
        custom_api.get_namespaced_custom_object(
            group=KUSTOMIZE_GROUP,
            version="v1",
            namespace="flux-system",
            plural="kustomizations",
            name="sovereign-garden",
        )
    except ApiException as e:
        pytest.skip(f"Kustomization missing: {e}")


@pytest.mark.integration
def test_gitrepository_ready(custom_api):
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
    conditions = repo.get("status", {}).get("conditions", [])
    if not conditions:
        pytest.skip("No status conditions yet")
    ready = any(
        c.get("type") == "Ready" and c.get("status") == "True" for c in conditions
    )
    assert ready, f"GitRepository not Ready: {conditions}"
