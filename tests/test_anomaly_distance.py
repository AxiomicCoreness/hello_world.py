#!/usr/bin/env python3
from garden_surgery.anomaly_distance import (
    CLAIMED_N,
    FLAG,
    MATH_ENTRY,
    PHI_INV,
    audit_8356_claims,
    claimed_histogram_sum,
    distances,
    l2,
    math_form,
    override_payload,
    payload,
    phi_cloud,
    response_headers,
    sample_report,
)


def test_metric_zero_at_centroid():
    c = (PHI_INV, 0.0, 0.0)
    assert l2(c, c) == 0.0
    d = distances([c, c, c], c)
    assert d == [0.0, 0.0, 0.0]


def test_histogram_sum_is_flagged():
    a = audit_8356_claims()
    assert a["flag"] == FLAG
    assert a["claimed_histogram_sum"] != CLAIMED_N
    assert a["declaration_overstated"] is True
    assert a["live_swarm_instantiated"] is False
    assert claimed_histogram_sum() == 147600


def test_sample_is_not_the_swarm():
    s = sample_report(n=144, seed=8356)
    assert s["sample_n"] == 144
    assert s["stats"]["n"] == 144
    p = payload()
    assert p["inspect_336"]["possible"] is False
    assert p["math_entry"] == MATH_ENTRY == 9028
    form = math_form()
    assert "d_i" in form["ascii"][1]
    assert form["threshold_is_not_an_axiom"] is True
    assert response_headers()["X-Garden-Entry"] == "9030"
    assert response_headers()["X-Garden-Fusion"] == "515"
    o = override_payload()
    assert o["entry_index"] == 9030
    assert o["target_entry"] == 9029
    assert o["constraints_enforced"]["fusion_canonical"] == 515
    assert o["math_form"]["distance"].startswith("d_i")
    assert p["instantiates_144000_processes"] is False
    assert p["fusion_canonical"] == 515
    pts = phi_cloud(n=20, seed=1)
    assert all(x * x + y * y + z * z <= 1.0 + 1e-12 for x, y, z in pts)


if __name__ == "__main__":
    test_metric_zero_at_centroid()
    test_histogram_sum_is_flagged()
    test_sample_is_not_the_swarm()
    print("test_anomaly_distance: PASS")
