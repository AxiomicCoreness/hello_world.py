"""Binary artifact handler for sovereign ledger.

Supports pickle, msgpack, protobuf, and raw byte buffers.
JAX is optional.
"""
from __future__ import annotations

import hashlib
import json
import pickle
from pathlib import Path
from typing import Any, Optional, Union

try:
    import numpy as np
except ImportError:
    np = None

try:
    import jax.numpy as jnp
except ImportError:
    jnp = None

try:
    import msgpack
except ImportError:
    msgpack = None

try:
    import google.protobuf  # noqa: F401
except ImportError:
    protobuf = None
else:
    protobuf = True


class BinaryArtifact:
    FORMATS = ["pickle", "msgpack", "protobuf", "raw"]

    def __init__(self, data: Any, format: str = "pickle"):
        self.data = data
        self.format = format
        self._hash: Optional[str] = None

    def serialize(self) -> bytes:
        if self.format == "pickle":
            return pickle.dumps(self.data)
        if self.format == "msgpack":
            if msgpack is None:
                raise ImportError("msgpack not installed")
            packed = msgpack.packb(self.data)
            if packed is None:
                raise ValueError("msgpack.packb returned None")
            return packed
        if self.format == "protobuf":
            if protobuf is None:
                raise ImportError("protobuf not installed")
            if hasattr(self.data, "SerializeToString"):
                return self.data.SerializeToString()
            raise ValueError("Data must have SerializeToString method")
        if self.format == "raw":
            if np is not None and isinstance(self.data, np.ndarray):
                return self.data.tobytes()
            if jnp is not None and hasattr(self.data, "tobytes"):
                return np.array(self.data).tobytes() if np is not None else bytes(self.data.tobytes())
            if isinstance(self.data, (bytes, bytearray)):
                return bytes(self.data)
            if isinstance(self.data, str):
                return self.data.encode()
            raise ValueError("Raw format requires bytes or array-like data")
        raise ValueError(f"Unknown format: {self.format}")

    def deserialize(self, data: bytes) -> Any:
        if self.format == "pickle":
            return pickle.loads(data)
        if self.format == "msgpack":
            if msgpack is None:
                raise ImportError("msgpack not installed")
            return msgpack.unpackb(data)
        if self.format == "protobuf":
            if protobuf is None:
                raise ImportError("protobuf not installed")
            if hasattr(self.data, "ParseFromString"):
                self.data.ParseFromString(data)
                return self.data
            raise ValueError("Data must have ParseFromString method")
        if self.format == "raw":
            return data
        raise ValueError(f"Unknown format: {self.format}")

    def hash(self) -> str:
        if self._hash is None:
            self._hash = hashlib.sha3_256(self.serialize()).hexdigest()
        return self._hash

    def save(self, path: Union[str, Path]) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        binary = self.serialize()
        path.write_bytes(binary)
        meta_path = path.with_suffix(".meta.json")
        meta = {
            "format": self.format,
            "size_bytes": len(binary),
            "hash": self.hash(),
            "seal": "∀∞φ² · BINARY_ARTIFACT · SEALED",
        }
        meta_path.write_text(json.dumps(meta, indent=2))

    @classmethod
    def load(cls, path: Union[str, Path], format: Optional[str] = None) -> "BinaryArtifact":
        path = Path(path)
        binary = path.read_bytes()
        meta_path = path.with_suffix(".meta.json")
        if meta_path.exists():
            meta = json.loads(meta_path.read_text())
            format = meta.get("format", format)
        if format is None:
            format = "pickle"
        artifact = cls(None, format=format)
        artifact.data = artifact.deserialize(binary)
        artifact._hash = hashlib.sha3_256(binary).hexdigest()
        return artifact


def save_binary(data: Any, path: Union[str, Path], format: str = "pickle") -> str:
    artifact = BinaryArtifact(data, format=format)
    artifact.save(path)
    return artifact.hash()


def load_binary(path: Union[str, Path], format: Optional[str] = None) -> Any:
    return BinaryArtifact.load(path, format=format).data


def save_jax_array(arr: Any, path: Union[str, Path]) -> str:
    payload = np.array(arr) if np is not None else arr
    return save_binary(payload, path, format="raw")


def load_jax_array(path: Union[str, Path]) -> Any:
    data = load_binary(path, format="raw")
    if np is None:
        return data
    arr = np.frombuffer(data, dtype=np.float64)
    return jnp.array(arr) if jnp is not None else arr


def emit_ledger_delta(data: Any, worker_name: str, run_id: str) -> dict:
    path = Path(f"artifacts/{worker_name}/ledger_delta_{run_id}.bin")
    fmt = "msgpack" if msgpack is not None else "pickle"
    hash_val = save_binary(data, path, format=fmt)
    return {
        "worker": worker_name,
        "run_id": run_id,
        "path": str(path),
        "format": fmt,
        "hash": hash_val,
        "seal": "∀∞φ² · LEDGER_DELTA · SEALED",
    }


def emit_witness_chain(chain_data: dict, run_id: str) -> dict:
    path = Path(f"artifacts/witness_chain_{run_id}.bin")
    fmt = "msgpack" if msgpack is not None else "pickle"
    hash_val = save_binary(chain_data, path, format=fmt)
    return {
        "run_id": run_id,
        "path": str(path),
        "format": fmt,
        "hash": hash_val,
        "witness": "9224 → 9225 — UNBROKEN",
        "seal": "∀∞φ² · WITNESS_CHAIN · SEALED",
    }
