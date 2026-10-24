# forlorn/ — ClarkeYoursaTee build, eval, seal and serve

ClarkeYoursaTee is the local fallback model for the `/llm` bridge. It is served
by `llama-server` on `127.0.0.1:8082` and replaces the earlier RalphSeek
fixture. The `deepseek-fixture` bridge backend has been removed, with no alias.

## What it is (honest provenance)

| | |
|---|---|
| Base weights | `huihui-ai/Qwen2.5-1.5B-Instruct-abliterated` (derived from `Qwen/Qwen2.5-1.5B-Instruct`, Apache-2.0) |
| Note | The `huihui-ai` HF repo currently returns HTTP 401 (private or removed); the GGUF below is the available copy |
| Base GGUF | `mradermacher/Qwen2.5-1.5B-Instruct-abliterated-GGUF`, file `Qwen2.5-1.5B-Instruct-abliterated.Q4_K_M.gguf` |
| Base sha256 | `59aa9f44bde5349dbe292d7024d197db605f422b8baf65f3246a59abbde4e8e9` (pinned in `build_gguf.sh`) |
| Base SHA3-256 | `599e9c2300056c0ea28ef223d961d4d8cdb9b1be2b28e18b177ef6de82abc719` |
| Output | `ClarkeYoursaTee-1.5B-Q4_K_M.gguf`; hashes are in `MANIFEST.json` |

**ClarkeYoursaTee is not fine-tuned.** `build_gguf.sh` copies all 338 tensors
byte for byte and fails if any of them differ. The only changes are metadata:
`general.name`, `general.description`, and the chat template. The chat template
now carries a softened default system prompt (`system_prompt.txt`) and nine
few-shot turns (`fewshot.json`). The build is deterministic: rebuilding gives an
identical sha256.

The default system prompt and few-shot turns are used **only when a client sends
no system message**. The `/llm` bridge always sends its own `SYSTEM_PROMPT`, so
bridge replies come from the base abliterated Qwen weights plus the bridge
prompt.

### Few-shot disclosure

The few-shot turns cover the same answer *formats* as the evals: plain
arithmetic, a bare YAML mapping, declining to answer about unknown DeepGEMM
items, and scientific notation. No shot contains an eval case's identifiers or
expected values. However, some shots deliberately follow the wording style of
the eval prompts: a DeepGEMM file request and two YAML prompts. The shots and
their order were tuned until the evals passed. A pass therefore shows format
compliance on these nine cases. It is not evidence of general capability.

### Reproducibility caveat

Even at temperature 0 with one slot and prompt caching off (the
`launch_8082.sh` flags), identical requests to this CPU build of llama.cpp
**sometimes produce different replies**. On some prompts the top two tokens are
nearly tied. Earlier prompt versions passed the gate only some of the time.
Treat the eval gate as a sample, not as a proof: run `make eval` several times
before trusting a rebuild.

## Hardware limits on this box

The box has no GPU. It is CPU-only: an 8-core Xeon (AVX-512/AMX) with 15 GiB of
RAM, of which typically only 2–4 GiB is free while the servers are running.

- **No QLoRA**: bitsandbytes 4-bit training needs CUDA.
- **No vLLM**: it needs a GPU. Serving uses `llama.cpp` `llama-server`, at about
  35–40 tok/s for this model.
- `llama.cpp` b11840 on the box has no `llama-finetune`, and `peft` and
  `transformers` are not installed.

Fine-tuning is a **future step**. Our rough, unmeasured estimate for bf16 LoRA
on the 1.5B model on this CPU is about 1.5–3 hours per 1M training tokens, and
it would need about 5–6 GB of free RAM. A GPU is strongly recommended. Nothing
in this directory trains a model.

## Layout

| Path | Purpose |
|---|---|
| `Makefile` | `build`, `eval`, `seal`, `serve` |
| `build_gguf.sh` | Verifies the base sha256, renders the template, writes the GGUF and `MANIFEST.json`, and checks that tensors are identical |
| `system_prompt.txt` | Softened default system prompt |
| `fewshot.json` | Few-shot turns baked into the template (see the disclosure above) |
| `skills/evaluation/` | Three loopback-only evals; each exits non-zero unless every case passes |
| `serving/launch_8082.sh` | `llama-server --jinja --host 127.0.0.1 --port 8082 -c 4096 -np 1 --no-cache-prompt --alias clarkeyoursatee` |
| `ledger_integration/seal_model_hash.py` | Prints sha256 and SHA3-256, writes or checks `MANIFEST.json`. It **never** edits the ledger |
| `MANIFEST.json` | Hashes of the model, base, template, prompt and few-shots |

No weights are committed: `.gitignore` excludes `*.gguf` and `build/`. This
directory has no curriculum or training data, and none is implied.

## Usage

```bash
make build GGUF_PY=/path/to/python-with-gguf-0.19.0   # writes /workspace/llama/ClarkeYoursaTee-1.5B-Q4_K_M.gguf
make seal                                             # verify the GGUF against MANIFEST.json
make serve                                            # 127.0.0.1:8082 only
make eval                                             # gate: all three evals must pass
```

Bridge configuration: `LLM_FALLBACK=clarkeyoursatee` (or `LLM_BACKEND=clarkeyoursatee`)
and `LLM_CLARKEYOURSATEE_URL=http://127.0.0.1:8082/v1/chat/completions` (the default).
Replies are prefixed with
`[ClarkeYoursaTee (Qwen2.5-1.5B-Instruct-abliterated derivative)] `.

## Evals

- `eval_ledger_syntax`: the reply must parse with `yaml.safe_load` into a mapping with exact values (3 cases).
- `eval_math_drift`: 17+25 and 12×12 with no stray numbers, plus a check that 164,000 K
  is written as 1.64×10^5 K and does not drift to 2.3e46. No repository source was found
  for the 1.64e5 K figure; the repo's PlanckEngine `hawkingTempK` is 8.405783e+07 K. This
  case tests notation fidelity only and makes no physics claim.
- `eval_hallucination_rate`: three questions about DeepGEMM items that do not exist. A pass
  requires a decline, no code, and no number that was not in the prompt.

## Out of scope

The following are not done here: the 135 MB corpus expansion, vLLM, Port-380, any
training, and any change to the ledger.
