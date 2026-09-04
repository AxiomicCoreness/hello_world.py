#!/usr/bin/env python3
"""Dual asyncio loops for CI/CD (ledger 9174).

One loop per lane: control and deepseek/offline.
Does not bind sockets. Does not fill MCP. Does not call 0.0.0.0.
Does not occupy Dual ASGI 127.0.0.1:8024.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Tuple

FILLED = False
BIND = "127.0.0.1"
DUAL_ASGI = "127.0.0.1:8024"
MAGIC = b"GARDEN.BIN.v1\n"
LAYER_ORDER = [
    "sovereign_core.bin",
    "ledger_tip.bin",
    "octonian_relay.bin",
    "adai_annihilator.bin",
]
EXPECTED_MERKLE = "3a00d16045470561e2d9f15f707a05c57dfc859948d559b898c00ffdefd8dc2a"
EXPECTED = {
    "sovereign_core.bin": "5c5184f9368c9ee443d860aa419a11ca6937af9d5a5b597df703b00c3cb7c755",
    "ledger_tip.bin": "ee1bc942cb2401f443804f6b836032fd5d93d8d26475bec77327cd82950c65bb",
    "octonian_relay.bin": "f6bcb0288f4f985c8f9633cc9d53276dc27b136a996f707e21758cd9c3c117eb",
    "adai_annihilator.bin": "f83ff65ffb86f670265819271a83f4603a79ce15d0f8366f67d8803d4c8f6f8a",
}


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _verify_layers(root: Path) -> Dict[str, Any]:
    layers: List[Tuple[str, str, Dict[str, Any]]] = []
    prev = None
    for name in LAYER_ORDER:
        path = root / name
        if not path.exists():
            raise FileNotFoundError(name)
        data = path.read_bytes()
        if not data.startswith(MAGIC):
            raise ValueError(f"{name}: missing magic")
        digest = hashlib.sha3_256(data).hexdigest()
        obj = json.loads(data.split(b"\n", 1)[1])
        if obj.get("executable") is not False or obj.get("mcp_filled") is not False:
            raise ValueError(f"{name}: contract")
        if prev is not None and obj.get("hash_prev") != prev:
            raise ValueError(f"{name}: hash_prev")
        if digest != EXPECTED[name]:
            raise ValueError(f"{name}: digest")
        layers.append((name, digest, obj))
        prev = digest
    mer = hashlib.sha3_256("".join(d for _, d, _ in layers).encode()).hexdigest()
    if mer != EXPECTED_MERKLE:
        raise ValueError("merkle")
    return {"ok": True, "count": len(layers), "merkle": mer}


async def lane_control(root: Path) -> Dict[str, Any]:
    await asyncio.sleep(0)
    body = _verify_layers(root)
    body.update({"lane": "control", "filled": FILLED, "dual_asgi": DUAL_ASGI})
    return body


async def lane_deepseek(root: Path) -> Dict[str, Any]:
    await asyncio.sleep(0)
    if os.environ.get("DEEPSEEK_API_KEY") and os.environ.get("DUAL_CI_REQUIRE_OFFLINE") == "1":
        raise RuntimeError("deepseek lane must stay offline")
    body = _verify_layers(root)
    body.update(
        {
            "lane": "deepseek",
            "filled": FILLED,
            "offline": not bool(os.environ.get("DEEPSEEK_API_KEY")),
            "dual_asgi": DUAL_ASGI,
            "bind_0000": False,
        }
    )
    return body


def _run_isolated(name: str, coro) -> Dict[str, Any]:
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    finally:
        loop.close()
        asyncio.set_event_loop(None)


def run_dual(root: Path | None = None) -> Dict[str, Any]:
    root = root or _root()
    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="dual-ci") as pool:
        f_ctl = pool.submit(_run_isolated, "control", lane_control(root))
        f_ds = pool.submit(_run_isolated, "deepseek", lane_deepseek(root))
        control = f_ctl.result()
        deepseek = f_ds.result()
    return {
        "ok": bool(control.get("ok") and deepseek.get("ok")),
        "filled": FILLED,
        "bind": BIND,
        "dual_asgi": DUAL_ASGI,
        "control": control,
        "deepseek": deepseek,
    }


def main() -> int:
    report = run_dual()
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
