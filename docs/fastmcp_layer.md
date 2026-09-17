# FastMCP as a new layer

9191. Does not rewrite 9174, 9179, 9185, 9188, 9189, or 9190.
FILLED remains false until a later index names a filled server.

## What FastMCP is

Prefect/jlowin FastMCP wraps the Model Context Protocol. A `FastMCP` object holds:

- **Tools** — callable functions (`@mcp.tool`)
- **Resources** — readable URIs (`@mcp.resource`)
- **Prompts** — message templates (`@mcp.prompt`)

It is a protocol adapter. It is not a ledger rewrite and not Dual ASGI.

Official transports:

| Transport | Role | Garden policy |
|-----------|------|----------------|
| stdio | Client spawns process; stdin/stdout JSON-RPC | Allowed. 9190 default. |
| HTTP / Streamable HTTP | `mcp.run(transport="http", host=..., port=...)` | Only `127.0.0.1`. Never `0.0.0.0`. Do not occupy 8024. |
| SSE | Legacy | Do not add. |
| in-memory | Tests | Allowed. |

STDIO does not inherit arbitrary env (no secrets unless passed in `env=`).

## Garden objects (live)

| Path | Layer | Notes |
|------|-------|-------|
| `ledger/event_hash.py` | hasher | `compute` = `event_hash_block` |
| `garden_surgery/mcp_event_hash_stub.py` | 9190 | tools exist; `FASTMCP_RUN=1` for stdio; import-safe without package |
| `clarke_yoursa_tee_worker.py` | 8665 | FastAPI + optional FastMCP mount `/mcp`; `__main__` still documents 0.0.0.0 — not edited here |
| Dual ASGI | 8024 | `app_main:app` via `scripts/codespace_app_main.sh` |

## Allowed future appends (not this file)

1. Extra **tools** on the 9190 stub (hash verify, merkle of BIN layers).
2. A **resource** `garden://ledger/{index}` that *reads* YAML and does not write it.
3. HTTP on `127.0.0.1:<ephemeral>` if named in a later ledger. Not port 380. Not 8024.
4. In-memory client tests.

Not allowed without a new index: filling MCP, binding `0.0.0.0`, rewriting sealed YAML, Option B.
