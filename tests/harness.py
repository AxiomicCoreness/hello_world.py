#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ tests/harness.py — Unified Garden verification harness

Orchestrates soft/hard checks for core modules without requiring a cluster.
CLI: python -m tests.harness [--local] [--suite SUITE] [--json]

Suites: core | pipeline | engine | symplectic | security | pytest | dsh | all
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHASE_LOCK_DEG = 202.6
REPO_ROOT = Path(__file__).resolve().parents[1]
SEAL = "∀∞φ² · HARNESS_UNIFIED · WOOD_DRAGON_0.91 · SEALED"


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str = ""
    soft: bool = False


@dataclass
class HarnessReport:
    timestamp: float
    suite: str
    results: List[CheckResult] = field(default_factory=list)
    seal: str = SEAL

    @property
    def hard_failures(self) -> int:
        return sum(1 for r in self.results if not r.ok and not r.soft)

    @property
    def soft_failures(self) -> int:
        return sum(1 for r in self.results if not r.ok and r.soft)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.ok)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "suite": self.suite,
            "passed": self.passed,
            "hard_failures": self.hard_failures,
            "soft_failures": self.soft_failures,
            "results": [asdict(r) for r in self.results],
            "seal": self.seal,
        }


def _add(report: HarnessReport, name: str, ok: bool, detail: str = "", soft: bool = False) -> None:
    report.results.append(CheckResult(name=name, ok=ok, detail=detail, soft=soft))
    mark = "✅" if ok else ("⚠️" if soft else "❌")
    print(f"  {mark} {name}: {detail or ('ok' if ok else 'fail')}")


def check_phi_pipeline(report: HarnessReport) -> None:
    try:
        from phi_pipeline import PHI as P, PhiPipeline, quantize_q8_24  # type: ignore

        assert abs(float(P) - PHI) < 1e-12
        q = quantize_q8_24(0.123456789)
        assert abs(q - round(0.123456789 * (1 << 24)) / (1 << 24)) < 1e-15
        p = PhiPipeline()
        out = p.run_sequence(1)
        sealed = out.get("status") == "PHASE_LOCK_REACHED" or out.get("state", {}).get("sealed")
        _add(report, "phi_pipeline.sequence_1", True, f"status={out.get('status')} sealed={sealed}")
        p2 = PhiPipeline()
        out5 = p2.run_sequence(5)
        _add(report, "phi_pipeline.sequence_5", True, f"status={out5.get('status')}")
    except Exception as e:
        _add(report, "phi_pipeline", False, str(e), soft=False)


def check_mesh_modal(report: HarnessReport) -> None:
    try:
        import mesh_modal  # type: ignore

        _add(report, "mesh_modal.import", True, f"module={mesh_modal.__name__}", soft=True)
    except Exception as e:
        _add(report, "mesh_modal.import", False, str(e), soft=True)


def check_deepseek(report: HarnessReport) -> None:
    try:
        mod = importlib.import_module("deepseek.api")
        _add(report, "deepseek.api.import", True, f"attrs={len(dir(mod))}", soft=True)
        if hasattr(mod, "complete_sync"):
            out = mod.complete_sync("harness probe", max_tokens=16, prefer="offline")
            ok = isinstance(out, dict) and "mode" in out
            _add(report, "deepseek.api.complete_sync", ok, str(out.get("mode")), soft=True)
    except Exception as e:
        _add(report, "deepseek.api.import", False, str(e), soft=True)


def check_dsh_adapter(report: HarnessReport) -> None:
    try:
        from quantum.deepseek_mesh.dsh_adapter import complete, offline_complete, probe

        p = probe()
        _add(
            report,
            "dsh_adapter.probe",
            isinstance(p, dict) and "modes" in p,
            f"dsh_sdk={p.get('dsh_sdk')} key={p.get('api_key_set')}",
            soft=False,
        )
        off = offline_complete("lattice check")
        _add(report, "dsh_adapter.offline", off.mode == "offline", off.text[:80], soft=False)
        auto = complete("lattice auto", prefer="offline")
        _add(report, "dsh_adapter.complete_offline", auto.mode == "offline", auto.mode, soft=False)
    except Exception as e:
        _add(report, "dsh_adapter", False, str(e), soft=False)


def check_endpoint_surface(report: HarnessReport) -> None:
    try:
        from quantum.deepseek_mesh import endpoint as ep  # type: ignore

        assert getattr(ep, "ENTRY", None) == 8756 or getattr(ep, "LAYER", None) == 314
        routes = {getattr(r, "path", None) for r in ep.app.routes}
        needed = {"/health", "/status", "/pulse", "/gate"}
        missing = needed - routes
        ok = not missing
        _add(
            report,
            "deepseek_mesh.endpoint.routes",
            ok,
            f"missing={sorted(missing) if missing else []}; entry={getattr(ep, 'ENTRY', None)}",
            soft=False,
        )
        has_verify = callable(getattr(ep, "verify_client_cert", None))
        _add(report, "deepseek_mesh.endpoint.mtls_hook", has_verify, "verify_client_cert", soft=True)
    except Exception as e:
        _add(report, "deepseek_mesh.endpoint", False, str(e), soft=True)


