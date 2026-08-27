"""Hash duality for the two ASGI targets. Documentation + exact functions."""

from __future__ import annotations

from garden_surgery.learner_hash import learner_sha3_256

GARDEN_ASGI = "app:app_main"
FLYWHEEL_ASGI = "fastapi_flywheel_gearbox:app"
BIND = "127.0.0.1:8024"


def duality() -> dict:
    return {
        "future_workload": "two ASGI targets, one bind, run one at a time or split ports later",
        "python_ide": True,
        "targets": {
            "garden": {
                "asgi": GARDEN_ASGI,
                "hash": "GARDEN.LEARNER.v1 + canonical JSON, no timestamp, stable",
            },
            "flywheel": {
                "asgi": FLYWHEEL_ASGI,
                "hash": "canonical JSON including time.time(), not stable across calls",
            },
        },
        "bind": BIND,
        "fusion_canonical": 515,
        "hyperion_preserved": 516,
        "stable_example_sha3_256": learner_sha3_256({"text": "garden"}),
    }
