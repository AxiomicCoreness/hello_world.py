# RUNBOOK.md

Operational steps for the two entry points on `hello_world.py` main.
Stdlib only. No Maven. No SLF4J.

## Compile

```bash
javac -d out src/main/java/com/fruitfly/brain/*.java
```

Exit 0 means the package compiles. No external jars.

## AutonomousDriver

Self-starting. Uses `SovereignConstants`, `DarkStateInvariant`, `SovereigntyState`, `LIFRK4`.

```bash
java -cp out com.fruitfly.brain.AutonomousDriver
```

Expected:

```
dark verify=true lambda2=1.0 seed=0.000e+00 residual=0.000e+00
tick 0 phase=RESONANCE ninja=233 v=-52.000
...
tick 6 phase=DARK_STATE ninja=1 v=-51.997
autonomous run complete — exit 0
```

Exit 1 if the dark-state gate fails. Exit 0 otherwise.

## SovereignMain

Four modes. `--chat`, `--sim` and `--repl` are mutually exclusive (combining them exits 2 with usage); with none of them the demo runs.

```bash
java -cp out com.fruitfly.brain.SovereignMain --chat "hello" --q 1.13 --p 25.96
```

Prints one line: `phase=... q=1.1300 p=25.9600 t=...`. Exit 0.

```bash
java -cp out com.fruitfly.brain.SovereignMain --steps 3
```

Prints connectome size, dark-state verify, simulation completion, gradient sync. Exit 0.

```bash
java -cp out com.fruitfly.brain.SovereignMain --sim --steps 100 --dt 1e-4
```

Headless. Runs `--steps` steps of `--dt` with drive 0.5 per step (the same drive the demo loop and `respond()` use) and prints one deterministic line:
`sim steps=100 dt=0.0001 t=0.010000 state=DARK_STATE neurons=8 synapses=13 mean_v=-52.426569`. Exit 0. `--steps`/`--dt` must be > 0, otherwise exit 2.

```bash
java -cp out com.fruitfly.brain.SovereignMain --repl
```

Reads commands from stdin, one per line: `chat <text>` (uses `--q`/`--p`; advances one 1e-4 step like `--chat`), `step [n]` (n steps of `--dt`, default 1), `state`, `help`, `exit` / `quit`. An unknown command prints a message and the loop continues. EOF exits 0. One automaton lives for the whole session.

All modes take `--connectome-file PATH` (else `Connectome.random(8, 0.25, 20260720)`); load progress goes to stderr. Exit codes: 0 ok, 2 bad argument / conflicting modes / unloadable connectome, 3 empty reply, 4 internal error. `--no-demo` with no mode exits 0 without running anything.

`--q` and `--p` are passthrough. They are not computed by the class.

## Files on disk

| File | Role |
|---|---|
| `AutonomousDriver.java` | self-starting entry |
| `SovereignMain.java` | CLI entry |
| `Connectome.java` | CSR + delay ring |
| `SovereignAutomaton.java` | swarm orchestrator |
| `GradientSynchronization.java` | Hebbian, eta = 1 |
| `DarkStateInvariant.java` | lambda2 = 1 gate |
| `SovereigntyState.java` | 8-phase ladder |
| `LIFRK4.java` | neuron |
| `SovereignConstants.java` | phi, eta |

## Failure modes

| Symptom | Cause |
|---|---|
| `Connectome` import fails | lowercase `connectome.java` present | rename |
| SLF4J missing | old `SovereignMain` | current file has no SLF4J |
| exit 1 from driver | dark gate failed | check `DarkStateInvariant` |

## Witness stream

`ledger/witness_stream.jsonl` carries HMAC-SHA3-256 over each line.
Key: `GARDEN` (public, documented). Algorithm: HMAC-SHA3-256.
Each line has `prev_hmac` linking to the prior line.
