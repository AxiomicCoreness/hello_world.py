from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "k8s" / "dual-asyncio-cicd.yaml"


def test_spec_replicas_zero_no_0000():
    docs = list(yaml.safe_load_all(MANIFEST.read_text()))
    assert len(docs) == 1
    dep = docs[0]
    assert dep["kind"] == "Deployment"
    assert dep["spec"]["replicas"] == 0
    env = {
        e["name"]: e["value"]
        for e in dep["spec"]["template"]["spec"]["containers"][0]["env"]
    }
    assert env["BIND"] == "127.0.0.1"
    assert env["DUAL_ASGI"] == "127.0.0.1:8024"
    assert env["FILLED"] == "false"
    cmd = dep["spec"]["template"]["spec"]["containers"][0]["command"]
    assert cmd == ["python", "scripts/dual_asyncio_cicd.py"]
    raw = MANIFEST.read_text()
    assert "0.0.0.0" not in raw
    assert "bash -c" not in raw
