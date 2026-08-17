"""Pytest suite for Argo Rollout progressive delivery (Entry 8809)."""
import pytest

try:
    from kubernetes import client, config
    K8S_AVAILABLE = True
except ImportError:
    K8S_AVAILABLE = False


@pytest.fixture
def k8s_client():
    if not K8S_AVAILABLE:
        pytest.skip("kubernetes package not installed")
    try:
        config.load_incluster_config()
    except Exception:
        try:
            config.load_kube_config()
        except Exception:
            pytest.skip("No kubeconfig available")
    return client.CustomObjectsApi()


def test_rollout_exists(k8s_client):
    rollout = k8s_client.get_namespaced_custom_object(
        group="argoproj.io",
        version="v1alpha1",
        namespace="sovereign-garden",
        plural="rollouts",
        name="sovereign-garden",
    )
    assert rollout.get("status", {}).get("currentPodHash") is not None or "spec" in rollout


def test_analysis_template_exists(k8s_client):
    template = k8s_client.get_namespaced_custom_object(
        group="argoproj.io",
        version="v1alpha1",
        namespace="sovereign-garden",
        plural="analysistemplates",
        name="sovereign-health-check",
    )
    assert template["spec"]["metrics"][0]["name"] == "health-check"
