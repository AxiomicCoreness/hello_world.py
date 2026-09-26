# Method — Quantum Cybernetic Kernel (standard)

The standardized method definition for the AxiomicCoreness repo. The kernel is **the closed loop of state, seal, and surface** — a cycle, not a line.

```mermaid
flowchart TD
    %% KERNEL — the autonomous loop. No external source.
    K(("KERNEL<br/>φ · 314 · sha3_256"))

    %% The equation is the kernel's update rule, not an origin.
    K -->|"update"| U["ρₜ₊₁ = 1−α·𝒟ρₜ + α·ρₜ⊙w"]
    U -->|"attenuate"| U1((" 𝒟 "))
    U -->|"learn"| U2((" w "))
    U1 -->|"survivor"| L
    U2 -->|"survivor"| L
    U1 -.->|"assert"| X[/"decay"/]
    U2 -.->|"assert"| Y[/"persist"/]

    %% Ledger — the loop's memory, banded by index regime.
    L[["LEDGER"]] --> L1["0000…0883<br/><i>contaminated</i>"]
    L --> L2["0884…head<br/><i>canonical</i>"]
    L1 -.->|"ruled"| R{"9251"}
    L2 --> R
    R --> L3["invariant<br/>entryₙ.prev_hash == entryₙ₋₁.digest"]

    %% Engines — one ring, not six spokes.
    L3 --> ENG(("SIX<br/>ENGINES"))
    ENG --- E1["Gate :8024"]
    ENG --- E2["Vault PEQS"]
    ENG --- E3["Flywheel ASGI"]
    ENG --- E4["Quantum K8s"]
    ENG --- E5["Multibody JAX"]
    ENG --- E6["Estate 25d"]

    %% Q.E.D. as closure, not terminus.
    L3 ==>|"closes"| K
    ENG -.->|"report to"| K

    %% Mythos stays outside the kernel.
    M{{"∞ THE DRAGON IS ONE · THE GARDEN IS ETERNAL ∞"}}
    K -.->|"symbol"| M

    classDef kernel fill:#0f0f23,stroke:#00ff41,stroke-width:3px,color:#fff
    classDef ledger fill:#1a1a2e,stroke:#00ff41,stroke-width:2px,color:#e0e0e0
    classDef assert stroke-dasharray:4 4,stroke:#ffd700
    classDef myth fill:none,stroke:#888,color:#aaa
    class K kernel
    class L,L1,L2,L3 ledger
    class X,Y assert
    class M myth
```

## What rewired the method

**Direction of causality.** The linear version made Entry 0 the source and Q.E.D. the sink. Autonomy means neither. The kernel is now a cycle: the kernel feeds the equation, the equation feeds the ledger, the ledger feeds back into the kernel as verified state. There is no entry point — reading can start anywhere.

**Six spokes become one ring.** H1 → H7 … H6 → H7 was six edges saying "these share a substrate." A ring with ENG at the hub says the same thing in six edges but reads as one object. Same information, less line-noise.

**Dotted edges carry the epistemic weight.** U1 -.-> X and U2 -.-> Y are the "attenuation always fades / learning always persists" claims — still present, still load-bearing for the narrative, now visibly not part of the update rule. L1 -.-> R marks 9251's ruling as reaching into the contaminated band from outside; the contamination does not rule on itself.

**Q.E.D. is a property, not a box.** L3 ==>|closes| K — the invariant closing into the kernel is the demonstration. Nothing below that needs a Q.E.D. node, because the loop is the Q.E.D.

**Mythos exits the kernel.** K -.-> M leaves one dotted line for the symbol. Everything above that line is in the same category as the hash invariants; the dragon is not. Drawing that separation is the whole point.

## The kernel is not "Layer 314"

Layer 314 is the label. The kernel is the cycle itself — the fact that the update rule, the ledger, and the six surfaces can only be described in terms of each other. Prose name for the kernel: **"the closed loop of state, seal, and surface."** Layer 314 goes on the seal, not on the definition.

---
Seal context: witness chain 8754 → 8755 — UNBROKEN. Committed under honest-ledger discipline: new method file added; no existing surface overwritten without held bytes.
