#!/usr/bin/env python3
"""Bin next to cambrian_stub.py. Prints config demo stats. No fire."""

from garden_surgery.berry_chern import demo_from_config, load_config
from garden_surgery.cambrian_stub import allocation


def main() -> int:
    cfg = load_config()
    demo = demo_from_config(cfg)
    stub = allocation()
    print("config_stub:", cfg.get("stub"))
    print("cambrian_filled:", stub["filled"])
    print("n_theta:", demo["n_theta"], "n_phi:", demo["n_phi"])
    print("mu_M:", demo["mu_M"])
    print("sigma:", demo["sigma"])
    print("bins:", len(demo["hist_counts"]))
    print("fire: no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
