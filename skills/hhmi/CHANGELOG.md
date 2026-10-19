# Changelog

## [1.0.3] - 2026-10-19
### Fixed
- SKILL.md and `assets/context.json` no longer say `port380_mcp.py` reads `SovereignMain --chat`
  output. GitHub main's `port380_mcp.py` does not invoke `SovereignMain`. `--chat` stdout is still
  kept to the bare reply, with load progress on stderr, so any future caller can parse it
  (`assets/context.json` adds `port380_mcp_invokes_sovereignmain: false`).

## [1.0.2] - 2026-10-19
### Changed
- The loader is now applied in `src/` on main at `1dfeaec`
  (`feat(brain): load connectome from HHMIJaneliaMap.xml via --connectome-file`):
  `ConnectomeLoader.java`, `ConnectomeLoaderTest.java`, `src/main/resources/HHMIJaneliaMap.xml`
  and `SovereignMain.diff`, byte-identical to this skill's `java/` copies
  (SKILL.md, `assets/context.json` `applied_to_src`).
- `run_java_tests.sh --fresh` skips `SovereignMain.diff` when main already has it.

## [1.0.1] - 2026-10-19
### Changed
- Known limits: the `SovereignAutomaton.step` self-feedback is fixed in main by `4b6d07d`
  (`fix(brain): deliver connectome currents to postsynaptic targets in SovereignAutomaton.step`)
  (SKILL.md, `assets/context.json`). Expected JUnit count is now 21 (adds 2
  `SovereignAutomatonPropagationTest`).
- SKILL.md and `assets/context.json` say the skill is committed under `skills/hhmi/`
  (the loader and `SovereignMain.diff` are still not applied to `src/`).
- `run_java_tests.sh`: the JDK hint points at the kernel skill's renamed
  `kernel_scripts/install_jdk.sh`.

## [1.0.0] - 2026-10-19
### Added
- `SKILL.md` with frontmatter (name, tagged description, tags) and the sections Context,
  Real data format, Steps, Known limits and Verify, built against main at `fd76685`.
- `assets/context.json` with the API facts, the loader rules and the hemibrain v1.2 export
  numbers (21,739 neurons; about 3.55M connection rows; weight = synapse count).
- `assets/HHMIJaneliaMap.xml`: the 3-neuron ring placeholder (marked NOT FlyEM data).
- `java/`: `ConnectomeLoader.java` (CSR builder, XXE-hardened DOM parse),
  `ConnectomeLoaderTest.java` (11 tests), the placeholder resource, and
  `SovereignMain.diff` (`--connectome-file`, `connectome.neuronCount()` instead of 8,
  progress on stderr, exit 2 on a bad file).
- `hhmi_scripts/csv_to_xml.py`: hemibrain CSV → loader XML, with `--min-weight` and
  `--limit N` (top N by total synapse weight, internal edges only). It XML-escapes ids,
  sums repeated pairs, and uses the stdlib only.
- `hhmi_scripts/check_hhmi.py`: validates XML against the loader's rules, prints counts,
  and exits 1 on failure.
- `evals/conftest.py` and `evals/test_hhmi.py` (synthetic fixtures only). The package is
  named `hhmi_scripts` so it cannot shadow the repo's `scripts/`.
- `run_java_tests.sh`: JUnit run against the reused tree or a fresh main (`--fresh`),
  followed by a `--chat` smoke run.

### Known limits (not fixed here; repo untouched)
- `Connectome.currentsFrom` allocates `double[n]` per neuron per step, which is O(n²) and
  impractical at 21,739.
- `SovereignAutomaton.step` feeds a neuron's outgoing currents back into itself.
