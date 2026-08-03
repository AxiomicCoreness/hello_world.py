#!/usr/bin/env python3
"""Sovereign plugin framework — refactored PluginManager (Entry 8313 lineage)."""
from __future__ import annotations

import hashlib
import inspect
import json
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Type


class PluginError(Exception):
    """Base error for plugin lifecycle failures."""


class PluginNotFound(PluginError):
    pass


class PluginStateError(PluginError):
    pass


class SovereignPlugin(ABC):
    """Base class for all plugins."""

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        ...

    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        ...

    @abstractmethod
    def terminate(self) -> None:
        ...

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "name": self.__class__.__name__,
            "version": getattr(self, "VERSION", "1.0.0"),
            "author": getattr(self, "AUTHOR", "workspace"),
        }

    def seal_plugin(self) -> str:
        source = inspect.getsource(self.__class__)
        return hashlib.sha3_256(source.encode()).hexdigest()


@dataclass
class PluginRecord:
    cls: Type[SovereignPlugin]
    source_hash: str
    active: bool = False
    instance: Optional[SovereignPlugin] = None
    config: Dict[str, Any] = field(default_factory=dict)


class PluginManager:
    """Registry + lifecycle for SovereignPlugin subclasses.

    States per plugin: registered → active → (execute)* → deactivated.
    Thread-safe for concurrent activate/execute from ASGI workers.
    """

    def __init__(self, phase_lock: float = 202.6) -> None:
        self._lock = threading.RLock()
        self._registry: Dict[str, PluginRecord] = {}
        self.phase_lock = phase_lock

    def register(self, plugin_class: Type[SovereignPlugin], *, validate: bool = True) -> str:
        if not issubclass(plugin_class, SovereignPlugin):
            raise PluginError(f"{plugin_class!r} is not a SovereignPlugin")
        probe = plugin_class()
        name = probe.get_metadata()["name"]
        source_hash = probe.seal_plugin()
        if validate:
            probe.initialize({})
            probe.terminate()
        with self._lock:
            if name in self._registry and self._registry[name].active:
                raise PluginStateError(f"cannot re-register active plugin {name}")
            self._registry[name] = PluginRecord(cls=plugin_class, source_hash=source_hash)
        return name

    def register_plugin(self, plugin_class: Type[SovereignPlugin]) -> bool:
        try:
            self.register(plugin_class)
            return True
        except Exception:
            return False

    def activate(self, name: str, config: Optional[Dict[str, Any]] = None) -> None:
        with self._lock:
            rec = self._require(name)
            if rec.active:
                raise PluginStateError(f"{name} already active")
            inst = rec.cls()
            cfg = dict(config or {})
            inst.initialize(cfg)
            rec.instance = inst
            rec.config = cfg
            rec.active = True

    def activate_plugin(self, name: str, config: Optional[Dict[str, Any]] = None) -> bool:
        try:
            self.activate(name, config)
            return True
        except Exception:
            return False

    def deactivate(self, name: str) -> None:
        with self._lock:
            rec = self._require(name)
            if not rec.active or rec.instance is None:
                raise PluginStateError(f"{name} not active")
            rec.instance.terminate()
            rec.instance = None
            rec.active = False
            rec.config = {}

    def deactivate_plugin(self, name: str) -> bool:
        try:
            self.deactivate(name)
            return True
        except Exception:
            return False

    def execute(self, name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            rec = self._require(name)
            if not rec.active or rec.instance is None:
                raise PluginStateError(f"{name} not active")
            inst = rec.instance
        return inst.execute(context)

    def execute_plugin(self, name: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            return self.execute(name, context)
        except Exception:
            return None

    def list_plugins(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "registered": list(self._registry.keys()),
                "active": [n for n, r in self._registry.items() if r.active],
                "hashes": {n: r.source_hash for n, r in self._registry.items()},
                "phase_lock": self.phase_lock,
            }

    def seal_manifest(self) -> str:
        with self._lock:
            manifest = {
                "plugins": list(self._registry.keys()),
                "active": [n for n, r in self._registry.items() if r.active],
                "hashes": {n: r.source_hash for n, r in self._registry.items()},
                "phase_lock": self.phase_lock,
            }
        return hashlib.sha3_256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()

    def _require(self, name: str) -> PluginRecord:
        if name not in self._registry:
            raise PluginNotFound(name)
        return self._registry[name]


class EntropyMonitor(SovereignPlugin):
    VERSION = "1.1.0"

    def initialize(self, config: Dict[str, Any]) -> None:
        self.threshold = float(config.get("threshold", 1e-300))

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        current = float(context.get("entropy", 1.0))
        return {"alert": current > self.threshold, "current": current, "threshold": self.threshold}

    def terminate(self) -> None:
        self.threshold = 1e-300


def mount_plugin_routes(app) -> PluginManager:
    from fastapi import HTTPException
    pm = PluginManager()
    pm.register(EntropyMonitor)

    @app.get("/plugin/list")
    async def plugin_list():
        return pm.list_plugins()

    @app.post("/plugin/activate")
    async def plugin_activate(name: str, config: Dict[str, Any] | None = None):
        ok = pm.activate_plugin(name, config or {})
        return {"success": ok, "name": name}

    @app.post("/plugin/deactivate")
    async def plugin_deactivate(name: str):
        return {"success": pm.deactivate_plugin(name), "name": name}

    @app.post("/plugin/execute")
    async def plugin_execute(name: str, context: Dict[str, Any]):
        result = pm.execute_plugin(name, context)
        if result is None:
            raise HTTPException(status_code=404, detail="Plugin not active or not found")
        return {"result": result}

    @app.get("/plugin/seal")
    async def plugin_seal():
        return {"manifest_seal": pm.seal_manifest()}

    return pm


def _self_test() -> None:
    pm = PluginManager()
    name = pm.register(EntropyMonitor)
    assert name == "EntropyMonitor"
    pm.activate(name, {"threshold": 0.5})
    assert pm.execute(name, {"entropy": 0.1})["alert"] is False
    assert pm.execute(name, {"entropy": 0.9})["alert"] is True
    pm.deactivate(name)
    try:
        pm.execute(name, {})
        raise AssertionError("expected PluginStateError")
    except PluginStateError:
        pass
    assert "EntropyMonitor" in pm.list_plugins()["registered"]
    assert pm.seal_manifest()
    pm2 = PluginManager()
    assert pm2.register_plugin(EntropyMonitor) is True
    assert pm2.activate_plugin("EntropyMonitor") is True
    assert pm2.execute_plugin("EntropyMonitor", {"entropy": 0.0}) is not None
    print("plugin_framework self-test OK")


if __name__ == "__main__":
    _self_test()
