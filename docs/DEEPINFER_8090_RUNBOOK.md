<!-- SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com> -->
<!-- SPDX-License-Identifier: MIT -->
# DeepInfer on 127.0.0.1:8090 — runbook

`/llm` tries **DeepInfer** first (`DEEPINFER_URL`, default `http://127.0.0.1:8090/v1/chat/completions`)
and falls back to the **deepseek tutor** GGUF on `127.0.0.1:8085` (`LLM_FALLBACK=clarkeyoursatee`).
This runbook covers both, in the order you need them. Everything binds to **127.0.0.1 only — never 0.0.0.0**.

Check where you stand at any point:

```sh
python -I sovereign-irc-bridge/src/deepinfer_status.py status          # human-readable
python -I sovereign-irc-bridge/src/deepinfer_status.py status --json   # full report
```

or type `/llm status` in the TeaVM CLI (same report, no model call).

## Step 1 — reassemble the GGUF (secondary tutor, 127.0.0.1:8085)

The model lives only as release assets (42 × 25 MiB parts of a `.tar.gz`), never in git history:
<https://github.com/AxiomicCoreness/hello_world.py/releases/tag/model-deepseek-r2-1.5b-q4km-v1>

Automatic (downloads, checks every part against `SHA256SUMS`, joins, extracts, checks the GGUF):

```sh
cd sovereign-irc-bridge/serving/models
./fetch-deepseek-r2.sh
```

Manual (Linux), from a folder holding all `*.part-*` assets and `SHA256SUMS`:

```sh
grep 'part-' SHA256SUMS | sha256sum -c
cat deepseek-r2-1.5b-Q4_K_M.tar.gz.part-* > deepseek-r2-1.5b-Q4_K_M.tar.gz
sha256sum -c --ignore-missing SHA256SUMS
tar -xzf deepseek-r2-1.5b-Q4_K_M.tar.gz
echo "80a49c2fe2410f704ceda4590212174a99899341b01e6af5433319481179e5c1  deepseek-r2-1.5b-Q4_K_M.gguf" | sha256sum -c
mv deepseek-r2-1.5b-Q4_K_M.gguf /path/to/sovereign-irc-bridge/serving/models/
```

Expected: `deepseek-r2-1.5b-Q4_K_M.gguf`, 1,117,320,640 bytes, sha256
`80a49c2fe2410f704ceda4590212174a99899341b01e6af5433319481179e5c1`.
`deepinfer_status.py` reads the same folder (`MODEL_DIR`, default `sovereign-irc-bridge/serving/models`)
and reports `verified` only when the full sha256 matches.

Serve it (the script refuses to start on a missing file or a sha256 mismatch):

```sh
sovereign-irc-bridge/serving/launch-8085-deepseek-r2.sh   # llama-server --host 127.0.0.1 --port 8085
```

## Why the GGUF cannot be the DeepInfer model

The vendored DeepInfer code (`deepinfer/model_executor/models/v4_modules`, pin
`deepseek-ai/DeepInfer@9bd9cf243fc53ef9afbf8f04d391d989117d6ab9`) builds **DeepSeek-V4.1** from a
Hugging Face checkpoint (`config.json` + safetensors). It has no GGUF loader. The 1.5B GGUF is a
different, R1-Distill-style model in llama.cpp's format, so it stays the **secondary** tutor on
`127.0.0.1:8085`; DeepInfer on `127.0.0.1:8090` needs its own weights and hardware.

## Step 2 — DeepInfer itself (needs a GPU host)

Upstream README at the pin, quoted:

> Supported hardware:
> - NVIDIA SM100 GPUs
> - Huawei Ascend 950 NPUs
>
> Prerequisites: Linux · GCC >= 13.0 · Python 3.12 · CUDA 13 (NVIDIA only) · CANN 9.2 (Ascend only)

> ``` bash
> # Use `ascend` instead for the Ascend platform
> # Keep it exported in the environment where you run DeepInfer
> export DEEPINFER_ACCELERATOR=nvidia
> ./build.sh
> ```

> The default checkpoint, `deepseek-ai/DeepSeek-V4.1-Flash-1017`, is downloaded into the Hugging Face
> cache on the first run; set `DEEPINFER_HF_MODEL_DIR=/path/to/DeepSeek-V4.1-Flash-1017` to run from a
> local copy instead.
>
> ``` bash
> python examples/offline_inference.py
> ```

