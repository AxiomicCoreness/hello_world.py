"""Bind policy tests — Dual ASGI 127.0.0.1:8024 only."""

import pytest
from fastMCP.bind import resolve, BIND_HOST, BIND_PORT


def test_resolve_default():
    host, port = resolve()
    assert host == BIND_HOST
    assert port == BIND_PORT


def test_resolve_wildcard():
    with pytest.raises(ValueError):
        resolve(host="0.0.0.0")
    with pytest.raises(ValueError):
        resolve(host="::")


def test_resolve_wrong_port():
    with pytest.raises(ValueError):
        resolve(port=8080)
