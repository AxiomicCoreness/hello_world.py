from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional

# ledger.v2/ sits at the repo root, one level above app/.
_REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEDGER_DIR = _REPO_ROOT / "ledger.v2"
LEDGER_HEAD_UNKNOWN = "unknown"

# Matched on raw text, not parsed YAML: a YAML 1.1 loader reads an unquoted
# leading-zero index such as 0755 as octal (493). Base-10 is forced below.
_ENTRY_INDEX_RE = re.compile(r"""^entry_index:[ \t]*["']?(\d+)["']?[ \t]*(?:#.*)?$""", re.MULTILINE)


def derive_ledger_head(ledger_dir: Optional[os.PathLike] = None) -> str:
    """Highest entry_index among ledger.v2/*.yml, as a decimal string.

    Returns "unknown" when the directory is missing or holds no readable
    entry, rather than a hardcoded number that goes stale.
    """
    d = Path(ledger_dir) if ledger_dir is not None else DEFAULT_LEDGER_DIR
    if not d.is_dir():
        return LEDGER_HEAD_UNKNOWN
    head = None
    for f in d.glob("*.yml"):
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        m = _ENTRY_INDEX_RE.search(text)
        if not m:
            continue
        idx = int(m.group(1), 10)
        if head is None or idx > head:
            head = idx
    return str(head) if head is not None else LEDGER_HEAD_UNKNOWN


def resolve_ledger_head() -> str:
    """LEDGER_HEAD env (non-blank) wins; otherwise derive from LEDGER_DIR
    (default: <repo>/ledger.v2)."""
    override = os.getenv("LEDGER_HEAD", "").strip()
    if override:
        return override
    return derive_ledger_head(os.getenv("LEDGER_DIR") or None)


class Settings:
    NAMESPACE = os.getenv("NAMESPACE", "seagate-mimic")
    LEDGER_HEAD = resolve_ledger_head()
    PHASE_LOCK = float(os.getenv("PHASE_LOCK", "202.6"))
    BIND_HOST = os.getenv("BIND_HOST", "0.0.0.0")
    BIND_PORT_START = int(os.getenv("BIND_PORT_START", "8080"))
    BIND_PORT_END = int(os.getenv("BIND_PORT_END", "8089"))
    BIND_PORT = BIND_PORT_START
    MCP_PORT = int(os.getenv("MCP_PORT", "380"))
    MCP_FILLED = os.getenv("MCP_FILLED", "false").lower() == "true"
    GARDEN_SECRET = os.getenv("GARDEN_SECRET", "")
    PHI = 1.618033988749895
    PHI_INV3 = 0.23606797749978967  # ATLAS
    SEAL = 1.509281238970


settings = Settings()
