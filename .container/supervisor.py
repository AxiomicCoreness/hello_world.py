#!/usr/bin/env python3
"""Stdlib process supervisor. No external deps.

Runs the child command. Respawns on exit code 75 (restart requested).
Propagates any other exit code. Forwards SIGTERM/SIGINT to the child.

Backoff: 0.5s doubling to 10s, reset after a run >= 30s.
"""
from __future__ import annotations

import signal
import subprocess
import sys
import time
from typing import List, Optional

RESTART_EXIT_CODE = 75
BACKOFF_MIN_S = 0.5
BACKOFF_MAX_S = 10.0
BACKOFF_RESET_AFTER_S = 30.0

_stopping = False
_proc: Optional[subprocess.Popen] = None


def _on_signal(signum: int, frame: object) -> None:
    global _stopping
    _stopping = True
    if _proc is not None and _proc.poll() is None:
        _proc.send_signal(signum)


def main(argv: List[str]) -> int:
    if not argv:
        sys.stderr.write("usage: supervisor.py <cmd> [args...]\n")
        return 2

    signal.signal(signal.SIGTERM, _on_signal)
    signal.signal(signal.SIGINT, _on_signal)

    global _proc
    backoff = BACKOFF_MIN_S

    while not _stopping:
        started = time.monotonic()
        _proc = subprocess.Popen(argv)
        rc = _proc.wait()
        elapsed = time.monotonic() - started

        if _stopping:
            return 0

        if rc == RESTART_EXIT_CODE:
            sys.stderr.write("supervisor: restart requested; respawn in %.1fs\n" % backoff)
            time.sleep(backoff)
            backoff = BACKOFF_MIN_S if elapsed >= BACKOFF_RESET_AFTER_S else min(backoff * 2.0, BACKOFF_MAX_S)
            continue

        sys.stderr.write("supervisor: child exited %d; propagating\n" % rc)
        return rc

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
