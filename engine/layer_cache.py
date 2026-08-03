"""layer_cache.py – φ-priority layer cache with optional sonify frequencies."""
from __future__ import annotations

import hashlib
from typing import Dict

import numpy as np

PHI = (1 + 5**0.5) / 2
PHI_INV = 1.0 / PHI
F0 = 10.501


class LayerCache:
    """RAM cache of decompressed layers; evict by PHI**(-age) priority."""

    def __init__(self, max_active: int = 16):
        self.max_active = max(1, int(max_active))
        self.cache: Dict[str, np.ndarray] = {}
        self.access_log: Dict[str, int] = {}
        self.cycle_counter = 0

    def priority(self, age: int) -> float:
        return PHI ** (-max(0, age))

    def load(self, layer_id: str, compressed_data: bytes) -> np.ndarray:
        import zlib
        raw = zlib.decompress(compressed_data)
        arr = np.frombuffer(raw, dtype=np.float32).copy()
        noise = np.random.random(arr.shape).astype(np.float32) * np.float32(PHI_INV)
        arr = np.floor(arr + noise).astype(np.float32)
        if len(self.cache) >= self.max_active and layer_id not in self.cache:
            self._evict_lowest_priority()
        self.cache[layer_id] = arr
        self.access_log[layer_id] = self.cycle_counter
        return arr

    def _evict_lowest_priority(self) -> None:
        if not self.cache:
            return
        scores = {
            lid: self.priority(self.cycle_counter - self.access_log.get(lid, 0))
            for lid in self.cache
        }
        lowest = min(scores, key=scores.get)
        del self.cache[lowest]
        del self.access_log[lowest]

    def get(self, layer_id: str) -> np.ndarray:
        if layer_id not in self.cache:
            raise KeyError(f"Layer {layer_id} not in cache")
        self.access_log[layer_id] = self.cycle_counter
        return self.cache[layer_id]

    def step_cycle(self) -> None:
        self.cycle_counter += 1

    def sonify_hz(self, layer_id: str) -> float:
        try:
            n = int(layer_id) % 144
        except ValueError:
            n = int(hashlib.sha3_256(layer_id.encode()).hexdigest(), 16) % 144
        return F0 * (PHI ** (n + 1))

    def stats(self) -> dict:
        return {
            "active": len(self.cache),
            "max_active": self.max_active,
            "cycle": self.cycle_counter,
            "layers": list(self.cache.keys()),
        }


def compress_array(arr: np.ndarray) -> bytes:
    import zlib
    return zlib.compress(np.asarray(arr, dtype=np.float32).tobytes(), level=6)
