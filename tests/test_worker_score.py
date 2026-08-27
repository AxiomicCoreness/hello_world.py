#!/usr/bin/env python3
import json
from pathlib import Path
from garden_surgery.worker_score import PHI4_SQRT7, coherence, phi_corrected_score, score_payload

def test_score_bounds_and_no_oidc():
    p = score_payload(12.5, 59.83)
    assert p["mcp_live"] is False
    assert p["oidc_client_credentials_used"] is False
    assert abs(PHI4_SQRT7 - 18.134249263375494) < 1e-9

def test_phase_zero_is_standard_line():
    assert abs(coherence(0.0) - 1.0) < 1e-15
    assert abs(phi_corrected_score(12.5, 0.0) - 12.5) < 1e-12

def test_contract_files_exist_without_secrets():
    root = Path(__file__).resolve().parents[1]
    cfg = json.loads((root / "contracts" / "orchestrator_config.example.json").read_text())
    assert "oidc_client_secret" not in cfg

if __name__ == "__main__":
    test_score_bounds_and_no_oidc()
    test_phase_zero_is_standard_line()
    test_contract_files_exist_without_secrets()
    print("test_worker_score: PASS")
