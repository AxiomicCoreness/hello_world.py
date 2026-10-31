# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""SQLite chat-history backend for the ``/llm`` bridge (HISTORY_BACKEND=sqlite).

Same contract as the JSONL history in :mod:`src.llm_chat`:

* turns are keyed by the bridge session name (``[A-Za-z0-9_-]{1,64}``);
* a user turn is only ever stored together with its assistant reply, in one
  transaction (``BEGIN IMMEDIATE`` … ``COMMIT``), so a failed model call or a
  failed write never leaves an unanswered question behind;
* ``/llm reset`` archives (``sessions.archived_at`` is set), it never deletes;
* every call is "never raises": errors are logged and the call returns an
  empty / falsy result. Nothing here exits the process.

Built on the repo's existing stdlib ``sqlite3`` patterns (``mesh_modal.py``:
env-var path override, a ``threading.Lock`` around a short-lived connection per
call, ``CREATE TABLE IF NOT EXISTS`` on first use, soft failure instead of an
import-time crash; ``witness_compiler.py``: ``FOREIGN KEY`` + ISO text
timestamps). New here: WAL, ``foreign_keys=ON``, ``busy_timeout`` and a
``user_version`` migration step.

Connection policy: one connection per call, opened under a per-file lock and
closed before returning. An idle bridge therefore holds no connection at all;
a deleted, locked or briefly unavailable DB is reopened on the next call (one
immediate retry, then the call gives up softly). A MariaDB backend can follow
the same interface (``load`` / ``append_pair`` / ``archive`` / ``stats``).

Schema (``PRAGMA user_version`` = 1)::

    sessions(id TEXT PK, name TEXT, created_at TEXT, updated_at TEXT,
             archived_at TEXT NULL)          -- one live row per name
    messages(id INTEGER PK, session_id TEXT FK→sessions.id,
             role TEXT CHECK IN ('user','assistant','system'),
             content TEXT, format TEXT NULL, thinking TEXT NULL,
             model_label TEXT NULL, ts TEXT, dedupe_key TEXT UNIQUE)
    INDEX messages(session_id, id)

