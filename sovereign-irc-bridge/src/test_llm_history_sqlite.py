# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""HISTORY_BACKEND=sqlite: window, reset/archive, atomicity, reopen, import, unicode.

Offline only (no model server: a loopback stub or a monkeypatched completion),
and every file lives under ``tmp_path``. A tripwire swaps the default history
path so that anything falling back to the live default
(/workspace/bridge-serving/llm_history.jsonl or its ``.sqlite3`` sibling)
lands inside tmp_path and fails the test instead.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from src import history_import, llm_chat, llm_history_sqlite as hs

LIVE_DEFAULT_JSONL = Path("/workspace/bridge-serving/llm_history.jsonl")
LIVE_DEFAULT_DB = LIVE_DEFAULT_JSONL.with_suffix(".sqlite3")
BRIDGE_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _env(monkeypatch, tmp_path):
    for k in ("HISTORY_BACKEND", "LLM_HISTORY_DB", "LLM_HISTORY_DB_BUSY_MS", "LLM_HISTORY_MAX_TOKENS",
              "LLM_BACKEND", "LLM_FALLBACK", "LLM_RAW_REPLY", "LLM_SYSTEM_PROMPT"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("LLM_BUILD_FEEDBACK", "0")
    monkeypatch.setenv("HISTORY_BACKEND", "sqlite")
    monkeypatch.setenv("LLM_HISTORY_PATH", str(tmp_path / "llm_history.jsonl"))
    tripwire = tmp_path / "DEFAULT_HISTORY_PATH_TRIPWIRE.jsonl"
    monkeypatch.setattr(llm_chat, "DEFAULT_HISTORY_PATH", str(tripwire))
    live_before = {p: (p.stat().st_mtime_ns if p.exists() else None) for p in (LIVE_DEFAULT_JSONL, LIVE_DEFAULT_DB)}
    yield
    assert not tripwire.exists() and not tripwire.with_suffix(".sqlite3").exists(), \
        "test wrote llm history to the default (live) path"
    for p, m in live_before.items():
        assert (p.stat().st_mtime_ns if p.exists() else None) == m, f"test touched live {p}"


@pytest.fixture()
def db(tmp_path) -> Path:
    return tmp_path / "llm_history.sqlite3"


def _fake_model(monkeypatch, reply="ok", err=None, reasoning=None):
    calls = []

    def fake(messages):
        calls.append(messages)
        meta = {"backend": "gguf", "path": "/v1/chat/completions", "mode": "jinja", "family": "chatml"}
        if reasoning:
            meta["reasoning"] = reasoning
        return (None if err else reply), err, meta
    monkeypatch.setattr(llm_chat, "complete_routed", fake)
    return calls


def _rows(db: Path, sql: str, args=()):
    con = sqlite3.connect(str(db))
    try:
        return con.execute(sql, args).fetchall()
    finally:
        con.close()


# ---------------------------------------------------------------- config / schema

def test_default_db_sits_next_to_jsonl_and_tests_never_resolve_live(tmp_path, monkeypatch):
    assert llm_chat.history_backend() == "sqlite"
    assert llm_chat.history_db_path() == tmp_path / "llm_history.sqlite3"
    monkeypatch.setenv("LLM_HISTORY_DB", str(tmp_path / "x.db"))
    assert llm_chat.history_db_path() == tmp_path / "x.db"
    monkeypatch.delenv("LLM_HISTORY_DB")
    monkeypatch.delenv("LLM_HISTORY_PATH")
    assert llm_chat.history_db_path() not in (LIVE_DEFAULT_DB, None)
    assert tmp_path in llm_chat.history_db_path().parents
    monkeypatch.setenv("LLM_HISTORY_PATH", "")
    assert llm_chat.history_db_path() is None and llm_chat.history_store() is None


def test_backend_default_is_jsonl_and_unknown_falls_back(monkeypatch):
    monkeypatch.delenv("HISTORY_BACKEND")
    assert llm_chat.history_backend() == "jsonl" and llm_chat.history_store() is None
    monkeypatch.setenv("HISTORY_BACKEND", "mariadb")  # not implemented yet → jsonl, logged
    assert llm_chat.history_backend() == "jsonl"


def test_schema_pragmas_and_user_version(db):
    st = hs.SqliteHistory(db).stats()
    assert st["schema"] == hs.SCHEMA_VERSION == 1 and st["journal_mode"] == "wal"
    tables = {r[0] for r in _rows(db, "SELECT name FROM sqlite_master WHERE type IN ('table','index')")}
    assert {"sessions", "messages", "messages_session_id", "sessions_one_live"} <= tables
    cols = [r[1] for r in _rows(db, "PRAGMA table_info(messages)")]
    assert cols == ["id", "session_id", "role", "content", "format", "thinking", "model_label", "ts", "dedupe_key"]
    # role CHECK and FK are enforced
    store = hs.SqliteHistory(db)
    assert store.append_pair("alpha", "q", "a")
    con = store._connect()
    try:
        with pytest.raises(sqlite3.IntegrityError):
            con.execute("INSERT INTO messages (session_id, role, content, ts, dedupe_key)"
                        " VALUES ((SELECT id FROM sessions), 'tool', 'x', 't', 'k1')")
        with pytest.raises(sqlite3.IntegrityError):
            con.execute("INSERT INTO messages (session_id, role, content, ts, dedupe_key)"
                        " VALUES ('nope', 'user', 'x', 't', 'k2')")
    finally:
        con.close()


def test_newer_schema_is_refused_softly(db):
    hs.SqliteHistory(db).stats()
    con = sqlite3.connect(str(db))
    con.execute("PRAGMA user_version = 99")
    con.close()
    store = hs.SqliteHistory(db)
    assert store.stats() is None and store.load("default") == [] and store.append_pair("d", "q", "a") is False


# ---------------------------------------------------------------- bridge behaviour

def test_round_trip_through_bridge_and_window(monkeypatch, db):
    calls = _fake_model(monkeypatch, reply="first answer")
    llm_chat.handle_llm_sync("/llm first question")
    assert llm_chat.load_history() == [{"role": "user", "content": "first question"},
                                       {"role": "assistant", "content": "first answer"}]
    _fake_model(monkeypatch, reply="second")
    calls = _fake_model(monkeypatch, reply="second")
    llm_chat.handle_llm_sync("/llm next")
    sent = calls[-1]
    assert [m["content"] for m in sent[1:]] == ["first question", "first answer", "next"]
    label = _rows(db, "SELECT model_label FROM messages WHERE role='assistant' ORDER BY id")[0][0]
    assert label.startswith("gguf:")
    assert not (db.parent / "llm_history.jsonl").exists(), "sqlite backend must not write the jsonl"


def test_window_matches_jsonl_trim(db, monkeypatch):
    store = hs.SqliteHistory(db)
    pairs = [("AAAA " * 200, "BBBB " * 200), ("mid q", "mid a"), ("newest user", "newest assistant")]
    for i, (q, a) in enumerate(pairs):
        assert store.append_pair("default", q, a, ts=f"2026-10-31T13:0{i}:00+00:00")
    full = store.load("default")
    assert len(full) == 6
    for budget in (0, 3, 10, 20, 500, 2500):
        monkeypatch.setenv("LLM_HISTORY_MAX_TOKENS", str(budget))
        windowed = llm_chat.load_history()
        assert llm_chat.trim_history(windowed, budget) == llm_chat.trim_history(full, budget)
    kept = llm_chat.trim_history(llm_chat.load_history(), 20)
    assert kept and all("AAAA" not in t["content"] for t in kept)


def test_sessions_are_separate(monkeypatch):
    _fake_model(monkeypatch, reply="A says hi")
    llm_chat.handle_llm_sync("/llm hi from a", session="alpha")
    _fake_model(monkeypatch, reply="B says hi")
    llm_chat.handle_llm_sync("/llm hi from b", session="beta")
    assert [t["content"] for t in llm_chat.load_history(session="alpha")] == ["hi from a", "A says hi"]
    assert [t["content"] for t in llm_chat.load_history(session="beta")] == ["hi from b", "B says hi"]


def test_reset_archives_never_deletes(monkeypatch, db):
    _fake_model(monkeypatch, reply="answer one")
    llm_chat.handle_llm_sync("/llm question one", session="alpha")
    llm_chat.handle_llm_sync("/llm keep me", session="beta")
    lines = llm_chat.handle_llm_sync("/llm reset", session="alpha")
    assert len(lines) == 1 and "session=alpha history archived in" in lines[0] and "2 messages kept" in lines[0]
    assert llm_chat.load_history(session="alpha") == []
    assert len(llm_chat.load_history(session="beta")) == 2
    assert _rows(db, "SELECT count(*) FROM messages")[0][0] == 4  # nothing deleted
    assert _rows(db, "SELECT count(*) FROM sessions WHERE name='alpha' AND archived_at IS NOT NULL")[0][0] == 1
    again = llm_chat.handle_llm_sync("/llm reset", session="alpha")
    assert again == ["[System] llm: history already empty for session=alpha (nothing to reset)"]
    # a fresh live session starts under the same name; the archived one is untouched
    _fake_model(monkeypatch, reply="fresh")
    llm_chat.handle_llm_sync("/llm new start", session="alpha")
    assert [t["content"] for t in llm_chat.load_history(session="alpha")] == ["new start", "fresh"]
    assert _rows(db, "SELECT count(*) FROM sessions WHERE name='alpha'")[0][0] == 2


def test_status_reports_backend_and_counts(monkeypatch, db):
    from src import deepinfer_status as ds
    monkeypatch.setattr(ds, "status_lines", lambda verify=True, rep=None: [ds.PREFIX + "stub"])
    _fake_model(monkeypatch, reply="r")
    llm_chat.handle_llm_sync("/llm q")
    out = llm_chat.handle_llm_sync("/llm status")
    assert out[0] == ds.PREFIX + "stub"
    assert re.search(r"backend=sqlite db=\S+llm_history\.sqlite3 schema=v1 journal=wal "
                     r"sessions=1 live/0 archived messages=2 \(live 2\)", out[1]), out[1]
    monkeypatch.setenv("HISTORY_BACKEND", "jsonl")
    assert "backend=jsonl" in llm_chat.handle_llm_sync("/llm status")[1]


# ---------------------------------------------------------------- atomicity / reopen

def test_model_failure_saves_nothing(monkeypatch, db):
    _fake_model(monkeypatch, err="127.0.0.1:8085 unreachable (refused)")
    lines = llm_chat.handle_llm_sync("/llm will fail")
    assert any("llm offline" in x for x in lines)
    assert not db.exists() or _rows(db, "SELECT count(*) FROM messages")[0][0] == 0


def test_write_failure_mid_pair_rolls_back_user_turn(db):
    store = hs.SqliteHistory(db)
    assert store.append_pair("default", "ok q", "ok a")
    con = sqlite3.connect(str(db))
    con.execute("CREATE TRIGGER boom BEFORE INSERT ON messages WHEN NEW.role = 'assistant'"
                " BEGIN SELECT RAISE(ABORT, 'assistant insert failed'); END")
    con.close()
    assert store.append_pair("default", "orphan question", "never stored") is False
    assert [r[0] for r in _rows(db, "SELECT content FROM messages ORDER BY id")] == ["ok q", "ok a"]


def test_locked_db_fails_softly_then_recovers(db, monkeypatch):
    store = hs.SqliteHistory(db, busy_ms=50)
    assert store.append_pair("default", "q1", "a1")
    holder = sqlite3.connect(str(db), isolation_level=None)
    holder.execute("BEGIN EXCLUSIVE")
    try:
        assert store.append_pair("default", "q2", "a2") is False  # locked → logged, no raise
    finally:
        holder.execute("ROLLBACK")
        holder.close()
    assert store.append_pair("default", "q3", "a3")  # reopened on the next call
    assert [t["content"] for t in store.load("default")] == ["q1", "a1", "q3", "a3"]


def test_deleted_db_is_recreated_on_next_call(db):
    store = hs.SqliteHistory(db)
    assert store.append_pair("default", "q1", "a1")
    for p in db.parent.glob(db.name + "*"):
        p.unlink()
    assert store.load("default") == []
    assert store.append_pair("default", "q2", "a2") and len(store.load("default")) == 2


def test_unopenable_path_never_raises(tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("x")
    store = hs.SqliteHistory(blocker / "sub" / "h.sqlite3")  # parent is a file
    assert store.load("default") == [] and store.append_pair("default", "q", "a") is False
    assert store.archive("default") is None and store.stats() is None


def test_bridge_modules_never_exit():
    for mod in (hs, llm_chat):
        src = Path(mod.__file__).read_text(encoding="utf-8")
        assert not re.search(r"\b(sys\.exit|os\._exit|os\.exit|SystemExit)\b", src), mod.__name__


# ---------------------------------------------------------------- unicode / LaTeX

def test_unicode_and_latex_round_trip(monkeypatch, db):
    reply = ("The golden ratio is \\(\\varphi=\\frac{1+\\sqrt5}{2}\\) ≈ 1.618 🌻\n$$\\varphi^2=\\varphi+1$$"
             "\n```python\nprint('$5')\n```")
    _fake_model(monkeypatch, reply=reply, reasoning="φ solves \\(x^2=x+1\\) — 思考")
    llm_chat.handle_llm_sync("/llm φ? «ünïcødé» 日本語 \\(x\\)")
    (u_c,), (a_c, a_f, a_t) = (_rows(db, "SELECT content FROM messages WHERE role='user'")[0],
                                _rows(db, "SELECT content, format, thinking FROM messages WHERE role='assistant'")[0])
    assert u_c == "φ? «ünïcødé» 日本語 \\(x\\)"
    assert a_f == "markdown" and "\\(\\varphi=\\frac{1+\\sqrt5}{2}\\)" in a_c and "$$\\varphi^2=\\varphi+1$$" in a_c
    assert "print('$5')" in a_c and "🌻" in a_c
    assert a_t == "φ solves \\(x^2=x+1\\) — 思考"
    assert all("思考" not in t["content"] for t in llm_chat.load_history())  # thinking not fed back


# ---------------------------------------------------------------- import tool

def _write_jsonl(path: Path, n_stubs=3):
    rows = [
        {"role": "user", "content": "legacy no session", "ts": "2026-10-29T10:00:00+00:00"},
        {"role": "assistant", "content": "[thinking]\nhm\n[/thinking]\nlegacy reply", "ts": "2026-10-29T10:00:00+00:00"},
    ]
    for i in range(n_stubs):
        ts = f"2026-10-30T15:31:0{i}.000000+00:00"
        rows += [{"role": "user", "content": history_import.STUB_PROMPT, "session": "default", "ts": ts},
                 {"role": "assistant", "content": history_import.STUB_REPLY, "session": "default", "ts": ts}]
    rows += [
        {"role": "user", "content": "φ?", "session": "alpha", "ts": "2026-10-30T20:00:00+00:00"},
        {"role": "assistant", "content": "\\(\\varphi\\) ≈ 1.618", "format": "markdown",
         "thinking": "x^2=x+1", "session": "alpha", "ts": "2026-10-30T20:00:00+00:00"},
        # a lone stub reply without its prompt is not a stub pair
        {"role": "assistant", "content": history_import.STUB_REPLY, "session": "beta", "ts": "2026-10-30T21:00:00+00:00"},
        {"role": "tool", "content": "bad role", "session": "beta", "ts": "2026-10-30T21:00:01+00:00"},
    ]
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n{not json\n", encoding="utf-8")
    return rows


def test_import_is_idempotent_and_never_touches_source(tmp_path, db):
    src = tmp_path / "copy.jsonl"
    _write_jsonl(src)
    digest = hashlib.sha256(src.read_bytes()).hexdigest()
    rep = history_import.run(src, db)
    assert rep["rows_read"] == 12 and rep["bad_lines"] == 1 and rep["bad_rows"] == 1
    assert rep["stub_pairs"] == 3 and rep["stub_pairs_skipped"] == 0
    assert rep["inserted"] == 11 and rep["duplicates"] == 0 and rep["sessions_created"] == 3
    again = history_import.run(src, db)
    assert again["inserted"] == 0 and again["duplicates"] == 11 and again["sessions_created"] == 0
    assert hashlib.sha256(src.read_bytes()).hexdigest() == digest
    store = hs.SqliteHistory(db)
    assert store.archive("alpha")  # import after a reset still does not duplicate
    assert history_import.run(src, db)["inserted"] == 0
    assert _rows(db, "SELECT format, thinking FROM messages WHERE content LIKE '%varphi%'") == [("markdown", "x^2=x+1")]
    assert _rows(db, "SELECT count(*) FROM messages")[0][0] == 11


def test_import_skip_stubs_only_when_asked(tmp_path):
    src = tmp_path / "copy.jsonl"
    _write_jsonl(src)
    rep = history_import.run(src, tmp_path / "skip.sqlite3", skip_stubs=True)
    assert rep["stub_pairs"] == 3 and rep["stub_pairs_skipped"] == 3 and rep["inserted"] == 5
    contents = [r[0] for r in _rows(tmp_path / "skip.sqlite3", "SELECT content FROM messages")]
    assert history_import.STUB_PROMPT not in contents
    assert contents.count(history_import.STUB_REPLY) == 1  # the lone beta reply is kept


def test_import_cli_isolated_subprocess(tmp_path):
    src = tmp_path / "copy.jsonl"
    _write_jsonl(src, n_stubs=1)
    db = tmp_path / "cli.sqlite3"
    cmd = [sys.executable, "-I", "-c",
           "import sys; sys.path.insert(0, sys.argv[1]); from src import history_import as h;"
           " raise SystemExit(h.main(sys.argv[2:]))",
           str(BRIDGE_DIR), "--from", "jsonl", "--to", "sqlite", "--src", str(src), "--db", str(db), "--json"]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    rep = json.loads(out.stdout)
    assert rep["inserted"] == 7 and rep["stub_pairs"] == 1 and rep["stats"]["messages"] == 7
    bad = subprocess.run(cmd[:5] + ["--from", "jsonl", "--to", "sqlite", "--src", str(tmp_path / "missing.jsonl"),
                                    "--db", str(db)], capture_output=True, text=True, timeout=60)
    assert bad.returncode == 2
