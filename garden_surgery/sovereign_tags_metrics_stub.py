"""Read-only integration point for Sovereign Tag Service metric sampling."""

from __future__ import annotations

import argparse
import json
import os
from typing import Any


METRICS_URL = "http://127.0.0.1:8090/metrics"
REQUIRED_METRICS = {
    "sovereign_tags_active",
    "sovereign_ledger_entries",
    "sovereign_http_requests_total",
    "sovereign_http_request_duration_seconds_count",
}


def sample_sovereign_tags_metrics(
    url: str | None = None, timeout: float = 5.0
) -> dict[str, Any]:
    """Return a sampled metrics payload without mutating Garden state."""
    from scripts.sovereign_tags_metrics_sampler import sample_metrics

    return sample_metrics(url or os.getenv("SOVEREIGN_TAGS_METRICS_URL", METRICS_URL), timeout)


def validate_sample(payload: dict[str, Any]) -> dict[str, Any]:
    """Report whether the service exposed every metric needed by panel 113."""
    available = set(payload.get("metrics", {}))
    missing = sorted(REQUIRED_METRICS - available)
    return {"ok": not missing, "missing": missing, "metric_families": len(available)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=None)
    parser.add_argument("--timeout", type=float, default=5.0)
    args = parser.parse_args()
    try:
        payload = sample_sovereign_tags_metrics(args.url, args.timeout)
    except OSError as error:
        print(json.dumps({"ok": False, "error": str(error)}))
        return 1
    result = {**payload, "validation": validate_sample(payload)}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["validation"]["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
