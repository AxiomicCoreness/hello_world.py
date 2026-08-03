# sovereign_engine.py

Full v7.4 source (~78KB, 1754 lines) is built in the agent workspace:

`/home/workdir/artifacts/sovereign_engine.py`

## Why not fully on GitHub yet

Single-file API upload of the full 78KB payload was truncated by transport limits. Working modules are already on `main` under `engine/`:

- plugin_framework.py
- instrumented_batch.py
- uprho_global_batch.py
- mini_token_server.py
- layer_cache.py
- workers.py
- restore_sovereign_engine.py

## Local install

```bash
cp /home/workdir/artifacts/sovereign_engine.py engine/
# or from a machine with the artifact:
python3 engine/sovereign_engine.py --m93-only --quiet
```

## Restore path (when full .gz.b64 is complete)

```bash
python3 engine/restore_sovereign_engine.py
```
