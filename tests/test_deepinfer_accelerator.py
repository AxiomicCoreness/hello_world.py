"""CPU-only tests for the optional DeepInfer accelerator adapter."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_deepinfer_unavailable_without_package(monkeypatch: pytest.MonkeyPatch) -> None:
    # Ensure a missing deepinfer does not crash import of our adapter.
    monkeypatch.setitem(sys.modules, "deepinfer", None)  # type: ignore[assignment]
    # Force re-import path: clear cached module if present
    sys.modules.pop("engine.deepinfer_accelerator", None)
    # Simulate ImportError by removing any real deepinfer
    real_import = importlib.import_module

    def fake_import(name: str, *args, **kwargs):
        if name == "deepinfer" or name.startswith("deepinfer."):
            raise ImportError("deepinfer not installed in test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(importlib, "import_module", fake_import)
    from engine import deepinfer_accelerator as acc

    # Reset module-level error from prior imports in same process
    acc._DEEPINFER_IMPORT_ERROR = None  # noqa: SLF001
    assert acc.deepinfer_available() is False
    status = acc.deepinfer_status()
    assert status["available"] is False
    assert status["role"] == "optional_accelerator"
    assert "deepseek.api" in status["primary_engines"]


def test_complete_falls_back_without_cuda(monkeypatch: pytest.MonkeyPatch) -> None:
    sys.modules.pop("engine.deepinfer_accelerator", None)
    from engine import deepinfer_accelerator as acc

    def boom_import(name: str, *args, **kwargs):
        if name == "deepinfer" or name.startswith("deepinfer."):
            raise ImportError("no deepinfer")
        return importlib.__dict__["import_module"](name) if False else __import__(name, fromlist=["*"])

    # Prefer patching _try_import_deepinfer for stability
    monkeypatch.setattr(acc, "_try_import_deepinfer", lambda: None)
    monkeypatch.delenv("DEEPINFER_FORCE", raising=False)
    monkeypatch.delenv("DEEPINFER_HF_MODEL_DIR", raising=False)

    # Stub deepseek.api so test does not need network
    class FakeApi:
        @staticmethod
        def complete_sync(prompt: str, max_tokens: int = 64, prefer: str = "auto"):
            return {"mode": "offline", "text": f"ok:{prompt}", "model": "test"}

    monkeypatch.setitem(sys.modules, "deepseek.api", FakeApi())  # type: ignore[arg-type]
    monkeypatch.setitem(sys.modules, "deepseek", FakeApi())  # type: ignore[arg-type]

    # Inject via import inside complete — patch the function after import attempt
    def fake_complete_sync(prompt: str, max_tokens: int = 64, prefer: str = "auto"):
        return {"mode": "offline", "text": f"ok:{prompt}", "model": "test"}

    import types

    fake_mod = types.ModuleType("deepseek.api")
    fake_mod.complete_sync = fake_complete_sync  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "deepseek.api", fake_mod)
    parent = types.ModuleType("deepseek")
    parent.api = fake_mod  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "deepseek", parent)

    out = acc.complete("ping", max_tokens=8)
    assert out["text"] == "ok:ping"
    assert out.get("backend") == "deepseek.api"
    assert out["deepinfer"]["available"] is False


def test_aime_number_re_accepts_four_digits() -> None:
    """Overlay regex must not truncate 4-digit AIME-style answers in tail fallback."""
    import re

    bench_path = ROOT / "eval" / "aime" / "bench.py"
    text = bench_path.read_text()
    # Body after header must use \\d+ (not \\d{1,3})
    body = text.split("_NUMBER_RE", 1)[1]
    assert r"(\d+)" in body
    assert r"(\d{1,3})" not in body
    pat = re.compile(r"(?<![\w.])(\d+)(?![\w.])")
    assert pat.findall("answer 2026 done") == ["2026"]
    assert pat.findall("score 42 end") == ["42"]
