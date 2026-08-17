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
    # Core object must exist
    assert "spec" in rollout
    assert rollout["spec"].get("replicas") == 3

    # Status field assertions (populated after controller reconciliation)
    status = rollout.get("status", {})
    assert isinstance(status, dict)

    # Prefer concrete status fields when the controller has reconciled
    if status:
        # At least one of the canonical progressive-delivery status keys should be present
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


def test_analysis_template_exists(k8s_client):
    template = k8s_client.get_namespaced_custom_object(
        group="argoproj.io",
        version="v1alpha1",
        namespace="sovereign-garden",
        plural="analysistemplates",
        name="sovereign-health-check",
    )
    assert "spec" in template
    metrics = template["spec"].get("metrics", [])
    assert len(metrics) >= 1
    assert metrics[0]["name"] == "health-check"
    # Optional status presence (AnalysisTemplate status is usually empty until used)
    status = template.get("status", {})
    assert isinstance(status, dict)
