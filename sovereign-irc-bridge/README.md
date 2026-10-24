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

### `/llm` → model server on loopback (GGUF path)

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

### `/llm` backends: DeepInfer (default), Qwen GGUF, DeepSeek-V4 fixture

`src/llm_backend.py` picks the server; every path goes through the same
`chatml_prebuild` routing and reply guard, and every reply says where it came from.

| `LLM_BACKEND` | URL env (default, loopback only) | reply label |
|---|---|---|
| `deepinfer` (default) | `DEEPINFER_URL` (`http://127.0.0.1:8090/v1/chat/completions`), `DEEPINFER_MODEL` (`deepinfer`) | `backend=deepinfer`, no prefix |
| `gguf` | `LLM_URL` (`http://127.0.0.1:8081/v1/chat/completions`), `LLM_MODEL` | `backend=gguf` |
| `deepseek-fixture` | `LLM_DEEPSEEK_URL` (`http://127.0.0.1:8082/v1/chat/completions`), `LLM_DEEPSEEK_MODEL` | `backend=deepseek-fixture`, prefix `[DeepSeek-V4 fixture: RalphSeek 122M — not a real model]` |

- **Offline DeepInfer.** With `LLM_FALLBACK` unset, `/llm` answers
  `[System] llm: deepinfer backend offline (…)` and nothing else.
- **`LLM_FALLBACK=gguf`** hands the turn to the Qwen GGUF server. The route line
  says `backend=qwen (gguf fallback from deepinfer)`, each reply line starts with
  `[Fallback: Qwen]`, and the JSON log record (`llm_reply {...}`) carries
  `"backend": "qwen"`. The log also says `DeepInfer unreachable, falling back to Qwen`.
- **`LLM_FALLBACK=deepseek-fixture`** works the same way with the RalphSeek
  fixture: `backend=deepseek-fixture (fixture fallback from deepinfer)` plus the
  fixture prefix. Neither fallback is ever shown as DeepInfer.
- **Fast fail.** DeepInfer liveness is checked in two steps. First a socket
  `connect_ex` bounded by `DEEPINFER_CONNECT_TIMEOUT` (default **0.5 s**), then
  `GET /health`, falling back to `GET /v1/models`. The bridge probes at startup
  and caches the result for `DEEPINFER_REPROBE_S` (default 30 s). A failed chat
  POST marks DeepInfer offline until the next probe, so a dead port never holds
  a `/llm` turn.
- **Startup line.** `python -m src.cli_loopback` prints one line to stderr, for example
  `[System] llm backend: deepinfer OFFLINE (no server at 127.0.0.1:8090 (Connection refused); deep_gemm missing; deep_ep missing; flash_mla missing; torch missing; deepinfer._C missing; no CUDA) → fallback …`.
  The module list comes from `importlib.util.find_spec`, and the CUDA part from
  `torch.cuda.is_available()` when torch is installed. These describe the
  machine only; the bridge itself is an HTTP client and needs none of them.
  `python -m src.llm_backend` prints the same probe.
- **Startup checks.** A non-loopback `DEEPINFER_URL` or `LLM_DEEPSEEK_URL`, or
  an unknown `LLM_BACKEND` / `LLM_FALLBACK`, exits with `FATAL: Cosmic Alignment`,
  the same as `LLM_URL`.

**Assumption to verify once a DeepInfer server exists.** This repo has only
DeepInfer's model code (`deepinfer/model_executor/models/v4_modules`) and copies
of its engine files (`engine/deepinfer_shim`). It has no server and no API
description. The upstream release at the pinned SHA is offline inference only
(`examples/offline_inference.py`); its README lists serving pieces as "not
included in this release". So the bridge's OpenAI-compatible request (role
messages to `/v1/chat/completions`, reading `choices[0].message.content`) and the
`/health` and `/v1/models` liveness paths are assumptions. They hold for whatever
OpenAI-compatible server is put in front of DeepInfer on 127.0.0.1:8090, and
nothing in the repo confirms them.

