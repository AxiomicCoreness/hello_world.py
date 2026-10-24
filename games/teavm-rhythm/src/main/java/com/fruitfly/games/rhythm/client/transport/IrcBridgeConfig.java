package com.fruitfly.games.rhythm.client.transport;

import com.fruitfly.games.rhythm.client.CliLines;

/**
 * TeaVM → IRC bridge constants. Browser TeaVM never dials IRC TCP directly;
 * it talks WebSocket to {@link #BRIDGE_SERVICE} {@link #WS_PATH}, and the
 * Python {@code sovereign-irc-bridge} performs mTLS TCP to
 * {@link #IRC_HOST}:{@link #PORT_TLS}.
 *
 * <p>UI channel labels remain {@link #PORTS_UI} (6666–6669) — display only;
 * no live sockets in CI / debug-oracle panel.
 */
public final class IrcBridgeConfig {
    public static final String IRC_HOST = "irc.abjects.net";
    public static final String BRIDGE_SERVICE = "sovereign-irc-bridge";
    public static final String WS_PATH = "/ws";
    public static final String HEALTH_PATH = "/health";
    /** Live mTLS IRC port (bridge outbound). */
    public static final int PORT_TLS = 6697;
    /** Debug-oracle UI channel labels only. */
    public static final int[] PORTS_UI = {6666, 6667, 6668, 6669};
    /** Cosmic Alignment: TeaVM dials loopback only; bridge may reach PORTS_UI[3]. */
    public static final String LOOPBACK_CLI_WS = CliLines.LOOPBACK_WS;
    public static final int LOOPBACK_CLI_PORT = 6680;
    public static final String LOOPBACK_CLI_HOST = "127.0.0.1";

    /** Env / PEM path names expected by the bridge (not shipped in git). */
    public static final String ENV_CERT = "IRC__MTLS_CERT_PATH";
    public static final String ENV_KEY = "IRC__MTLS_KEY_PATH";
    public static final String ENV_CA = "IRC__MTLS_CA_PATH";

    private IrcBridgeConfig() {
    }

    /** UI label for channel slot {@code n} (wraps 0..3). */
    public static String uiEndpoint(int n) {
        int port = PORTS_UI[Math.floorMod(n, PORTS_UI.length)];
        return IRC_HOST + ":" + port;
    }

    /** Default bridge WebSocket URL when serving on localhost. */
    public static String defaultWsUrl() {
        return "ws://127.0.0.1:8080" + WS_PATH;
    }
}
