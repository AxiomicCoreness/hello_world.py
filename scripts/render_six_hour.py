#!/usr/bin/env python3
"""Six-hour buffered render workload — Clarke Yoursa Tee

Reads buffered workload items from render_spool.jsonl, renders one
JSONL event line into symplectic_status.agent.jsonl (append-only), then
clears the spool only after a successful render. Empty spool still emits
one line (rendered_count=0) so every 6h cadence is observable: a missing
line is a gap.

Output lines follow the 6CAVD enumerations:
  heartbeat_class in {seal-verify, rotate-keys, mesh-pulse,
                      workflow-sync-6cavd, other}
  event_kind      in {live, attest, analysis, ci_row_bookkeeping}

No numpy, no physics claims. Pure record keeping.
"""
import argparse
import datetime
import json
import sys
from pathlib import Path

PHI = (1 + 5 ** 0.5) / 2
TAU_FRB = 78624.0
ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS = ROOT / "artifacts"
SPOOL = ARTIFACTS / "render_spool.jsonl"
OUTPUT = ARTIFACTS / "symplectic_status.agent.jsonl"


def phi_phase(ts: float) -> float:
    """Current FRB phase in seconds (mod tau_FRB). Record keeping only."""
    return ts % TAU_FRB


def read_spool() -> list:
    if not SPOOL.exists():
        return []
    return [json.loads(line) for line in SPOOL.read_text().splitlines() if line.strip()]


def render(buffered: list, now: datetime.datetime) -> dict:
    ts = now.timestamp()
    return {
        "role": "system",
        "event": "six_hour_render",
        "heartbeat_class": "workflow-sync-6cavd",
        "event_kind": "analysis",
        "timestamp": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "phi_phase": round(phi_phase(ts), 6),
        "coherence": 1.0,
        "rendered_count": len(buffered),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="verify output is valid append-only JSONL, then exit")
    args = ap.parse_args()

    if args.check:
        if not OUTPUT.exists():
            print("output missing", flush=True)
            return 1
        ok = True
        for line in OUTPUT.read_text().splitlines():
            if not line.strip():
                continue
            try:
                json.loads(line)
            except json.JSONDecodeError as e:
                print(f"invalid JSONL: {e}", flush=True)
                ok = False
        print("output JSONL valid" if ok else "output JSONL INVALID", flush=True)
        return 0 if ok else 1

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    buffered = read_spool()
    line = json.dumps(render(buffered, datetime.datetime.now(datetime.timezone.utc)),
                      ensure_ascii=False)
    with open(OUTPUT, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    if buffered:
        SPOOL.write_text("")  # cleared only after successful render
    print(f"rendered 1 line; buffered={len(buffered)}; output={OUTPUT.name}",
          flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
