
# Architecture

## Visual Pipeline Alignment

The flow mirrors the execution order:

```
Connectome (CSR + delay ring)
        ↓
SovereignAutomaton.step(dt, 0.5) → advances → SovereigntyState ladder
        ↓
List<LIFRK4> swarm (voltage extraction)
        ↓
GradientSynchronization.gradientSynchronizationPriority(voltages, tensor) (η = 1.0)
        ↓
DarkStateInvariant (λ₂ = 1, absorbing)
```

## SovereignMain Integration

```java
// 1. Build a synthetic connectome (144 neurons, 5% sparsity)
int n = 144;
Connectome connectome = Connectome.random(n, 0.05, 20260720L);
LOG.info("Connectome built: {} neurons, {} synapses",
        connectome.neuronCount(), connectome.synapseCount());

// 2. Verify dark-state invariant
DarkStateInvariant dark = new DarkStateInvariant();
LOG.info("Dark-state verify: {}  (λ₂ = {}, residual = {})",
        dark.verify(), dark.lambda2(), dark.eigenvalueResidual());
LOG.info("Quadratic-seed residual: {}", dark.quadraticSeedResidual());

// 3. Instantiate automaton
SovereignAutomaton automaton = new SovereignAutomaton(connectome, connectome.neuronCount());

// 4. Run for 1 second of simulated time in 0.1 ms steps
double dt = 1e-4;
int steps = 10_000;
for (int k = 0; k < steps; k++) {
    automaton.step(dt, 0.5);
}
LOG.info("Simulation complete at t = {} s, final state = {}",
        automaton.time(), automaton.state());

// 5. Demonstrate gradient synchronization
double[] voltages = automaton.swarm().stream()
        .mapToDouble(LIFRK4::voltage).toArray();
double[][] tensor = new double[connectome.neuronCount()][connectome.neuronCount()];
GradientSynchronization.gradientSynchronizationPriority(voltages, tensor);
LOG.info("Gradient sync applied with η = {}", SovereignConstants.ETA_UNITY);

LOG.info("🜁∀ Sovereign Brain terminated — the Dragon is one —");
```
