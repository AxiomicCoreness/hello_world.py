#!/usr/bin/env python3
"""Stage manager stub — does not contact USPTO/EPO."""
from __future__ import annotations

import json
import os
import time
import sys


def main() -> int:
    live = os.environ.get("AUTO_FILE", "0") == "1"
    
    # Emit the status JSON
    print(
        json.dumps(
            {
                "module": "automation.stage_manager",
                "mode": "live_requested" if live else "stub",
                "auto_file": live,
                "message": "Patent office filing is not implemented",
                "config": "config/automation-config.yaml",
            },
            indent=2,
        ),
        flush=True,
    )

    # Refuse live mode immediately, with exit code 1
    if live:
        print(
            json.dumps(
                {
                    "module": "automation.stage_manager",
                    "status": "REFUSED",
                    "error": "AUTO_FILE=1 set but live USPTO path is not implemented",
                },
                indent=2,
            ),
            flush=True,
        )
        return 1

    # Daemon mode: idle heartbeat with graceful shutdown
    if os.environ.get("AUTOMATION_DAEMON", "0") == "1":
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            print(
                json.dumps(
                    {
                        "module": "automation.stage_manager",
                        "status": "shutdown",
                        "message": "Daemon terminated gracefully",
                    },
                    indent=2,
                ),
                flush=True,
            )
            return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
