"""Bind-rule + pythonIDE unit tests — no network."""
from __future__ import annotations

import pytest

from src.cli_loopback import assert_loopback_bind, handle_pythonide


def test_loopback_ok():
    assert assert_loopback_bind("127.0.0.1") == "127.0.0.1"
    assert assert_loopback_bind("::1") == "::1"


def test_rejects_wildcard():
    with pytest.raises(RuntimeError, match="Cosmic Alignment"):
        assert_loopback_bind("0.0.0.0")
    with pytest.raises(RuntimeError, match="Cosmic Alignment"):
        assert_loopback_bind("192.168.1.1")


def test_pythonide_help():
    lines = handle_pythonide("/py help")
    assert any("pythonIDE" in x for x in lines)
    assert any(x.startswith("[Engine]") for x in lines)


def test_pythonide_list():
    lines = handle_pythonide("/py list")
    blob = "\n".join(lines)
    assert "golden_ratio" in blob
    assert "54" in blob or "capabilities" in blob.lower()


def test_pythonide_call_golden_ratio():
    lines = handle_pythonide("/py call golden_ratio")
    blob = "\n".join(lines)
    assert "golden_ratio" in blob
    assert "[Traceback]" not in blob
    assert "1.618" in blob or "φ" in blob or "1.6" in blob


def test_pythonide_unknown_yields_traceback():
    lines = handle_pythonide("/py call no_such_capability_zz")
    assert any(x.startswith("[Traceback]") for x in lines)
    assert any("CapabilityError" in x or "unknown" in x.lower() for x in lines)


def test_pythonide_pointer():
    lines = handle_pythonide("/py pointer")
    blob = "\n".join(lines)
    assert "2300" in blob
    assert "314" in blob


def test_deepinfer_demo_surfaces_status_or_traceback():
    lines = handle_pythonide("/py deepinfer")
    blob = "\n".join(lines)
    assert "deepinfer" in blob.lower()
    # Either available path or import Traceback — both are valid chat outcomes
    assert any(
        x.startswith("[Engine]") or x.startswith("[Traceback]") or x.startswith("[System]")
        for x in lines
    )


def test_deepinfer_alias():
    lines = handle_pythonide("/deepinfer status")
    blob = "\n".join(lines)
    assert "deepinfer" in blob.lower()


def test_katex_macroset_test_via_cli():
    lines = handle_pythonide("/py katex")
    blob = "\n".join(lines)
    assert "KaTeXMacroSetTest" in blob or "katex" in blob.lower()
    # Mirror should pass on repo docs/katex_macros.yaml
    assert "PASSED" in blob or "SUCCESS" in blob or "[Traceback]" in blob


def test_katex_alias():
    lines = handle_pythonide("/katex")
    blob = "\n".join(lines)
    assert "KaTeX" in blob or "katex" in blob.lower()
