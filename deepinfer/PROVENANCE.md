# Sparse DeepInfer vendor (v4_modules + the parent modules it imports)

| Field | Value |
|-------|-------|
| Upstream | https://github.com/deepseek-ai/DeepInfer |
| Commit | `9bd9cf243fc53ef9afbf8f04d391d989117d6ab9` |
| Path | `deepinfer/model_executor/models/v4_modules/` |
| License | Apache-2.0 |
| Scope | `v4_modules` (24 files) + the in-package modules they transitively import (85 files) + upstream `LICENSE` |

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

## Parent modules vendored for v4_modules (added 2026-10-30T13:11:37-04:00)

**Why.** `v4_modules` imports `deepinfer` (AttrDict / PLATFORM / envs), `parallel_utils`, `layers` +
`tilelang_ops`, `input_metadata`, `engine.engine_type`, `timer`, `model_executor.utils`, `worker.cache_engine`,
`eplb`, … With only the 24 files, `import` of any submodule could stop on a *missing in-package module*.
Now it can stop only on an external dependency (torch, deep_gemm, deep_ep, flash_mla, tile_kernels,
tilelang, deep_select, deep_cluster, …) or the compiled `deepinfer._C`.

**How the list was computed.** Transitive closure of every `deepinfer.*` import (module-level,
function-level and `TYPE_CHECKING`) starting from all `v4_modules/*.py`, over upstream at
`9bd9cf243fc53ef9afbf8f04d391d989117d6ab9`. `tests/test_deepinfer_vendor.py` recomputes it and requires it
to equal the vendored set exactly (Python >= 3.12, like upstream).

**Pin + integrity.** Every file's git blob sha (from
`gh api repos/deepseek-ai/DeepInfer/git/trees/9bd9cf243fc53ef9afbf8f04d391d989117d6ab9?recursive=1`) is in
`deepinfer/VENDOR_MANIFEST.json`; the test recomputes `git hash-object` in Python for each file.

**Byte-identical** (Apache-2.0 headers intact as upstream ships them), except:

| File | Treatment | Reason |
|---|---|---|
| `deepinfer/__init__.py` | repo header + upstream bytes after a marker line | the former 4-line stub lacked `AttrDict` / `PLATFORM` / `envs`, which v4_modules imports; header adds only a Python >= 3.12 guard that raises `ImportError` (upstream `environ.py` is 3.12-only syntax, so 3.10/3.11 would otherwise hit a `SyntaxError`) |
| `deepinfer/model_executor/models/__init__.py` | repo header (comments only) + upstream bytes | `hugging_face/config.py` imports `ModelRegistry` from here; the comment-only stub could not provide it |
| `deepinfer/model_executor/__init__.py` | repo stub kept | upstream file is empty (0 bytes); the stub is comments only, so behaviour is identical |

`deepinfer/LICENSE` is upstream's root `LICENSE`, byte-identical.

**Not vendored.** `deepinfer._C` (compiled C++/CUDA extension built by upstream `./build.sh`); no `.cu`/`.cpp`/`.so`.
`ModelRegistry` resolves `deepseek_vl` by string at runtime, so `models/deepseek_vl.py`, `deepseek.py` and
`decoder_layer.py` are outside the import closure and not vendored; `ModelRegistry.load_model_cls` therefore
returns nothing usable here. The vendored tree is for provenance, pin checks and `/llm status`, not for serving.

### Former repo stubs (preserved verbatim)

`deepinfer/__init__.py`:

```python
# Sparse vendor skeleton for DeepInfer v4_modules only.
# Full package: vendor/DeepInfer after scripts/init_deepinfer_vendors.sh
# Provenance: deepseek-ai/DeepInfer@9bd9cf243fc53ef9afbf8f04d391d989117d6ab9
# License: Apache-2.0 (upstream).
```

`deepinfer/model_executor/models/__init__.py`:

```python
# Sparse vendor parent for deepinfer.model_executor.models.v4_modules
# Full ModelRegistry lives upstream; not vendored here.
# Provenance: deepseek-ai/DeepInfer@9bd9cf243fc53ef9afbf8f04d391d989117d6ab9
```

### Vendored parent files (85)

