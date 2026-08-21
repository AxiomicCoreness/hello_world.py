"""Pure unit tests for argocd/ manifests — no cluster, no kubernetes client.

Runs in Argo CI and Sovereign CI/CD. Hard-fails on schema/contract drift.
Includes combinator sync-wave precedence: Services(0) → Analysis(1) →
Rollout(2) → HTTPRoute(3).
"""
from __future__ import annotations

import pathlib
import re

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
ARGO = ROOT / "argocd"
WAVE_ANN = "argocd.argoproj.io/sync-wave"


def _load(name: str):
    path = ARGO / name
    assert path.is_file(), f"missing {path}"
    docs = [d for d in yaml.safe_load_all(path.read_text()) if d is not None]
    assert docs, f"empty yaml: {path}"
    return docs[0] if len(docs) == 1 else docs


def _wave(doc) -> int:
    anns = (doc.get("metadata") or {}).get("annotations") or {}
    assert WAVE_ANN in anns, f"missing {WAVE_ANN} on {doc.get('kind')}/{doc.get('metadata', {}).get('name')}"
    return int(anns[WAVE_ANN])


def test_argocd_dir_exists():
    assert ARGO.is_dir()


def test_application_self_heal_and_destination():
    app = _load("application-sovereign-garden.yaml")
    assert app["kind"] == "Application"
    assert app["metadata"]["name"] == "sovereign-garden"
    assert app["spec"]["destination"]["namespace"] == "sovereign-garden"
    automated = app["spec"]["syncPolicy"]["automated"]
    assert automated.get("selfHeal") is True
    assert automated.get("prune") is True
    kinds = {d.get("kind") for d in app["spec"].get("ignoreDifferences", [])}
    assert "HTTPRoute" in kinds
    assert _wave(app) == 0


def test_rollout_canary_weights():
    rollout = _load("rollout-sovereign-garden.yaml")
    assert rollout["kind"] == "Rollout"
    assert rollout["spec"]["replicas"] == 3
    steps = rollout["spec"]["strategy"]["canary"]["steps"]
    weights = [s["setWeight"] for s in steps if "setWeight" in s]
    assert weights == [20, 40, 60, 80, 100]


def test_rollout_services_named():
    rollout = _load("rollout-sovereign-garden.yaml")
    canary = rollout["spec"]["strategy"]["canary"]
    assert canary.get("canaryService") == "sovereign-garden-canary"
    assert canary.get("stableService") == "sovereign-garden-stable"


def test_stable_and_canary_services():
    stable = _load("sovereign-garden-stable.yaml")
    canary = _load("sovereign-garden-canary.yaml")
    assert stable["kind"] == "Service"
    assert canary["kind"] == "Service"
    assert stable["metadata"]["name"] == "sovereign-garden-stable"
    assert canary["metadata"]["name"] == "sovereign-garden-canary"
    assert stable["spec"]["ports"][0]["port"] == 8000
    assert canary["spec"]["ports"][0]["port"] == 8000


def test_httproute_present():
    route = _load("sovereign-garden-httproute.yaml")
    assert route["kind"] == "HTTPRoute"
    assert route["metadata"]["name"]


def test_all_argocd_yaml_parse():
    files = sorted(ARGO.glob("*.yaml"))
    assert files, "no argocd/*.yaml"
    for p in files:
        docs = list(yaml.safe_load_all(p.read_text()))
        assert any(d is not None for d in docs), f"empty {p}"


def test_multistage_weights_if_present():
    p = ARGO / "rollout-sovereign-garden-gateway-multistage.yaml"
    if not p.is_file():
        pytest.skip("multistage rollout not present")
    text = p.read_text()
    weights = [int(x) for x in re.findall(r"setWeight:\s*(\d+)", text)]
    assert weights == [20, 40, 60, 80, 100]


def test_sync_wave_precedence_combinator():
    """Services → AnalysisTemplate → Rollout → HTTPRoute."""
    w_stable = _wave(_load("sovereign-garden-stable.yaml"))
    w_canary = _wave(_load("sovereign-garden-canary.yaml"))
    w_analysis = _wave(_load("analysis-health.yaml"))
    w_rollout = _wave(_load("rollout-sovereign-garden.yaml"))
    w_route = _wave(_load("sovereign-garden-httproute.yaml"))

    assert w_stable == 0
    assert w_canary == 0
    assert w_analysis == 1
    assert w_rollout == 2
    assert w_route == 3

    assert w_stable <= w_analysis < w_rollout < w_route
    assert w_canary <= w_analysis < w_rollout < w_route
