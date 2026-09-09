"""Pydantic model tests. FILLED enum exists; default state is IDLE."""

from fastMCP.models.envelope import Envelope
from fastMCP.models.state import State, StateEnum
from fastMCP.models.event import Event
from fastMCP.constants import PHI, FILLED


def test_envelope_default_phi():
    env = Envelope()
    assert abs(env.phi - PHI) < 1e-12
    assert env.state == "unfilled"


def test_state_default_idle():
    st = State()
    assert st.state == StateEnum.IDLE
    assert st.host == "127.0.0.1"
    assert st.port == 8024
    assert FILLED is False


def test_event_alias():
    ev = Event(entry=9196, event="/fastmcp_self_improve_stubs", hash="0" * 64)
    assert ev.entry == 9196
