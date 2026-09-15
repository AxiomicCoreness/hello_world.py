#!/usr/bin/env python3
"""Local search-engine optimizer stub for ledger 9229.

No crawl, no bind, no MCP fill. Ranks an in-memory corpus with phi weights.
"""
from __future__ import annotations

import hashlib
import math
from typing import Dict, List, Tuple

PHI = (1.0 + math.sqrt(5.0)) / 2.0
EVENT = "/search_engine_optimizer"
INDEX = 9229

CORPUS = {
    "toi": "two ball toi quadratic a2=0 R=0.2",
    "garden_bin": "garden.bin v1 magic GARDEN.B header 90",
    "ledger": "append only 9225 9226 9227 9228 9229",
    "hopper": "9220 open docker jax unfilled",
}


def event_hash() -> str:
    payload = f"{INDEX}|{EVENT}|phi2=2.618033988749895|delta=b^2-4ac|theta=2.5416018462"
    return hashlib.sha3_256(b"GARDEN.EVENT.v1\x00" + payload.encode("ascii")).hexdigest()


def score(query: str, doc: str) -> float:
    q = set(query.lower().split())
    d = doc.lower().split()
    hits = sum(1 for w in d if w in q)
    return hits * (PHI ** -1)


def rank(query: str) -> List[Tuple[str, float]]:
    scored = [(k, score(query, v)) for k, v in CORPUS.items()]
    scored.sort(key=lambda kv: (-kv[1], kv[0]))
    return scored


def optimize(query: str) -> Dict:
    ranking = rank(query)
    return {
        "event": EVENT,
        "index": INDEX,
        "hash": event_hash(),
        "query": query,
        "ranking": ranking,
        "mcp_filled": False,
        "bind": "127.0.0.1:8024",
    }


def main() -> None:
    out = optimize("toi ledger garden")
    print(out["hash"])
    for name, s in out["ranking"]:
        print(f"{s:.6f} {name}")


if __name__ == "__main__":
    main()
