#!/usr/bin/env python3
"""Entry point. Writes verification_log.json through pushdelta."""
from phi_verify.verify import run, write_log
from phi_verify import pushdelta

if __name__ == "__main__":
    log = run()
    delta = write_log(log)
    print(f"overall: {log['overall']}")
    print(f"seal:    {log['seal']}")
    print(f"delta:   {delta['digest'][:16]} → {delta['path']}")
    print(f"chain:   {'UNBROKEN' if pushdelta.verify_chain() else 'BROKEN'}")
