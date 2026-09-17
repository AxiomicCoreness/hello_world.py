"""
app/models/__init__.py

Model package for the hello_world.py application.

This file is intentionally minimal. Model classes should be imported
from the modules that define them, e.g.:

    from app.models.user import User
    from app.models.entry import LedgerEntry

Re-exports can be added below once the module layout is finalized.
Keep this file free of side effects: no network calls, no file
writes, no ledger access, no environment reads.
"""

from __future__ import annotations

__all__: list[str] = []
