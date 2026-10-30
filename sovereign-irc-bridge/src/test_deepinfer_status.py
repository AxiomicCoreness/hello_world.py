# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""`/llm status` report: vendored-tree pin check, external deps, GGUF sha256 (no network, no model)."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from src import deepinfer_status as ds
from src import llm_backend, llm_chat


def test_gpu_deps_cover_llm_backend_capability_modules() -> None:
    assert set(llm_backend.CAPABILITY_MODULES) <= set(ds.GPU_DEPS) | {ds.COMPILED_EXT}
    assert {"tile_kernels", "tilelang", "deep_cluster", "deep_select"} <= set(ds.GPU_DEPS)


def test_vendor_report_on_this_checkout_is_clean() -> None:
    rep = ds.vendor_report()
    assert rep["error"] is None
    assert rep["commit"] == ds.PIN
    assert rep["total"] >= 110
    assert rep["missing"] == [] and rep["drifted"] == []


def test_vendor_report_detects_drift_and_missing(tmp_path: Path) -> None:
    root = ds.repo_root()
    m = json.loads((root / "deepinfer" / "VENDOR_MANIFEST.json").read_text(encoding="utf-8"))
    pkg = tmp_path / "deepinfer"
    pkg.mkdir()
    (pkg / "VENDOR_MANIFEST.json").write_text(json.dumps(m), encoding="utf-8")
    first, second = [f for f in m["files"] if f["mode"] == "byte_identical"][:2]
    p = tmp_path / first["path"]
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes((root / first["path"]).read_bytes() + b"# drift\n")
    rep = ds.vendor_report(tmp_path)
    assert first["path"] in rep["drifted"]
    assert second["path"] in rep["missing"]


def test_deps_report_uses_find_spec_and_disk_probe(tmp_path: Path) -> None:
    (tmp_path / "deepinfer").mkdir()
    present = {"torch", "deep_gemm"}
    deps = ds.deps_report(find_spec=lambda n: object() if n in present else None,
                          cuda_check=lambda: True, root=tmp_path)
    assert deps["torch"] and deps["deep_gemm"] and not deps["tile_kernels"]
    assert deps["deepinfer._C"] is False and deps["cuda"] is True
    (tmp_path / "deepinfer" / "_C.cpython-312-x86_64-linux-gnu.so").write_bytes(b"")
    assert ds.deps_report(find_spec=lambda n: None, cuda_check=lambda: True, root=tmp_path)["deepinfer._C"]
    # CUDA is never claimed without torch.
    assert ds.deps_report(find_spec=lambda n: None, cuda_check=lambda: True, root=tmp_path)["cuda"] is False


def test_gguf_report_missing_verified_mismatch(tmp_path: Path) -> None:
    assert ds.gguf_report(directory=tmp_path)["state"] == "missing"
    data = b"GGUF fake bytes"
    (tmp_path / ds.GGUF_NAME).write_bytes(data)
    good = hashlib.sha256(data).hexdigest()
    rep = ds.gguf_report(directory=tmp_path, expected_sha256=good, expected_size=len(data))
    assert rep["state"] == "verified" and rep["verified"] and rep["sha256"] == good
    assert len(rep["sha256"]) == 64
    bad = ds.gguf_report(directory=tmp_path, expected_sha256="0" * 64, expected_size=len(data))
    assert bad["state"] == "sha256 mismatch" and not bad["verified"]
    assert ds.gguf_report(directory=tmp_path)["state"] == "size mismatch"  # real size is 1,117,320,640


def test_status_lines_render_blockers_and_gguf(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("MODEL_DIR", str(tmp_path))
    lines = ds.status_lines()
    assert all(ln.startswith(ds.PREFIX) for ln in lines)
    text = "\n".join(lines)
    assert "missing at" in text and "fetch-deepseek-r2.sh" in text
    assert ds.GGUF_URL in text and ds.GGUF_SHA256 in text
    assert "127.0.0.1:8085" in text and "0.0.0.0" not in text
    assert "verdict:" in lines[-1]


def test_llm_status_command_returns_report_without_model_call(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*a, **k):  # pragma: no cover - must not be reached
        raise AssertionError("/llm status must not call a model")

    monkeypatch.setattr(llm_chat, "complete_routed", boom)
    monkeypatch.setattr(ds, "status_lines", lambda verify=True, rep=None: [ds.PREFIX + "stub"])
    assert llm_chat.handle_llm_sync("/llm status") == [ds.PREFIX + "stub"]
    assert llm_chat.handle_llm_sync("/llm STATUS ") == [ds.PREFIX + "stub"]


def test_cli_runs_isolated_without_src_on_path(tmp_path: Path) -> None:
    script = Path(ds.__file__)
    env = {"MODEL_DIR": str(tmp_path), "PATH": "/usr/bin:/bin"}
    out = subprocess.run([sys.executable, "-I", str(script), "status", "--json"],
                         capture_output=True, text=True, timeout=120, env=env)
    assert out.returncode == 0, out.stderr
    rep = json.loads(out.stdout)
    assert rep["gguf"]["state"] == "missing"
    assert rep["vendor"]["missing"] == [] and rep["vendor"]["drifted"] == []


def test_single_file_gguf_url() -> None:
    assert ds.GGUF_URL == ("https://github.com/AxiomicCoreness/hello_world.py/releases/download/"
                           "model-deepseek-r2-1.5b-q4km-v1/deepseek-r2-1.5b-Q4_K_M.gguf")
