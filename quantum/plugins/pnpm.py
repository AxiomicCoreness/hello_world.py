#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pnpm plugin."""

import subprocess
from pathlib import Path

from .base import Plugin


class PnpmPlugin(Plugin):
    name = "pnpm"
    description = "pnpm and vitest.config.e2e.ts"
    soft = True

    def check(self, strict: bool = False):
        result = {"name": self.name, "passed": True, "message": ""}
        try:
            subprocess.run(["pnpm", "--version"], capture_output=True, check=True, timeout=5)
            result["message"] = "pnpm available"
        except Exception:
            result["passed"] = False
            result["message"] = "pnpm not found in PATH"
            return result
        config = Path("vitest.config.e2e.ts")
        if not config.exists():
            result["passed"] = False
            result["message"] += " | vitest.config.e2e.ts missing"
        else:
            result["message"] += " | vitest.config.e2e.ts present"
        return result
