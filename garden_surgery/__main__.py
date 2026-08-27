#!/usr/bin/env python3
"""PYTHONPATH=. python3 -m garden_surgery [--repo-root PATH] [--json]"""

from __future__ import annotations

import argparse
import json
import sys

from garden_surgery import diagnose
from garden_surgery.theorems import check_theorems


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Garden surgery diagnosis (no secret values)")
    p.add_argument("--repo-root", default=None)
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    theorems = check_theorems()
    report = diagnose(repo_root=args.repo_root)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("garden_surgery — cadaver diffusion (append-only)")
        print("theorems:", "PASS" if theorems.ok() else "FAIL", theorems.passed, theorems.failed)
        env = report["environment"]
        print("environment present:", {k: v for k, v in env["present"].items()})
        print("offline_viable:", env["offline_viable"])
        surf = report["surfaces"]
        print("surfaces ok:", surf["ok"])
        print("  hyperion_0516_preserved:", surf["hyperion_0516_preserved"])
        print("  fusion_canonical_515:", surf["fusion_canonical_515"])
        print("  claim_516_voided:", surf["claim_516_voided"])
        if surf["missing"]:
            print("  missing:", surf["missing"])
    return 0 if theorems.ok() else 1


def before_main() -> dict:
    from garden_surgery.learner_hash import restart_fingerprint

    return restart_fingerprint()


if __name__ == "__main__":
    print(before_main())
    sys.exit(main())
