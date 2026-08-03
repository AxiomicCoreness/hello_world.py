#!/usr/bin/env python3
"""Autonomous instrumented concurrent client with latency histogram and retries."""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sqlite3
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

import httpx

TRANSIENT = (
    httpx.ConnectError,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
    httpx.RemoteProtocolError,
    httpx.NetworkError,
)


def percentile(sorted_vals: List[float], p: float) -> float:
    if not sorted_vals:
        return 0.0
    k = (len(sorted_vals) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    if f == c:
        return sorted_vals[f]
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


async def one_request(client, url, i, max_retries, backoff_ms):
    attempts = 0
    last_err = None
    t0 = time.perf_counter()
    while attempts <= max_retries:
        attempts += 1
        try:
            resp = await client.post(
                url,
                json={
                    "grant_type": "client_credentials",
                    "client_id": f"uprho_{i}",
                    "client_secret": "instrumented",
                },
                timeout=5.0,
            )
            dt_ms = (time.perf_counter() - t0) * 1000.0
            return {
                "index": i,
                "status": resp.status_code,
                "latency_ms": round(dt_ms, 4),
                "attempts": attempts,
                "ok": 200 <= resp.status_code < 300,
            }
        except TRANSIENT as e:
            last_err = type(e).__name__
            if attempts <= max_retries:
                await asyncio.sleep((backoff_ms / 1000.0) * attempts)
            continue
        except Exception as e:
            dt_ms = (time.perf_counter() - t0) * 1000.0
            return {
                "index": i,
                "status": 0,
                "latency_ms": round(dt_ms, 4),
                "attempts": attempts,
                "ok": False,
                "error": f"{type(e).__name__}:{e}"[:120],
            }
    dt_ms = (time.perf_counter() - t0) * 1000.0
    return {
        "index": i,
        "status": 0,
        "latency_ms": round(dt_ms, 4),
        "attempts": attempts,
        "ok": False,
        "error": last_err or "unknown",
    }


async def run_batch(url, count, max_retries=2, backoff_ms=25.0, concurrency=100):
    limits = httpx.Limits(
        max_connections=min(count, max(10, concurrency)),
        max_keepalive_connections=min(50, concurrency),
    )
    sem = asyncio.Semaphore(concurrency)

    async def bounded(client, i):
        async with sem:
            return await one_request(client, url, i, max_retries, backoff_ms)

    t0 = time.perf_counter()
    async with httpx.AsyncClient(limits=limits) as client:
        results = await asyncio.gather(*[bounded(client, i) for i in range(count)])
    elapsed = time.perf_counter() - t0
    lats = sorted(r["latency_ms"] for r in results)
    ok = sum(1 for r in results if r.get("ok"))
    retries = sum(max(0, r.get("attempts", 1) - 1) for r in results)
    return {
        "target": url,
        "requests": count,
        "success": ok,
        "errors": count - ok,
        "elapsed_seconds": round(elapsed, 4),
        "retries_total": retries,
        "latency_ms": {
            "min": round(lats[0], 4) if lats else None,
            "p50": round(percentile(lats, 50), 4) if lats else None,
            "p95": round(percentile(lats, 95), 4) if lats else None,
            "p99": round(percentile(lats, 99), 4) if lats else None,
            "max": round(lats[-1], 4) if lats else None,
            "count_under_1ms": sum(1 for x in lats if x < 1.0),
            "count_under_0_2ms": sum(1 for x in lats if x < 0.2),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "instrumentation": "autonomous_retry+latency_histogram",
    }


def seal_ledger(summary, db="sovereign_ledger.db"):
    ts = datetime.now(timezone.utc).isoformat()
    event = "/instrumented_batch"
    data_json = json.dumps(summary, sort_keys=True)
    witness = hashlib.sha3_256(data_json.encode()).hexdigest()
    seal_body = hashlib.sha3_256(f"{event}|{ts}|{data_json}".encode()).hexdigest()
    seal = f"INSTR::{seal_body}"
    conn = sqlite3.connect(db)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS ledger (
            entry_index INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT, event TEXT, status TEXT, phase REAL,
            fiber_layer INTEGER, witness TEXT, seal TEXT, data TEXT)"""
    )
    status = "OK" if summary.get("errors", 1) == 0 else "PARTIAL"
    cur = conn.execute(
        """INSERT INTO ledger (timestamp, event, status, phase, fiber_layer, witness, seal, data)
           VALUES (?,?,?,?,?,?,?,?)""",
        (ts, event, status, 202.6, 0, witness, seal, data_json),
    )
    idx = cur.lastrowid
    conn.commit()
    conn.close()
    return {"db_entry_index": str(idx), "seal": seal, "witness": witness}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url", nargs="?", default="http://127.0.0.1:8089/oauth/token")
    ap.add_argument("count", nargs="?", type=int, default=500)
    ap.add_argument("--retries", type=int, default=2)
    ap.add_argument("--backoff-ms", type=float, default=25.0)
    ap.add_argument("--concurrency", type=int, default=100)
    ap.add_argument("--seal", action="store_true")
    args = ap.parse_args()
    summary = asyncio.run(
        run_batch(args.url, args.count, args.retries, args.backoff_ms, args.concurrency)
    )
    print(json.dumps(summary, indent=2))
    if args.seal:
        print(json.dumps({"ledger": seal_ledger(summary)}, indent=2))


if __name__ == "__main__":
    main()
