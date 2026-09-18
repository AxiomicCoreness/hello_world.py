"""Differential checks across T0 / P0 / C0 engines (one file)."""

from terminal_axiom import certificate as term_cert
from producer_axiom import certificate as prod_cert
from consumer_axiom import certificate as cons_cert
from consumer_axiom.axiom import Demand, Root, Stream, axiom_c0, invariant_holds
from producer_axiom.axiom import Generator, Root as ProdRoot, axiom_p0
from terminal_axiom.axiom import TerminalAxiom


def test_three_engines_emit_certificates():
    for cert_fn, engine_hint in (
        (term_cert, "Location"),
        (prod_cert, "Product"),
        (cons_cert, "Rate"),
    ):
        c = cert_fn()
        assert c["all_pass"] is True
        assert engine_hint.split()[0] in c["axiom"] or engine_hint in c["axiom"]
        assert c["policy"]["dual_asgi"] == "127.0.0.1:8024"
        assert c["policy"]["mcp_filled"] is False
        assert c["policy"]["bind_0000"] is False


def test_certificate_schema_keys_align():
    keys = {"axiom", "formal", "valence", "checks", "all_pass", "witness", "timestamp", "terminal_state", "policy"}
    for cert_fn in (term_cert, prod_cert, cons_cert):
        c = cert_fn()
        assert keys <= set(c.keys())


def test_engines_are_distinct():
    t = TerminalAxiom().axiom
    p = axiom_p0(Generator(1.0), ProdRoot("recognizable"))
    c = axiom_c0(Demand(2.0), Root(scale=2.0))
    assert t != "Product stems from generative root"
    assert p.coords[0] == 1.0
    assert c.value == 1.0
    assert invariant_holds(Demand(6.0), Root(2.0), Stream(3.0))


def test_consumer_identity_and_zero_peer_to_others():
    from consumer_axiom.axiom import IDENTITY_SCALE, ZeroRootError
    import pytest

    assert axiom_c0(Demand(9.0), Root(IDENTITY_SCALE)).value == 9.0
    with pytest.raises(ZeroRootError):
        axiom_c0(Demand(1.0), Root(0.0))
