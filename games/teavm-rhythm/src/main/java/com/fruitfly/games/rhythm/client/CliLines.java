package com.fruitfly.games.rhythm.client;

/**
 * Pure formatting for the TeaVM left CLI (System / Engine / User).
 * No sockets — safe for JVM unit tests.
 *
 * <p>Cosmic Alignment — CLI bridge URL resolution, in order
 * ({@link #resolveBridge}):
 * <ol>
 *   <li>explicit override: {@code ?bridge=} query param, else
 *       {@code <meta name="cli-bridge" content="...">}. Only {@code ws://} / {@code wss://}
 *       URLs are accepted; anything else is rejected (logged once) and ignored.</li>
 *   <li>loopback page ({@code 127.0.0.1}, {@code localhost}, {@code ::1}) or {@code file:}:
 *       {@code UI → ws://127.0.0.1:6680/cli → bridge → irc.abjects.net:6669}</li>
 *   <li>any other page with no override: stay disconnected and say so
 *       ({@link #REMOTE_NOT_CONFIGURED}). No remote domain is hardcoded.</li>
 * </ol>
 * Browser never dials abjects or {@code 0.0.0.0} directly.
 */
public final class CliLines {
    public static final String KIND_SYSTEM = "System";
    public static final String KIND_ENGINE = "Engine";
    public static final String KIND_USER = "User";
    /** Traceback / pythonIDE error lines in chat history. */
    public static final String KIND_TRACEBACK = "Traceback";

    /** Contract URL for the loopback CLI (TeaVM local/CI; never 0.0.0.0). */
    public static final String LOOPBACK_WS = "ws://127.0.0.1:6680/cli";
    /** Query param carrying an explicit bridge URL, e.g. {@code ?bridge=wss://host/cli}. */
    public static final String BRIDGE_QUERY_PARAM = "bridge";
    /** {@code <meta name="cli-bridge" content="wss://host/cli">} in index.html. */
    public static final String BRIDGE_META_NAME = "cli-bridge";
    /** One-line chat message when a remote page has no bridge override. */
    public static final String REMOTE_NOT_CONFIGURED =
            "remote bridge not configured \u2013 set ?bridge=wss://\u2026";
    /** Upper bound on an override URL (defensive; real bridge URLs are short). */
    static final int MAX_BRIDGE_URL_LENGTH = 512;
    /** Remote IRC label behind the bridge (UI ports slot 6669). */
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

    /** Outcome of {@link #resolveBridge}: a URL to dial, or null to stay disconnected. */
    public static final class BridgeResolution {
        public static final String SOURCE_QUERY = "query";
        public static final String SOURCE_META = "meta";
        public static final String SOURCE_LOOPBACK = "loopback";
        public static final String SOURCE_NONE = "none";

        /** URL to dial, or {@code null} (disconnected). */
        public final String url;
        /** One of the {@code SOURCE_*} constants. */
        public final String source;
        /** Human-readable reason an override was rejected, or {@code null}. */
        public final String rejected;
        /** Mixed-content warning (https page → non-loopback ws://), or {@code null}. */
        public final String warning;

        BridgeResolution(String url, String source, String rejected, String warning) {
            this.url = url;
            this.source = source;
            this.rejected = rejected;
            this.warning = warning;
        }

        public boolean connects() {
            return url != null;
        }
    }

    /**
     * Resolve the CLI WebSocket URL for a page.
     *
     * @param protocol      {@code window.location.protocol} (e.g. {@code "https:"}, {@code "file:"}); may be null
     * @param hostname      {@code window.location.hostname}; may be null
     * @param queryOverride value of {@code ?bridge=}; null/blank = absent
     * @param metaOverride  content of {@code <meta name="cli-bridge">}; null/blank = absent
     */
    public static BridgeResolution resolveBridge(String protocol, String hostname,
            String queryOverride, String metaOverride) {
        String rejected = null;
        String[][] overrides = {
            {BridgeResolution.SOURCE_QUERY, queryOverride},
            {BridgeResolution.SOURCE_META, metaOverride},
        };
        for (String[] o : overrides) {
            String raw = o[1];
            if (raw == null || raw.trim().isEmpty()) {
                continue;
            }
            String u = raw.trim();
            if (isValidBridgeOverride(u)) {
                return new BridgeResolution(u, o[0], rejected, mixedContentWarning(protocol, u));
            }
            if (rejected == null) {
                rejected = "ignored " + o[0] + " bridge override (need ws:// or wss://): "
                        + abbreviate(u);
            }
        }
        if (isLoopbackPage(protocol, hostname)) {
            return new BridgeResolution(LOOPBACK_WS, BridgeResolution.SOURCE_LOOPBACK, rejected, null);
        }
        return new BridgeResolution(null, BridgeResolution.SOURCE_NONE, rejected, null);
    }

    /** Hostname-only convenience: loopback/blank → {@link #LOOPBACK_WS}; anything else → null. */
    public static String resolveCliWsUrl(String hostname) {
        return resolveBridge(null, hostname, null, null).url;
    }

    /**
     * Loopback page: host {@code 127.0.0.1} / {@code localhost} / {@code ::1}, or {@code file:}.
     * Null / blank host (JVM tests, headless smoke without a browser location) counts as local.
     */
    public static boolean isLoopbackPage(String protocol, String hostname) {
        if (protocol != null && protocol.trim().toLowerCase().equals("file:")) {
            return true;
        }
        if (hostname == null) {
            return true;
        }
        String h = hostname.trim().toLowerCase();
        return h.isEmpty() || isLoopbackHost(h);
    }

