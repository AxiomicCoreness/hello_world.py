#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for Eridanus Dual – Sovereign Flow Field Engine (Entry 8226)
Validates dual flow invariants, Gravastar boundary conditions,
Agentic TileLang orchestrator, and quantum coherence tracking.
"""
import math
import sys
import os
import pytest

# Ensure the canvas module is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "canvases", "agentic-tilelang-eridanus-dual"))

from eridanus_dual import (
    PHI, PHI_INV, PHI_MINUS_1418, PHI16, PHI26, PHI8, PHI34,
    EridanusDualFlow, GravastarBoundary, AgenticTileLangOrchestrator,
    QuantumCoherenceTracker, demonstrate_eridanus_dual
)


class TestGoldenConstants:
    def test_phi_value(self):
        assert abs(PHI - (1 + math.sqrt(5)) / 2) < 1e-15

    def test_phi_inv(self):
        assert abs(PHI_INV - 1 / PHI) < 1e-15
        assert abs(PHI * PHI_INV - 1.0) < 1e-15

    def test_entropy_floor(self):
        assert PHI_MINUS_1418 > 0
        assert PHI_MINUS_1418 < 1e-100


class TestEridanusDualFlow:
    def setup_method(self):
        self.flow = EridanusDualFlow()

    def test_initial_state(self):
        assert self.flow.null_ban == 10.06
        assert self.flow.dual_mode is True
        assert self.flow.flow_state["coherence"] == 1.0
        assert self.flow.flow_state["phase_lock"] == 202.6
        assert self.flow.flow_state["entropy"] == PHI_MINUS_1418

    def test_compute_dual_flow_structure(self):
        result = self.flow.compute_dual_flow(0.0)
        assert "ℰ₁" in result
        assert "ℰ₂" in result
        assert "𝒩" in result
        assert "t" in result
        assert "dual_invariant" in result
        assert result["t"] == 0.0

    def test_step_advances_time(self):
        r1 = self.flow.step(dt=0.01)
        r2 = self.flow.step(dt=0.01)
        assert r2["t"] > r1["t"]

    def test_witness_seal(self):
        h = self.flow.seal_witness("TEST_EVENT", {"k": "v"})
        assert isinstance(h, str)
        assert len(h) == 64  # sha3_256 hex
        assert len(self.flow.witness_chain) == 1


class TestGravastarBoundary:
    def setup_method(self):
        self.gb = GravastarBoundary()

    def test_boundary_params(self):
        assert self.gb.boundary["type"] == "GRAVASTAR"
        assert self.gb.boundary["radius"] == PHI16
        assert self.gb.boundary["mass"] == PHI26
        assert self.gb.boundary["surface_gravity"] == PHI8
        assert self.gb.phase_lock == 202.6

    def test_apply_boundary_clamps_coherence(self):
        state = {"coherence": 1.5, "entropy": 0.0, "workload": -1.0}
        out = self.gb.apply_boundary(state)
        assert out["coherence"] == 1.0
        assert out["entropy"] == PHI_MINUS_1418
        assert out["workload"] == 0.0
        assert out["phase_lock"] == 202.6


class TestAgenticTileLangOrchestrator:
    def setup_method(self):
        self.orch = AgenticTileLangOrchestrator()

    def test_register_tile(self):
        ok = self.orch.register_tile("t1", {"type": "test"})
        assert ok is True
        assert "t1" in self.orch.tiles
        # duplicate should fail
        assert self.orch.register_tile("t1", {"type": "test"}) is False

    def test_register_agent(self):
        ok = self.orch.register_agent("a1", {"role": "tester"})
        assert ok is True
        assert "a1" in self.orch.agents

    def test_orchestrate_flow(self):
        result = self.orch.orchestrate_flow("dual_flow", {"dt": 0.01})
        assert "flow_type" in result
        assert "flow_state" in result
        assert "orchestration_state" in result
        assert "seal" in result
        assert result["orchestration_state"]["phase_lock"] == 202.6

    def test_get_status(self):
        status = self.orch.get_status()
        assert status["tiles"] == 0
        assert status["agents"] == 0
        assert status["dual_mode"] is True


class TestQuantumCoherenceTracker:
    def setup_method(self):
        self.tracker = QuantumCoherenceTracker()

    def test_initial(self):
        assert self.tracker.coherence == 1.0
        assert self.tracker.entropy == PHI_MINUS_1418
        assert self.tracker.phase_lock == 202.6

    def test_update_clamps(self):
        out = self.tracker.update(new_coherence=1.5, new_entropy=-1.0)
        assert out["coherence"] == 1.0
        assert out["entropy"] == PHI_MINUS_1418
        assert len(self.tracker.history) == 1


def test_demonstrate_runs_without_error(capsys):
    """Smoke test: the full demonstration completes without raising."""
    demonstrate_eridanus_dual()
    captured = capsys.readouterr()
    assert "ERIDANUS DUAL" in captured.out
    assert "DEMONSTRATION COMPLETE" in captured.out
