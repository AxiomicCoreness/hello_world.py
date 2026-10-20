# Changelog

## [1.0.0] - 2026-10-20
### Added
- `SKILL.md` with frontmatter (name, tagged description, tags), labelled throughout as a
  DISPLAY MOCK for demos and screenshots: local page DOM only, no battery read, no real
  data changed, not to be used to represent real readings.
- `bms_scripts/bms_display_mock.js`, rewritten from the user's bookmarklet:
  explicit selectors (`[data-bms=<key>]`, `#bms-<key>`, `.bms-<key>`) replacing the
  substring matches, an optional `BMS_MOCK_CONFIG.selectors` map, plain-decimal
  validation with per-field ranges, cancel per field, `textContent`, an on-page banner,
  marked elements, and a revert that restores the original child nodes and `title` and
  removes the injected style and banner. Hiding page chrome is optional (`hideChrome`,
  else `confirm()`), and the betting-site selectors, unrelated to a BMS, sit behind
  `hideBettingChrome` (off by default).
- `bms_scripts/build_bookmarklet.py` (stdlib minifier, percent-encoder and round-trip
  check) and the built `assets/bookmarklet.txt`.
- `assets/demo.html` fixture and `assets/context.json`.
- `evals/conftest.py`, `evals/test_bms_build.py`, `evals/test_bms_dom.py` and
  `evals/bms_dom_test.js` (node + jsdom).
