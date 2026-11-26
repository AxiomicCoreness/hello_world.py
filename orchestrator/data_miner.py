# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Clarke Yoursa Tee (AxiomicCoreness)
# Zenodo DOI: 10.5281/zenodo.23378305 (https://doi.org/10.5281/zenodo.23378305)
# Design by Clarke Yoursa Tee
"""
orchestrator/data_miner.py — Append-only SIMD batch aggregation ledger.

Implements L_k = L_{k-1} || R(B_k) where:
  R(B_k) = (k, |B_k|, mu(B_k), max_{x in B_k} tau(x), iota_seal)
  iota_seal = "DATA_MINING_CONVERGENCE_8837"
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

IOTA_SEAL: str = "DATA_MINING_CONVERGENCE_8837"
DEFAULT_OUT_DIR: str = "/work/out"
DEFAULT_LOG_FILENAME: str = "data_miner_ledger.jsonl"
DESIGN_CREDIT: str = "Design by Clarke Yoursa Tee"


def resolve_log_path(log_path: Optional[Union[str, Path]] = None) -> Path:
    """Resolve append-only ledger log path (env-overridable, default /work/out)."""
    if log_path is not None:
        return Path(log_path)
    explicit = os.environ.get("DATA_MINER_LOG_PATH", "").strip()
    if explicit:
        return Path(explicit)
    out_dir = os.environ.get("DATA_MINER_OUT_DIR", "").strip() or DEFAULT_OUT_DIR
    return Path(out_dir) / DEFAULT_LOG_FILENAME


def _extract_value_and_tau(item: Any) -> Tuple[float, float]:
    if isinstance(item, dict):
        val = float(item.get("value", item.get("v", 0.0)))
        tau = float(item.get("tau", item.get("tau_handover", val)))
        return val, max(0.0, tau)
    if isinstance(item, (tuple, list)) and len(item) >= 2:
        val = float(item[0])
        tau = float(item[1])
        return val, max(0.0, tau)
    val = float(item)
    return val, max(0.0, val)


def summarize_batch(k: int, batch: Sequence[Any]) -> Dict[str, Any]:
    """Compute batch summary tuple R(B_k) = (k, |B_k|, mu(B_k), max tau(x), iota_seal)."""
    batch_index = int(k)
    items = list(batch)
    size = len(items)
    if size == 0:
        mean_val = 0.0
        max_tau = 0.0
    else:
        extracted = [_extract_value_and_tau(x) for x in items]
        values = [v for v, _ in extracted]
        taus = [t for _, t in extracted]
        mean_val = float(sum(values) / size)
        max_tau = float(max(taus))
    return {
        "k": batch_index,
        "batch_size": size,
        "mean": mean_val,
        "max_tau": max_tau,
        "iota_seal": IOTA_SEAL,
        "R": [batch_index, size, mean_val, max_tau, IOTA_SEAL],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "design": DESIGN_CREDIT,
    }


def append_batch_record(
    k: int,
    batch: Sequence[Any],
    log_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Append one JSON line for R(B_k) using O_APPEND only (never truncates)."""
    target = resolve_log_path(log_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    record = summarize_batch(k, batch)
    line = (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )
    fd = os.open(str(target), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        os.write(fd, line)
    finally:
        os.close(fd)
    return record


def read_ledger(log_path: Optional[Union[str, Path]] = None) -> List[Dict[str, Any]]:
    """Read all JSONL records from the append-only ledger."""
    target = resolve_log_path(log_path)
    if not target.is_file():
        return []
    out: List[Dict[str, Any]] = []
    with target.open("r", encoding="utf-8") as fh:
        for raw in fh:
            s = raw.strip()
            if s:
                out.append(json.loads(s))
    return out


class DataMiner:
    """Stateful append-only SIMD batch aggregator."""

    def __init__(
        self,
        log_path: Optional[Union[str, Path]] = None,
        start_k: int = 0,
    ) -> None:
        self.log_path = resolve_log_path(log_path)
        self.k = int(start_k)

    def append_batch(self, batch: Sequence[Any]) -> Dict[str, Any]:
        rec = append_batch_record(self.k, batch, log_path=self.log_path)
        self.k += 1
        return rec
