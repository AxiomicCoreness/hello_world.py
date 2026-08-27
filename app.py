"""ASGI target: uvicorn app:app_main --host 127.0.0.1 --port 8024"""

from __future__ import annotations

from garden_surgery.declaration_flag import build_app
from garden_surgery.autonomous_starfire_311 import fire_payload, legend
from garden_surgery.deepseek_rate import status as deepseek_payload
from garden_surgery.era_policy import IGNORED_ERAS
from garden_surgery.october39 import TOKEN as OCTOBER39
from garden_surgery.learner_hash import learner_sha3_256, restart_fingerprint

try:
    app_main = build_app()
    app_main.title = "Garden app_main"
    app_main.version = "9077"

    @app_main.get("/starfire/legend")
    def starfire_legend():
        body = legend()
        body["october39"] = OCTOBER39
        body["ignored_eras"] = list(IGNORED_ERAS)
        return body

    @app_main.get("/starfire/311")
    def starfire_311():
        return fire_payload()

    @app_main.get("/harness/deepseek")
    def harness_deepseek():
        return deepseek_payload()

    @app_main.get("/learner/hash")
    def learner_hash(text: str = "garden"):
        digest = learner_sha3_256({"text": text})
        return {"sha3_256": digest, "len": len(digest), "truncated": False}

except ImportError:
    app_main = None


def before_main() -> dict:
    return restart_fingerprint()


def main() -> None:
    import uvicorn

    uvicorn.run("app:app_main", host="127.0.0.1", port=8024, log_level="warning")


if __name__ == "__main__":
    print(before_main())
    main()
