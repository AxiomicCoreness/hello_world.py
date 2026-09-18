"""Tests for terminal_axiom (T0) — semantic behavior unchanged."""

from terminal_axiom import TerminalAxiom, AXIOM_TEXT, verify, certificate
from terminal_axiom.axiom import MANEUVERS


def test_axiom_text():
    assert AXIOM_TEXT == "Location stems from propagated root"


def test_final_state():
    state = TerminalAxiom().compute_final_state()
    assert state["valence"] == "CLOSED_POSITIVE_PROVEN"
    assert "subject" in state["structure"]
    assert "propagated root" in state["axiom"].lower()


def test_verify_all_pass():
    checks = verify()
    assert all(checks.values()), checks


def test_certificate():
    cert = certificate()
    assert cert["all_pass"] is True
    assert cert["engine"] == "terminal_axiom"
    assert cert["policy"]["dual_asgi"] == "127.0.0.1:8024"
    assert cert["policy"]["mcp_filled"] is False
    assert cert["policy"]["bind_0000"] is False


def test_maneuvers_four():
    assert len(MANEUVERS) == 4
