from garden_surgery.learner_hash import learner_sha3_256, restart_fingerprint


def test_full_64_hex():
    digest = learner_sha3_256({"k": "v"})
    assert len(digest) == 64
    assert digest == digest.lower()
    int(digest, 16)


def test_stable():
    assert learner_sha3_256({"a": 1, "b": 2}) == learner_sha3_256({"b": 2, "a": 1})


def test_restart_fingerprint():
    fp = restart_fingerprint()
    assert fp["asgi"] == "app:app_main"
    assert len(fp["sha3_256"]) == 64
    assert fp["fusion_canonical"] == 515
    assert fp["hyperion_preserved"] == 516
