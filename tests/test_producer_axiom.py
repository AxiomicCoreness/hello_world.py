"""Tests for producer_axiom (P₀)."""

from producer_axiom.axiom import (
    Product,
    Generator,
    Root,
    axiom_p0,
    VALENCE,
    AXIOM_TEXT,
)
from producer_axiom.verification import verify, certificate


def test_axiom_text():
    assert AXIOM_TEXT == "Product stems from generative root"


def test_axiom_p0_returns_product():
    g = Generator(intensity=1.0)
    r = Root(pattern="recognizable")
    p = axiom_p0(g, r)
    assert isinstance(p, Product)
    assert p.coords[0] == 1.0


def test_axiom_p0_deterministic():
    g = Generator(intensity=1.0)
    r = Root(pattern="recognizable")
    assert axiom_p0(g, r) == axiom_p0(g, r)


def test_valence():
    assert VALENCE == "PRODUCTIVE_POSITIVE_PROVEN"


def test_verify_all_pass():
    checks = verify()
    assert all(checks.values()), checks


def test_certificate():
    cert = certificate()
    assert cert["all_pass"] is True
    assert cert["policy"]["dual_asgi"] == "127.0.0.1:8024"
    assert cert["policy"]["mcp_filled"] is False
    assert "PRODUCER_AXIOM" in cert["witness"]
