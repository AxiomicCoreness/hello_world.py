"""Path resolution for invariants."""
from __future__ import annotations

from pathlib import Path

def repo_root() -> Path:
    """Walk up from this file until we find .git."""
    here = Path(__file__).resolve()
    for parent in [here] + list(here.parents):
        if (parent / ".git").exists():
            return parent
    return Path.cwd()
