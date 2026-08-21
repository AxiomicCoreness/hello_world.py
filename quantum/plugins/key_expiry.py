#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Key expiry monitor plugin — soft by default."""

from .base import Plugin


class KeyExpiryPlugin(Plugin):
    name = "key_expiry"
    description = "Automated key expiry monitor status"
    soft = True

    def check(self, strict: bool = False):
        result = {"name": self.name, "passed": True, "message": ""}
        try:
            from quantum.security.key_expiry_monitor import KeyExpiryMonitor

            report = KeyExpiryMonitor(auto_rotate=False).evaluate()
            expired = [s.name for s in report.statuses if s.expired]
            due = [s.name for s in report.statuses if s.due_soon]
            result["message"] = (
                f"expired={expired or 'none'} due={due or 'none'} "
                f"checked={len(report.statuses)}"
            )
            if report.any_expired and strict:
                result["passed"] = False
            elif report.any_expired:
                result["message"] += " (soft: expired present)"
        except Exception as e:
            result["passed"] = False
            result["message"] = f"key expiry check failed: {e}"
        return result
