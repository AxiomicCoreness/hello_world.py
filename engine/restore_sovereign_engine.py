#!/usr/bin/env python3
import base64, gzip
from pathlib import Path
here = Path(__file__).resolve().parent
b64 = (here / "sovereign_engine.py.gz.b64").read_text().strip()
Path(here / "sovereign_engine.py").write_bytes(gzip.decompress(base64.b64decode(b64)))
print("restored sovereign_engine.py", (here / "sovereign_engine.py").stat().st_size, "bytes")
