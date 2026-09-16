#!/usr/bin/env python3
"""GitHub automation stub — no auto_release by default."""
from __future__ import annotations

import json
import os


def main() -> int:
    auto = os.environ.get("GITHUB_AUTO_RELEASE", "0") == "1"
    print(
        json.dumps(
            {
                "module": "automation.github_automation",
                "mode": "live" if auto else "stub",
                "auto_release": auto,
                "message": "No GitHub release created in stub mode",
            },
            indent=2,
        ),
        flush=True,
    )
    return 0 if not auto else 2  # refuse live until implemented


if __name__ == "__main__":
    raise SystemExit(main())
