"""Bind-rule unit test — no network."""
from __future__ import annotations

import pytest

from src.cli_loopback import assert_loopback_bind


def test_loopback_ok():
    assert assert_loopback_bind("127.0.0.1") == "127.0.0.1"
    assert assert_loopback_bind("::1") == "::1"


def test_rejects_wildcard():
    with pytest.raises(RuntimeError, match="Cosmic Alignment"):
        assert_loopback_bind("0.0.0.0")
    with pytest.raises(RuntimeError, match="Cosmic Alignment"):
        assert_loopback_bind("192.168.1.1")
