#!/usr/bin/env python3
from garden_surgery.kerr_atlassar_rrlyrae import (
    FORMULA_Q, PISANO_MOD10, audit_9032, audit_9033, audit_9034,
    pisano_period, report_payload, w_of_q,
)

def test_q_formula_is_half_not_declared_q():
    a = audit_9032()
    assert abs(FORMULA_Q - 0.5) < 1e-15
    assert a["declared_Q_matches_written_formula"] is False
    assert w_of_q(0.0) > 2.7

def test_pisano_mod10_is_60():
    assert pisano_period(10) == PISANO_MOD10 == 60
    a = audit_9033()
    assert a["period_matches"] is True
    assert a["euler"] == 2

def test_wisdom_couplings_are_phi_powers():
    a = audit_9034()
    assert a["coupling_is_phi_neg3"] is True
    assert a["dissipation_is_phi_neg7"] is True
    assert a["nonlinear_is_phi4"] is True

def test_report_rejects_placeholder_and_preserves_bodies():
    p = report_payload()
    assert p["placeholder_yaml_hash_rejected"] is True
    assert p["fusion_canonical"] == 515
    assert p["hyperion_preserved"] == 516
    assert len(p["substrata_sha3_256"]) == 64

if __name__ == "__main__":
    test_q_formula_is_half_not_declared_q()
    test_pisano_mod10_is_60()
    test_wisdom_couplings_are_phi_powers()
    test_report_rejects_placeholder_and_preserves_bodies()
    print("test_kerr_pisano: PASS")
