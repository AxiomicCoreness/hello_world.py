"""Offline: MODEL_PIN.json (active, 1.8B) and MODEL_PIN.1p5b.json (fallback) agree with
deepinfer_status.py and fetch-deepseek-r2.sh."""
import json
import re
from datetime import datetime
from pathlib import Path

from src import deepinfer_status as ds

MODELS = Path(__file__).resolve().parents[1] / "serving" / "models"
PIN = json.loads((MODELS / "MODEL_PIN.json").read_text(encoding="utf-8"))
FALLBACK = json.loads((MODELS / PIN["fallback_pin"]).read_text(encoding="utf-8"))
SCRIPT = (MODELS / "fetch-deepseek-r2.sh").read_text()


def _common(pin: dict) -> None:
    assert pin["quant"] == "Q4_K_M"
    assert re.fullmatch(r"[0-9a-f]{64}", pin["gguf_sha256"])
    assert pin["url"].endswith(f"/releases/download/{pin['release_tag']}/{pin['file']}")
    assert datetime.fromisoformat(pin["pinned_at"]).utcoffset() is not None


def test_pin_fields() -> None:
    _common(PIN)
    assert PIN["model"] == "deepseek-r2-1p8b" and PIN["layers"] == 33
    assert PIN["release_tag"] == "model-deepseek-r2-1p8b-q4km-v1"
    assert PIN["file"] == "deepseek-r2-1p8b-Q4_K_M.gguf" and PIN["parts"] == 0
    assert PIN["size"] == 1259979680
    assert PIN["gguf_sha256"] == "f19e0c500c4f734c6e8860e9f6e730e36d544c5f9500f74dce5339b188253af4"
    assert re.fullmatch(r"[0-9a-f]{40}", PIN["base_revision"])
    assert PIN["evaluated"] is False  # flip only after the 1.8B vs 1.5B eval has been reviewed


def test_fallback_pin_is_the_1p5b_release() -> None:
    _common(FALLBACK)
    assert FALLBACK["model"] == "deepseek-r2-1.5b" and FALLBACK["parts"] == 42
    assert FALLBACK["release_tag"] == "model-deepseek-r2-1.5b-q4km-v1"
    assert FALLBACK["gguf_sha256"] == "80a49c2fe2410f704ceda4590212174a99899341b01e6af5433319481179e5c1"
    assert re.fullmatch(r"[0-9a-f]{64}", FALLBACK["archive_sha256"])


def test_pin_matches_deepinfer_status() -> None:
    assert ds.load_model_pin() == PIN
    assert ds.GGUF_NAME == PIN["file"]
    assert ds.GGUF_SHA256 == PIN["gguf_sha256"]
    assert ds.GGUF_SIZE == PIN["size"]
    assert ds.GGUF_URL == PIN["url"]
    assert ds.RELEASE_URL.endswith("/releases/tag/" + PIN["release_tag"])


def test_fetch_script_reads_pin_and_keeps_1p5b_fallbacks() -> None:
    assert f'GGUF_SHA256="{FALLBACK["gguf_sha256"]}"' in SCRIPT
    assert f'GGUF_SIZE="{FALLBACK["size"]}"' in SCRIPT
    assert f'TAG="${{TAG:-{FALLBACK["release_tag"]}}}"' in SCRIPT
    assert f'BASE="{FALLBACK["file"][:-len(".gguf")]}"' in SCRIPT
    assert "MODEL_PIN.json" in SCRIPT and "MODEL_PIN.1p5b.json" in SCRIPT
    assert 'pin_get file' in SCRIPT and 'pin_get parts' in SCRIPT
