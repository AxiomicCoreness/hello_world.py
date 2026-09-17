#!/usr/bin/env python3
"""Deadline manager stub — logs only."""
from __future__ import annotations

import json
import os
import time


def main() -> int:
    print(
        json.dumps(
            {
                "module": "automation.deadline_manager",
                "mode": "stub",
                "message": "Deadline tracking offline; no renewals filed",
            },
            indent=2,
        ),
        flush=True,
    )
    while os.environ.get("AUTOMATION_DAEMON", "0") == "1":
        time.sleep(3600)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
