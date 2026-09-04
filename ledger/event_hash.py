#!/usr/bin/env python3
"""Mathematical event hash for ledger entries.

Form:
  H = SHA3-256(  "GARDEN.EVENT.v1"  ||  0x00  ||  payload )
  payload = index|event|phi2|delta=b^2-4ac|theta

Does not replace genesis_hash on 510510.yaml.
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Dict

PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI2 = PHI * PHI
THETA = PHI * math.pi / 2.0
DOMAIN = "GARDEN.EVENT.v1"
FORMULA = "H=SHA3-256(GARDEN.EVENT.v1 || 0x00 || index|event|phi2|delta=b^2-4ac|theta)"


def payload(index: int, event: str) -> str:
    return (
        f"{int(index)}|{event}|phi2={PHI2:.15f}|delta=b^2-4ac|theta={THETA:.10f}"
    )


def event_hash(index: int, event: str) -> str:
    raw = DOMAIN.encode("utf-8") + b"\x00" + payload(index, event).encode("utf-8")
    return hashlib.sha3_256(raw).hexdigest()


def event_hash_block(index: int, event: str) -> Dict[str, Any]:
    return {
        "algo": "sha3-256",
        "domain": DOMAIN,
        "formula": FORMULA,
        "payload": payload(index, event),
        "phi": PHI,
        "phi2": PHI2,
        "theta_rad": THETA,
        "discriminant": "delta = b^2 - 4ac",
        "hex": event_hash(index, event),
    }


def compute(index: int, event: str) -> Dict[str, Any]:
    return event_hash_block(index, event)


def attach(entry: Dict[str, Any]) -> Dict[str, Any]:
    idx = int(entry.get("entry_index", 0))
    ev = str(entry.get("event", ""))
    entry["event_hash"] = event_hash_block(idx, ev)
    return entry


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("index", type=int)
    p.add_argument("event")
    args = p.parse_args()
    print(json.dumps(event_hash_block(args.index, args.event), indent=2))
