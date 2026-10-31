# `/llm` chat-history backends

The `/llm` bridge (`src/llm_chat.py`) keeps per-session chat history so a
restarted bridge still has context. Two backends share one contract:

| | `jsonl` (default) | `sqlite` |
|---|---|---|
| Select | `HISTORY_BACKEND` unset or `jsonl` | `HISTORY_BACKEND=sqlite` |
| Where | `LLM_HISTORY_PATH` (default `/workspace/bridge-serving/llm_history.jsonl`) | `LLM_HISTORY_DB` (default `llm_history.sqlite3` next to the JSONL file) |
| Save | user + assistant appended together after a successful reply, fsync | user + assistant in one `BEGIN IMMEDIATE` transaction after a successful reply |
| `/llm reset` | session rows moved to `*.reset-<session>-<utc>` | `sessions.archived_at` set; rows kept, a new live session starts |
| `/llm status` | last line: `backend=jsonl path=… rows=N sessions=M` | last line: `backend=sqlite db=… schema=v1 journal=wal sessions=L live/A archived messages=N (live K)` |
| Window | newest turns within `LLM_HISTORY_MAX_TOKENS` (chars/4) | same function (`trim_history`); only the newest rows are read |

Both: a failed model call stores nothing (no unanswered questions), the
assistant row carries `format` (`markdown`) and a separate `thinking` field
(PR #166), and `thinking` is never sent back to the model. `LLM_HISTORY_PATH=""`
disables history for both unless `LLM_HISTORY_DB` is set explicitly. Unknown
`HISTORY_BACKEND` values log a warning and use `jsonl`.

## Enable SQLite

```bash
cd sovereign-irc-bridge
# 1. one-shot import of the existing JSONL (read-only on the source, idempotent)
python -m src.history_import --from jsonl --to sqlite \
    --src /workspace/bridge-serving/llm_history.jsonl \
    --db  /workspace/bridge-serving/llm_history.sqlite3          # add --skip-stubs to drop test stubs
# 2. restart the bridge with
export HISTORY_BACKEND=sqlite
export LLM_HISTORY_DB=/workspace/bridge-serving/llm_history.sqlite3   # optional, this is the default
export LLM_HISTORY_DB_BUSY_MS=5000                                     # optional
```

Switching back is `HISTORY_BACKEND=jsonl` (or unset). The JSONL file is never
modified by the SQLite backend or the importer.

### Import tool

`python -m src.history_import --from jsonl --to sqlite [--src F] [--db F] [--skip-stubs] [--json]`

* Imports everything by default and reports counts: rows read, unparseable
  lines, rows with an unknown role, stub pairs found / skipped, inserted,
  duplicates, sessions created.
* Dedupe key per message: sha256 of session + ts + role + content (unique
  column), so a rerun inserts nothing, even after a `/llm reset`.
* `--skip-stubs` drops only complete pairs of user `what is the brain doing?`
  followed in the same session by assistant `Lane L3 is busiest.`, the stub
  reply unit tests wrote into the live file before PR #166.
* One transaction: on any error nothing is written (exit status 1).

## SQLite schema (`PRAGMA user_version = 1`)

```sql
CREATE TABLE sessions (
    id          TEXT PRIMARY KEY,      -- "<name>~<utc stamp>~<hex>"
    name        TEXT NOT NULL,         -- bridge session ([A-Za-z0-9_-]{1,64})
    created_at  TEXT NOT NULL,         -- ISO 8601, UTC with +00:00
    updated_at  TEXT NOT NULL,
    archived_at TEXT NULL              -- set by /llm reset; never deleted
);
CREATE UNIQUE INDEX sessions_one_live ON sessions(name) WHERE archived_at IS NULL;
CREATE TABLE messages (
    id          INTEGER PRIMARY KEY,
    session_id  TEXT NOT NULL REFERENCES sessions(id) ON DELETE RESTRICT,
    role        TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content     TEXT NOT NULL,         -- Markdown, math as \( … \) / $$ … $$
    format      TEXT NULL,             -- 'markdown'; NULL = legacy plain text
    thinking    TEXT NULL,             -- model reasoning, kept apart from content
    model_label TEXT NULL,             -- e.g. 'clarkeyoursatee:deepseek-r2-1.5b'
    ts          TEXT NOT NULL,         -- ISO 8601, UTC with +00:00 (same as JSONL ts)
    dedupe_key  TEXT NOT NULL UNIQUE   -- sha256(session, ts, role, content)
);
CREATE INDEX messages_session_id ON messages(session_id, id);
```

Each connection sets `journal_mode=WAL`, `foreign_keys=ON` and
`busy_timeout` (`LLM_HISTORY_DB_BUSY_MS`). Migrations are numbered steps keyed
on `user_version`; a file with a newer version than the code is refused
(logged, history calls return empty) rather than rewritten.

Sessions use a separate `name` column because a reset session name is reused:
the archived row keeps its id and messages, and the next message under the
same name opens a new live row.

## Never exits, reopens on demand

There is no long-lived connection. Every load / save / reset / status opens a
connection under a per-file lock and closes it before returning. A locked,
deleted or unreachable DB makes that one call log a warning and return empty
(save → not stored, reply still shown); the next message opens the file again
(and recreates the schema if the file is gone). Nothing in the history path
calls `sys.exit` / `os._exit`, and an idle bridge holds no DB handle.

## Reused from the repo's existing SQLite

`mesh_modal.py` (`MESH_LEDGER_DB` env override, `threading.Lock` around a
short-lived connection per call, `CREATE TABLE IF NOT EXISTS` on first use,
soft failure instead of crashing) and `witness_compiler.py` (`FOREIGN KEY`,
ISO text timestamps) are the only SQLite users in the repo; neither has a DB
file related to chat history, so the bridge starts a new file.

## MariaDB later

A MariaDB backend (`HISTORY_BACKEND=mariadb`, planned: utf8mb4, `time_zone =
'+00:00'` per connection, credentials only in server env vars, reconnect on
the next message after an idle drop) can implement the same four methods as
`src/llm_history_sqlite.SqliteHistory` (`load`, `append_pair`, `archive`,
`stats`, plus `import_rows` for the importer) with the same two tables. Until
then `HISTORY_BACKEND=mariadb` is treated as unknown and falls back to `jsonl`.
