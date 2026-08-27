#!/usr/bin/env python3
"""Name-seal for DeepSeek 2.2.2(4). Not a live API daemon.

quantum/gemini_daemon.py and ledger/8953.yaml are not rewritten.
Handoff default is false. No secret is read into logs.
Infinite loop is off unless DEEPSEEK_DAEMON_LOOP=true.
"""

from __future__ import annotations

import os

NAME = "DeepSeek 2.2.2(4)"
ASGI = "deepseek_app_main:app"
HANDOFF_DEFAULT = False


def status() -> dict:
    handoff = os.environ.get("DEEPSEEK_HANDOFF", "false").lower() == "true"
    loop = os.environ.get("DEEPSEEK_DAEMON_LOOP", "false").lower() == "true"
    key_present = bool(os.environ.get("DEEPSEEK_API_KEY"))
    return {
        "name": NAME,
        "asgi": ASGI,
        "handoff_enabled": handoff,
        "handoff_policy": "default_false_no_secret_echo",
        "api_key_present": key_present,
        "api_key_value": None,
        "loop": loop,
        "gemini_daemon_rewritten": False,
        "alpha_eff": 0.0,
        "training": False,
    }


def main() -> int:
    report = status()
    print(report)
    if report["loop"]:
        print("loop requested but refused in this seal — use flywheel ASGI instead")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
