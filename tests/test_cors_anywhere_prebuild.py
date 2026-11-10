# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""cors_anywhere_prebuild checks loopback refusal, preflight, and /healthz."""
from __future__ import annotations

import importlib.util
import json
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location(
        "cors_anywhere_prebuild_under_test", ROOT / "scripts" / "cors_anywhere_prebuild.py"
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


gate = _load()

_JS = textwrap.dedent(
    """
    var hostEnv = '127.0.0.1';
    if (hostEnv === '0.0.0.0' || hostEnv === '::' || hostEnv === '[::]' ||
        hostEnv === '*' || hostEnv !== '127.0.0.1') {
      process.exit(1);
    }
    var host = '127.0.0.1';
    """
)

_HTTP = textwrap.dedent(
    '''
    DEFAULT_BIND = "127.0.0.1"

    def resolve_loopback_host(host):
        raw = DEFAULT_BIND if not host else str(host)
        if raw in ("0.0.0.0", "::", "[::]", "*") or raw not in ("127.0.0.1", "localhost"):
            raise SystemExit("refuse")
        return "127.0.0.1"

    def do_OPTIONS(self):
        return ("Vary", "Origin")

    def health():
        return "/healthz"
    '''
)


def _cors(root: Path, server_js: str = _JS) -> None:
    directory = root / "tools" / "cors-anywhere"
    directory.mkdir(parents=True)
    (directory / "server.js").write_text(server_js, encoding="utf-8")
    (directory / "package.json").write_text('{"name": "cors"}\n', encoding="utf-8")
    (directory / "README.md").write_text("cors\n", encoding="utf-8")
    (directory / "help.txt").write_text("help\n", encoding="utf-8")


def _http(root: Path, source: str = _HTTP) -> None:
    pkg = root / "paper_mcp"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "server.py").write_text(source, encoding="utf-8")


def _json(capsys, *argv):
    code = gate.main([*map(str, argv), "--json"])
    cap = capsys.readouterr()
    return code, json.loads(cap.out), cap.err


def test_both_absent_skips(tmp_path, capsys):
    code = gate.main([str(tmp_path)])
    out = capsys.readouterr().out
    assert code == 0
    assert "skipped: tools/cors-anywhere/ absent" in out


def test_cors_tree_alone_is_clean(tmp_path, capsys):
    _cors(tmp_path)
    code, data, _err = _json(capsys, tmp_path)
    assert code == 0, data
    assert data["findings"] == []


def test_open_bind_in_server_js_exits_1(tmp_path, capsys):
    _cors(tmp_path, server_js="var host = '0.0.0.0';\n")
    code, data, _err = _json(capsys, tmp_path)
    assert code == 1
    assert data["metrics"]["by_kind"]["bind"] == 1


def test_missing_layout_file_exits_1(tmp_path, capsys):
    _cors(tmp_path)
    (tmp_path / "tools" / "cors-anywhere" / "help.txt").unlink()
    code, data, _err = _json(capsys, tmp_path)
    assert code == 1
    assert data["metrics"]["by_kind"]["layout"] == 1


def test_bad_package_json_is_incomplete(tmp_path, capsys):
    _cors(tmp_path)
    (tmp_path / "tools" / "cors-anywhere" / "package.json").write_text("{", encoding="utf-8")
    code, data, err = _json(capsys, tmp_path)
    assert code == 2
    assert data["parse_failures"][0]["reason"] == "parse_error"
    assert "INCOMPLETE SCAN" in err


def test_known_list_downgrades_bad_json(tmp_path, capsys):
    _cors(tmp_path)
    (tmp_path / "tools" / "cors-anywhere" / "package.json").write_text("{", encoding="utf-8")
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    listing = scripts / "known.txt"
    listing.write_text("tools/cors-anywhere/package.json  # broken\n", encoding="utf-8")
    code, data, _err = _json(capsys, tmp_path, "--known-unparsed", listing)
    assert code == 0, data
    assert data["parse_failures"][0]["known"] is True


def test_http_without_healthz_exits_1(tmp_path, capsys):
    _http(tmp_path, source=_HTTP.replace('return "/healthz"', 'return "/status"'))
    code, data, _err = _json(capsys, tmp_path)
    assert code == 1
    assert "healthz" in data["metrics"]["by_kind"]


def test_http_refuses_wildcard_bind(tmp_path, capsys):
    _http(tmp_path)
    code, data, _err = _json(capsys, tmp_path)
    assert code == 0, data


def test_committed_known_list_is_empty():
    known = gate.load_known_unparsed(ROOT / "scripts" / "cors_anywhere_prebuild_known_unparsed.txt")
    assert known == {}


def test_repo_scan_is_clean():
    assert gate.main([str(ROOT), "--json"]) == 0
