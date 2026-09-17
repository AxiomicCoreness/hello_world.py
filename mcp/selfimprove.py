"""
MCP self-improvement loop — opt-in, offline-safe.

Never widens MCP surface. Never mutates math_origin or the 7-key contract.
Proposals land under .mcp/proposals/ for human review only.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from collections import Counter
from pathlib import Path

ENABLED = os.environ.get("MCP_SELFIMPROVE", "0") == "1"
PROPOSAL_DIR = Path(os.environ.get("MCP_PROPOSAL_DIR", ".mcp/proposals"))
MIN_SAMPLES = int(os.environ.get("MCP_SELFIMPROVE_MIN", "25"))


def _collect_recent(context_log_path: Path, k: int = 200) -> list[tuple[str, str]]:
    if not context_log_path.exists():
        return []
    out: list[tuple[str, str]] = []
    with open(context_log_path, "r", encoding="utf-8") as fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            ctx = rec.get("context", "")
            comp = rec.get("completion", "")
            if ctx and comp:
                out.append((ctx, comp))
    return out[-k:]


def propose() -> Path | None:
    if not ENABLED:
        return None

    log_path = Path(os.environ.get("LOG_DIR", "/var/log/sovereign")) / "feedback.jsonl"
    samples = _collect_recent(log_path)
    if len(samples) < MIN_SAMPLES:
        return None

    counts = Counter((ctx[-30:], comp) for ctx, comp in samples)
    novel = {k: v for k, v in counts.items() if v >= 2}

    proposal = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sample_count": len(samples),
        "candidates": [
            {"context_tail": ctx, "completion": comp, "votes": n}
            for (ctx, comp), n in sorted(novel.items(), key=lambda x: -x[1])[:50]
        ],
    }

    digest = hashlib.sha3_256(
        json.dumps(proposal, sort_keys=True).encode()
    ).hexdigest()[:16]

    PROPOSAL_DIR.mkdir(parents=True, exist_ok=True)
    out = PROPOSAL_DIR / f"proposal-{digest}.json"
    out.write_text(json.dumps(proposal, indent=2, sort_keys=True), encoding="utf-8")
    return out


def status() -> dict:
    return {
        "enabled": ENABLED,
        "min_samples": MIN_SAMPLES,
        "proposal_dir": str(PROPOSAL_DIR),
        "mutates_math_origin": False,
        "widens_mcp_surface": False,
    }
