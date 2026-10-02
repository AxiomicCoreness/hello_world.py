#!/usr/bin/env python3
"""
iphone12_ioc_terminal.py — MVT IOC analogue for the iPhone12-quantum-terminal
FastAPI stack.

Mirrors two shell commands:
  1. mvt-ios download-iocs | grep -o 'Downloaded indicators "[^"]*"' | head -4
  2. python3 iocs.py            # aggregate counts per malware family

Discipline:
  - Binds 127.0.0.1 only. Never 0.0.0.0.
  - --check-config emits one JSON object (7-key contract, matching
    the shape used elsewhere in this repo).
  - Does NOT fabricate IOCs. If mvt-ios is absent, that is an explicit
    error, not a stub.
  - Writes only under --iocs-dir (default: artifacts/iocs/).
"""

from __future__ import annotations
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

# ---------------------------------------------------------------------------
# Contract
# ---------------------------------------------------------------------------
BIND_HOST = "127.0.0.1"
BIND_PORT = 8025           # distinct from ASGI (8024) and MCP (380/3800)
DEFAULT_IOCS_DIR = "artifacts/iocs"
DOWNLOAD_RE = re.compile(r'Downloaded indicators "([^"]+)"')
HOST_MAX = 4               # the `head -4` in the original pipeline

# ---------------------------------------------------------------------------
# --check-config : one JSON object, stable keys
# ---------------------------------------------------------------------------
def check_config() -> dict:
    return {
        "host":             BIND_HOST,
        "bind_host":        BIND_HOST,
        "port":             BIND_PORT,
        "namespace":        os.environ.get("MCP_NAMESPACE", "sovereign-garden"),
        "surface":          ["/ioc/healthz", "/ioc/indicators", "/ioc/summary"],
        "legacy_out_of_surface": [],
        "url":              f"http://{BIND_HOST}:{BIND_PORT}/ioc/healthz",
    }

# ---------------------------------------------------------------------------
# mvt-ios availability
# ---------------------------------------------------------------------------
def mvt_available() -> bool:
    return shutil.which("mvt-ios") is not None

# ---------------------------------------------------------------------------
# Command 1 analogue: download-iocs | grep | head
# ---------------------------------------------------------------------------
def download_iocs(limit: int = HOST_MAX) -> list[str]:
    """
    Run `mvt-ios download-iocs`, parse the names it prints, return the
    first `limit`. Raises RuntimeError if mvt-ios is not installed.
    """
    if not mvt_available():
        raise RuntimeError(
            "mvt-ios not found on PATH. Install with: "
            "pip install mvt  (https://github.com/mvt-project/mvt)"
        )
    proc = subprocess.run(
        ["mvt-ios", "download-iocs"],
        capture_output=True, text=True, check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"mvt-ios download-iocs failed (rc={proc.returncode}): "
            f"{proc.stderr.strip()[:200]}"
        )
    names = DOWNLOAD_RE.findall(proc.stdout)
    return names[:limit]

# ---------------------------------------------------------------------------
# Command 2 analogue: iocs.py aggregation
# ---------------------------------------------------------------------------
def summarize(iocs_dir: Path) -> dict:
    """
    Walk `iocs_dir` for *.json, count indicators per malware family
    (file stem) and total indicators across all files.
    """
    if not iocs_dir.exists():
        return {
            "iocs_dir":     str(iocs_dir),
            "families":     {},
            "total_files":  0,
            "total_indicators": 0,
            "status":       "EMPTY",
        }
    families: Counter = Counter()
    total = 0
    files = 0
    for p in sorted(iocs_dir.rglob("*.json")):
        files += 1
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        count = 0
        if isinstance(data, dict):
            for key in ("indicators", "iocs", "domains", "urls", "hashes"):
                v = data.get(key)
                if isinstance(v, list):
                    count += len(v)
        elif isinstance(data, list):
            count = len(data)
        families[p.stem] += count
        total += count
    return {
        "iocs_dir":         str(iocs_dir),
        "families":         dict(families),
        "total_files":      files,
        "total_indicators": total,
        "status":           "OK" if files else "EMPTY",
    }

# ---------------------------------------------------------------------------
# FastAPI sub-app (optional — only imported when --serve is used)
# ---------------------------------------------------------------------------
def build_app():
    from fastapi import FastAPI, HTTPException
    app = FastAPI(title="iPhone12 IOC Terminal", version="1.0.0")
    iocs_dir = Path(os.environ.get("IOCS_DIR", DEFAULT_IOCS_DIR))

    @app.get("/ioc/healthz")
    def healthz():
        return {"ok": True, "mvt_available": mvt_available(),
                "iocs_dir": str(iocs_dir)}

    @app.get("/ioc/indicators")
    def indicators(limit: int = HOST_MAX):
        try:
            names = download_iocs(limit=limit)
        except RuntimeError as e:
            raise HTTPException(status_code=503, detail=str(e))
        return {"count": len(names), "names": names}

    @app.get("/ioc/summary")
    def summary():
        return summarize(iocs_dir)

    return app

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(prog="iphone12_ioc_terminal.py")
    ap.add_argument("--check-config", action="store_true",
                    help="print bind plan as one JSON object and exit")
    ap.add_argument("--download-iocs", action="store_true",
                    help="mirror: mvt-ios download-iocs | grep | head")
    ap.add_argument("--summarize", action="store_true",
                    help="mirror: python3 iocs.py")
    ap.add_argument("--iocs-dir", default=DEFAULT_IOCS_DIR)
    ap.add_argument("--limit", type=int, default=HOST_MAX)
    ap.add_argument("--serve", action="store_true",
                    help="run FastAPI on 127.0.0.1:8025")
    args = ap.parse_args()

    if args.check_config:
        print(json.dumps(check_config(), indent=2))
        return 0

    if args.download_iocs:
        try:
            for name in download_iocs(limit=args.limit):
                print(name)
            return 0
        except RuntimeError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 2

    if args.summarize:
        print(json.dumps(summarize(Path(args.iocs_dir)), indent=2))
        return 0

    if args.serve:
        import uvicorn
        uvicorn.run(build_app(), host=BIND_HOST, port=BIND_PORT)
        return 0

    ap.print_help()
    return 1

if __name__ == "__main__":
    sys.exit(main())