All timestamps are ISO 8601 with an explicit offset, written in UTC
(``+00:00``) exactly like the JSONL ``ts`` field.
"""
from __future__ import annotations

import hashlib
import logging
import secrets
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Final, Iterable, List, Optional, Tuple, TypeVar

logger = logging.getLogger("sovereign-irc-bridge.llm.history.sqlite")

SCHEMA_VERSION: Final = 1
DEFAULT_BUSY_MS: Final = 5000
ROLES: Final = ("user", "assistant", "system")

T = TypeVar("T")

_LOCKS: Dict[str, threading.Lock] = {}
_LOCKS_GUARD = threading.Lock()

_SCHEMA_V1: Final = (
    """CREATE TABLE IF NOT EXISTS sessions (
        id          TEXT PRIMARY KEY,
        name        TEXT NOT NULL,
        created_at  TEXT NOT NULL,
        updated_at  TEXT NOT NULL,
        archived_at TEXT NULL
    )""",
    # At most one live (not archived) session per bridge session name.
    """CREATE UNIQUE INDEX IF NOT EXISTS sessions_one_live
        ON sessions(name) WHERE archived_at IS NULL""",
    """CREATE TABLE IF NOT EXISTS messages (
        id          INTEGER PRIMARY KEY,
        session_id  TEXT NOT NULL REFERENCES sessions(id) ON DELETE RESTRICT,
        role        TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
        content     TEXT NOT NULL,
        format      TEXT NULL,
        thinking    TEXT NULL,
        model_label TEXT NULL,
        ts          TEXT NOT NULL,
        dedupe_key  TEXT NOT NULL UNIQUE
    )""",
    "CREATE INDEX IF NOT EXISTS messages_session_id ON messages(session_id, id)",
)


def utc_now() -> str:
    """ISO 8601 with offset, UTC — same shape as the JSONL ``ts`` field."""
    return datetime.now(timezone.utc).isoformat()


def dedupe_key(session: str, ts: str, role: str, content: str) -> str:
    """sha256 over session + ts + role + content (NUL-separated)."""
    h = hashlib.sha256()
    for part in (session, ts, role, content):
        h.update((part or "").encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()


def _lock_for(path: Path) -> threading.Lock:
    key = str(path)
    with _LOCKS_GUARD:
        lock = _LOCKS.get(key)
        if lock is None:
            lock = _LOCKS[key] = threading.Lock()
        return lock


def _est_tokens(text: str) -> int:
    # Same chars/4 estimate as llm_chat._est_tokens.
    return max(1, (len(text or "") + 3) // 4)


class SchemaTooNew(sqlite3.DatabaseError):
    """The DB was written by a newer schema than this code knows."""


class SqliteHistory:
    """History store on one SQLite file. Thread-safe; never raises from public methods."""

    backend_name: Final = "sqlite"

    def __init__(self, path: Path, *, busy_ms: int = DEFAULT_BUSY_MS) -> None:
        self.path = Path(path)
        self.busy_ms = max(0, int(busy_ms))

    # ------------------------------------------------------------------ plumbing

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(str(self.path), timeout=self.busy_ms / 1000.0,
                              isolation_level=None, check_same_thread=False)
        try:
            con.execute(f"PRAGMA busy_timeout = {self.busy_ms}")
            con.execute("PRAGMA foreign_keys = ON")
            mode = con.execute("PRAGMA journal_mode = WAL").fetchone()
            if not mode or str(mode[0]).lower() != "wal":
                logger.warning("llm history sqlite: journal_mode=%s (WAL unavailable) at %s",
                               mode[0] if mode else None, self.path)
            self._migrate(con)
        except BaseException:
            con.close()
            raise
        return con

    def _migrate(self, con: sqlite3.Connection) -> None:
        version = con.execute("PRAGMA user_version").fetchone()[0]
        if version == SCHEMA_VERSION:
            return
        if version > SCHEMA_VERSION:
            raise SchemaTooNew(f"{self.path} has user_version={version} > {SCHEMA_VERSION}")
        con.execute("BEGIN IMMEDIATE")
        try:
            version = con.execute("PRAGMA user_version").fetchone()[0]
            if version < 1:
                for stmt in _SCHEMA_V1:
                    con.execute(stmt)
                con.execute("PRAGMA user_version = 1")
            # Future: `if version < 2: ...; PRAGMA user_version = 2`
            con.execute("COMMIT")
        except BaseException:
            con.execute("ROLLBACK")
            raise

    def _run(self, what: str, fn: Callable[[sqlite3.Connection], T], default: T) -> T:
        """Open → fn → close under the per-file lock. One reopen retry, then ``default``."""
        last: Optional[BaseException] = None
        for attempt in (1, 2):
            try:
                with _lock_for(self.path):
                    con = self._connect()
                    try:
                        return fn(con)
                    finally:
                        con.close()
            except (sqlite3.Error, OSError) as exc:
                last = exc
                if isinstance(exc, SchemaTooNew):
                    break
                logger.info("llm history sqlite %s attempt %d failed (%s): %s",
                            what, attempt, self.path, exc)
        logger.warning("llm history sqlite %s failed (%s): %s", what, self.path, last)
        return default

    @staticmethod
    def _tx(con: sqlite3.Connection, body: Callable[[], T]) -> T:
        con.execute("BEGIN IMMEDIATE")
        try:
            out = body()
        except BaseException:
            con.execute("ROLLBACK")
            raise
        con.execute("COMMIT")
        return out

    @staticmethod
    def _live_session(con: sqlite3.Connection, name: str, ts: str, *, create: bool) -> Optional[str]:
        row = con.execute("SELECT id FROM sessions WHERE name = ? AND archived_at IS NULL",
                          (name,)).fetchone()
        if row:
            return row[0]
        if not create:
            return None
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        sid = f"{name}~{stamp}~{secrets.token_hex(3)}"
        con.execute("INSERT INTO sessions (id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (sid, name, ts, ts))
        return sid

    @staticmethod
    def _insert(con: sqlite3.Connection, sid: str, name: str, role: str, content: str, ts: str,
                fmt: Optional[str] = None, thinking: Optional[str] = None,
                model_label: Optional[str] = None, *, key_ts: Optional[str] = None,
                ignore_duplicate: bool = False) -> bool:
        key = dedupe_key(name, ts if key_ts is None else key_ts, role, content)
        verb = "INSERT OR IGNORE" if ignore_duplicate else "INSERT"
        cur = con.execute(
            f"{verb} INTO messages (session_id, role, content, format, thinking, model_label, ts, dedupe_key)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (sid, role, content, fmt, thinking if (thinking and thinking.strip()) else None,
             model_label, ts, key),
        )
        return cur.rowcount == 1

    # ------------------------------------------------------------------ public API

    def load(self, session: str, budget_tokens: Optional[int] = None) -> List[Dict[str, str]]:
        """Live-session user/assistant turns, oldest first (``thinking`` is never returned).

        With ``budget_tokens`` only the newest rows are read: everything
        ``llm_chat.trim_history`` could keep, plus the one turn it stops at, so
        the trimmed result is identical to trimming the full list.
        """
        def q(con: sqlite3.Connection) -> List[Dict[str, str]]:
            cur = con.execute(
                "SELECT m.role, m.content FROM messages m JOIN sessions s ON s.id = m.session_id"
                " WHERE s.name = ? AND s.archived_at IS NULL AND m.role IN ('user', 'assistant')"
                " AND trim(m.content) != '' ORDER BY m.id DESC", (session,))
            out: List[Dict[str, str]] = []
            used = 0
            for role, content in cur:
                out.append({"role": role, "content": content})
                used += _est_tokens(content)
                if budget_tokens is not None and used > budget_tokens:
                    break
            out.reverse()
            return out
        return self._run("load", q, [])

    def append_pair(self, session: str, user: str, assistant: str, *,
                    assistant_format: Optional[str] = None, thinking: Optional[str] = None,
                    model_label: Optional[str] = None, ts: Optional[str] = None) -> bool:
        """Store user + assistant atomically. → True on commit, False (logged) otherwise."""
        ts = ts or utc_now()

        def w(con: sqlite3.Connection) -> bool:
            def body() -> bool:
                sid = self._live_session(con, session, ts, create=True)
                assert sid is not None
                self._insert(con, sid, session, "user", user, ts)
                self._insert(con, sid, session, "assistant", assistant, ts,
                             assistant_format, thinking if assistant_format else None, model_label)
                con.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (ts, sid))
                return True
            return self._tx(con, body)
        return self._run("append", w, False)

    def archive(self, session: str) -> Optional[Dict[str, Any]]:
        """Mark the live session archived (rows kept). → {id, messages, archived_at} or None."""
        def w(con: sqlite3.Connection) -> Optional[Dict[str, Any]]:
            def body() -> Optional[Dict[str, Any]]:
                sid = self._live_session(con, session, "", create=False)
                if sid is None:
                    return None
                n = con.execute("SELECT count(*) FROM messages WHERE session_id = ?", (sid,)).fetchone()[0]
                if n == 0:
                    return None
                now = utc_now()
                con.execute("UPDATE sessions SET archived_at = ?, updated_at = ? WHERE id = ?",
                            (now, now, sid))
                return {"id": sid, "messages": n, "archived_at": now}
            return self._tx(con, body)
        return self._run("archive", w, None)

    def stats(self) -> Optional[Dict[str, Any]]:
        """Counts for ``/llm status``. None if the DB cannot be opened."""
        def q(con: sqlite3.Connection) -> Dict[str, Any]:
            one = lambda sql: con.execute(sql).fetchone()[0]  # noqa: E731
            return {
                "schema": one("PRAGMA user_version"),
                "journal_mode": one("PRAGMA journal_mode"),
                "sessions_live": one("SELECT count(*) FROM sessions WHERE archived_at IS NULL"),
                "sessions_archived": one("SELECT count(*) FROM sessions WHERE archived_at IS NOT NULL"),
                "messages": one("SELECT count(*) FROM messages"),
                "messages_live": one("SELECT count(*) FROM messages m JOIN sessions s ON s.id = m.session_id"
                                     " WHERE s.archived_at IS NULL"),
            }
        return self._run("stats", q, None)

    def import_rows(self, rows: Iterable[Tuple[str, str, str, str, Optional[str], Optional[str]]]
                    ) -> Optional[Dict[str, int]]:
        """Bulk import (session, role, content, ts, format, thinking) in ONE transaction.

        Duplicates (same session + ts + role + content) are ignored, so a rerun
        is a no-op. Rows land in the session's live row (created if missing).
        → {"inserted", "duplicates", "sessions_created"} or None on failure.
        """
        rows = list(rows)

        def w(con: sqlite3.Connection) -> Dict[str, int]:
            def body() -> Dict[str, int]:
                inserted = dup = created = 0
                sids: Dict[str, str] = {}
                for name, role, content, ts, fmt, thinking in rows:
                    key_ts = ts or ""
                    when = ts or utc_now()
                    key = dedupe_key(name, key_ts, role, content)
                    if con.execute("SELECT 1 FROM messages WHERE dedupe_key = ?", (key,)).fetchone():
                        dup += 1
                        continue
                    sid = sids.get(name)
                    if sid is None:
                        sid = self._live_session(con, name, when, create=False)
                        if sid is None:
                            sid = self._live_session(con, name, when, create=True)
                            created += 1
                        sids[name] = sid  # type: ignore[assignment]
                    self._insert(con, sid, name, role, content, when, fmt, thinking, key_ts=key_ts)  # type: ignore[arg-type]
                    inserted += 1
                    con.execute(
                        "UPDATE sessions SET created_at = min(created_at, ?),"
                        " updated_at = max(updated_at, ?) WHERE id = ?", (when, when, sid))
                return {"inserted": inserted, "duplicates": dup, "sessions_created": created}
            return self._tx(con, body)
        return self._run("import", w, None)
