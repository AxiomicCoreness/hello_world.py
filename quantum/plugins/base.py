#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Plugin base class — minimal, no external deps."""

from typing import Any, Dict


class Plugin:
    name: str = "base"
    description: str = "A Garden plugin"
    soft: bool = True

    def check(self, strict: bool = False) -> Dict[str, Any]:
        raise NotImplementedError("Plugins must implement check()")
