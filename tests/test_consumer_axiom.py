"""Tests for consumer_axiom (C₀ / saturating ⊘)."""

from consumer_axiom.axiom import (
    Consumption,
    Demand,
    Supply,
    axiom_c0,
    VALENCE,
    IDENTITY_DEMAND,
)
from consumer_axiom.verification import verify, certificate


def test_axiom_c0_basic():
    c = axiom_c0(Demand(10.0), Supply(3.0))
    assert isinstance(c, Consumption)
    assert c.amount == 7.0


def test_axiom_c0_clamping():
    assert axiom_c0(Demand(3.0), Supply(10.0)).amount == 0.0


def test_axiom_c0_zero_root():
    assert axiom_c0(Demand(5.0), Supply(0.0)).amount == 5.0


def test_axiom_c0_non_negative():
    assert axiom_c0(Demand(1.0), Supply(100.0)).amount >= 0


def test_axiom_c0_identity_inf():
    c = axiom_c0(Demand(IDENTITY_DEMAND), Supply(5.0))
    assert c.amount == float("inf")


def test_valence():
    assert VALENCE == "SATURATING_POSITIVE_PROVEN"


def test_verify_and_certificate():
    assert all(verify().values())
    cert = certificate()
    assert cert["all_pass"] is True
    assert cert["engine"] == "consumer_axiom"
