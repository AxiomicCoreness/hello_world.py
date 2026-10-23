# engine/deepinfer_shim/

These files were previously at `engine/llm_engine.py`, `engine/arg_utils.py`,
and `engine/engine_type.py`. They are **byte-identical copies** of
`deepinfer/engine/*` from DeepSeek DeepInfer and collided with the sovereign
engine workspace documented in `engine/README.md` /
`engine/SOVEREIGN_ENGINE_SOURCE.md`.

They were relocated (not deleted) so history stays searchable. **Do not import
them as the primary engine.** The real package lives at
`vendor/DeepInfer/deepinfer/` after `./scripts/init_deepinfer_vendors.sh`.

Optional accelerator entry point for this repo:

```python
from engine.deepinfer_accelerator import complete, deepinfer_available
```

Sovereign / personal engines remain primary.
