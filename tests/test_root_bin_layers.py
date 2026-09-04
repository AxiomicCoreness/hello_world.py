"""Substantive pytest for root GARDEN.BIN.v1 layers (ledger 9167/9171).

Does not execute bookmarklets. Does not spawn EXE. MCP stays unfilled.
Does not rewrite harness.py.
"""
from __future__ import annotations

from pathlib import Path

from scripts.garden_bin_codec import LAYER_ORDER, load_layers, merkle

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_MERKLE = "3a00d16045470561e2d9f15f707a05c57dfc859948d559b898c00ffdefd8dc2a"
EXPECTED = {
    "sovereign_core.bin": "5c5184f9368c9ee443d860aa419a11ca6937af9d5a5b597df703b00c3cb7c755",
    "ledger_tip.bin": "ee1bc942cb2401f443804f6b836032fd5d93d8d26475bec77327cd82950c65bb",
    "octonian_relay.bin": "f6bcb0288f4f985c8f9633cc9d53276dc27b136a996f707e21758cd9c3c117eb",
    "adai_annihilator.bin": "f83ff65ffb86f670265819271a83f4603a79ce15d0f8366f67d8803d4c8f6f8a",
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
