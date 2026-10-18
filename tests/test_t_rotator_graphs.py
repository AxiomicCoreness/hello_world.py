"""Tests for scripts/t_rotator_graphs.py (synthetic ledgers in tmp dirs)."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("t_rotator_graphs", ROOT / "scripts" / "t_rotator_graphs.py")
trg = importlib.util.module_from_spec(_spec)
sys.modules["t_rotator_graphs"] = trg
_spec.loader.exec_module(trg)


def _write(d: Path, name: str, body: str) -> None:
    (d / name).write_text(body, encoding="utf-8")


def _entry(n, event, ts, prev=None, seal_hex=None, raw_index=None):
    lines = [f"entry_index: {raw_index if raw_index is not None else n}",
             f"timestamp: {ts}", f"event: {event}", "status: SEALED"]
    if prev:
        lines.append(f"prev_hash: {prev}")
    if seal_hex:
        lines.append(f'seal: "∀∞φ² · TEST · SEALED · {seal_hex}"')
    return "\n".join(lines) + "\n"


@pytest.fixture
def ledger(tmp_path):
    d = tmp_path / "ledger.v2"
    d.mkdir()
    s1 = trg.regime_b_seal(9281, "/a")
    s2 = trg.regime_b_seal(9282, "/b")
    _write(d, "9280.yml", "entry_index: 9280\ntimestamp: ETERNAL_NOW_ANCHORED_TO_2026-09-30Z\n"
                          "event: /old\nseal_sha3_256: " + "1" * 64 + "\n")
    _write(d, "9281.yml", _entry(9281, "/a", "'2026-10-01T12:00:00Z'", prev="1" * 64, seal_hex=s1))
    _write(d, "9282.yml", _entry(9282, "/b", "'2026-10-02T13:30:00Z'", prev=s1, seal_hex=s2))
    # wrong seal and a prev_hash that does not match 9282
    _write(d, "9283.yml", _entry(9283, "/c", "PENDING_9283", prev="f" * 64, seal_hex="0" * 64))
    _write(d, "README.md", "not an entry\n")
    return d


def test_regime_b_seal_known_vector():
    # 9287 in the real ledger.v2 declares this digest.
    assert trg.regime_b_seal(9287, "/timestamp_resolution_9286") == (
        "e22df48390050e90dea511bde535c45db01ed58298c7349faceb5c88bf88fb34")


def test_index_from_raw_text_avoids_octal(tmp_path):
    d = tmp_path / "l"
    d.mkdir()
    _write(d, "0010.yml", "entry_index: 0010\ntimestamp: '2026-10-01T12:00:00Z'\nevent: /x\n")
    (e,) = trg.load_entries(d)
    assert e.index == 10  # yaml.safe_load would give 8


@pytest.mark.parametrize("raw,kind,offset", [
    ("'2026-10-17T03:42:00Z'", "strict", -8 * 3600 - 18 * 60),
    ('"2026-10-16T12:00:00Z"', "strict", 0.0),
    ("2026-10-16T13:00:00+01:00", "lenient", 0.0),
    ("ETERNAL_NOW_ANCHORED_TO_2026-09-27Z", "date_only", None),
    ("PENDING_9283", "unparsed", None),
])
def test_parse_timestamp_noon_offset(raw, kind, offset):
    r = trg.parse_timestamp(raw)
    assert r["kind"] == kind
    assert r["offset"] == offset
    assert r["strict"] is (kind == "strict")


def test_chain_links_and_seal_breaks(ledger):
    by = {e.index: e for e in trg.load_entries(ledger)}
    assert sorted(by) == [9280, 9281, 9282, 9283]
    assert by[9280].seal_status == "not_judged"
    assert by[9281].link_status == "ok"      # via 9280 seal_sha3_256
    assert by[9281].seal_status == "ok"
    assert by[9282].link_status == "ok"
    assert by[9283].seal_status == "mismatch"
    assert by[9283].link_status == "broken"


def test_mermaid_marks_breaks(ledger):
    mm = trg.mermaid(trg.load_entries(ledger))
    assert mm.splitlines()[1] == "flowchart LR"
    assert "E9281 -->|prev_hash| E9282" in mm
    assert "E9282 -.-x|prev_hash break| E9283" in mm
    assert "SEAL BREAK" in mm
    assert 'E9281["9281<br/>/a<br/>seal ok"]' in mm
    assert "class E9283 brk" in mm or ",E9283" in mm


def test_run_writes_outputs_and_leaves_ledger_untouched(ledger, tmp_path):
    before = {p.name: p.read_bytes() for p in ledger.iterdir()}
    out = tmp_path / "out"
    summary = trg.run(ledger, out, plots=True)
    for name in ("chain.mmd", "entries.json", "drift.png", "timeline.png", "summary.json"):
        assert (out / name).stat().st_size > 0
    assert (out / "drift.png").read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert summary["seal_breaks"] == [9283]
    assert summary["link_breaks"] == [9283]
    assert json.loads((out / "entries.json").read_text())[1]["noon_offset_s"] == 0.0
    assert {p.name: p.read_bytes() for p in ledger.iterdir()} == before


def test_refuses_out_dir_inside_ledger(ledger):
    with pytest.raises(SystemExit):
        trg.run(ledger, ledger / "graphs", plots=False)


def test_cli_no_plots(ledger, tmp_path, capsys):
    rc = trg.main(["--ledger-dir", str(ledger), "--out-dir", str(tmp_path / "o"), "--no-plots"])
    assert rc == 0
    assert (tmp_path / "o" / "chain.mmd").exists()
    assert not (tmp_path / "o" / "drift.png").exists()
    assert json.loads(capsys.readouterr().out)["entries"] == 4


def test_matplotlib_fallback_without_seaborn(ledger, tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "seaborn", None)  # import seaborn -> ImportError
    trg.run(ledger, tmp_path / "nosns", plots=True)
    assert (tmp_path / "nosns" / "drift.png").stat().st_size > 0
