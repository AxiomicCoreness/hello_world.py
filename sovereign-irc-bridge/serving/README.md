# /llm serving layout (loopback only)

Launch and supervisor scripts for the `/llm` chat command of the sovereign-irc-bridge.
Every listener binds **127.0.0.1** only. Model weights (`*.gguf`, ~1 GiB) are git-ignored and never
committed; pid/lock files and `tunnel.log` are also ignored.

Committed snapshot (2026-10-30, from the serving host, scanned for tokens/secrets before commit):

- `llm_history.jsonl` — `/llm` chat history at the time of commit (includes the alpha/beta/default
  session test exchanges; the words "secret"/"token" in it are test prompts, not credentials).
- `keepalive.log` — supervisor restart log.
- `llama-8085.log` — deepseek-r2 llama-server startup/serving log (listening on 127.0.0.1:8085).

The live runtime copies are written to `$RUN_DIR`, not to this folder.

## Port map

| Port | Process | Model / role |
|------|---------|--------------|
| 8081 | llama-server | base Qwen2.5-1.5B-Instruct Q4_K_M (`LLM_URL`) |
| 8082 | llama-server | ClarkeYoursaTee v1 fine-tune Q4_K_M (`launch-8082-ft.sh`) |
| 8083 | llama-server | Qwen2.5-1.5B-Instruct abliterated Q4_K_M |
| 8084 | llama-server | old ClarkeYoursaTee-1.5B (metadata-only derivative, not fine-tuned) (`launch-8084-old.sh`) |
| 8085 | llama-server | **deepseek-r2-1.5b Q4_K_M** — current `/llm` fallback (`launch-8085-deepseek-r2.sh`) |
| 8090 | DeepInfer | primary backend (`LLM_BACKEND=deepinfer`); currently offline |
| 6680 | bridge | `/cli` WebSocket (`src/cli_loopback.py`) (`launch-6680-deepseek-r2.sh`) |

deepseek-r2-1.5b GGUF: `deepseek-r2-1.5b-Q4_K_M.gguf`, 1,117,320,640 bytes,
sha256 `80a49c2fe2410f704ceda4590212174a99899341b01e6af5433319481179e5c1`,
from Kaggle `clarkeyoursatee/deepseek-r2-1-5b-q4-k-m`.
Direct single-file download (phones / PocketPal AI, or any machine): https://github.com/AxiomicCoreness/hello_world.py/releases/download/model-deepseek-r2-1.5b-q4km-v1/deepseek-r2-1.5b-Q4_K_M.gguf
`models/fetch-deepseek-r2.sh` uses that file first and falls back to the 42-part reassembly. Drop it into `models/` (see `models/README.md`);
`launch-8085-deepseek-r2.sh` defaults `MODEL_DIR` to that folder and refuses to start if the file is
missing or its sha256 does not match.

## Expected layout on the serving host

```
$MODEL_DIR/
├── Qwen2.5-1.5B-Instruct-Q4_K_M.gguf               → 8081
├── clarkeyoursatee-v1-ft-Q4_K_M.gguf               → 8082
├── Qwen2.5-1.5B-Instruct-abliterated.Q4_K_M.gguf   → 8083
├── ClarkeYoursaTee-1.5B-Q4_K_M.gguf                → 8084
└── (8085's GGUF lives in serving/models/ by default)
$RUN_DIR/
├── llm_history.jsonl        # LLM_HISTORY_PATH default
├── keepalive.pid / .lock / .log
└── llama-8085.log, bridge.log
sovereign-irc-bridge/serving/  (this folder)
├── launch-8082-ft.sh
├── launch-8084-old.sh
├── launch-8085-deepseek-r2.sh   # -c 4096, 127.0.0.1:8085, sha256-checked
├── models/                      # drop-in: deepseek-r2-1.5b-Q4_K_M.gguf (git-ignored)
├── launch-6680-deepseek-r2.sh   # bridge, fallback → 8085
├── launch-6680-revert-8082.sh   # bridge, fallback → 8082 (v1 fine-tune)
├── keepalive.sh                 # restarts 8085 and 6680 if their ports drop
└── stop-tunnel.sh               # unused: outbound Cloudflare tunnel edges are blocked
```

## /llm flow

1. The TeaVM page sends `/llm <text>` over the `/cli` WebSocket to `src/cli_loopback.py` on 127.0.0.1:6680.
2. `src/llm_chat.py` builds the prompt (with saved history) and marks reasoning as `[thinking]`.
3. `src/llm_backend.py` tries DeepInfer on 127.0.0.1:8090 first; when it is unreachable it falls back to
   the llama-server named by `LLM_FALLBACK` / `LLM_CLARKEYOURSATEE_URL` (127.0.0.1:8085, deepseek-r2-1.5b).

## Environment variables

Script paths (all optional, with defaults):

| Var | Default | Used by |
|-----|---------|---------|
| `MODEL_DIR` | `./models` next to the script for launch-8085; `$HOME/llama` for launch-8082/8084 | launch-808x |
| `LLAMA_SERVER` | `llama-server` (on PATH) | launch-808x |
| `BRIDGE_DIR` | parent of this folder | launch-6680-* |
| `PYTHON` | `python3` | launch-6680-* |
| `RUN_DIR` | `${XDG_STATE_HOME:-$HOME/.local/state}/sovereign-bridge` | launch-6680-deepseek-r2, keepalive, stop-tunnel |
| `LLAMA_LAUNCH`, `BRIDGE_LAUNCH` | sibling launch scripts | keepalive |

Bridge `LLM_*` settings set by `launch-6680-deepseek-r2.sh`:

| Var | Value |
|-----|-------|
| `LLM_URL` | `http://127.0.0.1:8081/v1/chat/completions` |
| `LLM_MODEL` | `local-gguf` |
| `LLM_BACKEND` | `deepinfer` |
| `LLM_FALLBACK` | `clarkeyoursatee` |
| `LLM_CLARKEYOURSATEE_URL` | `http://127.0.0.1:8085/v1/chat/completions` |
| `LLM_CLARKEYOURSATEE_MODEL` | `deepseek-r2-1.5b` |
| `LLM_MAX_TOKENS` | `1024` (the model reasons first; at 256 replies came back empty) |
| `LLM_RAW_REPLY` | `1` |
| `LLM_HISTORY_PATH` | `$RUN_DIR/llm_history.jsonl` |
| `LLM_HISTORY_MAX_TOKENS` | `2500` |

## Suggestions reviewed

- **DeepSeek "DeepTutor" layout.** The suggested files `chat/history_manager.py`, `chat/capability.py`,
  `api/module_routes.py` and an HTTP `/llm` route do not exist in this repo. `/llm` is a command on the
  `/cli` WebSocket, not an HTTP route.
- **Per-session history, atomic save, locking.** These ideas are implemented in PR #155
  (`feat/llm-history-sessions`), not in this folder.
- **DeepInfer platform.** DeepInfer is the primary backend on 127.0.0.1:8090 (currently offline);
  the GGUF llama-server on 127.0.0.1:8085 is the fallback.