**DeepSeek-V4 fixture.** [RalphSeek-V4-Flash](https://huggingface.co/ji-farthing/RalphSeek-V4-Flash-GGUF)
is a 122M-parameter model with the `deepseek4` architecture, trained on a tiny
synthetic corpus. Its author says it is **not a usable language model**; use it
as a fixture to exercise the DeepSeek-V4 chat template and the bridge plumbing on
CPU. The bridge sends `chat_template_kwargs: {"enable_thinking": false}`, so the
prompt ends `<｜Assistant｜></think>` as the fixture's README shows. The stop set
for this template family is `<｜end▁of▁sentence｜>`, `<｜User｜>` and
`<｜Assistant｜>` plus the role-echo stops; stray `<think>` / `</think>` tags are
stripped.

```bash
curl -L -o ralphseek-v4-flash-iq4_nl.gguf https://huggingface.co/ji-farthing/RalphSeek-V4-Flash-GGUF/resolve/main/ralphseek-v4-flash-iq4_nl.gguf
# sha256 e3481e25c7d523dc2e95485ac29e2c29fbfbbfb4f69764967783e5c41322e7d0 (90,863,488 bytes)
llama-server -m ralphseek-v4-flash-iq4_nl.gguf --jinja --host 127.0.0.1 --port 8082 -c 4096
```

`deepseek4` loads in llama.cpp release b11840 (`version: 0.7.0-dev (build 11840, commit 36e36e63a)`).

Live game with DeepInfer offline and the fixture answering, labeled:

```bash
LLM_BACKEND=deepinfer LLM_FALLBACK=deepseek-fixture \
LLM_DEEPSEEK_URL=http://127.0.0.1:8082/v1/chat/completions \
LLM_URL=http://127.0.0.1:8081/v1/chat/completions python -m src.cli_loopback
```

Qwen GGUF stays the CPU fallback for real answers: use `LLM_FALLBACK=gguf`, or
`LLM_BACKEND=gguf` to use it directly.

## DeepInfer Server Requirements

These are taken from the upstream READMEs at the SHAs pinned in
`scripts/init_deepinfer_vendors.sh` (`vendor/PINNED_SHAS.md`). This box (CPU only)
meets none of them, which is why the bridge's live default is DeepInfer
**offline** with a labeled fallback.

| component (pinned SHA) | hardware | toolchain / deps | install |
|---|---|---|---|
| DeepInfer `9bd9cf24` | **NVIDIA SM100** GPUs (or Huawei Ascend 950 NPUs) | Linux, GCC ≥ 13, Python 3.12, **CUDA 13** | `export DEEPINFER_ACCELERATOR=nvidia && ./build.sh` in an empty Python 3.12 env |
| DeepGEMM `1fc9c669` | NVIDIA **SM90 or SM100** | Python ≥ 3.8, C++20 compiler (`<format>`), **CUDA Toolkit ≥ 12.9**, PyTorch ≥ 2.3, CUTLASS ≥ 4.0 (submodule) | `./install.sh` (builds a wheel, `pip install`). Kernels compile at runtime (DeepJIT), and nvcc is found via `DG_JIT_NVCC_COMPILER`, `CUDA_HOME`, `CUDA_PATH`, `which nvcc`, then `/usr/local/cuda` |
| DeepEP `f6aa38fe` | NVIDIA **Hopper or newer**, NVLink intranode, RDMA (InfiniBand tested) internode | Linux, Python ≥ 3.10, **CUDA Toolkit ≥ 13.1** (DeepJIT), C++20, PyTorch ≥ 2.10 with CUDA, NCCL ≥ 2.32.3; NVSHMEM is no longer a dependency | builds the host extension against CUDA + NCCL. GPU kernels are DeepJIT-compiled at runtime, so the CUDA toolkit must stay available at run time |
| FlashMLA `2e5429fc` | NVIDIA **SM100 / SM103** | CUDA ≥ 13.1 (13.2 recommended), PyTorch ≥ 2.0 | per upstream README |

Together that means Blackwell-class (SM100) GPUs with CUDA 13.x, because
DeepInfer and FlashMLA require SM100. SM80 (Ampere) and CUDA 11.8 are not
supported by any of the pinned components. No `LD_LIBRARY_PATH` step is
documented: DeepGEMM and DeepEP JIT-compile with the CUDA toolkit they find at
run time.

Steps once such a machine exists:

1. `./scripts/init_deepinfer_vendors.sh` clones DeepInfer, DeepGEMM, DeepEP,
   FlashMLA and DeepSelect at the pinned SHAs. Then build per the table.
2. Get the weights. DeepInfer's default checkpoint is
   `deepseek-ai/DeepSeek-V4.1-Flash-1017` (Hugging Face cache, or
   `DEEPINFER_HF_MODEL_DIR=/path`). Upstream benchmarks use 4 SM100 GPUs for
   prefill and 64 for decode.
3. Put an OpenAI-compatible HTTP server in front of the engine on
   **127.0.0.1:8090**, because upstream ships none. It needs `POST
   /v1/chat/completions` plus `GET /health` or `GET /v1/models`. The port must
   stay loopback.
4. Start the bridge with `LLM_BACKEND=deepinfer DEEPINFER_URL=http://127.0.0.1:8090/v1/chat/completions`.
   The startup line should read `deepinfer ONLINE`.

Until then the Qwen GGUF server (`LLM_FALLBACK=gguf`) is the CPU fallback, and
its replies are always labeled `[Fallback: Qwen]`.
