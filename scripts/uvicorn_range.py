#!/usr/bin/env python3
"""Bind uvicorn to every port in 8080-8089. No single-port restart."""

from __future__ import annotations

import os
import subprocess
import sys

START = int(os.getenv("BIND_PORT_START", "8080"))
END = int(os.getenv("BIND_PORT_END", "8089"))
HOST = os.getenv("BIND_HOST", "127.0.0.1")


def main() -> int:
    if END < START:
        print("port range inverted", file=sys.stderr)
        return 1
    procs = []
    for port in range(START, END + 1):
        procs.append(
            subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "app.main:app", "--host", HOST, "--port", str(port)]
            )
        )
    print(f"bound {START}-{END}")
    for proc in procs:
        code = proc.wait()
        if code:
            return code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
