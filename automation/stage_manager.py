#!/usr/bin/env python3
"""Stage manager stub — does not contact USPTO/EPO."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path


def main() -> int:
    live = os.environ.get("AUTO_FILE", "0") == "1"
    print(
        json.dumps(
            {
                "module": "automation.stage_manager",
                "mode": "live" if live else "stub",
                "auto_file": live,
                "message": "No patent office calls in stub mode",
                "config": "config/automation-config.yaml",
            },
            indent=2,
        ),
        flush=True,
    )
    if not live:
        # Idle heartbeat for process managers; no network
        while os.environ.get("AUTOMATION_DAEMON", "0") == "1":
            time.sleep(3600)
        return 0
    print("AUTO_FILE=1 set but live USPTO path not implemented — refusing", flush=True)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
