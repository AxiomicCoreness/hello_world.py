# Changelog

## [1.0.0] - 2026-10-19
### Added
- `SKILL.md` with frontmatter (name, tagged description, tags) and steps, built
  from `kernel/` at commit `1e449302`; every constant cited as file:line
  (checked with `git grep` at that commit).
- `assets/context.json` with the kernel constants, computed values, audit
  status (11 defects, 8 fixed, D9 OPEN_UNFIXED) and known discrepancies.
- `scripts/check_kernel.py`: re-checks the φ gate, the open band, composition,
  500-deep deepening and the audited false claims; loads and runs
  `kernel/math_origin_audit.py`; `--claim NAME VALUE` classifies a value as
  `[+] OK`, `[!] WARNING` (audited false claim) or `[?] UNRECOGNISED`.
- `evals/conftest.py` (skill root on `sys.path`, works under `python -P`) and
  `evals/test_kernel.py`.
- `templates/CITATION.cff` citing concept DOI 10.5281/zenodo.23378305 with the
  GitCode and AtomGit mirror identifiers.

### Known repo discrepancies (not fixed here; repo untouched)
- `kernel/README.md:6` says 19 assertions; `closure_kernel.test.ts` has 15.
- `kernel/README.md:29` says 871.6 Hz; 261.63 · φ^2.5 = 871.28 Hz.
- `kernel/README.md:29` / `closure_kernel.test.ts:12` say φ^2.5 ≈ 3.331; it is 3.33019.
- `kernel/exactness.test.ts` never sets a failing exit code.