- `deepinfer/__init__.py`
- `deepinfer/attrdict.py`
- `deepinfer/config.py`
- `deepinfer/distributed/__init__.py`
- `deepinfer/distributed/shm_broadcast.py`
- `deepinfer/engine/__init__.py`
- `deepinfer/engine/engine_type.py`
- `deepinfer/environ.py`
- `deepinfer/hugging_face/__init__.py`
- `deepinfer/hugging_face/config.py`
- `deepinfer/hugging_face/loading.py`
- `deepinfer/hugging_face/names.py`
- `deepinfer/hugging_face/parameters.py`
- `deepinfer/hugging_face/processor.py`
- `deepinfer/hugging_face/tokenizer.py`
- `deepinfer/hugging_face/weights.py`
- `deepinfer/load_class.py`
- `deepinfer/logger.py`
- `deepinfer/model_config_loader.py`
- `deepinfer/model_executor/__init__.py`
- `deepinfer/model_executor/eplb/__init__.py`
- `deepinfer/model_executor/eplb/policy.py`
- `deepinfer/model_executor/eplb/shuffle.py`
- `deepinfer/model_executor/input_metadata/__init__.py`
- `deepinfer/model_executor/input_metadata/dflash.py`
- `deepinfer/model_executor/input_metadata/input_metadata.py`
- `deepinfer/model_executor/input_metadata/prepare_tensor_input_zos.py`
- `deepinfer/model_executor/input_metadata/yoco.py`
- `deepinfer/model_executor/layer_utils.py`
- `deepinfer/model_executor/layers/__init__.py`
- `deepinfer/model_executor/layers/attention_backend.py`
- `deepinfer/model_executor/layers/layernorm.py`
- `deepinfer/model_executor/layers/linear.py`
- `deepinfer/model_executor/layers/rotary_embedding.py`
- `deepinfer/model_executor/layers/tilelang_ops/__init__.py`
- `deepinfer/model_executor/layers/tilelang_ops/cache_common.py`
- `deepinfer/model_executor/layers/tilelang_ops/candidate_blocks.py`
- `deepinfer/model_executor/layers/tilelang_ops/common.py`
- `deepinfer/model_executor/layers/tilelang_ops/compress.py`
- `deepinfer/model_executor/layers/tilelang_ops/flash_mla_utils.py`
- `deepinfer/model_executor/layers/tilelang_ops/fused_transform.py`
- `deepinfer/model_executor/layers/tilelang_ops/gather.py`
- `deepinfer/model_executor/layers/tilelang_ops/gather_engram_tokens_zos.py`
- `deepinfer/model_executor/layers/tilelang_ops/gather_input_ids_zos.py`
- `deepinfer/model_executor/layers/tilelang_ops/get_kv_index.py`
- `deepinfer/model_executor/layers/tilelang_ops/kv_index_cat.py`
- `deepinfer/model_executor/layers/tilelang_ops/load_paged_kv_cache.py`
- `deepinfer/model_executor/layers/tilelang_ops/norm.py`
- `deepinfer/model_executor/layers/tilelang_ops/ops.py`
- `deepinfer/model_executor/layers/tilelang_ops/prepare_cp_mirror.py`
- `deepinfer/model_executor/layers/tilelang_ops/prepare_v4_decode_metadata.py`
- `deepinfer/model_executor/layers/tilelang_ops/state_cache.py`
- `deepinfer/model_executor/layers/tilelang_ops/store_kv_cache.py`
- `deepinfer/model_executor/layers/tilelang_ops/swa_index.py`
- `deepinfer/model_executor/model_metadata_utils.py`
- `deepinfer/model_executor/models/__init__.py`
- `deepinfer/model_executor/models/vision_encoder/__init__.py`
- `deepinfer/model_executor/models/vision_encoder/mlp_projector.py`
- `deepinfer/model_executor/models/vision_encoder/vit.py`
- `deepinfer/model_executor/parallel_utils/__init__.py`
- `deepinfer/model_executor/parallel_utils/communication_op.py`
- `deepinfer/model_executor/parallel_utils/cp.py`
- `deepinfer/model_executor/parallel_utils/parallel_state.py`
- `deepinfer/model_executor/parallel_utils/userbuffer.py`
- `deepinfer/model_executor/utils.py`
- `deepinfer/multimodal_tokens.py`
- `deepinfer/npu_ops/__init__.py`
- `deepinfer/npu_ops/patch_imports.py`
- `deepinfer/platform.py`
- `deepinfer/sequence.py`
- `deepinfer/shared_memory.py`
- `deepinfer/testing.py`
- `deepinfer/timer.py`
- `deepinfer/utils.py`
- `deepinfer/ve/__init__.py`
- `deepinfer/ve/prepare_tensor_input_vl.py`
- `deepinfer/ve/processor/__init__.py`
- `deepinfer/ve/processor/common.py`
- `deepinfer/ve/processor/image_processor.py`
- `deepinfer/ve/processor/mm_processor.py`
- `deepinfer/ve/processor/text_processor.py`
- `deepinfer/ve/schema.py`
- `deepinfer/worker/__init__.py`
- `deepinfer/worker/cache_engine.py`
- `deepinfer/worker/zos_status.py`

See `docs/DEEPINFER_8090_RUNBOOK.md` for running DeepInfer on a GPU host and `sovereign-irc-bridge/src/deepinfer_status.py` (`/llm status`) for what this machine is missing.
