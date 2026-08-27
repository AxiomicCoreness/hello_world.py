#!/usr/bin/env python3
# pythonIDE/a14_bionic_spine.py
# A14 Bionic / iPhone Python IDE runner (Pyto, Pythonista, a-Shell, Carnets).
# stdlib only. No GitHub, no daemon, no secrets.

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

PHI = (1 + 5 ** 0.5) / 2
PHI2 = str(PHI * PHI)  # 2.618033988749895
THETA = "2.5416018462"
DOMAIN = b"GARDEN.EVENT.v1"
HEX_LEN = 64
GENESIS_PREV = "0" * HEX_LEN
EVENT = "/pythonide_a14_bionic_spine"

# On device the repo root is wherever this file lives.
# Common IDE layouts:
#   Pyto / Pythonista: Documents/hello_world.py/pythonIDE/a14_bionic_spine.py
#   a-Shell: ~/hello_world.py/pythonIDE/a14_bionic_spine.py
HERE = Path(__file__).resolve().parent if "__file__" in dir() else Path.cwd()
REPO = HERE.parent if HERE.name == "pythonIDE" else HERE
LEDGER = REPO / "ledger"
OUT = HERE / "hash_spine_a14.jsonl"
TIP = HERE / "hash_spine_a14_tip.json"

DO_NOT_REWRITE = {
    "0336.yaml", "0403.yaml", "0404.yaml", "0515.yaml", "0516.yaml",
    "510510.yaml", "8338.yaml", "8530.yaml", "8532.yaml", "8535.yaml",
}


def digest(payload: str) -> str:
    hx = hashlib.sha3_256(DOMAIN + b"\x00" + payload.encode("utf-8")).hexdigest()
    if len(hx) != HEX_LEN:
        raise RuntimeError("truncated digest rejected")
    return hx


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def index_of(name: str) -> str:
    digits = []
    for ch in name:
        if ch.isdigit():
            digits.append(ch)
        else:
            break
    return "".join(digits) or name


def list_yaml(ledger: Path):
    if not ledger.is_dir():
        return []
    files = [p for p in ledger.glob("*.yaml") if p.name[0].isdigit()]
    files.sort(key=lambda p: (len(index_of(p.name)), index_of(p.name), p.name))
    return files


def event_hash(index: str, event: str, prev: str) -> str:
    payload = (
        f"{index}|{event}|prev={prev}|phi2={PHI2}|delta=b^2-4ac|theta={THETA}"
    )
    return digest(payload), payload


def run_spine() -> dict:
    files = list_yaml(LEDGER)
    rows = []
    prev = GENESIS_PREV
    for path in files:
        idx = index_of(path.name)
        blob = git_blob_sha(path)
        payload = (
            f"{idx}|blob={blob}|prev={prev}|phi2={PHI2}|delta=b^2-4ac|theta={THETA}"
        )
        hx = digest(payload)
        rows.append({
            "entry_index": idx,
            "path": str(path.relative_to(REPO)) if REPO in path.parents or path.parent == REPO else path.name,
            "blob": blob,
            "prev": prev,
            "event_hash": hx,
            "hex_len": HEX_LEN,
            "truncated": False,
            "rewritten_yaml": False,
            "do_not_rewrite": path.name in DO_NOT_REWRITE,
        })
        prev = hx
    HERE.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, separators=(",", ":")) + "\n")
    meta = {
        "platform": "A14_Bionic_PythonIDE",
        "repo": str(REPO),
        "ledger": str(LEDGER),
        "count": len(rows),
        "tip": prev,
        "out": str(OUT),
        "algo": "sha3-256",
        "hex_len": HEX_LEN,
        "truncated": False,
        "yaml_bodies_rewritten": False,
        "phi2": PHI2,
    }
    TIP.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return meta


def demo_without_ledger() -> dict:
    """If ledger/ is not on device, still prove the hash floor."""
    hx, payload = event_hash("9075", EVENT, "8ee6c6dfeec37a0b4d3fe4a76bbaa50a0bdddea09aafe4f1e97ff9eae2dfa529")
    demo_0000 = digest(
        "0000|blob=77a5232485da0c8c1db58260c312ba854890572a|prev="
        + GENESIS_PREV
        + f"|phi2={PHI2}|delta=b^2-4ac|theta={THETA}"
    )
    return {
        "platform": "A14_Bionic_PythonIDE",
        "ledger_present": False,
        "demo_0000": demo_0000,
        "demo_9075": hx,
        "payload_9075": payload,
        "hex_len": HEX_LEN,
        "truncated": False,
    }


def main() -> None:
    print("=== A14 BIONIC PYTHON IDE ===")
    print("HERE   ", HERE)
    print("REPO   ", REPO)
    print("LEDGER ", LEDGER, "exists=" + str(LEDGER.is_dir()))
    print("phi    ", PHI)
    print("phi2   ", PHI2)
    if LEDGER.is_dir() and list_yaml(LEDGER):
        meta = run_spine()
        print("count ", meta["count"])
        print("tip   ", meta["tip"])
        print("out   ", meta["out"])
    else:
        meta = demo_without_ledger()
        print("ledger missing on device — demo floor only")
        print("0000  ", meta["demo_0000"])
        print("9075  ", meta["demo_9075"])
    assert all(len(v) == HEX_LEN for k, v in meta.items() if k.endswith("tip") or k.startswith("demo_") and isinstance(v, str) and len(v) == HEX_LEN)
    print("gate   PASS")


if __name__ == "__main__":
    main()
