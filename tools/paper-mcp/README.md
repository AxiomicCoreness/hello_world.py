# paper-mcp

Loopback launcher for the `paper_mcp` package. Same shape as
`tools/cors-anywhere/`: a README, a plain-text help file, a launcher, and
a small config. The server implementation is the `paper_mcp` package
(import path `paper_mcp`), not a second copy in this directory.

| Constraint | Value |
|---|---|
| Bind | **`127.0.0.1` only** (never `0.0.0.0`, `::`, or `*`) |
| stdio | `serve` — MCP JSON-RPC on stdin/stdout |
| HTTP | `serve-http` — `POST /mcp`, `GET /healthz` |
| Canvas root | `PAPER_MCP_ROOT` (package default `./.paper_canvases`) |
| Package | imported; this tree does not vendor it |

`localhost` is accepted as an alias and the socket is still `127.0.0.1`.
`HOST`, `BIND_HOST`, or `PAPER_MCP_BIND` set to anything else exits `FATAL`
before the interpreter starts the listener. That is the same refusal rule
as `tools/cors-anywhere/server.js`.

## Tree

```text
tools/paper-mcp/
├── README.md      this file
├── help.txt       plain-text help (cors-anywhere/help.txt shape)
├── launch.sh      reads defaults.conf, execs scripts/paper_mcp.sh
├── defaults.conf  default bind 127.0.0.1 and port 8765
└── .gitignore     local canvas dir, bytecode, env files

scripts/paper_mcp.sh          stdio serve and serve-http
scripts/sovereign_cli.py      python -m sovereign wrapper
sovereign/__main__.py         dispatcher (engine, kernel, octonion_table,
                              phi_mod_mean, aklt_e2e, paper)
sovereign/paper_mcp.py        lazy re-export of the paper_mcp package
paper_mcp/                    package itself (separate change; import only)
```

## Quick start

```bash
# stdio MCP. Set the canvas directory yourself.
export PAPER_MCP_ROOT=./.paper_canvases
bash scripts/paper_mcp.sh serve

# loopback HTTP
bash scripts/paper_mcp.sh serve-http
# → http://127.0.0.1:8765/healthz

bash tools/paper-mcp/launch.sh serve-http
```

`python -m sovereign paper …` forwards the remaining arguments to
`paper_mcp.cli.main`. Example: `python -m sovereign paper --root ./.paper_canvases list`.

## Healthz

`serve-http` answers `GET /healthz` with
`{"status":"ok","service":"paper-mcp"}` and
`Cross-Origin-Resource-Policy: cross-origin`. The body has no secrets.
CORS reflects the request `Origin` unless the process was started to send
`*`. Methods `GET`, `POST`, `OPTIONS`. This directory does not open a
second port and does not relax port380 `/healthz`.

## Env

| Variable | Default | Notes |
|---|---|---|
| `PAPER_MCP_ROOT` | package default `./.paper_canvases` | Forwarded as `--root` when set |
| `PAPER_MCP_PORT` / `PORT` | `8765` | `serve-http` only |
| `HOST` / `BIND_HOST` / `PAPER_MCP_BIND` | `127.0.0.1` | Non-loopback is `FATAL` |
| `PYTHON` | `python3` | Interpreter used for `-m paper_mcp` |
