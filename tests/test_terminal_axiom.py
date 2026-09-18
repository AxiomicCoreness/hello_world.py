"""Tests for terminal_axiom (T₀ / ⊕)."""

from terminal_axiom import (
    TerminalAxiom,
    AXIOM_TEXT,
    Propagation,
    Root,
    axiom_t0,
    verify,
    certificate,
    MANEUVERS,
)


def test_axiom_text():
    assert AXIOM_TEXT == "Location stems from propagated root"


def test_axiom_t0_additive():
    loc = axiom_t0(Propagation(strength=2.0), Root(scale=3.0))
    assert loc.coords[0] == 5.0


def test_identity_zero():
    loc = axiom_t0(Propagation(strength=4.0), Root(scale=0.0))
    assert loc.coords[0] == 4.0


def test_final_state_narrative():
    state = TerminalAxiom().compute_final_state()
    assert state["valence"] == "CLOSED_POSITIVE_PROVEN"
    assert "subject" in state["structure"]


def test_verify_and_certificate():
    assert all(verify().values())
    cert = certificate()
    assert cert["all_pass"] is True
    assert cert["policy"]["dual_asgi"] == "127.0.0.1:8024"


def test_maneuvers_four():
    assert len(MANEUVERS) == 4
