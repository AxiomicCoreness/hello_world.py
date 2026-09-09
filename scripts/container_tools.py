#!/usr/bin/env python3
"""Dependency-free read-only tools for the Sovereign Tag container."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_ENDPOINTS = ("/health", "/metrics", "/tags", "/ledger/latest")


def probe(base_url: str, paths: tuple[str, ...], timeout: float) -> dict[str, object]:
    base_url = base_url.rstrip("/")
    results: dict[str, object] = {}
    for path in paths:
        url = f"{base_url}{path}"
        try:
            request = Request(url, headers={"Accept": "application/json, text/plain"})
            with urlopen(request, timeout=timeout) as response:
                body = response.read().decode("utf-8")
                content_type = response.headers.get("Content-Type", "")
                value: object = json.loads(body) if "json" in content_type else body
                results[path] = {"ok": True, "status": response.status, "value": value}
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as error:
            results[path] = {"ok": False, "error": str(error)}
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "read_only": True,
        "endpoints": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8090")
    parser.add_argument("--timeout", type=float, default=5.0)
    args = parser.parse_args()
    report = probe(args.base_url, DEFAULT_ENDPOINTS, args.timeout)
    print(json.dumps(report, sort_keys=True))
    return 0 if all(item.get("ok") for item in report["endpoints"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
