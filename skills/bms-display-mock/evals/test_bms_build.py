"""Build checks for the BMS DISPLAY MOCK bookmarklet (stdlib + pytest)."""
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from bms_scripts import build_bookmarklet as bb

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "bms_scripts" / "bms_display_mock.js"
COMMITTED = ROOT / "assets" / "bookmarklet.txt"


def _strip(js: str) -> str:
    """Source minus comments and all whitespace (strings included, on both sides)."""
    js = re.sub(r"/\*.*?\*/", "", js, flags=re.S)
    return re.sub(r"\s+", "", js)


def test_url_decodes_back_to_minified_js():
    min_js, url = bb.build()
    assert url.startswith("javascript:(function(){")
    assert bb.from_bookmarklet(url) == min_js


def test_minified_is_source_without_comments_or_whitespace():
    min_js, _ = bb.build()
    assert _strip(min_js) == _strip(SRC.read_text(encoding="utf-8"))


def test_every_string_literal_survives():
    src = SRC.read_text(encoding="utf-8")
    code = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    min_js, _ = bb.build()
    for lit in re.findall(r"'(?:\\.|[^'\\])*'", code):
        assert lit in min_js, lit


def test_build_is_deterministic_and_committed_copy_is_fresh():
    a = bb.build()
    b = bb.build()
    assert a == b
    assert COMMITTED.read_text(encoding="utf-8").strip() == a[1], (
        "assets/bookmarklet.txt is stale: run python -P bms_scripts/build_bookmarklet.py -o assets/bookmarklet.txt"
    )


def test_url_has_no_raw_unsafe_chars():
    _, url = bb.build()
    body = url[len("javascript:"):]
    for ch in ' "#%\n\r\t`\\':
        if ch == "%":
            assert re.fullmatch(r"(%[0-9A-F]{2}|[^%])*", body)
        else:
            assert ch not in body, repr(ch)
    assert all(ord(c) < 128 for c in body)


def test_labels_present_in_built_code():
    min_js, _ = bb.build()
    for needle in (
        "DISPLAY MOCK",
        "No battery was read and no real data was changed.",
        "Do not present these as real readings.",
        "bms-display-mock-banner",
        "(demo/screenshot only)",
    ):
        assert needle in min_js, needle


def test_default_selectors_are_explicit_hooks_only():
    min_js, _ = bb.build()
    m = re.search(r"var DEFAULT_SELECTORS=\{(.*?)\};", min_js)
    assert m, "DEFAULT_SELECTORS not found"
    block = m.group(1)
    assert "*=" not in block
    for key in ("voltage", "current", "temp", "soc"):
        for hook in (f'[data-bms="{key}"]', f"#bms-{key}", f".bms-{key}"):
            assert hook in block, hook


def test_betting_selectors_are_separate_and_opt_in():
    src = SRC.read_text(encoding="utf-8")
    chrome = re.search(r"var CHROME_SELECTORS = \[(.*?)\];", src, re.S).group(1)
    betting = re.search(r"var BETTING_SELECTORS = \[(.*?)\];", src, re.S).group(1)
    assert "leaderboard" not in chrome.lower() and "bet" not in chrome.lower()
    assert ".bet-history" in betting and ".live-bets" in betting
    assert "cfg.hideBettingChrome === true" in src


@pytest.mark.parametrize(
    "bad, msg",
    [
        ("var a = `x`;", "template literals"),
        ("var r = /ab+c/;", "regex or division"),
        ("var a = 1 / 2;", "regex or division"),
        ("var s = 'open;", "unterminated string"),
        ("/* never closed", "unterminated block comment"),
    ],
)
def test_tokenizer_refuses_what_it_cannot_minify_safely(bad, msg):
    with pytest.raises(bb.MinifyError, match=msg):
        bb.minify(bad)


def test_tokenizer_keeps_needed_spaces():
    assert bb.minify("var  a = b +\n +c;\nreturn x;") == "var a=b+ +c;return x;"
    assert bb.minify("a = 'x  /* not a comment */ y';") == "a='x  /* not a comment */ y';"


def test_cli_writes_url(tmp_path):
    out = tmp_path / "b.txt"
    assert bb.main(["-o", str(out)]) == 0
    assert out.read_text().strip() == bb.build()[1]


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_minified_js_parses_in_node(tmp_path):
    f = tmp_path / "min.js"
    f.write_text(bb.build()[0], encoding="utf-8")
    r = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_no_secrets_or_ledger_paths_in_skill():
    pat = re.compile(r"(ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{60,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|xox[abp]-[0-9A-Za-z-]{10,})")
    for p in ROOT.rglob("*"):
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc":
            text = p.read_text(encoding="utf-8", errors="replace")
            assert not pat.search(text), p
    assert not (ROOT / "ledger").exists() and not (ROOT / "ledger.v2").exists()
