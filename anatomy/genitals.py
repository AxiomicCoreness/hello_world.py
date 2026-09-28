"""anatomy/genitals.py — allowlist, root confinement, no symlinks.

Generation organ: anything this anatomy creates is confined to the
allowlisted roots and never follows symlinks out of confinement.
"""

import os
from pathlib import Path

ALLOWED_ROOTS = (Path("ledger"), Path("anatomy"))
LEDGER_PATTERN = "####.yaml"


def _confined(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def assert_writable(path: Path) -> None:
    """Refuse: outside allowlist roots, symlink anywhere in path, escaping root."""
    p = Path(path)
    if not any(_confined(p, root) for root in ALLOWED_ROOTS):
        raise PermissionError(f"path outside allowlist roots: {p}")
    probe = p
    while probe != probe.parent:
        if probe.is_symlink():
            raise PermissionError(f"symlink refused: {probe}")
        probe = probe.parent
    if p.is_symlink():
        raise PermissionError(f"symlink refused: {p}")


def next_ledger_path(highest_index: int) -> Path:
    """Next append-only ledger tail path, confined, no symlink."""
    target = Path("ledger") / f"{highest_index + 1:04d}.yaml"
    assert_writable(target)
    return target


if __name__ == "__main__":
    print("genitals: allowlist roots:", ", ".join(str(r) for r in ALLOWED_ROOTS))
    print("genitals: symlink policy: refused everywhere in write path")
