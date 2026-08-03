#!/usr/bin/env python3
"""uprho_global_batch — merged instrumented concurrent token client."""
from __future__ import annotations
import argparse, asyncio, json, sys
from instrumented_batch import run_batch, seal_ledger
DEFAULT_URL = "http://127.0.0.1:8089/oauth/token"
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--count", type=int, default=500)
    ap.add_argument("--retries", type=int, default=2)
    ap.add_argument("--backoff-ms", type=float, default=25.0)
    ap.add_argument("--concurrency", type=int, default=100)
    ap.add_argument("--seal", action="store_true")
    args = ap.parse_args()
    summary = asyncio.run(run_batch(args.url, args.count, args.retries, args.backoff_ms, args.concurrency))
    summary["event"] = "/uprho_global_batch"
    summary["concurrency"] = args.concurrency
    print(json.dumps(summary, indent=2))
    if args.seal:
        print(json.dumps({"ledger": seal_ledger(summary)}, indent=2))
    if summary.get("errors", 0) > 0:
        sys.exit(1)
if __name__ == "__main__":
    main()
