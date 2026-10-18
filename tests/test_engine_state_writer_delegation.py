"""beacons/sovereign_engine_deepseek.py delegates to beacons/sovereign_state_writer.py
(one writer, no duplicate)."""
import ast
import importlib.util
from pathlib import Path

import pytest

BEACONS = Path(__file__).resolve().parents[1] / "beacons"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_engine_has_no_inline_writer():
    tree = ast.parse((BEACONS / "sovereign_engine_deepseek.py").read_text(encoding="utf-8"))
    names = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    assert "write_sovereign_state" not in names and "_to_native" not in names
    assert "_state_writer" in names


def test_engine_state_writer_is_user_writer(tmp_path, monkeypatch):
    pytest.importorskip("numpy")
    monkeypatch.setenv("HOME", str(tmp_path / "home"))  # engine mkdirs under ~ at import
    eng = _load("sovereign_engine_deepseek_deleg", BEACONS / "sovereign_engine_deepseek.py")
    w = eng._state_writer()
    assert Path(w.__file__).resolve() == (BEACONS / "sovereign_state_writer.py").resolve()
    out = w.write_sovereign_state({"timestamp": "t", "x": 1}, path=str(tmp_path / "s.py"))
    loader = _load("sovereign_state_loader_deleg", BEACONS / "sovereign_state_loader.py")
    assert loader.load_precomputed_state(out)["x"] == 1
