# Live checks for the demo Java endpoint (kernel_scripts/run_endpoint.sh). Skipped when
# nothing is listening on 127.0.0.1:8025.
import json
import struct
import urllib.request
import urllib.error
from pathlib import Path

import pytest

BASE = "http://127.0.0.1:8025"
SCHEMA_FILE = Path(__file__).resolve().parents[1] / "assets" / "render_schema.json"


def _get(path):
    with urllib.request.urlopen(BASE + path, timeout=5) as r:
        return r.status, r.headers, r.read()


def _reachable():
    try:
        return _get("/healthz")[0] == 200
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _reachable(), reason="endpoint not running on 127.0.0.1:8025")


def _chunks(png):
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    i, out = 8, {}
    while i < len(png):
        n, t = struct.unpack(">I4s", png[i:i + 8])
        out.setdefault(t, png[i + 8:i + 8 + n])
        i += 12 + n
    return out


def test_healthz():
    status, _, body = _get("/healthz")
    assert status == 200 and json.loads(body) == {"status": "ok"}


def test_schema_parses_and_matches_asset():
    _, _, body = _get("/schema")
    served = json.loads(body)
    assert served["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert served == json.loads(SCHEMA_FILE.read_text(encoding="utf-8"))
    req = served["$defs"]["RenderRequest"]["properties"]
    assert req["device"]["default"] == "iPhone12,A14 Bionic"
    assert req["dpi"]["default"] == 300 and req["scale"]["default"] == 3


def test_render_png_600x900_at_300dpi():
    status, headers, png = _get("/render?widthIn=2&heightIn=3&dpi=300")
    assert status == 200 and headers["Content-Type"] == "image/png"
    c = _chunks(png)
    assert struct.unpack(">II", c[b"IHDR"][:8]) == (600, 900)
    x, y, unit = struct.unpack(">IIB", c[b"pHYs"])
    assert (x, y, unit) == (11811, 11811, 1) == (round(300 / 0.0254), round(300 / 0.0254), 1)


@pytest.mark.parametrize("q", ["dpi=5000", "widthIn=abc", "widthIn=0"])
def test_render_rejects_bad_input(q):
    with pytest.raises(urllib.error.HTTPError) as e:
        _get("/render?" + q)
    assert e.value.code == 400
