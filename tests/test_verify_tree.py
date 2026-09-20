#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pytest for scripts/verify_tree.py."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from verify_tree import extract_nodes, verify_tree, main  # noqa: E402


def test_valid_chain():
    nodes = {
        "root": {"parent": None},
        "child": {"parent": "root"},
        "leaf": {"parent": "child"},
    }
    assert verify_tree(nodes) == []


def test_missing_parent():
    problems = verify_tree({"a": {"parent": "missing"}})
    assert any("does not exist" in p for p in problems)


def test_cycle():
    problems = verify_tree({"a": {"parent": "b"}, "b": {"parent": "a"}})
    assert any("cycle" in p for p in problems)


def test_two_roots():
    problems = verify_tree({"a": {"parent": None}, "b": {"parent": None}})
    assert any("root count" in p for p in problems)


def test_empty():
    assert "empty tree" in verify_tree({})


def test_extract_nodes_wrapper():
    doc = {"nodes": {"r": {"parent": None}, "c": {"parent": "r"}}}
    nodes = extract_nodes(doc)
    assert verify_tree(nodes) == []


def test_cli_smoke(capsys):
    rc = main(["--smoke"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "OK" in out


def test_cli_file(tmp_path):
    p = tmp_path / "t.json"
    p.write_text(
        json.dumps({"nodes": {"r": {"parent": None}, "c": {"parent": "r"}}}),
        encoding="utf-8",
    )
    assert main([str(p)]) == 0


def test_cli_bad_file(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text(
        json.dumps({"nodes": {"a": {"parent": "nope"}}}),
        encoding="utf-8",
    )
    assert main([str(p)]) == 1


def test_cli_missing_file():
    assert main(["/nonexistent/tree.json"]) == 2
