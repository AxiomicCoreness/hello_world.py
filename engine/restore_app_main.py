#!/usr/bin/env python3
import base64, gzip
from pathlib import Path
here = Path(__file__).resolve().parent
b64 = (here / "app_main.py.gz.b64").read_text().strip()
out = here / "app_main.py"
out.write_bytes(gzip.decompress(base64.b64decode(b64)))
print("restored", out, out.stat().st_size, "bytes")
