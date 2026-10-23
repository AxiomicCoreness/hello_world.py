# Sparse DeepInfer vendor (v4_modules only)

| Field | Value |
|-------|-------|
| Upstream | https://github.com/deepseek-ai/DeepInfer |
| Commit | `9bd9cf243fc53ef9afbf8f04d391d989117d6ab9` |
| Path | `deepinfer/model_executor/models/v4_modules/` |
| License | Apache-2.0 |
| Scope | **Only** `v4_modules` (+ minimal parent `__init__.py` stubs) |

## Why top-level `deepinfer/`

Repo imports already use the package name, e.g.
`from deepinfer.model_executor.models.v4_modules.engram import CompressedTokenizer`
(`engine/deepinfer_shim/llm_engine.py`). A top-level tree matches that path without
PYTHONPATH hacks.

The full DeepInfer checkout remains the **submodule** plan under
`vendor/DeepInfer` (pin in `vendor/PINNED_SHAS.md`). After
`./scripts/init_deepinfer_vendors.sh`, the same tree also exists at:

`vendor/DeepInfer/deepinfer/model_executor/models/v4_modules/`

This sparse copy is the in-repo anchor for skill / CI / provenance when the
submodule gitlink is not yet recorded. It is **not** a Swift/Xcode source and
does **not** replace Sovereign PlanckEngine.

## Files (24)

See listing under `model_executor/models/v4_modules/`.
