#!/usr/bin/env python3
"""Restart sequence for app:app_main. Loopback only. No secret echo."""

from __future__ import annotations

import os
import signal
import subprocess
import time
from pathlib import Path

BIND_HOST = "127.0.0.1"
BIND_PORT = 8024


def restart_sequence() -> dict:
    from garden_surgery.learner_hash import restart_fingerprint

    killed = []
    try:
        out = subprocess.check_output(["lsof", "-t", f"-iTCP:{BIND_PORT}", "-sTCP:LISTEN"], text=True)
        for pid in out.split():
            os.kill(int(pid), signal.SIGTERM)
            killed.append(int(pid))
    except (subprocess.CalledProcessError, FileNotFoundError, ProcessLookupError, PermissionError):
        pass
    time.sleep(0.4)
    return restart_fingerprint(f"{BIND_HOST}:{BIND_PORT}") | {"killed": killed}


def main() -> int:
    report = restart_sequence()
    print(report)
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root) + os.pathsep + env.get("PYTHONPATH", "")
    subprocess.Popen(
        [
            "python3",
            "-m",
            "uvicorn",
            "app:app_main",
            "--host",
            BIND_HOST,
            "--port",
            str(BIND_PORT),
        ],
        cwd=str(root),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
