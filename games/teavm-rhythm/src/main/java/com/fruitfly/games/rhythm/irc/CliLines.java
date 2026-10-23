package com.fruitfly.games.rhythm.irc;

/**
 * Pure formatting for the TeaVM left CLI (System / Engine / User).
 * No sockets — safe for JVM unit tests.
 *
 * <p>Cosmic Alignment path:
 * {@code UI → ws://127.0.0.1:6669/cli → bridge → irc.abjects.net:6669}.
 */
public final class CliLines {
    public static final String KIND_SYSTEM = "System";
    public static final String KIND_ENGINE = "Engine";
    public static final String KIND_USER = "User";
    /** Traceback / pythonIDE error lines in chat history. */
    public static final String KIND_TRACEBACK = "Traceback";

    /** Contract URL for the loopback CLI (TeaVM must use this, not abjects directly). */
    public static final String LOOPBACK_WS = "ws://127.0.0.1:6669/cli";
    /** Remote IRC label behind the loopback bridge (UI ports slot 6669). */
    public static final String REMOTE_IRC = "irc.abjects.net:6669";

    private CliLines() {
    }

    public static String format(String kind, String body) {
        if (kind == null || kind.isEmpty()) {
            kind = KIND_SYSTEM;
        }
        if (body == null) {
            body = "";
        }
        return "[" + kind + "] " + body;
    }

    /** True only for the Cosmic Alignment loopback CLI URL (127.0.0.1, not 0.0.0.0). */
    public static boolean isLoopbackCliUrl(String url) {
        if (url == null) {
            return false;
        }
        String u = url.trim();
        return u.equals(LOOPBACK_WS)
                || u.startsWith("ws://127.0.0.1:6669/")
                || u.startsWith("ws://[::1]:6669/");
    }

    public static String bootSystemLine() {
        return format(KIND_SYSTEM, "TeaVM CLI → " + LOOPBACK_WS + " → " + REMOTE_IRC);
    }

    public static String pagesHttpsHint() {
        return format(KIND_SYSTEM,
                "Pages HTTPS needs wss + tunnel; local contract is " + LOOPBACK_WS);
    }
}
