from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "dual_asyncio_cicd.sh"
MANIFEST = ROOT / "k8s" / "dual-asyncio-cicd.yaml"


def test_actualized_sh_is_dry_run_client():
    text = SCRIPT.read_text()
    assert "0.0.0.0" not in text
    assert "bash -c" not in text
    assert "--dry-run=client" in text
    assert "apply services" not in text
    assert MANIFEST.exists()
