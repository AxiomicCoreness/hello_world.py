# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""Garden plugin namespace — zero external deps."""
from .base import Plugin
from .loader import discover_plugins, run_plugins

__all__ = ["Plugin", "discover_plugins", "run_plugins"]
