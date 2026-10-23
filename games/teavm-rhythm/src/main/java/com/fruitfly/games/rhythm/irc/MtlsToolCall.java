package com.fruitfly.games.rhythm.irc;

/**
 * Java-side {@code /mtls} tool call for TeaVM debug-oracle / rhythm clients.
 * Pure logic: builds the same summary lines the panel echoes — no sockets,
 * no PEM I/O. Live dial is the bridge's job once certs mount.
 */
public final class MtlsToolCall {
    public static final String COMMAND = "/mtls";

    private MtlsToolCall() {
    }

    /** Whether {@code op} is the mtls tool (with or without leading slash). */
    public static boolean matches(String op) {
        if (op == null) {
            return false;
        }
        String s = op.trim().toLowerCase();
        return s.equals("mtls") || s.equals("/mtls");
    }

    /**
     * Result of invoking {@code /mtls}. {@link #channel()} is the TLS endpoint
     * label; {@link #message()} is the hex-chat body; {@link #echoLines()} are
     * the prompt-bar echoes (host / tls port / ui ports / ws).
     */
    public static final class Result {
        private final String channel;
        private final String message;
        private final String[] echoLines;

        Result(String channel, String message, String[] echoLines) {
            this.channel = channel;
            this.message = message;
            this.echoLines = echoLines;
        }

        public String channel() {
            return channel;
        }

        public String message() {
            return message;
        }

        public String[] echoLines() {
            return echoLines.clone();
        }
    }

    /** Invoke {@code /mtls} using {@link IrcBridgeConfig} defaults. */
    public static Result invoke() {
        String host = IrcBridgeConfig.IRC_HOST;
        int tls = IrcBridgeConfig.PORT_TLS;
        StringBuilder ui = new StringBuilder();
        for (int i = 0; i < IrcBridgeConfig.PORTS_UI.length; i++) {
            if (i > 0) {
                ui.append(',');
            }
            ui.append(IrcBridgeConfig.PORTS_UI[i]);
        }
        String channel = host + ":" + tls;
        String message = "mTLS host " + host
                + " · UI ports " + ui
                + " · bridge " + IrcBridgeConfig.BRIDGE_SERVICE
                + " " + IrcBridgeConfig.WS_PATH
                + " · fail-fast without certs";
        String[] echo = {
            "mtls host    →  " + host,
            "tls port     →  " + tls,
            "ui ports     →  " + ui.toString().replace(',', ' '),
            "ws           →  " + IrcBridgeConfig.WS_PATH + " (no live dial in CI)",
        };
        return new Result(channel, message, echo);
    }
}
