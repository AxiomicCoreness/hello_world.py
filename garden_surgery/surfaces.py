"""Interoperability surfaces — files and contracts that must exist.

Does not start servers. Does not call live APIs.
Hard-fails only on missing *local* contracts.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict, List, Optional

REQUIRED_FILES = (
    "hello_world.py",
    "run_port380.py",
    "golden_ratio.py",
    "ledger/event_hash.py",
    "ledger/0515.yaml",
    "ledger/0516.yaml",
    "ledger/9020.yaml",
    "ledger/9021.yaml",
    ".env.example",
)

# Hyperion 0516 must remain a self-writing agent, not a fusion body.
HYPERION_MARKERS = ("HYPERION-16807-001", "hyperion_agent")
FUSION_515_MARKERS = ("phi_grok_fusion.py", "witness_prefix: \"0203020302030203\"")
VOID_CLAIM_MARKERS = ("void_claim: \"516-as-fusion\"", "preserved_entry: 516")


@dataclass
class SurfaceReport:
    repo_root: str
    files: Dict[str, bool]
    hyperion_0516_preserved: bool
    fusion_canonical_515: bool
    claim_516_voided: bool
    missing: List[str] = field(default_factory=list)

    def ok(self) -> bool:
        return (
            not self.missing
            and self.hyperion_0516_preserved
            and self.fusion_canonical_515
            and self.claim_516_voided
        )

    def as_dict(self) -> Dict:
        d = asdict(self)
        d["ok"] = self.ok()
        return d


def _find_root(explicit: Optional[str] = None) -> Path:
    if explicit:
        return Path(explicit)
    here = Path(__file__).resolve()
    for p in [here.parent.parent, Path.cwd()]:
        if (p / "ledger" / "0516.yaml").exists():
            return p
    return Path.cwd()


def _contains(path: Path, markers) -> bool:
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    return all(m in text for m in markers)


def probe_surfaces(repo_root: Optional[str] = None) -> SurfaceReport:
    root = _find_root(repo_root)
    files = {rel: (root / rel).is_file() for rel in REQUIRED_FILES}
    missing = [k for k, ok in files.items() if not ok]
    return SurfaceReport(
        repo_root=str(root),
        files=files,
        hyperion_0516_preserved=_contains(root / "ledger" / "0516.yaml", HYPERION_MARKERS),
        fusion_canonical_515=_contains(root / "ledger" / "0515.yaml", FUSION_515_MARKERS),
        claim_516_voided=_contains(root / "ledger" / "9021.yaml", VOID_CLAIM_MARKERS),
        missing=missing,
    )
