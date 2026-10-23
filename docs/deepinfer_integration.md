# DeepInfer optional accelerator integration

Status: local branch `deepinfer-optional-accelerator` (not pushed by default).

## Role

| Layer | Owns |
|-------|------|
| Primary | `garden_surgery/`, `engine/sovereign_engine*`, `deepseek.api`, `quantum/` |
| Optional accelerator | `vendor/DeepInfer` + kernels; entry `engine/deepinfer_accelerator.py` |

DeepInfer never replaces personal engines. `complete()` prefers `deepseek.api`
unless `DEEPINFER_FORCE=1` and the package is installed.

## Pins (do not invent)

From `deepseek-ai/DeepInfer@9bd9cf243fc53ef9afbf8f04d391d989117d6ab9`:

- DeepInfer `9bd9cf243fc53ef9afbf8f04d391d989117d6ab9`
- DeepGEMM `1fc9c66975ee322d628b3288534ca0e9ce12a64d`
- FlashMLA `2e5429fc5653bab6e081f09477126f731882a6a9`
- DeepEP `f6aa38fe06cd4a0489e7730365d4e0114970a2f3`
- DeepSelect `bfa4507d935f17ebfc3d0f00ff7d3c9a4d0e5c18`
- DeepGEMM-Ascend `3a35326271b069b8b5bf1a754435acd6cc91575b`
- DeepEP-Ascend `3b25377d04b24fc6154698ded78a2bcb2c59afff`

See `vendor/PINNED_SHAS.md`. Initialize checkouts:

```bash
./scripts/init_deepinfer_vendors.sh
```

First land may be **text-only** (`.gitmodules` + pin docs + script). Recording
gitlinks requires a machine that can `git clone` those remotes, then
`git add vendor/...`.

## Engine collision untangle

Identical DeepInfer copies formerly at:

- `engine/llm_engine.py`
- `engine/arg_utils.py`
- `engine/engine_type.py`

moved to `engine/deepinfer_shim/` so sovereign modules keep `engine/` clear.
Import the accelerator via `engine.deepinfer_accelerator`, not the shim.

Diverged files (`profile_server.py`, `stats_logger.py`) were left in place for
a follow-up diff against upstream.

## Kaniko

Jobs now use `--dockerfile=argocd/Dockerfile.deepinfer`. PAT placeholders were
removed; auth is `TODO(auth)` with secret name left to cluster owners.

## Follow-ups (open)

1. **CUDA 12.4.1 vs CUDA 13** — `argocd/Dockerfile.deepinfer` still uses 12.4.1;
   upstream DeepInfer documents CUDA 13 + `torch==2.13.0+cu132` + SM100.
2. **`requirements-nvidia.txt`** — missing at repo root; after vendor init use
   `vendor/DeepInfer/requirements-nvidia.txt` (do not invent a partial copy).
3. Record submodule **gitlinks** after running the init script.
4. Wire a real offline generate path only on hardware that can build `_C`.
5. Align or drop diverged `engine/profile_server.py` / `stats_logger.py`.

## AIME overlay

`eval/aime/bench.py` is a vendored copy of upstream AIME harness with one
regex change (`\d{1,3}` → `\d+`) for 4+ digit tail fallbacks. Header cites
upstream SHA. Needs `eval/common/io.py` (also vendored, unmodified).
