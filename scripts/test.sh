#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT

set -euo pipefail
exec python -m pytest tests/test_bind.py tests/test_gearbox.py tests/test_routes.py tests/test_models.py -q
