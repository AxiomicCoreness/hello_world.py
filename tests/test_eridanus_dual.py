#!/usr/bin/env python3
"""Smoke tests for sealed Entry 8226 (Eridanus Dual). Does not rewrite ledger."""
from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANVAS = ROOT / "canvases" / "agentic-tilelang-eridanus-dual"
sys.path.insert(0, str(CANVAS))

from eridanus_dual import (  # noqa: E402
    PHI,
    PHI_INV,
    PHI_MINUS_1418,
    AgenticTileLangOrchestrator,
    EridanusDualFlow,
    GravastarBoundary,
    QuantumCoherenceTracker,
    demonstrate_eridanus_dual,
)


def test_phi_identity():
    assert abs(PHI - (1 + math.sqrt(5)) / 2) < 1e-12
    assert abs(PHI_INV - 1 / PHI) < 1e-15
    assert abs(PHI * PHI_INV - 1.0) < 1e-15


def test_dual_flow_keys_and_bounds():
    flow = EridanusDualFlow()
    state = flow.compute_dual_flow(0.0)
    assert set(state) >= {"ℰ₁", "ℰ₂", "𝓝", "t", "dual_invariant"}
    assert abs(state["ℰ₁"]) <= PHI_INV + 1e-12
    assert abs(state["ℰ₂"]) <= PHI_INV * PHI_INV + 1e-12
    assert state["𝓝"] >= 0.0
    stepped = flow.step(0.01)
    assert stepped["t"] > 0.0
    digest = flow.seal_witness("TEST", {"ok": True})
    assert isinstance(digest, str) and len(digest) == 64
    assert len(flow.witness_chain) == 1


def test_gravastar_clamps():
    bound = GravastarBoundary()
    out = bound.apply_boundary({"coherence": 1.5, "entropy": 0.0, "workload": -3.0})
    assert out["coherence"] == 1.0
    assert out["entropy"] == PHI_MINUS_1418
    assert out["workload"] == 0.0
    assert out["phase_lock"] == 202.6


def test_orchestrator_register_and_flow():
    orch = AgenticTileLangOrchestrator()
    assert orch.register_tile("t1", {"k": 1}) is True
    assert orch.register_tile("t1", {"k": 2}) is False
    assert orch.register_agent("a1", {"role": "test"}) is True
    result = orch.orchestrate_flow("dual_flow", {"dt": 0.01})
    assert result["flow_type"] == "dual_flow"
    assert "seal" in result and len(result["seal"]) == 64
    status = orch.get_status()
    assert status["tiles"] == 1
    assert status["agents"] == 1
    assert status["witness_count"] >= 1
    assert status["orchestration_state"]["coherence"] <= 1.0


def test_coherence_tracker_bounds():
    tracker = QuantumCoherenceTracker()
    high = tracker.update(new_coherence=2.0, new_entropy=-1.0)
    assert high["coherence"] == 1.0
    assert high["entropy"] == PHI_MINUS_1418
    low = tracker.update(new_coherence=-0.5)
    assert low["coherence"] == 0.0
    assert len(tracker.history) == 2


def test_demo_runs():
    demonstrate_eridanus_dual()


if __name__ == "__main__":
    test_phi_identity()
    test_dual_flow_keys_and_bounds()
    test_gravastar_clamps()
    test_orchestrator_register_and_flow()
    test_coherence_tracker_bounds()
    test_demo_runs()
    print("test_eridanus_dual: PASS")
