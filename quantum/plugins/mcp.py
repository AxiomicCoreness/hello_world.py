#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MCP Gate plugin."""

from pathlib import Path

from .base import Plugin


class MCPPlugin(Plugin):
    name = "mcp"
    description = "MCP gate (port380_mcp.py) presence and import"
    soft = True

    def check(self, strict: bool = False):
        result = {"name": self.name, "passed": True, "message": ""}
        mcp_file = Path("port380_mcp.py")
        if not mcp_file.exists():
            result["passed"] = False
            result["message"] = "port380_mcp.py not found in root"
            return result
        try:
            import port380_mcp  # noqa: F401

            result["message"] = "MCP module imported successfully"
        except Exception as e:
            result["passed"] = False
            result["message"] = f"Import failed: {e}"
        return result
