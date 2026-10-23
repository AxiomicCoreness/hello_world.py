"""Gearbox module tests. Does not start uvicorn."""

import pytest

# Local fastMCP package (bind/gearbox/models/routes) is not the PyPI fastmcp SDK.
pytest.importorskip("fastMCP", reason="local fastMCP package not present; PyPI fastmcp ≠ fastMCP.bind")

from fastMCP.gearbox import FILLED, gearbox, before_main, app
from fastapi_flywheel_gearbox import Gearbox


def test_filled_false():
    assert FILLED is False


def test_gearbox_instance():
    assert isinstance(gearbox, Gearbox)


def test_before_main_fingerprint():
    out = before_main()
    assert "restart_fingerprint" in out


def test_app_is_shared_object():
    from fastapi_flywheel_gearbox import app as root_app
    assert app is root_app
