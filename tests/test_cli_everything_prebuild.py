# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""cli_everything_prebuild runs --help for every present entrypoint under python -I."""
from __future__ import annotations

import importlib.util
import json
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location(
        "cli_everything_prebuild_under_test", ROOT / "scripts" / "cli_everything_prebuild.py"
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


gate = _load()

_MAIN = textwrap.dedent(
    '''
    from .cli import main
    import sys
    if __name__ == "__main__":
        sys.exit(main())
    '''
)

_CLI = textwrap.dedent(
    '''
    import argparse
    def main(argv=None):
        parser = argparse.ArgumentParser(prog="paper_mcp")
        sub = parser.add_subparsers(dest="command")
        sub.add_parser("list")
        sub.add_parser("read")
        parser.parse_args(argv)
        return 0
    '''
)


def _paper(root: Path, cli: str = _CLI) -> None:
    pkg = root / "paper_mcp"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "cli.py").write_text(cli, encoding="utf-8")
    (pkg / "__main__.py").write_text(_MAIN, encoding="utf-8")


def _json(capsys, *argv):
    code = gate.main([*map(str, argv), "--json"])
    out = capsys.readouterr().out
    return code, json.loads(out)


def test_no_entrypoints_skips(tmp_path, capsys):
    code = gate.main([str(tmp_path)])
    out = capsys.readouterr().out
    assert code == 0
    assert "skipped: paper_mcp/ absent" in out


def test_help_for_every_subcommand_exits_0(tmp_path, capsys):
    _paper(tmp_path)
    code, data = _json(capsys, tmp_path)
    assert code == 0, data
    commands = data["metrics"]["commands"]
    assert "paper_mcp --help" in commands
    assert "paper_mcp list --help" in commands
    assert "paper_mcp read --help" in commands


def test_failing_subcommand_help_exits_1(tmp_path, capsys):
    cli = textwrap.dedent(
        '''
        import argparse, sys
        def main(argv=None):
            if argv is None:
                argv = sys.argv[1:]
            if argv and argv[0] == "list":
                sys.exit(3)
            parser = argparse.ArgumentParser(prog="paper_mcp")
            sub = parser.add_subparsers(dest="command")
            sub.add_parser("list")
            parser.parse_args(argv)
            return 0
        '''
    )
    _paper(tmp_path, cli=cli)
    code, data = _json(capsys, tmp_path)
    assert code == 1
    assert data["metrics"]["by_kind"]["help_failed"] == 1


def test_broken_entrypoint_is_incomplete_until_known(tmp_path, capsys):
    _paper(tmp_path)
    (tmp_path / "paper_mcp" / "__main__.py").write_text("raise SystemExit(9)\n", encoding="utf-8")
    code, data = _json(capsys, tmp_path)
    assert code == 2
    assert data["metrics"]["blocking_unparsed"] == 1
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    listing = scripts / "known.txt"
    listing.write_text("paper_mcp/__main__.py\n", encoding="utf-8")
    code, data = _json(capsys, tmp_path, "--known-unparsed", listing)
    assert code == 0, data
    assert data["parse_failures"][0]["known"] is True


def test_script_entrypoint_help(tmp_path, capsys):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "sovereign_cli.py").write_text(
        "import argparse, sys\n"
        "p = argparse.ArgumentParser(prog='sovereign')\n"
        "sub = p.add_subparsers(dest='command')\n"
        "sub.add_parser('status')\n"
        "p.parse_args()\n",
        encoding="utf-8",
    )
    code, data = _json(capsys, tmp_path)
    assert code == 0, data
    assert "sovereign_cli status --help" in data["metrics"]["commands"]


def test_does_not_pass_dash_p():
    source = (ROOT / "scripts" / "cli_everything_prebuild.py").read_text(encoding="utf-8")
    assert '"-P"' not in source
    assert "'-P'" not in source


def test_committed_known_list_is_empty():
    known = gate.load_known_unparsed(ROOT / "scripts" / "cli_everything_prebuild_known_unparsed.txt")
    assert known == {}


def test_repo_scan_is_clean():
    assert gate.main([str(ROOT), "--json"]) == 0
