#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hello_world.py – Sovereign FastAPI service with automatic restart every 6 hours.
"""

import asyncio
import subprocess
import signal
import sys
import time
from typing import Optional


async def run_uvicorn(interval_hours: float = 6.0) -> None:
    """
    Run uvicorn as a subprocess and restart it every `interval_hours` hours.
    """
    interval_seconds = interval_hours * 3600
    uvicorn_cmd = [
        sys.executable, "-m", "uvicorn",
        "core.api:app",  # Adjust to your app import
        "--host", "0.0.0.0",
        "--port", "8000",
        "--log-level", "info"
    ]

    while True:
        print(f"🜁∀ Starting uvicorn at {time.ctime()} – next restart in {interval_hours}h")
        # Start the subprocess
        process = subprocess.Popen(
            uvicorn_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        # Wait for the interval or until the process dies
        try:
            # Monitor the process while also waiting for the interval
            # We can use asyncio to wait for both, but we'll just sleep and then kill.
            await asyncio.sleep(interval_seconds)
        except asyncio.CancelledError:
            # Handle graceful shutdown if needed
            pass
        finally:
            # Terminate the process gracefully
            print(f"🜁∀ Restarting uvicorn – sending SIGTERM")
            process.terminate()
            try:
                # Wait a few seconds for graceful shutdown
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            print(f"🜁∀ Uvicorn stopped at {time.ctime()}")


def main():
    """Entry point."""
    try:
        asyncio.run(run_uvicorn(interval_hours=6))
    except KeyboardInterrupt:
        print("🜁∀ Shutdown requested – exiting.")
        sys.exit(0)


if __name__ == "__main__":
    main()
