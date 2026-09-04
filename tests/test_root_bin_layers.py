"""Substantive pytest for root GARDEN.BIN.v1 layers (ledger 9167).

Does not execute bookmarklets. Does not spawn EXE. MCP stays unfilled.
Does not rewrite harness.py.
"""
from __future__ import annotations

from pathlib import Path

from scripts.garden_bin_codec import LAYER_ORDER, load_layers, merkle

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_MERKLE = "e9e9f6749ecc3bba07d17ac7361fc32f9484cf2d0daa9b20f4914540c66c075b"
EXPECTED = {
    "sovereign_core.bin": "72301f4be2e1a32c85d8da5f002433e8fd611ec885c735c56aac0204e1deb9ee",
    "ledger_tip.bin": "0d52385456d8da81a7d9f2da2c25609613ea77a2a70dde9787ef2358e1061a01",
    "octonian_relay.bin": "67fdce5e3d2456d24fc3f4c139f485b6c2b0e2ddcd77cc5ebd8189ba0b8c2ff3",
    "adai_annihilator.bin": "e37ff65b9691382249d8671246625ed1faae3488ee0ad75b53161c842316950c",
}


def test_layers_exist_and_order():
    names = [n for n, _, _ in load_layers(ROOT)]
    assert names == LAYER_ORDER


def test_digests_and_merkle():
    layers = load_layers(ROOT)
    digests = []
    for name, digest, _obj in layers:
        assert digest == EXPECTED[name]
        digests.append(digest)
    assert merkle(digests) == EXPECTED_MERKLE


def test_chain_and_contracts():
    layers = load_layers(ROOT)
    prev = None
    for name, digest, obj in layers:
        assert obj.get("executable") is False
        assert obj.get("mcp_filled") is False
        if prev is not None:
            assert obj["hash_prev"] == prev
        prev = digest
    core = layers[0][2]
    assert core["dual_asgi"] == "127.0.0.1:8024"
    assert core["bind_0000"] is False
    assert core["rewrite_harness"] is False
    relay = layers[2][2]
    assert relay["rewrite_harness"] is False
    assert relay["rewrite_relay"] is False
    assert relay["harness"] == "harness.py"
    adai = layers[3][2]
    assert adai["bookmarklet_exec"] is False
    assert adai["kind"] == "specification_token"


def test_not_pe_or_elf():
    for name in LAYER_ORDER:
        head = (ROOT / name).read_bytes()[:4]
        assert head != b"MZ\x90\x00"
        assert head != b"\x7fELF"
        assert head.startswith(b"GARD")
