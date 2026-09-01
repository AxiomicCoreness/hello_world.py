#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core/__init__.py – Sovereign service entry point with automatic restart.

Usage:
  python -m core
  python core/__init__.py

Environment:
  RESTART_INTERVAL_HOURS = 6 (default, float)
"""

import asyncio
import os
import signal
import subprocess
import sys
import time
from typing import Optional


def get_restart_interval() -> float:
    """Read RESTART_INTERVAL_HOURS from env, default 6.0."""
    try:
        return float(os.getenv("RESTART_INTERVAL_HOURS", "6.0"))
    except ValueError:
        return 6.0


async def run_uvicorn(interval_hours: float) -> None:
    """
    Run uvicorn as a subprocess and restart it every `interval_hours` hours.
    """
    interval_seconds = interval_hours * 3600

    uvicorn_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "hello_world:app",          # Entry point: hello_world.py
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--log-level",
        "info"
    ]

    while True:
        print(f"∀ Starting uvicorn at {time.ctime()} – next restart in {interval_hours}h")
        process = subprocess.Popen(
            uvicorn_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        try:
            await asyncio.sleep(interval_seconds)
        except asyncio.CancelledError:
            # Allow graceful cancellation
            pass
        finally:
            print(f"∀ Restarting uvicorn – sending SIGTERM")
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            print(f"∀ Uvicorn stopped at {time.ctime()}")


def main():
    """Entry point with signal handling."""
    interval = get_restart_interval()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def signal_handler():
        print("∀ Shutdown requested – exiting.")
        loop.stop()
        sys.exit(0)

    try:
        signal.signal(signal.SIGINT, lambda s, f: signal_handler())
        signal.signal(signal.SIGTERM, lambda s, f: signal_handler())
        loop.run_until_complete(run_uvicorn(interval))
    except KeyboardInterrupt:
        print("∀ Keyboard interrupt – exiting.")
        sys.exit(0)
    finally:
        loop.close()


if __name__ == "__main__":
    main()
