# sovereign-irc-bridge

Autonomous WebSocket-to-TCP bridge **stubs** targeting **irc.abjects.net**,
with TeaVM UI wired to `games/teavm-rhythm` **debug-oracle**.

## Safety

- No real certs in git — `.env.example` only.
- **mTLS required at startup**: missing `IRC__MTLS_*` → `pydantic.ValidationError` (lifespan); no ghost-pass.
- **Live wire**: `WsTcpProxy` pumps WS↔TCP bytes over mTLS to `irc.abjects.net` once PEMs mount.
- Deploy workflow **skips green** when `secrets.KUBECONFIG` is empty.
- No dual-gate pytest files under this tree (no `test_*.py`).

## Layout

See `src/` (FastAPI + Pydantic), `deploy/k8s/`, `teavm-client/README.md`.

## Local

```bash
cd sovereign-irc-bridge
pip install -e .
# PEMs required (see .env.example) — app refuses to start without them
export IRC__MTLS_CERT_PATH=/etc/mtls/client.crt
export IRC__MTLS_KEY_PATH=/etc/mtls/client.key
export IRC__MTLS_CA_PATH=/etc/mtls/ca.crt
uvicorn src.main:app --host 0.0.0.0 --port 8080
```
## Debug-oracle chat commands

TeaVM panel `games/teavm-rhythm/.../debug-oracle` understands `/stokes`, `/flux`, `/mtls` — emits KaTeX from `docs/katex_stokes_mandala_9300_micro.*` via `hex_locks.json`. Host **irc.abjects.net**; live dial still fail-fast without mTLS.

## TeaVM CLI loopback (Cosmic Alignment)

```bash
# MUST bind 127.0.0.1 only — never 0.0.0.0
python -m src.cli_loopback
# → ws://127.0.0.1:6680/cli  →  (label) irc.abjects.net:6669
```

TeaVM `CliClient` dials that URL from the rhythm page left column. Pages HTTPS
needs a `wss://` tunnel; the local contract stays `ws://127.0.0.1:6680/cli`.
Set `CLI_LIVE_IRC=1` to open plain TCP to `irc.abjects.net:6669` from the
bridge process (browser still never dials abjects). Default is stub echo.

The local CLI port moved from 6669 to **6680**: Chrome and Firefox refuse
WebSocket dials to their "unsafe port" list (IRC 6665-6669, 6697), so the
old port only worked with `--explicitly-allowed-ports`. 6680 needs no browser
flags. `CLI_BIND_PORT` still overrides it; the bind stays loopback-only and a
non-loopback `CLI_BIND_HOST` exits with `FATAL: Cosmic Alignment`.

### `/llm` → GGUF (llama-server on loopback)

`/llm <text>` lines (plus the TeaVM `#neuro` spike snapshot and `#feedback`
traceback block) go to `src/llm_chat.py`, which posts an OpenAI-style chat
request to `LLM_URL` (default `http://127.0.0.1:8081/v1/chat/completions`,
loopback only; `LLM_MODEL` default `local-gguf`). A down model server returns
`[System] llm offline: …`. Role messages only: llama-server applies the
GGUF's chat template (recommended model Qwen2.5-1.5B-Instruct Q4_K_M, run with
`--jinja`). Replies pass a guard (stop sequences, `repeat_penalty` /
`frequency_penalty`, cut at role echoes like `User 1:` and at 3-gram loops),
with a `[System] llm: reply trimmed …` line when it fires. Tests: `pytest src/test_llm_chat.py` (stub server,
no model download). Full run steps: `games/teavm-rhythm/README.md`,
"LLM chat (/llm, GGUF on loopback)".