    private static boolean isLoopbackHost(String h) {
        return h.equals("127.0.0.1")
                || h.equals("localhost")
                || h.equals("::1")
                || h.equals("[::1]");
    }

    /**
     * Accept only {@code ws://host[:port][/path]} or {@code wss://...}. Rejects other schemes
     * ({@code javascript:}, {@code http:}, ...), empty hosts, credentials ({@code user@}),
     * whitespace/control chars, {@code 0.0.0.0}, and direct {@code abjects.net} (IRC stays
     * behind the bridge).
     */
    public static boolean isValidBridgeOverride(String url) {
        if (url == null) {
            return false;
        }
        String u = url.trim();
        if (u.isEmpty() || u.length() > MAX_BRIDGE_URL_LENGTH) {
            return false;
        }
        for (int i = 0; i < u.length(); i++) {
            char c = u.charAt(i);
            if (c <= 0x20 || c == 0x7f || c == '\\' || c == '"' || c == '<' || c == '>') {
                return false;
            }
        }
        String lower = u.toLowerCase();
        int rest;
        if (lower.startsWith("ws://")) {
            rest = 5;
        } else if (lower.startsWith("wss://")) {
            rest = 6;
        } else {
            return false;
        }
        String host = authorityHost(lower.substring(rest));
        if (host == null || host.isEmpty()) {
            return false;
        }
        if (host.equals("0.0.0.0") || host.equals("[::]")) {
            return false;
        }
        if (host.equals("abjects.net") || host.endsWith(".abjects.net")) {
            return false;
        }
        return true;
    }

    /** Host part of {@code authority[/path]}; null when malformed or carrying userinfo. */
    private static String authorityHost(String afterScheme) {
        int end = afterScheme.length();
        for (int i = 0; i < afterScheme.length(); i++) {
            char c = afterScheme.charAt(i);
            if (c == '/' || c == '?' || c == '#') {
                end = i;
                break;
            }
        }
        String authority = afterScheme.substring(0, end);
        if (authority.indexOf('@') >= 0) {
            return null;
        }
        if (authority.startsWith("[")) {
            int close = authority.indexOf(']');
            if (close < 0) {
                return null;
            }
            String tail = authority.substring(close + 1);
            if (!tail.isEmpty() && !isPortSuffix(tail)) {
                return null;
            }
            return authority.substring(0, close + 1);
        }
        int colon = authority.indexOf(':');
        if (colon >= 0) {
            if (!isPortSuffix(authority.substring(colon))) {
                return null;
            }
            return authority.substring(0, colon);
        }
        return authority;
    }

    private static boolean isPortSuffix(String s) {
        if (s.length() < 2 || s.length() > 6 || s.charAt(0) != ':') {
            return false;
        }
        for (int i = 1; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c < '0' || c > '9') {
                return false;
            }
        }
        return true;
    }

    /** Browsers block {@code ws://} to non-loopback hosts from an https page (mixed content). */
    static String mixedContentWarning(String protocol, String url) {
        if (protocol == null || !protocol.trim().toLowerCase().equals("https:")) {
            return null;
        }
        if (!url.toLowerCase().startsWith("ws://") || isLoopbackCliUrl(url)) {
            return null;
        }
        String host = authorityHost(url.toLowerCase().substring(5));
        if (host != null && isLoopbackHost(host)) {
            return null;
        }
        return "ws:// bridge from an https page is blocked as mixed content \u2013 use wss://";
    }

    private static String abbreviate(String s) {
        return s.length() <= 80 ? s : s.substring(0, 77) + "...";
    }

    /** True only for the Cosmic Alignment loopback CLI URL (127.0.0.1 / ::1, not 0.0.0.0). */
    public static boolean isLoopbackCliUrl(String url) {
        if (url == null) {
            return false;
        }
        String u = url.trim();
        return u.equals(LOOPBACK_WS)
                || u.startsWith("ws://127.0.0.1:6680/")
                || u.startsWith("ws://[::1]:6680/");
    }

    /**
     * Allowed dial targets: loopback CLI URLs <strong>or</strong> a valid explicit
     * {@code ws://}/{@code wss://} override ({@link #isValidBridgeOverride}).
     * Rejects {@code ws://0.0.0.0…}, direct abjects, and non-WebSocket schemes.
     */
    public static boolean isAllowedCliUrl(String url) {
        if (url == null) {
            return false;
        }
        String u = url.trim();
        return isLoopbackCliUrl(u) || isValidBridgeOverride(u);
    }

    public static String bootSystemLine() {
        return format(KIND_SYSTEM, "TeaVM CLI → " + LOOPBACK_WS + " → " + REMOTE_IRC);
    }

    /** Boot hint: how remote pages pick a bridge (vs the local loopback contract). */
    public static String pagesHttpsHint() {
        return format(KIND_SYSTEM,
                "remote pages: ?" + BRIDGE_QUERY_PARAM + "=wss://\u2026 or <meta name=\""
                        + BRIDGE_META_NAME + "\">; local/CI dials " + LOOPBACK_WS);
    }
}
