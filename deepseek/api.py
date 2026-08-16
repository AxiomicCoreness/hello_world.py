"""
deepseek.api stub — satisfies CI import:
  from deepseek.api import warning, ignore

Replace or extend when a real DeepSeek client is wired.
"""
from __future__ import annotations

from typing import Any


def warning(msg: str) -> None:
    """No-op warning sink for CI."""
    return None


def ignore(msg: str, *args: Any) -> None:
    """No-op ignore sink; accepts optional route-count args."""
    return None
