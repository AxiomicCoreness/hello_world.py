# CI Wire Confirmation — Hybrid RK4 + Stack

**Date:** 2026-08-06

## Changes
- `.github/workflows/pytest.yml`
  - Matrix expanded to 3.10 / 3.11 / 3.12
  - Explicit step: `tests/test_hybrid_rk4.py` + import gate for `hybrid_rk4_simulator`
  - `PYTEST_ADDOPTS=-p no:cacheprovider`

- `.github/workflows/sovereign-engine-ci.yml`
  - Path filters now include:
    - `hybrid_rk4_simulator.py`
    - `tests/**`
    - `toolkit/**`
    - `metrics.py`, `verifier_worker.py`, `precision_policy.py`, `fuse_stack.py`
  - New step: Hybrid RK4 smoke + `pytest tests/test_hybrid_rk4.py`
  - Byte-compile covers hybrid_rk4 + related modules

## Local verification
```
pytest tests/ -q  →  10 passed
pytest tests/test_hybrid_rk4.py → 6 passed
```

## Notes
- Measured digests only. Local workflow files ready.
- `requirements-ci.txt` remains minimal (`pytest`, `numpy`).
