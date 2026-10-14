"""Base types for structure invariants."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

@dataclass(frozen=True)
class Result:
    passed: bool
    name: str
    detail: str = ""
    remediation: str = ""

@dataclass(frozen=True)
class Invariant:
    name: str
    description: str
    check: Callable[[], Result]
