#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Codespace idle-health soft plugin — Entry 8953."""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timedelta, timezone

from .base import Plugin


class CodespacePlugin(Plugin):
    name = "codespace"
    description = "Check codespace idle timeout and warn before expiry"
    soft = True

    def check(self, strict: bool = False):
        result = {"name": self.name, "passed": True, "message": ""}
        try:
            timeout = int(os.environ.get("CODESPACE_IDLE_TIMEOUT_MINUTES", "30"))
            warn_min = int(os.environ.get("CODESPACE_WARNING_MIN", "5"))
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
            warnings = []
            for cs in data if isinstance(data, list) else []:
                state = str(cs.get("state") or "").lower()
                if state not in {"available", "active", "running"}:
                    continue
                last = datetime.fromisoformat(
                    str(cs["lastActivityAt"]).replace("Z", "+00:00")
                )
                expiry = last + timedelta(minutes=timeout)
                remaining = (expiry - datetime.now(timezone.utc)).total_seconds()
                name = cs.get("name", "?")
                if remaining < 0:
                    warnings.append(f"{name} past idle timeout")
                elif remaining < warn_min * 60:
                    warnings.append(f"{name} expires in {remaining/60:.0f} min")
            if warnings:
                result["message"] = "; ".join(warnings)
                if strict:
                    result["passed"] = False
            else:
                result["message"] = "All active codespaces are safe (or none listed)"
        except FileNotFoundError:
            result["message"] = "gh CLI not available — codespace check skipped"
            if strict:
                result["passed"] = False
        except Exception as e:
            result["passed"] = False
            result["message"] = f"Codespace check failed: {e}"
        return result
