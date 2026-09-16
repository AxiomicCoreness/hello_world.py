# tests/test_reward_protocol.py

import pytest

from reward_protocol import (
    PHI, Gate, phi_harmonic_weights, spu, verdict,
    bounded_reward, timescales_separated,
)
from fiduciary_node_rewards import (
    PHI as PHI2, Q_INVARIANT, N_NODES, TIERS,
    tier_of, nodes_in_tier, calculate_node_reward,
    total_pool, verify_reward_pool,
)


# --- reward_protocol -------------------------------------------------------

def test_phi_consistent():
    assert PHI == pytest.approx(PHI2)


def test_weights_sum_to_one():
    for n in (1, 3, 7, 20):
        w = phi_harmonic_weights(n)
        assert abs(sum(w) - 1.0) < 1e-12


def test_spu_linear_known():
    m = (1.0, 0.5, 0.0)
    w = (0.5, 0.25, 0.25)
    assert spu(m, w, "linear") == pytest.approx(0.625)


def test_spu_geometric_zero_kills():
    m = (1.0, 0.0, 1.0)
    w = (1/3, 1/3, 1/3)
    assert spu(m, w, "geometric") == 0.0


def test_spu_harmonic_unity():
    m = (1.0, 1.0, 1.0)
    w = (1/3, 1/3, 1/3)
    assert spu(m, w, "harmonic") == pytest.approx(1.0)


def test_spu_rejects_out_of_range():
    with pytest.raises(ValueError):
        spu((1.5,), (1.0,))


def test_spu_rejects_bad_weights():
    with pytest.raises(ValueError):
        spu((0.5,), (0.4,))


def test_gate_verdicts():
    g = Gate(tau_hi=0.618, tau_lo=0.382, eps=0.05)
    assert verdict(0.9, 0.9, g) == "PASS"
    assert verdict(0.1, 0.1, g) == "FAIL"
    assert verdict(0.5, 0.5, g) == "HOLD"
    assert verdict(0.9, 0.1, g) == "DRIFT"


def test_bounded_reward():
    assert bounded_reward(0.5, 10.0) == pytest.approx(5.0)


def test_timescales():
    assert timescales_separated(1000.0, 10.0, 0.1)
    assert not timescales_separated(1000.0, 500.0, 0.1)


# --- fiduciary_node_rewards ------------------------------------------------

def test_tier_boundaries():
    assert tier_of(1) == 1
    assert tier_of(7) == 1
    assert tier_of(8) == 2
    assert tier_of(49) == 2
    assert tier_of(50) == 3
    assert tier_of(144008) == 7


def test_tier_counts_sum():
    assert sum(nodes_in_tier(t) for _, t in TIERS) == N_NODES


def test_rewards_decrease_with_tier():
    r1 = calculate_node_reward(1)
    r_last = calculate_node_reward(N_NODES)
    assert r1 > r_last
    assert r1 == pytest.approx(Q_INVARIANT * PHI ** -1)
    assert r_last == pytest.approx(Q_INVARIANT * PHI ** -7)


def test_pool_equals_manual_sum():
    manual = 0.0
    for upper, tier in TIERS:
        lower = next((u for u, t in TIERS if t == tier - 1), 0)
        manual += (upper - lower) * Q_INVARIANT * PHI ** -tier
    assert total_pool() == pytest.approx(manual)


def test_verify_pool_no_expectation():
    ok, total = verify_reward_pool()
    assert ok
    assert total > 0


def test_verify_pool_correct_expectation():
    ok, total = verify_reward_pool(expected=total_pool())
    assert ok


def test_verify_pool_rejects_old_ledger_value():
    # 4.486 was the previously declared pool; it does not match the tier sum.
    ok, _ = verify_reward_pool(expected=4.486, tol=1e-3)
    assert not ok
