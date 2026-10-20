"""port380_mcp (root and mcp/ copies): ledger_head is derived, not the
hardcoded "8754", and the unverified "8754 -> 8755 — UNBROKEN" chain claim
is gone from /status and /status/internal."""
import importlib.util
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
COPIES = {"root": ROOT / "port380_mcp.py", "mcp": ROOT / "mcp" / "port380_mcp.py"}
SECRET = "s3cret-for-ledger-head-tests"
AUTH = {"X-Garden-Secret": SECRET}


def _load(name, path):
    spec = importlib.util.spec_from_file_location(f"port380_ledger_head_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _repo_head():
    best = None
    for f in (ROOT / "ledger.v2").glob("*.yml"):
        m = re.search(r"^entry_index:\s*[\"']?(\d+)", f.read_text(encoding="utf-8", errors="replace"), re.M)
        if m:
            v = int(m.group(1), 10)
            best = v if best is None or v > best else best
    return None if best is None else str(best)


@pytest.fixture(params=sorted(COPIES), ids=sorted(COPIES))
def mod(request, monkeypatch):
    monkeypatch.delenv("LEDGER_HEAD", raising=False)
    monkeypatch.delenv("LEDGER_DIR", raising=False)
    m = _load(request.param, COPIES[request.param])
    monkeypatch.setattr(m, "GARDEN_SECRET", SECRET)
    return m


def _bodies(mod):
    c = TestClient(mod.app)
    return c.get("/status").json(), c.get("/status/internal", headers=AUTH).json()


def test_default_head_is_repo_max(mod):
    exp = _repo_head()
    if exp is None:
        pytest.skip("no ledger.v2 entries in this checkout")
    pub, internal = _bodies(mod)
    assert pub["ledger_head"] == internal["ledger_head"] == exp
    assert exp != "8754"


def test_no_hardcoded_head_or_unbroken_claim(mod):
    for body in _bodies(mod):
        assert body.get("ledger_head") != "8754"
        assert "witness_chain" not in body
        assert "UNBROKEN" not in str(body)


def test_env_override(mod, monkeypatch):
    monkeypatch.setenv("LEDGER_HEAD", "4242")
    pub, internal = _bodies(mod)
    assert pub["ledger_head"] == internal["ledger_head"] == "4242"


def test_blank_env_override_ignored(mod, monkeypatch, tmp_path):
    (tmp_path / "a.yml").write_text("entry_index: 17\n", encoding="utf-8")
    monkeypatch.setenv("LEDGER_HEAD", "   ")
    monkeypatch.setenv("LEDGER_DIR", str(tmp_path))
    assert _bodies(mod)[1]["ledger_head"] == "17"


def test_unknown_fallback(mod, monkeypatch, tmp_path):
    monkeypatch.setenv("LEDGER_DIR", str(tmp_path / "absent"))
    pub, internal = _bodies(mod)
    assert pub["ledger_head"] == internal["ledger_head"] == "unknown"


def test_raw_text_base10_and_top_level_only(mod, tmp_path):
    (tmp_path / "a.yml").write_text("entry_index: 0755\n", encoding="utf-8")
    (tmp_path / "b.yml").write_text("payload:\n  entry_index: 99999\nentry_index: 9001\n", encoding="utf-8")
    (tmp_path / "c.yaml").write_text("entry_index: 99998\n", encoding="utf-8")
    (tmp_path / "d.yml").write_text('entry_index: "10000"  # quoted\n', encoding="utf-8")
    assert mod.derive_ledger_head(tmp_path) == "10000"
    (tmp_path / "d.yml").unlink()
    assert mod.derive_ledger_head(tmp_path) == "9001"


def test_internal_still_protected(mod):
    assert TestClient(mod.app).get("/status/internal").status_code == 403
