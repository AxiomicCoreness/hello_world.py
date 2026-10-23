package com.fruitfly.games.rhythm.irc;

/**
 * TeaVM-side IRC bridge client <em>stub</em>. Records the intended WebSocket
 * dial to {@link IrcBridgeConfig#BRIDGE_SERVICE} without opening sockets.
 * mTLS to {@link IrcBridgeConfig#IRC_HOST} happens only inside the Python
 * bridge after PEMs mount — this class never loads certs.
 */
public final class IrcBridgeClientStub {
    public enum State {
        IDLE,
        PLANNED,
        /** Set only by tests / explicit mark; never implies a live socket. */
        DRY_RUN_MARKED
    }

    private final String wsUrl;
    private State state = State.IDLE;
    private String lastPlan;

    public IrcBridgeClientStub() {
        this(IrcBridgeConfig.defaultWsUrl());
    }

    public IrcBridgeClientStub(String wsUrl) {
        if (wsUrl == null || wsUrl.isEmpty()) {
            throw new IllegalArgumentException("wsUrl required");
        }
        this.wsUrl = wsUrl;
    }

    public String wsUrl() {
        return wsUrl;
    }

    public State state() {
        return state;
    }

    public String lastPlan() {
        return lastPlan;
    }

    /**
     * Plan a bridge dial. Does not connect. Returns a one-line plan including
     * host {@link IrcBridgeConfig#IRC_HOST} and mTLS port.
     */
    public String planDial() {
        lastPlan = "PLAN ws=" + wsUrl
                + " → " + IrcBridgeConfig.BRIDGE_SERVICE
                + " → mTLS " + IrcBridgeConfig.IRC_HOST + ":" + IrcBridgeConfig.PORT_TLS
                + " (no live dial; certs via " + IrcBridgeConfig.ENV_CERT + ")";
        state = State.PLANNED;
        return lastPlan;
    }

    /** Return to IDLE and clear the last plan (local disconnect). */
    public void reset() {
        state = State.IDLE;
        lastPlan = null;
    }

    /** Mark dry-run without connecting (CI / unit tests). */
    public void markDryRun() {
        state = State.DRY_RUN_MARKED;
    }

    /** Dispatch a debug-oracle-style tool; currently {@code /mtls} only. */
    public MtlsToolCall.Result toolCall(String op) {
        if (!MtlsToolCall.matches(op)) {
            throw new IllegalArgumentException("unsupported tool: " + op);
        }
        return MtlsToolCall.invoke();
    }
}
