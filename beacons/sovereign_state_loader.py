"""Read-only loader for the data-only beacons/sovereign_state.py.

beacons/sovereign_state_writer.py:write_sovereign_state() writes
`STATE = {...}` (built-in literals only) next to itself, so this loader
lives in the same folder and reads the file from there. The file is
parsed with ast.literal_eval; it is never imported or exec'd.
"""
from __future__ import annotations

import ast
import os
import re
from typing import Any, Dict, Optional

STATE_FILE = "sovereign_state.py"
_STATE_RE = re.compile(r"^STATE\s*=\s*(\{.*\})\s*$", re.DOTALL | re.MULTILINE)


def load_precomputed_state(path: Optional[str] = None) -> Dict[str, Any]:
    """Return the STATE dict from sovereign_state.py, or {} if the file is
    missing, unreadable, or not a pure literal dict."""
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), STATE_FILE)
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except (OSError, UnicodeDecodeError):
        return {}
    m = _STATE_RE.search(content)
    if not m:
        return {}
    try:
        state = ast.literal_eval(m.group(1))
    except (ValueError, SyntaxError, TypeError, MemoryError, RecursionError):
        return {}
    return state if isinstance(state, dict) else {}
