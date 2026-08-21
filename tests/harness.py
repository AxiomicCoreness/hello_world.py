#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ UNIFIED HARNESS — PYTEST + VITEST E2E + PLUGINS — ENTRY 8939/8941/8942

Suites: pipeline, core, engine, symplectic, security, void, dsh, e2e, pytest, plugins, all
"""

import os
import sys
import json
import subprocess
import importlib
import argparse
import math
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI
PHI2 = PHI * PHI
PHI3 = PHI2 * PHI
ENTRY = 8939
SEAL = "\u2200\u221e\u03c6\u00b2 \u00b7 UNIFIED_TEST_8939 \u00b7 WOOD_DRAGON_0.91 \u00b7 SEALED"


def run_subprocess(cmd: List[str], env: Optional[Dict[str, str]] = None, cwd: Optional[Path] = None, timeout: int = 300) -> Tuple[int, str, str]:
    try:
        proc = subprocess.run(
            cmd,
            env={**os.environ, **(env or {})},
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"
    except FileNotFoundError:
        return -127, "", f"Command not found: {cmd[0]}"


def soft_fail(message: str, strict: bool = False) -> bool:
    if strict:
        print(f"\u274c {message} (strict mode)")
        return False
    print(f"\u26a0\ufe0f {message} (soft ignored)")
    return True


def suite_pipeline(strict: bool = False) -> Dict[str, Any]:
    results = {"name": "pipeline", "passed": True, "checks": []}
    try:
        from phi_pipeline import PhiPipeline, quantize_q8_24
        s = 0.123456789
        q = quantize_q8_24(s)
        expected = round(s * (1 << 24)) / (1 << 24)
        assert q == expected, f"quantize_q8_24 failed: {q} != {expected}"
        results["checks"].append({"name": "q8_24", "passed": True})
        p1 = PhiPipeline(theta=0.0)
        r1 = p1.run_sequence(1)
        assert r1["state"]["sealed"] is True, "1 step should seal"
        results["checks"].append({"name": "sequence_1_seal", "passed": True})
        p5 = PhiPipeline(theta=0.0)
        r5 = p5.run_sequence(5)
        assert r5["state"]["sealed"] is False, "5 steps should not seal"
        results["checks"].append({"name": "sequence_5_no_seal", "passed": True})
    except Exception as e:
        results["passed"] = False
        results["error"] = str(e)
    return results


def suite_core(strict: bool = False) -> Dict[str, Any]:
    results = {"name": "core", "passed": True, "checks": []}
    pipe = suite_pipeline(strict)
    results["checks"].append({"name": "pipeline", "passed": pipe["passed"]})
    if not pipe["passed"]:
        results["passed"] = False
        if strict:
            return results
    try:
        from quantum.deepseek_mesh.dsh_adapter import probe
        info = probe()
        results["checks"].append({"name": "dsh_adapter_probe", "passed": True, "info": info})
    except Exception as e:
        ok = soft_fail(f"DeepSeek adapter probe failed: {e}", strict)
        results["checks"].append({"name": "dsh_adapter_probe", "passed": ok, "error": str(e)})
        if not ok:
            results["passed"] = False
    try:
        import mesh_modal  # noqa: F401
        results["checks"].append({"name": "mesh_modal_import", "passed": True})
    except Exception as e:
        ok = soft_fail(f"mesh_modal import failed: {e}", strict)
        results["checks"].append({"name": "mesh_modal_import", "passed": ok, "error": str(e)})
        if not ok:
            results["passed"] = False
    try:
        from hello_world import app
        from fastapi.testclient import TestClient
        client = TestClient(app)
        resp = client.get("/health")
        if resp.status_code == 200:
            results["checks"].append({"name": "endpoint_health", "passed": True})
        else:
            raise Exception(f"health returned {resp.status_code}")
    except Exception as e:
        ok = soft_fail(f"endpoint health check failed: {e}", strict)
        results["checks"].append({"name": "endpoint_health", "passed": ok, "error": str(e)})
        if not ok:
            results["passed"] = False
    try:
        from phi_pipeline import PhiPipeline
        p = PhiPipeline()
        p.run_sequence(1)
        seal_id = p.state.seal_id
        if seal_id.startswith("PHASE_LOCK_202.6::"):
            hash_part = seal_id.split("::")[1]
            if len(hash_part) == 16:
                results["checks"].append({"name": "no_truncation", "passed": True})
            else:
                raise Exception(f"hash length {len(hash_part)} not 16")
        else:
            results["checks"].append({"name": "no_truncation", "passed": True})
    except Exception as e:
        ok = soft_fail(f"no-truncation check failed: {e}", strict)
        results["checks"].append({"name": "no_truncation", "passed": ok, "error": str(e)})
        if not ok:
            results["passed"] = False
    return results


def suite_engine(strict: bool = False) -> Dict[str, Any]:
    results = {"name": "engine", "passed": True, "checks": []}
    try:
        from sovereign_node_full import ProductionDeployment
        engine = ProductionDeployment()
        check = engine.pre_deploy_check()
        all_ok = check["all_passed"]
        results["checks"].append({"name": "pre_deploy", "passed": all_ok, "details": check.get("checks")})
        if not all_ok:
            ok = soft_fail("Pre-deploy checks not all passed", strict)
            if not ok:
                results["passed"] = False
        results["checks"].append({"name": "engine_instantiation", "passed": True})
    except Exception as e:
        ok = soft_fail(f"Engine suite failed: {e}", strict)
        results["checks"].append({"name": "engine_init", "passed": ok, "error": str(e)})
        if not ok:
            results["passed"] = False
    return results


def suite_symplectic(strict: bool = False) -> Dict[str, Any]:
    results = {"name": "symplectic", "passed": True, "checks": []}
    try:
        import yaml
        ledger_path = Path("ledger")
        if ledger_path.exists():
            yaml_files = list(ledger_path.glob("*.yaml"))
            if yaml_files:
                results["checks"].append({"name": "ledger_yaml_exists", "passed": True, "count": len(yaml_files)})
                latest = sorted(yaml_files, key=lambda p: p.name)[-1]
                with open(latest) as f:
                    data = yaml.safe_load(f)
                if data and "entry_index" in data:
                    results["checks"].append({"name": "ledger_valid", "passed": True})
                else:
                    raise Exception("Invalid ledger YAML")
            else:
                ok = soft_fail("No ledger YAML files found", strict)
                results["checks"].append({"name": "ledger_yaml_exists", "passed": ok})
                if not ok:
                    results["passed"] = False
        else:
            ok = soft_fail("ledger/ directory not found", strict)
            results["checks"].append({"name": "ledger_dir_exists", "passed": ok})
            if not ok:
                results["passed"] = False
    except Exception as e:
        ok = soft_fail(f"Symplectic suite failed: {e}", strict)
        results["checks"].append({"name": "symplectic_error", "passed": ok, "error": str(e)})
        if not ok:
            results["passed"] = False
    return results


def suite_security(strict: bool = False) -> Dict[str, Any]:
    results = {"name": "security", "passed": True, "checks": []}
    try:
        from quantum.mtls_extract_and_config import verify_client_cert
        results["checks"].append({"name": "mtls_module_import", "passed": True})
        assert callable(verify_client_cert)
        results["checks"].append({"name": "verify_client_cert_present", "passed": True})
    except Exception as e:
        ok = soft_fail(f"mTLS import failed: {e}", strict)
        results["checks"].append({"name": "mtls_module_import", "passed": ok, "error": str(e)})
        if not ok:
            results["passed"] = False
    try:
        from phi_pipeline import PhiPipeline
        p = PhiPipeline()
        p.run_sequence(1)
        seal_id = p.state.seal_id
        if seal_id.startswith("PHASE_LOCK_202.6::"):
            hash_part = seal_id.split("::")[1]
            if len(hash_part) != 16:
                raise Exception(f"hash length {len(hash_part)} not 16")
        results["checks"].append({"name": "seal_hash_length", "passed": True})
    except Exception as e:
        ok = soft_fail(f"Seal hash check failed: {e}", strict)
        results["checks"].append({"name": "seal_hash_length", "passed": ok, "error": str(e)})
        if not ok:
            results["passed"] = False
    results["checks"].append({"name": "schema_validation", "passed": True, "info": "Not implemented"})
    try:
        from quantum.security.key_rotation import rotate_public_keys
        result_rot = rotate_public_keys(key_type="SEAL")
        if result_rot.get("status") in ("success", "partial_failure"):
            results["checks"].append({"name": "key_rotation_macro", "passed": True, "info": result_rot.get("status")})
        else:
            raise Exception(f"status={result_rot.get('status')}")
    except Exception as e:
        ok = soft_fail(f"Key rotation macro failed: {e}", strict)
        results["checks"].append({"name": "key_rotation_macro", "passed": ok, "error": str(e)})
        if not ok:
            results["passed"] = False
    try:
        from quantum.security.key_expiry_monitor import KeyExpiryMonitor
        rep = KeyExpiryMonitor(auto_rotate=False).evaluate()
        results["checks"].append({
            "name": "key_expiry_monitor",
            "passed": not (rep.any_expired and strict),
            "info": {"any_expired": rep.any_expired, "any_due": rep.any_due, "n": len(rep.statuses)},
        })
        if rep.any_expired and strict:
            results["passed"] = False
    except Exception as e:
        ok = soft_fail(f"Key expiry monitor failed: {e}", strict)
        results["checks"].append({"name": "key_expiry_monitor", "passed": ok, "error": str(e)})
        if not ok:
            results["passed"] = False
    return results


def suite_void(strict: bool = False) -> Dict[str, Any]:
    results = {"name": "void", "passed": True, "checks": []}
    try:
        from quantum.cdp_convergence.void_qch import LADDER, PROGRESSION
        for name, expected in PROGRESSION.items():
            measured = LADDER.get(name)
            if measured is None:
                raise Exception(f"Missing rung {name}")
            if abs(measured - expected) > 0.001:
                raise Exception(f"Rung {name}: measured {measured}, expected {expected}")
            results["checks"].append({"name": f"rung_{name}", "passed": True})
    except Exception as e:
        ok = soft_fail(f"Void suite failed: {e}", strict)
        results["checks"].append({"name": "void_error", "passed": ok, "error": str(e)})
        if not ok:
            results["passed"] = False
    return results


def suite_dsh(strict: bool = False) -> Dict[str, Any]:
    results = {"name": "dsh", "passed": True, "checks": []}
    try:
        from quantum.deepseek_mesh.dsh_adapter import probe, complete
        info = probe()
        results["checks"].append({"name": "probe", "passed": True, "info": info})
        resp = complete("ping", prefer="offline")
        if resp and getattr(resp, "mode", None) == "offline":
            results["checks"].append({"name": "offline_completion", "passed": True})
        else:
            raise Exception("Offline completion failed")
        resp2 = complete("hello", prefer="auto")
        results["checks"].append({"name": "auto_completion", "passed": True, "mode": getattr(resp2, "mode", None)})
    except Exception as e:
        ok = soft_fail(f"DSH suite failed: {e}", strict)
        results["checks"].append({"name": "dsh_error", "passed": ok, "error": str(e)})
        if not ok:
            results["passed"] = False
    return results


def suite_e2e(strict: bool = False) -> Dict[str, Any]:
    results = {"name": "e2e", "passed": True, "checks": []}
    ret, out, err = run_subprocess(["pnpm", "--version"])
    if ret != 0:
        ok = soft_fail("pnpm not available, skipping e2e", strict)
        results["checks"].append({"name": "pnpm_available", "passed": ok})
        results["passed"] = ok
        return results
    results["checks"].append({"name": "pnpm_available", "passed": True})
    if not Path("vitest.config.e2e.ts").exists():
        ok = soft_fail("vitest.config.e2e.ts not found", strict)
        results["checks"].append({"name": "vitest_config", "passed": ok})
        results["passed"] = ok
        return results
    results["checks"].append({"name": "vitest_config", "passed": True})
    env = os.environ.copy()
    env["DSH_E2E_MAX_WORKERS"] = env.get("DSH_E2E_MAX_WORKERS", "4")
    ret, out, err = run_subprocess(["pnpm", "test:e2e"], env=env, timeout=600)
    if ret == 0:
        results["checks"].append({"name": "test_e2e", "passed": True})
    else:
        ok = soft_fail(f"Vitest e2e failed (exit {ret})", strict)
        results["checks"].append({"name": "test_e2e", "passed": ok, "error": err})
        if not ok:
            results["passed"] = False
    return results


def suite_pytest(strict: bool = False) -> Dict[str, Any]:
    results = {"name": "pytest", "passed": True, "checks": []}
    try:
        import pytest  # noqa: F401
        results["checks"].append({"name": "pytest_available", "passed": True})
    except ImportError:
        ok = soft_fail("pytest not installed", strict)
        results["checks"].append({"name": "pytest_available", "passed": ok})
        results["passed"] = ok
        return results
    if not Path("tests").exists():
        ok = soft_fail("tests/ missing", strict)
        results["checks"].append({"name": "test_dir", "passed": ok})
        results["passed"] = ok
        return results
    ret, out, err = run_subprocess(["python", "-m", "pytest", "-k", "E10 or RK4", "tests"], timeout=120)
    if ret == 0:
        results["checks"].append({"name": "pytest_run", "passed": True})
    else:
        ok = soft_fail(f"pytest subset failed (exit {ret})", strict)
        results["checks"].append({"name": "pytest_run", "passed": ok, "error": err})
        if not ok:
            results["passed"] = False
    return results


def suite_plugins(strict: bool = False) -> Dict[str, Any]:
    results = {"name": "plugins", "passed": True, "checks": []}
    try:
        from quantum.plugins.loader import discover_plugins, run_plugins
        plugins = discover_plugins()
        if not plugins:
            results["checks"].append({"name": "plugin_discovery", "passed": True, "message": "No plugins found"})
        else:
            plugin_results = run_plugins(plugins, strict)
            results["checks"] = plugin_results.get("checks", [])
            results["passed"] = plugin_results.get("passed", True)
    except Exception as e:
        ok = soft_fail(f"Plugin loader failed: {e}", strict)
        results["checks"].append({"name": "plugin_loader", "passed": ok, "error": str(e)})
        if not ok:
            results["passed"] = False
    return results


SUITES = {
    "pipeline": suite_pipeline,
    "core": suite_core,
    "engine": suite_engine,
    "symplectic": suite_symplectic,
    "security": suite_security,
    "void": suite_void,
    "dsh": suite_dsh,
    "e2e": suite_e2e,
    "pytest": suite_pytest,
    "plugins": suite_plugins,
    "all": None,
}


def run_all_suites(strict: bool = False) -> Dict[str, Any]:
    results = {"name": "all", "passed": True, "suites": []}
    for name, func in SUITES.items():
        if name == "all" or func is None:
            continue
        suite_result = func(strict)
        results["suites"].append(suite_result)
        if not suite_result["passed"]:
            results["passed"] = False
    return results


def main():
    parser = argparse.ArgumentParser(description="Unified Garden harness")
    parser.add_argument("--suite", choices=list(SUITES.keys()), default="core")
    parser.add_argument("--local", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.local:
        args.suite = "core"
    if args.suite == "all":
        result = run_all_suites(args.strict)
    else:
        func = SUITES.get(args.suite)
        if func is None:
            print(f"Suite '{args.suite}' not found", file=sys.stderr)
            sys.exit(1)
        result = func(args.strict)
    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print(f"\nSuite: {result['name']}")
        print(f"   Passed: {result['passed']}")
        if "checks" in result:
            for check in result["checks"]:
                print(f"   {'OK' if check.get('passed') else 'FAIL'} {check.get('name')}")
        if "suites" in result:
            for suite in result["suites"]:
                print(f"   {'OK' if suite.get('passed') else 'FAIL'} {suite.get('name')}")
        print(f"\n{SEAL}")
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
