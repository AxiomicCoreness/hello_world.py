"""binary_artifacts.py — GARDEN.BIN.v1 worker deltas + pickle/msgpack/raw helpers.

Ledger 9225 remains the first container seal.
Ledger 9226 seals this framed codec.
"""
from __future__ import annotations

import hashlib
import json
import os
import pickle
import struct
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Union

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

MAGIC = b"GARDEN.B"
VERSION = 1
HEADER_SIZE = 90
HASH_SIZE = 32
WORKERS = ["deploy", "notify", "verify", "ledger", "north-star"]
PHI = (1.0 + 5.0 ** 0.5) / 2.0
PHI_SQ = PHI ** 2
THETA_SOVEREIGN = 2.5416018462


def _pad32(text: str) -> bytes:
    raw = text.encode("utf-8")
    if len(raw) > 32:
        raise ValueError(f"field exceeds 32 bytes: {text!r}")
    return raw.ljust(32, b"\x00")


@dataclass
class BinaryDelta:
    worker: str
    run_id: str
    payload: bytes
    timestamp_ns: int = field(default_factory=lambda: time.time_ns())
    sha3_256: str = field(init=False, default="")

    def __post_init__(self) -> None:
        if self.worker not in WORKERS:
            raise ValueError(f"Unknown worker: {self.worker}. Must be one of {WORKERS}")
        self.sha3_256 = hashlib.sha3_256(self.pack()).hexdigest()

    def pack(self) -> bytes:
        return (
            MAGIC
            + struct.pack(">H", VERSION)
            + _pad32(self.worker)
            + _pad32(self.run_id)
            + struct.pack(">q", self.timestamp_ns)
            + struct.pack(">Q", len(self.payload))
            + self.payload
        )

    def serialize(self) -> bytes:
        packed = self.pack()
        return packed + hashlib.sha3_256(packed).digest()

    @staticmethod
    def deserialize(data: bytes) -> "BinaryDelta":
        if len(data) < HEADER_SIZE + HASH_SIZE:
            raise ValueError(f"Binary too short: {len(data)} bytes")
        if data[:8] != MAGIC:
            raise ValueError(f"Bad magic: {data[:8]!r}")
        version = struct.unpack(">H", data[8:10])[0]
        if version != VERSION:
            raise ValueError(f"Unsupported version: {version}")
        worker = data[10:42].rstrip(b"\x00").decode("utf-8")
        run_id = data[42:74].rstrip(b"\x00").decode("utf-8")
        timestamp_ns = struct.unpack(">q", data[74:82])[0]
        payload_len = struct.unpack(">Q", data[82:90])[0]
        end = HEADER_SIZE + payload_len
        if len(data) < end + HASH_SIZE:
            raise ValueError(f"Truncated payload: expected {payload_len} bytes")
        payload = data[HEADER_SIZE:end]
        stored = data[end:end + HASH_SIZE]
        computed = hashlib.sha3_256(data[:end]).digest()
        if computed != stored:
            raise ValueError("Hash mismatch: container integrity violated")
        return BinaryDelta(
            worker=worker,
            run_id=run_id,
            payload=payload,
            timestamp_ns=timestamp_ns,
        )

    def verify(self) -> bool:
        try:
            BinaryDelta.deserialize(self.serialize())
            return True
        except ValueError:
            return False


def emit_json_delta(data: dict, worker: str, run_id: str) -> BinaryDelta:
    payload = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return BinaryDelta(worker=worker, run_id=run_id, payload=payload)


def get_artifact_dir(worker: str, base_dir: Union[str, Path] = "artifacts") -> Path:
    if worker not in WORKERS:
        raise ValueError(f"Unknown worker: {worker}")
    path = Path(base_dir) / worker
    path.mkdir(parents=True, exist_ok=True)
    return path


def upload_artifact(delta: BinaryDelta, base_dir: Union[str, Path] = "artifacts") -> str:
    filepath = get_artifact_dir(delta.worker, base_dir) / f"run_{delta.run_id}.bin"
    filepath.write_bytes(delta.serialize())
    return str(filepath)


def load_artifact(filepath: Union[str, Path]) -> BinaryDelta:
    return BinaryDelta.deserialize(Path(filepath).read_bytes())


class BinaryArtifact:
    FORMATS = ["pickle", "msgpack", "protobuf", "raw", "garden_bin"]

    def __init__(self, data: Any, format: str = "pickle"):
        self.data = data
        self.format = format
        self._hash: Optional[str] = None

    def serialize(self) -> bytes:
        if self.format == "garden_bin" and isinstance(self.data, BinaryDelta):
            return self.data.serialize()
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
            if isinstance(self.data, (bytes, bytearray)):
                return bytes(self.data)
            if isinstance(self.data, str):
                return self.data.encode()
            raise ValueError("Raw format requires bytes or array-like data")
        raise ValueError(f"Unknown format: {self.format}")

    def deserialize(self, data: bytes) -> Any:
        if self.format == "garden_bin":
            return BinaryDelta.deserialize(data)
        if self.format == "pickle":
            return pickle.loads(data)
        if self.format == "msgpack":
            if msgpack is None:
                raise ImportError("msgpack not installed")
            return msgpack.unpackb(data)
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
        path.with_suffix(".meta.json").write_text(
            json.dumps(
                {
                    "format": self.format,
                    "size_bytes": len(binary),
                    "hash": self.hash(),
                    "seal": "∀∞φ² · BINARY_ARTIFACT · SEALED",
                },
                indent=2,
            )
        )

    @classmethod
    def load(cls, path: Union[str, Path], format: Optional[str] = None) -> "BinaryArtifact":
        path = Path(path)
        binary = path.read_bytes()
        meta_path = path.with_suffix(".meta.json")
        if meta_path.exists():
            format = json.loads(meta_path.read_text()).get("format", format)
        if format is None:
            format = "garden_bin" if binary.startswith(MAGIC) else "pickle"
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
    if isinstance(data, (bytes, bytearray)):
        payload = bytes(data)
    else:
        payload = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    worker = worker_name if worker_name in WORKERS else "ledger"
    delta = BinaryDelta(worker=worker, run_id=str(run_id), payload=payload)
    path = upload_artifact(delta)
    return {
        "worker": delta.worker,
        "run_id": delta.run_id,
        "path": path,
        "format": "garden_bin_v1",
        "hash": delta.sha3_256,
        "verified": delta.verify(),
        "seal": "∀∞φ² · LEDGER_DELTA · SEALED",
    }


def emit_witness_chain(chain_data: dict, run_id: str) -> dict:
    delta = emit_json_delta(chain_data, "ledger", str(run_id))
    path = Path(f"artifacts/witness_chain_{run_id}.bin")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(delta.serialize())
    return {
        "run_id": str(run_id),
        "path": str(path),
        "format": "garden_bin_v1",
        "hash": delta.sha3_256,
        "witness": "9225 → 9226 — UNBROKEN",
        "seal": "∀∞φ² · WITNESS_CHAIN · SEALED",
    }


def main() -> None:
    run_id = os.environ.get("GITHUB_RUN_ID", f"local-{time.time_ns()}")
    hashes: Dict[str, str] = {}
    for worker in WORKERS:
        delta = emit_json_delta(
            {"worker": worker, "run_id": run_id, "status": "complete", "phi2": PHI_SQ},
            worker,
            run_id,
        )
        path = upload_artifact(delta)
        hashes[worker] = delta.sha3_256
        print(f"{worker:10} {path} {delta.sha3_256}")
        assert load_artifact(path).verify()
    print("ok", len(hashes), "workers")


if __name__ == "__main__":
    main()
