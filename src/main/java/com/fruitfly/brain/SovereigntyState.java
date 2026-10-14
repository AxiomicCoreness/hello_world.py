package com.fruitfly.brain;

public enum SovereigntyState {
    OBSERVATION(144),
    RESONANCE(233),
    HARMONIZATION(377),
    SYNTHESIS(610),
    INTEGRATION(987),
    PERPETUATION(1597),
    TRANSCENDENCE(2584),
    DARK_STATE(1);

    private final int ninjaNumber;

    SovereigntyState(int ninjaNumber) { this.ninjaNumber = ninjaNumber; }

    public int ninjaNumber() { return ninjaNumber; }

    public boolean isAbsorbing() { return this == DARK_STATE; }

    public SovereigntyState next() {
        if (isAbsorbing()) return DARK_STATE;
        SovereigntyState[] values = values();
        int idx = ordinal();
        return (idx + 1 < values.length) ? values[idx + 1] : DARK_STATE;
    }
}
