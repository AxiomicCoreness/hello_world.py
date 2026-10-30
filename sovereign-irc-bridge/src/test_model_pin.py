"""Offline: MODEL_PIN.json agrees with constants used in deepinfer_status.py and fetch-deepseek-r2.sh."""
import json
import re
from datetime import datetime
from pathlib import Path

from src import deepinfer_status as ds

MODELS = Path(__file__).resolve().parents[1] / "serving" / "models"
PIN = json.loads((MODELS / "MODEL_PIN.json").read_text(encoding="utf-8"))
SCRIPT = (MODELS / "fetch-deepseek-r2.sh").read_text()


def test_pin_fields() -> None:
    assert PIN["model"] == "deepseek-r2-1.5b" and PIN["quant"] == "Q4_K_M"
    assert PIN["release_tag"] == "model-deepseek-r2-1.5b-q4km-v1" and PIN["parts"] == 42
    assert re.fullmatch(r"[0-9a-f]{64}", PIN["gguf_sha256"])
    assert re.fullmatch(r"[0-9a-f]{64}", PIN["archive_sha256"])
    assert PIN["url"].endswith(f"/releases/download/{PIN['release_tag']}/{PIN['file']}")
    assert datetime.fromisoformat(PIN["pinned_at"]).utcoffset() is not None


def test_pin_matches_deepinfer_status() -> None:
    assert ds.load_model_pin() == PIN
    assert ds.GGUF_NAME == PIN["file"]
    assert ds.GGUF_SHA256 == PIN["gguf_sha256"]
    assert ds.GGUF_SIZE == PIN["size"]
    assert ds.GGUF_URL == PIN["url"]


def test_pin_matches_fetch_script_fallbacks() -> None:
    assert f'GGUF_SHA256="{PIN["gguf_sha256"]}"' in SCRIPT
    assert f'GGUF_SIZE="{PIN["size"]}"' in SCRIPT
    assert f'TAG="${{TAG:-{PIN["release_tag"]}}}"' in SCRIPT
    assert "MODEL_PIN.json" in SCRIPT
