#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
quantum/gemini_daemon.py — Integrated Garden service (not standalone).

Runs inside docker-compose as service 'gemini-daemon'.
Checks codespace idle health; optional Gemini API handoff; Prometheus metrics file.

Seal: ∀∞φ² · GEMINI_DAEMON_8953 · WOOD_DRAGON_0.91 · SEALED
Witness: 8952 → 8953 — UNBROKEN
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
)
logger = logging.getLogger("gemini-daemon")

CHECK_INTERVAL = int(os.environ.get("DAEMON_CHECK_INTERVAL", "60"))
WARNING_THRESHOLD_MIN = int(os.environ.get("CODESPACE_WARNING_MIN", "5"))
IDLE_TIMEOUT_MIN = int(os.environ.get("CODESPACE_IDLE_TIMEOUT_MINUTES", "30"))
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
HANDOFF_ENABLED = os.environ.get("GEMINI_HANDOFF", "false").lower() in {
    "1",
    "true",
    "yes",
    "on",
}
METRICS_PATH = os.environ.get("DAEMON_METRICS_PATH", "/tmp/gemini_daemon.prom")
SEAL = "∀∞φ² · GEMINI_DAEMON_8953 · WOOD_DRAGON_0.91 · SEALED"


def get_codespaces() -> List[Dict[str, Any]]:
    """List codespaces via gh CLI. Empty list if gh unavailable."""
    try:
        out = subprocess.check_output(
            [
                "gh",
                "codespace",
                "list",
                "--json",
                "name,state,lastActivityAt,repository",
            ],
            text=True,
            timeout=20,
        )
        data = json.loads(out or "[]")
        return data if isinstance(data, list) else []
    except FileNotFoundError:
        logger.warning("gh CLI not installed — codespace check skipped")
        return []
    except Exception as e:
        logger.error("gh codespace list failed: %s", e)
        return []


def check_expiry(cs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Return alert dict if codespace is near or past idle expiry."""
    if cs.get("state") != "Available" and cs.get("state") != "active":
        state = str(cs.get("state") or "").lower()
        if state not in {"available", "active", "running"}:
            return None
    try:
        raw = cs.get("lastActivityAt") or ""
        last = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        expiry = last + timedelta(minutes=IDLE_TIMEOUT_MIN)
        now = datetime.now(timezone.utc)
        remaining = (expiry - now).total_seconds()
        name = cs.get("name") or "unknown"
        repo = cs.get("repository") or "unknown"
        if remaining < 0:
            return {
                "severity": "CRITICAL",
                "codespace": name,
                "repository": repo,
                "remaining_min": remaining / 60.0,
                "message": f"Codespace {name} has exceeded idle timeout",
            }
        if remaining < WARNING_THRESHOLD_MIN * 60:
            return {
                "severity": "WARNING",
                "codespace": name,
                "repository": repo,
                "remaining_min": remaining / 60.0,
                "message": f"Codespace {name} expires in {remaining / 60.0:.0f} min",
            }
    except Exception as e:
        logger.error("Parse error for %s: %s", cs.get("name"), e)
    return None


def handoff_to_gemini(alerts: List[Dict[str, Any]]) -> bool:
    """Optional handoff to Gemini generateContent API."""
    if not HANDOFF_ENABLED:
        logger.info("Gemini handoff disabled (GEMINI_HANDOFF!=true)")
        return False
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY missing — handoff skipped")
        return False

    prompt = (
        "Analyze these GitHub Codespace idle alerts and suggest brief actions:\n"
        + json.dumps(alerts, indent=2)
    )
    try:
        import urllib.request

        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
        )
        payload = json.dumps(
            {"contents": [{"parts": [{"text": prompt}]}]}
        ).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode() or "{}")
            text = (
                result.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )
            logger.info("Gemini response: %s...", text[:200])
            return True
    except Exception as e:
        logger.error("Gemini handoff failed: %s", e)
        return False


def write_metrics(alerts: List[Dict[str, Any]]) -> None:
    """Write Prometheus textfile metrics."""
    lines = [
        "# HELP gemini_daemon_codespace_remaining_min Minutes until idle expiry (negative if past)",
        "# TYPE gemini_daemon_codespace_remaining_min gauge",
    ]
    for alert in alerts:
        labels = (
            f'codespace="{alert["codespace"]}",'
            f'severity="{alert["severity"]}"'
        )
        lines.append(
            f"gemini_daemon_codespace_remaining_min{{{labels}}} "
            f"{float(alert['remaining_min']):.4f}"
        )
    lines.append(
        f"gemini_daemon_last_check_timestamp "
        f"{datetime.now(timezone.utc).timestamp():.0f}"
    )
    lines.append(f"gemini_daemon_alert_count {len(alerts)}")
    try:
        with open(METRICS_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    except Exception as e:
        logger.error("metrics write failed: %s", e)


def run_cycle() -> int:
    """One check cycle. Returns alert count."""
    codespaces = get_codespaces()
    alerts: List[Dict[str, Any]] = []
    for cs in codespaces:
        alert = check_expiry(cs)
        if alert:
            alerts.append(alert)
            logger.warning("%s", alert["message"])
    if alerts:
        handoff_to_gemini(alerts)
    else:
        logger.info("All codespaces healthy (or none listed) — seal %s", SEAL)
    write_metrics(alerts)
    return len(alerts)


def main() -> None:
    logger.info("Gemini daemon starting — integrated Garden mode (not standalone)")
    logger.info(
        "interval=%ss warn=%smin idle=%smin handoff=%s",
        CHECK_INTERVAL,
        WARNING_THRESHOLD_MIN,
        IDLE_TIMEOUT_MIN,
        HANDOFF_ENABLED,
    )
    while True:
        try:
            run_cycle()
        except Exception as e:
            logger.error("Cycle failed: %s", e)
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
