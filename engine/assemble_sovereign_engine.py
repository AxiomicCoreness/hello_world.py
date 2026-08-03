#!/usr/bin/env python3
"""Assemble engine/sovereign_engine.py from base64 parts."""
import base64
from pathlib import Path
here = Path(__file__).resolve().parent
parts = sorted(here.glob("sovereign_engine.b64.*"))
data = "".join(p.read_text().strip() for p in parts)
out = here / "sovereign_engine.py"
out.write_bytes(base64.b64decode(data))
print("wrote", out, "from", len(parts), "parts", "bytes", out.stat().st_size)
