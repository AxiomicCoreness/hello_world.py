# Sovereign Engine (workspace)

## Run
```bash
python3 engine/sovereign_engine.py --m93-only --quiet
python3 -m uvicorn engine.mini_token_server:app --host 127.0.0.1 --port 8089
python3 engine/uprho_global_batch.py --count 500 --seal
python3 engine/plugin_framework.py
```

## DeepInfer (optional)

DeepInfer is an **optional GPU accelerator**, not the control plane.
Use `engine/deepinfer_accelerator.py`. Copied DeepInfer engine modules live under
`engine/deepinfer_shim/` (see that README). Full package: `vendor/DeepInfer`
after `./scripts/init_deepinfer_vendors.sh`. Details: `docs/deepinfer_integration.md`.
