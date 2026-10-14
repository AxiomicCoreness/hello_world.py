package com.fruitfly.brain;

/**
 * Self-starting entry point for the fruitfly.brain package.
 *
 * Stdlib only. Runs the dark-state gate, advances the phase ladder,
 * and ticks one LIFRK4 neuron. Exits 0 on gate pass, 1 on gate fail.
 * No external scheduler, no SLF4J, no Maven.
 */
public final class AutonomousDriver {

    public static void main(String[] args) {
        DarkStateInvariant dark = new DarkStateInvariant();
        boolean gate = dark.verify();
        System.out.printf("dark verify=%s lambda2=%.1f seed=%.3e residual=%.3e%n",
                gate, dark.lambda2(), dark.quadraticSeedResidual(), dark.eigenvalueResidual());
        if (!gate) {
            System.out.println("gate refused — exit 1");
            System.exit(1);
        }

        SovereigntyState state = SovereigntyState.OBSERVATION;
        LIFRK4 neuron = new LIFRK4();
        for (int tick = 0; tick < 8 && !state.isAbsorbing(); tick++) {
            neuron.stepTick(0.1);
            state = state.next();
            System.out.printf("tick %d phase=%s ninja=%d v=%.3f%n",
                    tick, state, state.ninjaNumber(), neuron.v());
        }
        System.out.println("autonomous run complete — exit 0");
    }

    private AutonomousDriver() {}
}
