"""app.config ledger_head: derived from the highest ledger.v2/*.yml
entry_index (raw text, base 10), LEDGER_HEAD env override, 'unknown'
fallback instead of a hardcoded stale number."""
import importlib
import re
from pathlib import Path

import pytest

import app.config as config

ROOT = Path(__file__).resolve().parents[1]


def _expected_head_from_repo():
    best = None
    for f in (ROOT / "ledger.v2").glob("*.yml"):
        m = re.search(r"^entry_index:\s*[\"']?(\d+)", f.read_text(encoding="utf-8", errors="replace"), re.M)
        if m:
            v = int(m.group(1), 10)
            best = v if best is None or v > best else best
    return best


def _write(d, name, body):
    (d / name).write_text(body, encoding="utf-8")


def test_repo_head_matches_highest_entry_index():
    exp = _expected_head_from_repo()
    if exp is None:
        pytest.skip("no ledger.v2 entries in this checkout")
    assert config.derive_ledger_head() == str(exp)
    assert config.derive_ledger_head() != "9142"


def test_highest_index_not_filename_or_lexical(tmp_path):
    _write(tmp_path, "a.yml", "entry_index: 999\n")
    _write(tmp_path, "b.yml", "entry_index: 10000\n")
    _write(tmp_path, "c.yml", "entry_index: 9295\n")
    assert config.derive_ledger_head(tmp_path) == "10000"


def test_leading_zero_is_decimal_not_octal(tmp_path):
    # YAML 1.1 would read 0755 as 493 and 0999 as a string.
    _write(tmp_path, "x.yml", "entry_index: 0755\n")
    assert config.derive_ledger_head(tmp_path) == "755"
    _write(tmp_path, "y.yml", "entry_index: 0999\n")
    assert config.derive_ledger_head(tmp_path) == "999"


def test_quoted_and_commented_index(tmp_path):
    _write(tmp_path, "q.yml", 'entry_index: "9300"  # quoted\n')
    _write(tmp_path, "s.yml", "entry_index: '9299'\n")
    assert config.derive_ledger_head(tmp_path) == "9300"


def test_only_top_level_key_counts(tmp_path):
    _write(tmp_path, "n.yml", "payload:\n  entry_index: 99999\nentry_index: 9001\n")
    _write(tmp_path, "t.yml", "prev_entry_index: 88888\n")
    assert config.derive_ledger_head(tmp_path) == "9001"


def test_non_yml_files_ignored(tmp_path):
    _write(tmp_path, "README.md", "entry_index: 99999\n")
    _write(tmp_path, "e.yaml", "entry_index: 99998\n")
    _write(tmp_path, "ok.yml", "entry_index: 7\n")
    assert config.derive_ledger_head(tmp_path) == "7"


def test_missing_dir_unknown(tmp_path):
    assert config.derive_ledger_head(tmp_path / "nope") == "unknown"


def test_empty_or_unparseable_dir_unknown(tmp_path):
    assert config.derive_ledger_head(tmp_path) == "unknown"
    _write(tmp_path, "bad.yml", "entry_index: not-a-number\n")
    assert config.derive_ledger_head(tmp_path) == "unknown"


def test_env_override_wins(monkeypatch, tmp_path):
    _write(tmp_path, "a.yml", "entry_index: 5\n")
    monkeypatch.setenv("LEDGER_DIR", str(tmp_path))
    monkeypatch.setenv("LEDGER_HEAD", "1234")
    assert config.resolve_ledger_head() == "1234"


def test_blank_env_override_ignored(monkeypatch, tmp_path):
    _write(tmp_path, "a.yml", "entry_index: 5\n")
    monkeypatch.setenv("LEDGER_DIR", str(tmp_path))
    monkeypatch.setenv("LEDGER_HEAD", "  ")
    assert config.resolve_ledger_head() == "5"


def test_ledger_dir_env_missing_gives_unknown(monkeypatch, tmp_path):
    monkeypatch.delenv("LEDGER_HEAD", raising=False)
    monkeypatch.setenv("LEDGER_DIR", str(tmp_path / "absent"))
    assert config.resolve_ledger_head() == "unknown"


def test_health_route_reports_derived_head(monkeypatch):
    fastapi = pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    monkeypatch.delenv("LEDGER_HEAD", raising=False)
    monkeypatch.delenv("LEDGER_DIR", raising=False)
    importlib.reload(config)
    import app.routes.health as health
    importlib.reload(health)
    a = fastapi.FastAPI()
    a.include_router(health.router)
    body = TestClient(a).get("/health").json()
    exp = _expected_head_from_repo()
    assert body["ledger_head"] == (str(exp) if exp is not None else "unknown")
    assert body["ledger_head"] != "9142"