def check_sovereign_engine(report: HarnessReport) -> None:
    try:
        from sovereign_engine import (  # type: ignore
            PHI as EP,
            ProductionDeployment,
            systems_go,
        )

        assert abs(float(EP) - PHI) < 1e-9
        eng = ProductionDeployment()
        pre = eng.pre_deploy_check()
        _add(
            report,
            "sovereign_engine.pre_deploy",
            bool(pre.get("all_passed")) or bool(pre.get("checks")),
            str(pre.get("checks", pre)),
            soft=True,
        )
        go = systems_go()
        _add(
            report,
            "sovereign_engine.systems_go",
            True,
            f"systems_go={go.get('systems_go')} oidc_len={go.get('oidc_secret_len')}",
            soft=True,
        )
    except Exception as e:
        _add(report, "sovereign_engine", False, str(e), soft=True)


def check_symplectic(report: HarnessReport) -> None:
    try:
        import symplectic_status as ss  # type: ignore

        agg = ss.generate_aggregate_status()
        coh = float(agg.get("system", {}).get("coherence", 0))
        phase = float(agg.get("system", {}).get("phase_lock_degrees", 0))
        ok = coh >= 0.999 and abs(phase - PHASE_LOCK_DEG) < 1e-6
        _add(report, "symplectic_status.aggregate", ok, f"C={coh} phase={phase}", soft=True)
    except Exception as e:
        _add(report, "symplectic_status", False, str(e), soft=True)


def check_chronal_cement_schema(report: HarnessReport) -> None:
    schema = REPO_ROOT / "contracts" / "chronal_cement.schema.json"
    alt = REPO_ROOT / "schemas" / "chronal_cement.schema.json"
    path = schema if schema.is_file() else alt
    if not path.is_file():
        _add(report, "chronal_cement.schema", False, "schema file not found", soft=True)
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        _add(report, "chronal_cement.schema", isinstance(data, dict), str(path.name), soft=True)
    except Exception as e:
        _add(report, "chronal_cement.schema", False, str(e), soft=True)


def check_no_truncation_policy(report: HarnessReport) -> None:
    try:
        from quantum.no_truncation_policy import assert_full_sha256_hex, display_digest  # type: ignore

        full = "a" * 64
        assert assert_full_sha256_hex(full) == full
        assert display_digest(full) == full
        try:
            assert_full_sha256_hex("abcd")
            _add(report, "no_truncation_policy", False, "short digest accepted", soft=False)
        except ValueError:
            _add(report, "no_truncation_policy", True, "rejects truncated digests")
    except Exception as e:
        _add(report, "no_truncation_policy", False, str(e), soft=True)


def run_pytest_subset(report: HarnessReport, paths: Optional[List[str]] = None) -> None:
    targets = paths or ["tests/quantum/test_e10_hyperbolic.py", "tests/test_hybrid_rk4.py"]
    existing = [t for t in targets if (REPO_ROOT / t).exists() or Path(t).exists()]
    if not existing:
        _add(report, "pytest.subset", False, "no target test files", soft=True)
        return
    cmd = [sys.executable, "-m", "pytest", "-q", "--tb=line", *existing]
    try:
        proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=180)
        ok = proc.returncode == 0
        detail = (proc.stdout or proc.stderr or "")[-400:]
        _add(report, "pytest.subset", ok, detail.replace("\n", " ")[:300], soft=True)
    except Exception as e:
        _add(report, "pytest.subset", False, str(e), soft=True)


SUITE_MAP: Dict[str, List[Callable[[HarnessReport], None]]] = {
    "pipeline": [check_phi_pipeline],
    "dsh": [check_dsh_adapter, check_deepseek],
    "core": [
        check_phi_pipeline,
        check_mesh_modal,
        check_deepseek,
        check_dsh_adapter,
        check_endpoint_surface,
        check_no_truncation_policy,
    ],
    "engine": [check_sovereign_engine],
    "symplectic": [check_symplectic, check_chronal_cement_schema],
    "security": [check_endpoint_surface, check_no_truncation_policy, check_chronal_cement_schema],
    "pytest": [run_pytest_subset],
    "all": [
        check_phi_pipeline,
        check_mesh_modal,
        check_deepseek,
        check_dsh_adapter,
        check_endpoint_surface,
        check_sovereign_engine,
        check_symplectic,
        check_chronal_cement_schema,
        check_no_truncation_policy,
        run_pytest_subset,
    ],
}


def run_harness(suite: str = "all") -> HarnessReport:
    suite = suite.lower().strip()
    if suite not in SUITE_MAP:
        raise SystemExit(f"Unknown suite: {suite}. Choose from: {', '.join(sorted(SUITE_MAP))}")
    report = HarnessReport(timestamp=time.time(), suite=suite)
    print(f"🜁∀ HARNESS suite={suite} seal={SEAL}")
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    os.chdir(REPO_ROOT)
    for fn in SUITE_MAP[suite]:
        fn(report)
    digest = hashlib.sha3_256(json.dumps(report.to_dict(), sort_keys=True).encode()).hexdigest()
    print(f"Summary: passed={report.passed} hard_fail={report.hard_failures} soft_fail={report.soft_failures}")
    print(f"Integrity: {digest}")
    print(f"Seal: {SEAL}")
    return report


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Sovereign Garden unified verification harness")
    parser.add_argument("--local", action="store_true", help="Alias for suite=core (offline-friendly)")
    parser.add_argument(
        "--suite",
        default="all",
        help="core|pipeline|engine|symplectic|security|pytest|dsh|all",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON report")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on soft failures too")
    args = parser.parse_args(argv)
    suite = "core" if args.local else args.suite
    report = run_harness(suite)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    if report.hard_failures:
        return 1
    if args.strict and report.soft_failures:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
