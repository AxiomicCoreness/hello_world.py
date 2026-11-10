<!--
SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
SPDX-License-Identifier: MIT
-->

# paper_mcp

Small Model Context Protocol server for design canvases. Files live on disk
under `PAPER_MCP_ROOT` (default `./.paper_canvases`). The Python is stdlib
only: JSON-RPC 2.0, one JSON object per line on stdio.

Tools (shared by MCP and the CLI):

| Tool | Arguments |
|---|---|
| `canvas_list` | — |
| `canvas_read` | `name` |
| `canvas_write` | `name`, `content` (HTML, SVG, JSON, Markdown, or plain text) |
| `canvas_delete` | `name` |
| `canvas_patch` | `name`, `find`, `replace` (every occurrence) |

Names are one path segment: letters, digits, `_`, `-`, and an optional
`.html`, `.svg`, `.json`, `.txt`, or `.md`. `..`, absolute paths, separators,
and symlinks are rejected. Writes are atomic (`tempfile` + `fsync` +
`os.replace`) and capped at `PAPER_MCP_MAX_BYTES` (default 1 MiB). `.json`
canvases must be valid JSON.

## CLI

`python -m paper_mcp` is stdio MCP. `--root` overrides `PAPER_MCP_ROOT`.
`--json` prints JSON for the local commands. Flags may come before or after
the subcommand.

```bash
python -m paper_mcp serve
python -m paper_mcp --root ./.paper_canvases list
python -m paper_mcp read board.html
python -m paper_mcp write board.html --file ./board.html
printf '<p>hi</p>' | python -m paper_mcp write board.html
python -m paper_mcp patch board.html --find hi --replace hello
python -m paper_mcp delete board.html
python -m paper_mcp resources
python -m paper_mcp serve-http --port 8765
python -m paper_mcp serve-http --cors-origin '*'
```

## HTTP

`serve-http` is `http.server` on **127.0.0.1 only**. The refusal rule is the
one in `tools/cors-anywhere/server.js` (PR #129): `0.0.0.0`, `::`, and `*`
do not bind. `localhost` is an alias of `127.0.0.1`.

* `POST /mcp` — one JSON-RPC message (the same handler as stdio).
* `GET /healthz` — public `{"status":"ok","service":"paper-mcp"}` with
  `Cross-Origin-Resource-Policy: cross-origin`, following the port380
  `/healthz` probe (no secrets, readable cross-origin).
* `OPTIONS` — preflight. `Access-Control-Allow-Origin` reflects the request
  `Origin` unless `--cors-origin '*'` sends `*`. Methods `GET`, `POST`,
  `OPTIONS`. Headers `Content-Type`, `Authorization`. `Vary: Origin`.

## Cursor

No secrets. Point `--root` at a directory you want the agent to use.

```json
{
  "mcpServers": {
    "paper-canvas": {
      "command": "python",
      "args": ["-m", "paper_mcp", "serve"],
      "env": {
        "PAPER_MCP_ROOT": "./.paper_canvases"
      }
    }
  }
}
```

Put that object in `.cursor/mcp.json` locally. Do not commit a canvas store
or credentials. `.paper_canvases/` is gitignored.
