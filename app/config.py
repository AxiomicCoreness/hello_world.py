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
    
    # Safely strip and check if the env var was explicitly provided
    ledger_dir_env = os.getenv("LEDGER_DIR", "").strip()
    return derive_ledger_head(ledger_dir_env if ledger_dir_env else None)


def _safe_int(val: str, default: int) -> int:
    """Safely parse an environment variable to an int, falling back on error."""
    try:
        return int(val.strip())
    except (ValueError, TypeError):
        return default


def _safe_float(val: str, default: float) -> float:
    """Safely parse an environment variable to a float, falling back on error."""
    try:
        return float(val.strip())
    except (ValueError, TypeError):
        return default


class Settings:
    NAMESPACE = os.getenv("NAMESPACE", "seagate-mimic")
    LEDGER_HEAD = resolve_ledger_head()
    
    # Safe float parsing
    PHASE_LOCK = _safe_float(os.getenv("PHASE_LOCK", "202.6"), 202.6)
    
    # SECURITY FIX: Changed default from 0.0.0.0 to 127.0.0.1 to enforce loopback
    BIND_HOST = os.getenv("BIND_HOST", "127.0.0.1").strip()
    
    # Safe int parsing
    BIND_PORT_START = _safe_int(os.getenv("BIND_PORT_START", "8080"), 8080)
    BIND_PORT_END = _safe_int(os.getenv("BIND_PORT_END", "8089"), 8089)
    BIND_PORT = BIND_PORT_START
    
    MCP_PORT = _safe_int(os.getenv("MCP_PORT", "380"), 380)
    MCP_FILLED = os.getenv("MCP_FILLED", "false").strip().lower() == "true"
    
    GARDEN_SECRET = os.getenv("GARDEN_SECRET", "").strip()
    
    # Mathematical constants
    PHI = 1.618033988749895
    PHI_INV3 = 0.23606797749978967  # ATLAS
    SEAL = 1.509281238970

    def __post_init__(self):
        """Sanity checks on configuration to fail fast at boot."""
        if self.BIND_PORT_START > self.BIND_PORT_END:
            raise ValueError(
                f"BIND_PORT_START ({self.BIND_PORT_START}) cannot be greater than "
                f"BIND_PORT_END ({self.BIND_PORT_END})"
            )
        if not (0 < self.BIND_PORT_START < 65536):
            raise ValueError(f"Invalid BIND_PORT_START: {self.BIND_PORT_START}")


# Instantiate the settings singleton
settings = Settings()
