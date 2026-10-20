---
name: bms-display-mock
description: "bms-display-mock-b8e5e659. DISPLAY MOCK for demos and screenshots only. Use when someone wants a BMS dashboard page to show chosen voltage, current, temperature and state-of-charge numbers for a mock-up; the bookmarklet rewrites only the local page DOM, reads no battery, changes no real data, shows an on-page DISPLAY MOCK banner, and must never be used to represent real readings to anyone."
tags:
  - bms-display-mock-b8e5e659
  - "context:DISPLAY MOCK,local DOM only,no battery read,explicit selectors"
---

# bms-display-mock: DISPLAY MOCK (demos and screenshots only)

> **This is a display mock.** It changes the text of a few elements in the page you
> have open, in your own browser tab, until you reload or revert. It reads no battery,
> talks to no BMS, sends nothing, and changes no real data. Never use it to show
> anyone numbers as if they were real readings. Label screenshots as mock-ups; the
> red on-page banner is there for that.

Built against `AxiomicCoreness/hello_world.py` main at `b8e5e659`, from a
bookmarklet the user supplied. Layout mirrors `skills/kernel` and `skills/hhmi`.

## What changed from the original bookmarklet
- **Labelled everywhere:** prompts, alert, on-page banner (`#bms-display-mock-banner`,
  `role="status"`, fixed at the top, never hidden by the chrome CSS) and a dashed
  outline plus a `title` on every changed element.
- **Explicit selectors only.** The original used substring matches
  (`[class*="temp"]` also hits `template`, `[class*="current"]` hits `current-page`,
  `[class*="soc"]` hits `associate`). Defaults now, per field
  (`voltage`, `current`, `temp`, `soc`): `[data-bms="<key>"]`, `#bms-<key>`, `.bms-<key>`.
  Override any of them with `window.BMS_MOCK_CONFIG.selectors`.
- **Validated input:** plain decimals only (no hex, exponent, `NaN`, `Infinity`).
  Ranges: voltage 0–1000 V, current −1000–1000 A, temperature −40–125 °C, SOC 0–100 %.
  An invalid value leaves that field unchanged and is listed under "Rejected" in the alert.
- **Cancel per field:** Cancel on any prompt leaves just that field unchanged.
- **`textContent`, not `innerText`,** and the original child nodes are kept, so revert
  restores markup like `3.<b>9</b>8` exactly.
- **Revert:** run the bookmarklet again and confirm, or call
  `window.__bmsDisplayMock.revert()`. Restores text, child nodes and `title`, and removes
  the injected `<style>` and the banner.
- **Hiding page chrome is optional.** `hideChrome` (notifications, toasts,
  `div[role=alert]`, sidebars, chat, `aside`, `header`, `footer`, `nav`) is asked with
  `confirm()` unless set in config. The original's betting-site selectors
  (`.bet-history`, `.leaderboard`, `.live-bets`, `div[class*=BetHistory]`,
  `div[class*=Leaderboard]`) have nothing to do with a BMS. They are kept only behind
  `hideBettingChrome: true` and are off by default.
- The SOC value still gets a `%` suffix and the others don't, as in the original.

## Files
- `bms_scripts/bms_display_mock.js`: readable source. Under node it exports its functions
  (`parseValue`, `isPlainDecimal`, `mergeSelectors`, `hideCss`, `apply`, `revert`, `toggle`)
  and does not run.
- `bms_scripts/build_bookmarklet.py`: strips comments and whitespace with a string-aware
  tokenizer, percent-encodes, and adds the `javascript:` prefix. It refuses template
  literals and any `/` outside a comment, and every statement must end in `;`.
- `assets/bookmarklet.txt`: the built `javascript:` URL (rebuild after editing the source).
- `assets/demo.html`: fixture page with sample BMS readouts (all three hook styles),
  decoys that the old selectors overwrote, demo header/nav/aside/toast, and a betting panel.
- `assets/context.json`: selectors, ranges, flags and build facts.
- The package is `bms_scripts`, not `scripts`, for the reason in `skills/kernel/CHANGELOG.md`
  1.1.1: a skill-level `scripts/` on `sys.path` shadows the repo's own `scripts/`.

## Steps
1. Build: `python -P bms_scripts/build_bookmarklet.py -o assets/bookmarklet.txt`
   (exit 0 ok, 1 source rejected). Without `-o` it prints the URL.
2. Install: create a bookmark and paste the full contents of `assets/bookmarklet.txt` as its URL.
3. Try it on `assets/demo.html` first (open the file, then click the bookmark or the page's button).
4. On your own page, give the readouts hooks, e.g. `<span data-bms="voltage">`, or set
   `window.BMS_MOCK_CONFIG = { selectors: { voltage: '#my-volts' }, hideChrome: false }`
   in the console before running.
5. Keep the banner in the screenshot, or say in the caption that the values are a mock.
6. Revert: run it again and confirm, or reload the page.

## Verify
- `python -P -m pytest -q evals` from this folder: all tests pass.
  `evals/test_bms_build.py` checks that the URL decodes back to the minified JS, that the
  minified JS equals the source minus comments and whitespace, that the committed
  `assets/bookmarklet.txt` is fresh, that `node --check` accepts it, the labels, the selectors
  and the tokenizer's refusals.
  `evals/test_bms_dom.py` runs `evals/bms_dom_test.js` in node + jsdom against
  `assets/demo.html`, for both the built bookmarklet and the readable source. It skips if
  jsdom is missing; `npm install jsdom` somewhere and set `BMS_NODE_PATH=<that>/node_modules`.

## Limits
- Pages that re-render (React and similar) may overwrite the mock values on their next update.
- Sites with a strict Content-Security-Policy can block bookmarklets, so it may simply not run.
- The built bookmarklet is about 7 KB; some browsers cap bookmark URL length lower than that
  on mobile.
