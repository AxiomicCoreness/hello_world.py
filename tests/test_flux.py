"""pytest — Flux GitRepository / Kustomization (needs live cluster + Flux)."""
from __future__ import annotations

import pytest
from kubernetes import client, config
from kubernetes.client.rest import ApiException

SOURCE_GROUP = "source.toolkit.fluxcd.io"
KUSTOMIZE_GROUP = "kustomize.toolkit.fluxcd.io"


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


def test_flux_namespace_exists(core_api):
    try:
        core_api.read_namespace("flux-system")
    except ApiException as e:
        pytest.fail(f"Namespace flux-system missing: {e}")


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
        pytest.fail(f"GitRepository missing: {e}")


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
        pytest.fail(f"Kustomization missing: {e}")


def test_gitrepository_ready(custom_api):
    repo = custom_api.get_namespaced_custom_object(
        group=SOURCE_GROUP,
        version="v1",
        namespace="flux-system",
        plural="gitrepositories",
        name="sovereign-garden",
    )
    conditions = repo.get("status", {}).get("conditions", [])
    if not conditions:
        pytest.skip("No status conditions yet")
    ready = any(
        c.get("type") == "Ready" and c.get("status") == "True" for c in conditions
    )
    assert ready, f"GitRepository not Ready: {conditions}"
