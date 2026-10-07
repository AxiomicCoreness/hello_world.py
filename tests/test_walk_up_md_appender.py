"""Contract tests for scripts/walk_up_md_appender.py (ledger 9163)."""
from __future__ import annotations

import importlib.util
from pathlib import Path


def _load():
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / "walk_up_md_appender.py"
    spec = importlib.util.spec_from_file_location("walk_up_md_appender", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_contract_unfilled_no_wildcard_bind():
    mod = _load()
    assert mod.FILLED is False
    assert mod.BIND == "127.0.0.1"
    assert mod.DUAL_ASGI == "127.0.0.1:8024"
    assert Path("/") in mod.FORBIDDEN_STOPS


def test_dry_run_does_not_write(tmp_path):
    mod = _load()
    sample = tmp_path / "NOTE.md"
    sample.write_text("# keep\n", encoding="utf-8")
    change = "\n<!-- TAP -->\n"
    appended, skipped = mod.walk_up_append_md(change, start_dir=str(tmp_path), apply=False)
    assert appended == 0
    assert skipped >= 1
    assert sample.read_text(encoding="utf-8") == "# keep\n"


def test_apply_is_append_only_and_idempotent(tmp_path):
    mod = _load()
    sample = tmp_path / "NOTE.md"
    sample.write_text("# keep\n", encoding="utf-8")
    change = "\n<!-- TAP -->\n"
    appended, _ = mod.walk_up_append_md(change, start_dir=str(tmp_path), apply=True)
    assert appended == 1
    assert sample.read_text(encoding="utf-8") == "# keep\n\n<!-- TAP -->\n"
    appended2, skipped2 = mod.walk_up_append_md(change, start_dir=str(tmp_path), apply=True)
    assert appended2 == 0
    assert skipped2 >= 1
    assert sample.read_text(encoding="utf-8") == "# keep\n\n<!-- TAP -->\n"
