"""Tests for consumer_axiom (C₀ Spec B)."""

import pytest

from consumer_axiom.axiom import (
    AXIOM_TEXT,
    VALENCE,
    IDENTITY_SCALE,
    Demand,
    Root,
    Stream,
    Rate,
    ZeroRootError,
    axiom_c0,
    output_from,
    invariant_holds,
)
from consumer_axiom.verification import verify, certificate


def test_axiom_text():
    assert AXIOM_TEXT == "Rate stems from demand over root"


def test_axiom_c0_division():
    c = axiom_c0(Demand(value=6.0), Root(scale=2.0))
    assert isinstance(c, Rate)
    assert c.value == pytest.approx(3.0)


def test_identity_scale():
    c = axiom_c0(Demand(value=5.0), Root(scale=IDENTITY_SCALE))
    assert c.value == pytest.approx(5.0)


def test_zero_root_raises_at_division():
    r0 = Root(scale=0.0)  # construction allowed
    with pytest.raises(ZeroRootError):
        axiom_c0(Demand(value=1.0), r0)


def test_negatives_allowed():
    c = axiom_c0(Demand(value=-4.0), Root(scale=2.0))
    assert c.value == pytest.approx(-2.0)
    c2 = axiom_c0(Demand(value=4.0), Root(scale=-2.0))
    assert c2.value == pytest.approx(-2.0)


def test_invariant_c_o_eq_d_s():
    d = Demand(value=6.0)
    r = Root(scale=2.0)
    s = Stream(intensity=3.0)
    assert invariant_holds(d, r, s)
    rate = axiom_c0(d, r)
    out = output_from(s, r)
    assert rate.value * out.value == pytest.approx(d.value * s.intensity)


def test_determinism():
    d, r = Demand(value=1.5), Root(scale=0.5)
    assert axiom_c0(d, r) == axiom_c0(d, r)


def test_valence():
    assert VALENCE == "CONSUMING_POSITIVE_PROVEN"


def test_verify_and_certificate():
    assert all(verify().values())
    cert = certificate()
    assert cert["all_pass"] is True
    assert cert["engine"] == "consumer_axiom"
    assert cert["policy"]["dual_asgi"] == "127.0.0.1:8024"
    assert cert["policy"]["mcp_filled"] is False