and from `examples/README.md` at the pin:

> ``` bash
> python examples/offline_inference.py --ep 8
> python examples/offline_inference.py --ep 2 --dp 8
> python examples/offline_inference.py --ep 2 --cp 8
> ```

So on a GPU host:

```sh
git clone https://github.com/deepseek-ai/DeepInfer && cd DeepInfer
git checkout 9bd9cf243fc53ef9afbf8f04d391d989117d6ab9
# fresh, empty Python 3.12 environment first (upstream requirement)
export DEEPINFER_ACCELERATOR=nvidia
./build.sh
export DEEPINFER_HF_MODEL_DIR=/path/to/DeepSeek-V4.1-Flash-1017   # optional local copy
python examples/offline_inference.py --ep 8
```

The vendored copy in this repo is for provenance, CI pin checks and `/llm status`; it is **not**
runnable on its own: it has no compiled `deepinfer._C` extension (built by upstream `./build.sh`)
and none of torch / deep_gemm / deep_ep / flash_mla / tile_kernels / tilelang / deep_select /
deep_cluster.

### Honest gap: upstream has no HTTP server on 8090

At this pin DeepInfer ships **offline inference only**. Its README says so ("This open-source
release provides offline inference …") and lists what a complete inference service still needs
("not included in this release": a KV cache system, VE/Prefill/Decode disaggregation, load balancing
across data-parallel replicas). There is no OpenAI-compatible server, no `/v1/chat/completions`
and no `/health`, so there is no upstream command that listens on `127.0.0.1:8090`, and this
runbook does not invent one.

The only HTTP listener upstream has is the optional profiling API
(`deepinfer/engine/profile_server.py`, `DEEPINFER_PROFILE_HTTP_ENABLE`, port base 6070). It binds
`0.0.0.0` and is not a chat API. **Leave `DEEPINFER_PROFILE_HTTP_ENABLE` unset.**

To make `/llm` reach DeepInfer, someone has to write a small adapter around upstream's offline
`deepinfer.entrypoints.llm` API. To work with the bridge unchanged it must:

- listen on `127.0.0.1:8090` only;
- answer `GET /health` (or `GET /v1/models`) with HTTP 200 (the bridge's liveness probe);
- accept `POST /v1/chat/completions` with OpenAI-style `messages` and return
  `choices[0].message.content` (what `sovereign-irc-bridge/src/llm_backend.py` sends and reads).

That adapter is not in this repo or upstream yet.

## Step 3 — point the bridge at it

The bridge already defaults to DeepInfer first. With the adapter up on the GPU host's loopback
(reach it from the bridge host through an SSH local forward, which also stays on loopback):

```sh
ssh -N -L 127.0.0.1:8090:127.0.0.1:8090 gpu-host &      # optional, when the GPU is elsewhere
export DEEPINFER_URL=http://127.0.0.1:8090/v1/chat/completions   # the default; shown for clarity
export DEEPINFER_MODEL=deepinfer                                  # whatever the adapter expects
sovereign-irc-bridge/serving/launch-6680-deepseek-r2.sh
```

The launch script itself sets `LLM_BACKEND=deepinfer`, `LLM_FALLBACK=clarkeyoursatee` and the tutor
at `http://127.0.0.1:8085/v1/chat/completions` (`deepseek-r2-1.5b`); it does not touch
`DEEPINFER_URL` / `DEEPINFER_MODEL`, so the exports above carry through.

`llm_backend` refuses non-loopback URLs, so a `0.0.0.0` or public URL will not start.

What the order line shows in the CLI:

| State | Line |
|---|---|
| DeepInfer answered | `[System] llm order: primary=deepinfer answered` |
| DeepInfer down, tutor answered | `[System] llm order: primary=deepinfer offline → secondary: deepseek tutor (deepseek-r2-1.5b) answered` |
| DeepInfer down, no fallback | `[System] llm order: primary=deepinfer offline, no secondary (LLM_FALLBACK unset)` |

Liveness is cached for `DEEPINFER_REPROBE_S` (default 30 s), so allow up to 30 s after the adapter
starts before the first line flips to `primary=deepinfer answered`.
