"""Garden plugin namespace — zero external deps."""
from .base import Plugin
from .loader import discover_plugins, run_plugins

__all__ = ["Plugin", "discover_plugins", "run_plugins"]
