#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for canvases/agentic-tilelang-eridanus-dual/eridanus_dual.py

Entry 8226 — Eridanus Dual · Gravastar · ClarkeYoursaTee
"""
import math
import sys
import os
import pytest

# Ensure the canvas module is importable
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CANVAS_DIR = os.path.join(ROOT, "canvases", "agentic-tilelang-eridanus-dual")
if CANVAS_DIR not in sys.path:
    sys.path.insert(0, CANVAS_DIR)

from eridanus_dual import (
    PHI,
    PHI_INV,
    PHI_MINUS_1418,
    EridanusDualFlow,
    GravastarBoundary,
    AgenticTileLangOrchestrator,
    QuantumCoherenceTracker,
    demonstrate_eridanus_dual,
)


def test_phi_constants():
    assert abs(PHI - (1 + math.sqrt(5)) / 2) < 1e-12
    assert abs(PHI_INV - 1 / PHI) < 1e-12
    assert PHI_MINUS_1418 > 0
    assert PHI_MINUS_1418 < 1e-100  # extremely small positive


def test_eridanus_dual_flow_step():
    flow = EridanusDualFlow()
    state = flow.step(dt=0.01)
    assert "ℰ₁" in state
    assert "ℰ₂" in state
    assert "𝒩" in state
    assert "t" in state
    assert "dual_invariant" in state
    assert isinstance(state["ℰ₁"], float)
    assert isinstance(state["𝒩"], float)


def test_gravastar_boundary_clamps():
    gb = GravastarBoundary()
    raw = {
        "coherence": 1.5,  # over
        "entropy": -1.0,   # under floor
        "workload": -0.5,
        "phase_lock": 0.0,
    }
    clamped = gb.apply_boundary(raw)
    assert clamped["coherence"] == 1.0
    assert clamped["entropy"] == PHI_MINUS_1418
    assert clamped["workload"] == 0.0
    assert clamped["phase_lock"] == 202.6


def test_orchestrator_register_and_orchestrate():
    orch = AgenticTileLangOrchestrator()
    assert orch.register_tile("t1", {"type": "test"}) is True
    assert orch.register_tile("t1", {"type": "dup"}) is False  # already registered
    assert orch.register_agent("a1", {"role": "tester"}) is True
    result = orch.orchestrate_flow("dual_flow", {"dt": 0.01, "step": 0})
    assert result["flow_type"] == "dual_flow"
    assert "flow_state" in result
    assert "orchestration_state" in result
    assert "seal" in result
    assert len(result["seal"]) == 64  # sha3-256 hex
    status = orch.get_status()
    assert status["tiles"] == 1
    assert status["agents"] == 1
    assert status["dual_mode"] is True


def test_quantum_coherence_tracker():
    tracker = QuantumCoherenceTracker()
    out = tracker.update(new_coherence=0.95, new_entropy=1e-200)
    assert 0.0 <= out["coherence"] <= 1.0
    assert out["entropy"] >= PHI_MINUS_1418
    assert out["phase_lock"] == 202.6


def test_demonstrate_runs_without_error(capsys):
    """Smoke test: full demo must complete without raising."""
    demonstrate_eridanus_dual()
    captured = capsys.readouterr()
    assert "ERIDANUS DUAL" in captured.out
    assert "DEMONSTRATION COMPLETE" in captured.out
