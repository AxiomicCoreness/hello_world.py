#!/usr/bin/env python3
"""Sample Prometheus metrics from the Sovereign Tag Service."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

_NUMBER = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
_SAMPLE = re.compile(rf"^(?P<name>[a-zA-Z_:][a-zA-Z0-9_:]*)(?:\{{(?P<labels>[^}}]*)\}})?\s+(?P<value>{_NUMBER})")


def sample_metrics(url: str, timeout: float) -> dict[str, Any]:
    request = Request(url, headers={"Accept": "text/plain; version=0.0.4"})
    with urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8")

    metrics: dict[str, list[dict[str, Any]]] = {}
    for line in body.splitlines():
        match = _SAMPLE.match(line)
        if not match:
            continue
        metrics.setdefault(match.group("name"), []).append(
            {"labels": match.group("labels") or "", "value": float(match.group("value"))}
        )

    return {"url": url, "metric_families": len(metrics), "metrics": metrics}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=os.getenv("SOVEREIGN_TAGS_METRICS_URL", "http://127.0.0.1:8090/metrics"))
    parser.add_argument("--timeout", type=float, default=5.0)
    args = parser.parse_args()
    try:
        print(json.dumps(sample_metrics(args.url, args.timeout), sort_keys=True))
    except (HTTPError, URLError, TimeoutError, OSError) as error:
        print(json.dumps({"url": args.url, "error": str(error)}), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
