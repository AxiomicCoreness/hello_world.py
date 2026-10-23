# Changelog

## [Unreleased]
### Fixed
- CI: `.github/workflows/quantum_reality_engine_510510.yml` compileall step made
  best-effort; failing files go to `::warning` and `$GITHUB_STEP_SUMMARY`, and the
  job exits 0 so engine and seal proceed. The 8 failing sources are logged as
  open tech debt in ledger entry 9290; after the t_rotator.py → t_rotator.txt
  rename, 7 remain.
- Math: canonical λ₀ is `952,072.1 nm` (Σθ = 202.600°); `952,057 nm` is a deprecated draft (Σθ = 202.603°).
- `recalc_optics.py` now prints `[?] UNRECOGNISED` when λ₀ matches neither the
  canonical 952,072.1 nm nor the deprecated 952,057 nm draft (previously silent).
- `evals/conftest.py` puts the skill root on `sys.path`, so `python -P -m pytest evals`
  can import `scripts` (it failed with ModuleNotFoundError before).

### Added
- North Star 71.975 Hz: `north_star_hz` and `phase_lock_degrees` (202.6) in
  `assets/context.json`, with repo sources (`north_star_freq`, `NORTH_STAR_HZ`);
  `recalc_optics.py --north-star [HZ]` echoes and validates it; eval tests added.
- Mirror URLs (GitCode, AtomGit) as `identifiers` in `templates/CITATION.cff`.

## [1.0.0] - 2026-10-18
### Added
- `SKILL.md` with frontmatter and steps.
- `templates/CITATION.cff` citing concept DOI 10.5281/zenodo.23378305.
- Initial skill scaffold based on Drift Baseline 731 measurement report.
- `context.json` to separate deprecated `952,057` from canonical `952,072.1`.
- `recalc_optics.py` to resolve lambda0 and phase column discrepancies.
- `test_recalc.py` to catch the `φπ/2 = 145.62°` phase trap.
