# Changelog

## [1.1.1] - 2026-10-19
### Changed
- Renamed the skill package `scripts/` to `kernel_scripts/` (`__init__.py`,
  `check_kernel.py`, `install_jdk.sh`, `run_endpoint.sh`,
  `java/com/fruitfly/brain/Endpoint.java`). `evals/conftest.py` puts the skill root
  first on `sys.path`, so under a repo-root `pytest` the old name resolved
  `scripts` to this folder and shadowed the repo's own `scripts/` (breaking
  `tests/test_dual_asyncio_cicd.py` and `tests/test_hook_branch_policy.py`).
  Updated `evals/test_kernel.py`, `evals/conftest.py`, `evals/test_endpoint.py`,
  `SKILL.md` and the javac path inside `run_endpoint.sh`. Entries below keep the
  old paths as they were at the time.

## [1.1.0] - 2026-10-19
### Added
- Demo Java endpoint `scripts/java/com/fruitfly/brain/Endpoint.java` (JDK 17 stdlib:
  `HttpServer`, `ImageIO`, headless AWT) on 127.0.0.1:8025 with `/healthz`, `/schema`,
  `/render` (PNG with pHYs set from dpi; 400 on bad input).
- `scripts/install_jdk.sh` (idempotent JDK 17; Temurin fallback) and `scripts/run_endpoint.sh`.
- `assets/render_schema.json` (JSON Schema 2020-12, iPhone 12 / A14 Bionic) and
  `assets/sample_300dpi.png` (600×900 px, 11811 px/m = 300 dpi).
- `templates/RenderClient.swift` (URLSession client) and `evals/test_endpoint.py`.

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
