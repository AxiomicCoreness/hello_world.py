#!/usr/bin/env python3
"""GitHub automation stub — no auto_release by default."""
from __future__ import annotations

import json
import os
import sys


def main() -> int:
    auto = os.environ.get("GITHUB_AUTO_RELEASE", "0") == "1"
    
    # If live mode is triggered but not implemented, emit a clear error
    if auto:
        print(
            json.dumps(
                {
                    "module": "automation.github_automation",
                    "mode": "live_requested",
                    "auto_release": True,
                    "status": "NOT_IMPLEMENTED",
                    "error": "GitHub auto_release is not implemented in this stub",
                },
                indent=2,
            ),
            flush=True,
        )
        # Return a standard error code (1), not a fatal config code (2)
        return 1
        
    print(
        json.dumps(
            {
                "module": "automation.github_automation",
                "mode": "stub",
                "auto_release": False,
                "message": "No GitHub release created in stub mode",
            },
            indent=2,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
