"""Tests for producer_axiom (P₀ / ⊗)."""

from producer_axiom.axiom import Product, Generator, Root, Stream, axiom_p0, VALENCE, AXIOM_TEXT
from producer_axiom.verification import verify, certificate


def test_axiom_text():
    assert AXIOM_TEXT == "Product stems from generative root"


def test_axiom_p0_multiply():
    p = axiom_p0(Generator(intensity=2.0), Root(scale=3.0))
    assert isinstance(p, Product)
    assert p.coords[0] == 6.0


def test_stream_alias():
    p = axiom_p0(Stream(intensity=2.0), Root(scale=4.0))
    assert p.coords[0] == 8.0


def test_identity_one():
    p = axiom_p0(Generator(5.0), Root(scale=1.0))
    assert p.coords[0] == 5.0


def test_absorbing_zero():
    assert axiom_p0(Generator(5.0), Root(scale=0.0)).coords[0] == 0.0


def test_valence():
    assert VALENCE == "PRODUCTIVE_POSITIVE_PROVEN"


def test_verify_and_certificate():
    assert all(verify().values())
    assert certificate()["all_pass"] is True
