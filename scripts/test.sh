#!/usr/bin/env bash
set -euo pipefail
exec python -m pytest tests/test_bind.py tests/test_gearbox.py tests/test_routes.py tests/test_models.py -q
