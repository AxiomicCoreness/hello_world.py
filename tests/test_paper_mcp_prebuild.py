# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""paper_mcp_prebuild refuses an incomplete compile and skips a missing tree."""
from __future__ import annotations

import importlib.util
import json
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location(
        "paper_mcp_prebuild_under_test", ROOT / "scripts" / "paper_mcp_prebuild.py"
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


gate = _load()

_SERVER = textwrap.dedent(
    '''
    class CanvasError(Exception):
        pass

    DEFAULT_BIND = "127.0.0.1"

    class CanvasStore:
        def __init__(self, root):
            self.root = root
        def validate_name(self, name):
            if not isinstance(name, str) or not name or "/" in name or "\\\\" in name or ".." in name:
                raise CanvasError("rejected")
            if name.startswith("/"):
                raise CanvasError("absolute")
            return name

    def resolve_loopback_host(host):
        raw = DEFAULT_BIND if host is None or str(host).strip() == "" else str(host).strip()
        if raw in ("0.0.0.0", "::", "[::]", "*") or raw not in ("127.0.0.1", "localhost"):
            raise SystemExit("refuse " + raw)
        return "127.0.0.1"

    def _tool_schemas():
        return [{"name": "canvas_list"}, {"name": "canvas_read"}]
    '''
)

_CLI = textwrap.dedent(
    '''
    import argparse
    def build_parser():
        parser = argparse.ArgumentParser(prog="paper_mcp")
        sub = parser.add_subparsers(dest="command")
        for name in ("serve", "serve-http", "resources", "list", "read"):
            sub.add_parser(name)
        return parser
    '''
)


def _package(root: Path, server: str = _SERVER, cli: str = _CLI, extra: str = "") -> None:
    pkg = root / "paper_mcp"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "__main__.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
    (pkg / "server.py").write_text(server, encoding="utf-8")
    (pkg / "cli.py").write_text(cli, encoding="utf-8")
    (pkg / "README.md").write_text("canvas\n", encoding="utf-8")
    if extra:
        (pkg / "extra.py").write_text(extra, encoding="utf-8")


def _json(capsys, *argv):
    code = gate.main([*map(str, argv), "--json"])
    cap = capsys.readouterr()
    return code, json.loads(cap.out), cap.err


def test_absent_tree_skips(tmp_path, capsys):
    code = gate.main([str(tmp_path), "--json"])
    out = capsys.readouterr().out
    assert code == 0
    assert "skipped: paper_mcp/ absent" in out
    assert json.loads(out)["class"] == "paper_mcp_prebuild"


def test_clean_fixture_exits_0(tmp_path, capsys):
    _package(tmp_path)
    code, data, _err = _json(capsys, tmp_path)
    assert code == 0, data
    assert data["metrics"]["blocking_unparsed"] == 0
    assert data["findings"] == []


def test_compile_error_is_incomplete(tmp_path, capsys):
    _package(tmp_path, extra="def (\n")
    code, data, err = _json(capsys, tmp_path)
    assert code == 2
    assert data["metrics"]["blocking_unparsed"] == 1
    assert "INCOMPLETE SCAN" in err


def test_known_unparsed_downgrades_compile_error(tmp_path, capsys):
    _package(tmp_path, extra="def (\n")
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    listing = scripts / "known.txt"
    listing.write_text("# note\npaper_mcp/extra.py  # syntax\n", encoding="utf-8")
    code, data, _err = _json(capsys, tmp_path, "--known-unparsed", listing)
    assert code == 0, data
    assert data["metrics"]["known_unparsed"] == 1
    assert data["parse_failures"][0]["known"] is True


def test_known_list_does_not_excuse_missing_required(tmp_path, capsys):
    _package(tmp_path)
    (tmp_path / "paper_mcp" / "README.md").unlink()
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    listing = scripts / "known.txt"
    listing.write_text("paper_mcp/README.md\n", encoding="utf-8")
    code, data, _err = _json(capsys, tmp_path, "--known-unparsed", listing)
    assert code == 2
    assert data["metrics"]["known_unparsed"] == 0


def test_tool_mismatch_exits_1(tmp_path, capsys):
    cli = textwrap.dedent(
        '''
        import argparse
        def build_parser():
            parser = argparse.ArgumentParser(prog="paper_mcp")
            sub = parser.add_subparsers(dest="command")
            sub.add_parser("serve")
            return parser
        '''
    )
    _package(tmp_path, cli=cli)
    code, data, _err = _json(capsys, tmp_path)
    assert code == 1
    assert data["metrics"]["by_kind"]["tool_cli_mismatch"] == 1


def test_unsafe_name_exits_1(tmp_path, capsys):
    server = _SERVER.replace(
        'if not isinstance(name, str) or not name or "/" in name or "\\\\" in name or ".." in name:',
        "if False and name:",
    )
    _package(tmp_path, server=server)
    code, data, _err = _json(capsys, tmp_path)
    assert code == 1
    assert "path_sanitization" in data["metrics"]["by_kind"]


def test_open_bind_exits_1(tmp_path, capsys):
    server = _SERVER.replace(
        'if raw in ("0.0.0.0", "::", "[::]", "*") or raw not in ("127.0.0.1", "localhost"):',
        "if False and raw:",
    )
    _package(tmp_path, server=server)
    code, data, _err = _json(capsys, tmp_path)
    assert code == 1
    assert "bind" in data["metrics"]["by_kind"]


def test_missing_known_list_is_usage_error(tmp_path, capsys):
    _package(tmp_path)
    assert gate.main([str(tmp_path), "--known-unparsed", str(tmp_path / "nope")]) == 2


def test_committed_known_list_is_empty():
    known = gate.load_known_unparsed(ROOT / "scripts" / "paper_mcp_prebuild_known_unparsed.txt")
    assert known == {}


def test_repo_scan_is_clean():
    assert gate.main([str(ROOT), "--json"]) == 0
