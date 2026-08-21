#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Plugin loader — discovers and runs plugins without external deps."""

from __future__ import annotations

import importlib.util
import inspect
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from .base import Plugin


def discover_plugins(plugin_dir: Optional[Path] = None) -> List[Type[Plugin]]:
    if plugin_dir is None:
        plugin_dir = Path(__file__).parent
    plugins: List[Type[Plugin]] = []
    for file in plugin_dir.glob("*.py"):
        if file.stem in ("__init__", "base", "loader"):
            continue
        module_name = f"quantum.plugins.{file.stem}"
        try:
            spec = importlib.util.spec_from_file_location(module_name, file)
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            for _name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, Plugin) and obj is not Plugin:
                    plugins.append(obj)
        except Exception as e:
            print(f"\u26a0\ufe0f Failed to load plugin {file.stem}: {e}", file=sys.stderr)
    return plugins


def run_plugins(plugins: List[Type[Plugin]], strict: bool = False) -> Dict[str, Any]:
    results: Dict[str, Any] = {"name": "plugins", "passed": True, "checks": []}
    for plugin_cls in plugins:
        try:
            instance = plugin_cls()
            check_result = instance.check(strict=strict)
            results["checks"].append(check_result)
            if not check_result.get("passed", False):
                if strict or not getattr(instance, "soft", True):
                    results["passed"] = False
        except Exception as e:
            results["checks"].append(
                {
                    "name": getattr(plugin_cls, "name", "unknown"),
                    "passed": False,
                    "error": str(e),
                }
            )
            if strict or not getattr(plugin_cls, "soft", True):
                results["passed"] = False
    return results
