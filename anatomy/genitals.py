"""anatomy/genitals.py — allowlist, root confinement, no symlinks.

Generation organ: anything this anatomy creates is confined to the
allowlisted roots and never follows symlinks out of confinement.
"""

import os
from pathlib import Path

ALLOWED_ROOTS = (Path("ledger"), Path("anatomy"))
LEDGER_PATTERN = "####.yaml"


def _confined(path: Path, root: Path) -> bool:
    """Check if the resolved path is within the resolved root."""
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def assert_writable(path: Path) -> None:
    """
    Refuse: outside allowlist roots, symlink anywhere in path, escaping root.
    """
    p = Path(path)
    
    # 1. Resolve the root to its true absolute path
    resolved_roots = [root.resolve() for root in ALLOWED_ROOTS]
    
    # 2. Check if the path is confined to one of the allowed roots
    if not any(_confined(p, root) for root in resolved_roots):
        raise PermissionError(f"path outside allowlist roots: {p}")
        
    # 3. Walk up the path chain and check for symlinks
    # We stop when we hit the allowlist root, so we don't trigger false positives
    # on the system's /tmp or /var symlinks.
    probe = p
    while probe != probe.parent:
        if probe.is_symlink():
            raise PermissionError(f"symlink refused: {probe}")
        
        # If we reach the allowlist root, stop searching upwards
        if probe in resolved_roots:
            break
            
        probe = probe.parent


def next_ledger_path(highest_index: int) -> Path:
    """Next append-only ledger tail path, confined, no symlink."""
    target = Path("ledger") / f"{highest_index + 1:04d}.yaml"
    assert_writable(target)
    return target


if __name__ == "__main__":
    print("genitals: allowlist roots:", ", ".join(str(r) for r in ALLOWED_ROOTS))
    print("genitals: symlink policy: refused everywhere in write path")
