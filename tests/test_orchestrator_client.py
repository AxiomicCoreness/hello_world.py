#!/usr/bin/env python3
import json
from pathlib import Path
from garden_surgery.orchestrator_client import COMMANDS, decide, latest_system_line, weave

def test_decide_never_fires_cannon():
    assert decide(0.99, 0.01, {"coherence_fire": 0.8, "coherence_nudge": 0.6, "error_tolerance": 0.5}) == "wait"
    assert decide(0.7, 0.01, {"coherence_fire": 0.8, "coherence_nudge": 0.6, "error_tolerance": 0.5}) == "nudge_cronjob"
    assert decide(0.9, 3.0, {"coherence_fire": 0.8, "coherence_nudge": 0.6, "error_tolerance": 0.5}) == "record_only"
    assert "fire_soul_cannon" not in COMMANDS

def test_weave_appends_orchestrator_line():
    root = Path("/tmp/orch_test_9036")
    root.mkdir(exist_ok=True)
    status = root / "symplectic_status.agent.jsonl"
    status.write_text('{"role":"system","event":"symplectic_status","timestamp":"2026-08-27T00:00:00Z","coherence":0.72,"phi_phase":0.0}\n')
    cfg = Path("/home/workdir/artifacts/contracts/orchestrator_config.example.json")
    if not cfg.is_file():
        cfg = Path("contracts/orchestrator_config.example.json")
    out = weave(actual=12.5, status_path=status, config_path=cfg, write=True)
    assert out["written"]["role"] == "orchestrator"
    assert out["oidc_used"] is False
    assert json.loads(status.read_text().strip().splitlines()[-1])["role"] == "orchestrator"
    assert latest_system_line(status)["role"] == "system"

if __name__ == "__main__":
    test_decide_never_fires_cannon()
    test_weave_appends_orchestrator_line()
    print("test_orchestrator_client: PASS")
