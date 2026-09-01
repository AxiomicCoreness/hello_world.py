# tests/test_argo.py
import pytest
from kubernetes import client, config
from kubernetes.client.rest import ApiException

@pytest.fixture(scope="session")
def k8s_custom_client():
    try:
        config.load_incluster_config()
    except:
        config.load_kube_config()
    return client.CustomObjectsApi()

def test_argocd_namespace_exists(k8s_custom_client):
    v1 = client.CoreV1Api()
    ns = "argocd"
    try:
        v1.read_namespace(ns)
    except ApiException as e:
        pytest.fail(f"Namespace {ns} does not exist")

def test_argocd_application_exists(k8s_custom_client):
    app_name = "sovereign-garden"
    try:
        k8s_custom_client.get_namespaced_custom_object(
            group="argoproj.io",
            version="v1alpha1",
            namespace="argocd",
            plural="applications",
            name=app_name
        )
    except ApiException as e:
        pytest.fail(f"Application {app_name} not found: {e}")

def test_argocd_application_synced(k8s_custom_client):
    app = k8s_custom_client.get_namespaced_custom_object(
        group="argoproj.io",
        version="v1alpha1",
        namespace="argocd",
        plural="applications",
        name="sovereign-garden"
    )
    status = app.get("status", {})
    sync = status.get("sync", {})
    assert sync.get("status") == "Synced", "Application not synced"
