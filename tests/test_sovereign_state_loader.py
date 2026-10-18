"""Round-trip the sovereign_state.py writer and the data-only loader."""
import importlib.util
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
BEACONS = ROOT / "beacons"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def loader():
    return _load("sovereign_state_loader", BEACONS / "sovereign_state_loader.py")


@pytest.fixture
def writer():
    np = pytest.importorskip("numpy")
    return np, _load("sovereign_state_writer", BEACONS / "sovereign_state_writer.py")


def test_writer_round_trip(writer, loader, tmp_path):
    np, w = writer
    metrics = {
        "timestamp": "2026-10-18T00:00:00+00:00",
        "planck_reconstruction": {"rho_purity": np.float64(1.618), "lattice_nodes": np.int64(34)},
        "genesis_gate": {"actualized_state": np.array([[1.0, 0.0], [0.0, 1.0]])},
        "flags": [np.bool_(True), None, "ok"],
        "psi_lock": complex(-0.5, 1.5),
        "pair": (np.float32(0.5), 2),
        "nonfinite": float("inf"),
    }
    out = tmp_path / "sovereign_state.py"
    assert w.write_sovereign_state(metrics, path=str(out)) == str(out)
    text = out.read_text(encoding="utf-8")
    assert "STATE = {" in text and "np." not in text and "\nstate =" not in text
    got = loader.load_precomputed_state(str(out))
    assert got["planck_reconstruction"] == {"rho_purity": 1.618, "lattice_nodes": 34}
    assert type(got["planck_reconstruction"]["rho_purity"]) is float
    assert got["genesis_gate"]["actualized_state"] == [[1.0, 0.0], [0.0, 1.0]]
    assert got["flags"] == [True, None, "ok"]
    assert got["psi_lock"] == complex(-0.5, 1.5)
    assert got["pair"] == (0.5, 2)
    assert got["nonfinite"] == "inf"


def test_writer_default_path_is_next_to_module(writer, monkeypatch, tmp_path):
    _, w = writer
    written = {}

    real_open = open

    def fake_open(path, *a, **k):
        written["path"] = path
        return real_open(tmp_path / "x.py", *a, **k)

    monkeypatch.setattr("builtins.open", fake_open)
    w.write_sovereign_state({"timestamp": "t"})
    assert written["path"] == str(BEACONS / "sovereign_state.py")


def test_missing_file(loader, tmp_path):
    assert loader.load_precomputed_state(str(tmp_path / "nope.py")) == {}


@pytest.mark.parametrize("body", [
    "state = {'a': 1}\n",                       # old lowercase writer
    "STATE = {'rho': np.float64(1.0)}\n",       # numpy repr, not a literal
    "STATE = {'a': __import__('os').getcwd()}\n",
    "STATE = {'a': 1\n",                        # truncated
    "\xff\xfe garbage",
])
def test_malformed_file(loader, tmp_path, body):
    p = tmp_path / "sovereign_state.py"
    p.write_text(body, encoding="utf-8")
    assert loader.load_precomputed_state(str(p)) == {}


def test_loader_never_executes(loader, tmp_path):
    p = tmp_path / "sovereign_state.py"
    marker = tmp_path / "pwned"
    p.write_text(f"open({str(marker)!r}, 'w').close()\nSTATE = {{'ok': 1}}\n", encoding="utf-8")
    assert loader.load_precomputed_state(str(p)) == {"ok": 1}
    assert not marker.exists()
