// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT

package com.fruitfly.games.rhythm.client.irc;

import com.fruitfly.games.rhythm.client.CliLines;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Pure-logic IRC-over-WebSocket client for the TeaVM left chatbox (direct mode).
 *
 * <p>A static page (GitHub Pages) cannot open raw TCP, so the browser dials an
 * IRC network's own WebSocket gateway. Default: the abjects network's browser
 * gateway {@link #DEFAULT_URL} (live-probed from GitHub runners with the Pages
 * Origin: HTTP 101 + 001 welcome), channel
 * {@link #DEFAULT_CHANNEL}, nick {@code Guest<5 digits>}. Every default is
 * overridable from the page URL: {@code ?irc=wss://…&channel=#…&nick=…};
 * {@code ?irc=off} disables direct mode.
 *
 * <p>One IRC line per WebSocket text frame (IRCv3 WebSocket / webircgateway
 * convention); inbound frames are still split on CR/LF defensively. Every
 * outbound line is built here and passes {@link #clean} so user text can never
 * inject CR / LF / NUL (a second IRC command). No sockets — JVM unit tests stay
 * offline ({@code IrcWsProtocolTest}).
 */
public final class IrcWsProtocol {
    /** abjects IRC network's browser WebSocket gateway (the network the bridge already uses). */
    public static final String DEFAULT_URL = "wss://irc.abjects.net:6680/";
    public static final String DEFAULT_NETWORK = "abjects";
    /**
     * Libera.Chat's gateway (from web.libera.chat/gamja/config.json). Still selectable with
     * {@code ?irc=}; not the default because its Cloudflare front answered 403 to GitHub-runner probes.
     */
    public static final String LIBERA_URL = "wss://web.libera.chat/webirc/websocket/";
    public static final String DEFAULT_CHANNEL = "#axiomiccoreness";
    public static final String NICK_PREFIX = "Guest";
    public static final String QUERY_URL = "irc";
    public static final String QUERY_CHANNEL = "channel";
    public static final String QUERY_NICK = "nick";
    /** {@code ?irc=off} keeps the chatbox off IRC (old "remote bridge not configured"). */
    public static final String OFF = "off";
    /** In-channel trigger the IRC LLM bot answers ({@code /llm <text>}). */
    public static final String LLM_TRIGGER = "/llm";
    public static final String REALNAME = "AxiomicCoreness TeaVM rhythm page (web guest)";
    /** IRC lines are 512 bytes incl. CRLF; keep text well under after the prefix. */
    public static final int MAX_TEXT = 400;
    public static final int MAX_NICK = 16;
    public static final int MAX_CHANNEL = 50;
    static final int MAX_URL = 512;
    /** CTCP delimiter (0x01). */
    static final char CTCP = (char) 1;

    private IrcWsProtocol() {
    }

    // ------------------------------------------------------------------ config

    /** Resolved direct-IRC settings for one page load. */
    public static final class Config {
        /** wss:// URL to dial, or null when direct mode is off. */
        public final String url;
        public final String channel;
        public final String nick;
        /** Notes about rejected overrides (shown once in the chatbox). */
        public final List<String> notes;

        Config(String url, String channel, String nick, List<String> notes) {
            this.url = url;
            this.channel = channel;
            this.nick = nick;
            this.notes = Collections.unmodifiableList(notes);
        }

        public boolean enabled() {
            return url != null;
        }
    }

    /**
     * Resolve direct-IRC settings from page query params.
     *
     * @param urlParam     {@code ?irc=}; blank → {@link #DEFAULT_URL}; {@code off} → disabled
     * @param channelParam {@code ?channel=}; blank/invalid → {@link #DEFAULT_CHANNEL}
     * @param nickParam    {@code ?nick=}; blank/invalid → {@code Guest<digits>}
     * @param digits       random digits for the guest nick (caller supplies; tests fix it)
     */
    public static Config resolve(String urlParam, String channelParam, String nickParam, String digits) {
        List<String> notes = new ArrayList<>();
        String url = DEFAULT_URL;
        if (urlParam != null && !urlParam.trim().isEmpty()) {
            String u = urlParam.trim();
            if (u.equalsIgnoreCase(OFF)) {
                url = null;
            } else if (isValidIrcWsUrl(u)) {
                url = u;
            } else {
                notes.add("ignored ?" + QUERY_URL + "= (need wss://host[:port][/path]): " + abbreviate(u));
            }
        }
        String channel = DEFAULT_CHANNEL;
        if (channelParam != null && !channelParam.trim().isEmpty()) {
            String c = channelParam.trim();
            if (!c.startsWith("#") && !c.startsWith("&")) {
                c = "#" + c; // ?channel=foo → #foo (URL fragments can't carry a bare #)
            }
            if (isValidChannel(c)) {
                channel = c;
            } else {
                notes.add("ignored ?" + QUERY_CHANNEL + "= (invalid channel): " + abbreviate(channelParam.trim()));
            }
        }
        String nick = guestNick(digits);
        if (nickParam != null && !nickParam.trim().isEmpty()) {
            String n = nickParam.trim();
            if (isValidNick(n)) {
                nick = n;
            } else {
                notes.add("ignored ?" + QUERY_NICK + "= (invalid nick): " + abbreviate(n));
            }
        }
        return new Config(url, channel, nick, notes);
    }

    /**
     * Mode choice for the chatbox. An explicit bridge override ({@code ?bridge=} / meta,
     * {@code bridgeSource} "query" / "meta") keeps the bridge; an explicit {@code ?irc=}
     * then wins over the loopback default; otherwise direct IRC only when no bridge URL
     * resolved (remote pages such as GitHub Pages). Disabled config → never direct.
     */
    public static boolean useDirect(String bridgeSource, boolean bridgeHasUrl, String ircParam, Config c) {
        if (c == null || !c.enabled()) {
            return false;
        }
        if (CliLines.BridgeResolution.SOURCE_QUERY.equals(bridgeSource)
                || CliLines.BridgeResolution.SOURCE_META.equals(bridgeSource)) {
            return false;
        }
        boolean explicitIrc = ircParam != null && !ircParam.trim().isEmpty();
        return explicitIrc || !bridgeHasUrl;
    }

    public static String guestNick(String digits) {
        StringBuilder d = new StringBuilder();
        if (digits != null) {
            for (int i = 0; i < digits.length() && d.length() < 5; i++) {
                char c = digits.charAt(i);
                if (c >= '0' && c <= '9') {
                    d.append(c);
                }
            }
        }
        while (d.length() < 5) {
            d.append('0');
        }
        return NICK_PREFIX + d;
    }

    /**
     * {@code wss://host[:port][/path]} only, plus {@code ws://} to loopback for local
     * gateways. Rejects other schemes, userinfo, whitespace/control/quote chars and
     * {@code 0.0.0.0}.
     */
    public static boolean isValidIrcWsUrl(String url) {
        if (url == null) {
            return false;
        }
        String u = url.trim();
        if (u.isEmpty() || u.length() > MAX_URL) {
            return false;
        }
        for (int i = 0; i < u.length(); i++) {
            char c = u.charAt(i);
            if (c <= 0x20 || c == 0x7f || c == '\\' || c == '"' || c == '\'' || c == '<' || c == '>') {
                return false;
            }
        }
        String lower = u.toLowerCase();
        boolean secure;
        String rest;
        if (lower.startsWith("wss://")) {
            secure = true;
            rest = lower.substring(6);
        } else if (lower.startsWith("ws://")) {
            secure = false;
            rest = lower.substring(5);
        } else {
            return false;
        }
        int end = rest.length();
        for (int i = 0; i < rest.length(); i++) {
            char c = rest.charAt(i);
            if (c == '/' || c == '?' || c == '#') {
                end = i;
                break;
            }
        }
        String authority = rest.substring(0, end);
        if (authority.isEmpty() || authority.indexOf('@') >= 0) {
            return false;
        }
        String host;
        if (authority.startsWith("[")) {
            int close = authority.indexOf(']');
            if (close < 0 || !portOk(authority.substring(close + 1))) {
                return false;
            }
            host = authority.substring(0, close + 1);
        } else {
            int colon = authority.indexOf(':');
            if (colon >= 0) {
                if (!portOk(authority.substring(colon))) {
                    return false;
                }
                host = authority.substring(0, colon);
            } else {
                host = authority;
            }
        }
        if (host.isEmpty() || host.equals("0.0.0.0") || host.equals("[::]")) {
            return false;
        }
        boolean loopback = host.equals("127.0.0.1") || host.equals("localhost") || host.equals("[::1]");
        return secure || loopback;
    }

    private static boolean portOk(String s) {
        if (s.isEmpty()) {
            return true;
        }
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

    /** RFC 2812 nick chars; first char a letter or special; max {@link #MAX_NICK}. */
    public static boolean isValidNick(String n) {
        if (n == null || n.isEmpty() || n.length() > MAX_NICK) {
            return false;
        }
        for (int i = 0; i < n.length(); i++) {
            char c = n.charAt(i);
            boolean letter = (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z');
            boolean special = "[]\\`_^{|}".indexOf(c) >= 0;
            boolean tail = (c >= '0' && c <= '9') || c == '-';
            if (!(letter || special || (i > 0 && tail))) {
                return false;
            }
        }
        return true;
    }

    /** {@code #name} / {@code &name}; no space, comma, BEL, CR, LF, NUL; max {@link #MAX_CHANNEL}. */
    public static boolean isValidChannel(String c) {
        if (c == null || c.length() < 2 || c.length() > MAX_CHANNEL) {
            return false;
        }
        if (c.charAt(0) != '#' && c.charAt(0) != '&') {
            return false;
        }
        for (int i = 1; i < c.length(); i++) {
            char ch = c.charAt(i);
            if (ch <= 0x20 || ch == ',' || ch == 0x7f || ch == ':') {
                return false;
            }
        }
        return true;
    }

    /** One-line, injection-safe text: CR / LF / NUL → space, trimmed, capped. */
    public static String clean(String s) {
        if (s == null) {
            return "";
        }
        StringBuilder b = new StringBuilder(s.length());
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            b.append(c == '\r' || c == '\n' || c == '\0' ? ' ' : c);
        }
        // Trim spaces/tabs only: String.trim() would also eat the CTCP 0x01 delimiters.
        int st = 0;
        int en = b.length();
        while (st < en && (b.charAt(st) == ' ' || b.charAt(st) == '\t')) {
            st++;
        }
        while (en > st && (b.charAt(en - 1) == ' ' || b.charAt(en - 1) == '\t')) {
            en--;
        }
        String t = b.substring(st, en);
        return t.length() <= MAX_TEXT ? t : t.substring(0, MAX_TEXT);
    }

    /** Remove mIRC formatting (bold, colour, reverse, italic, underline, ...) for display. */
    public static String stripFormatting(String s) {
        if (s == null) {
            return "";
        }
        StringBuilder b = new StringBuilder(s.length());
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c == 0x03) { // colour: \x03[fg[,bg]]
                int j = i + 1;
                int n = 0;
                while (j < s.length() && n < 2 && Character.isDigit(s.charAt(j))) {
                    j++;
                    n++;
                }
                if (n > 0 && j + 1 < s.length() && s.charAt(j) == ',' && Character.isDigit(s.charAt(j + 1))) {
                    j++;
                    n = 0;
                    while (j < s.length() && n < 2 && Character.isDigit(s.charAt(j))) {
                        j++;
                        n++;
                    }
                }
                i = j - 1;
                continue;
            }
            if (c == 0x02 || c == 0x0f || c == 0x11 || c == 0x16 || c == 0x1d || c == 0x1e
                    || c == 0x1f || c == 0x01) {
                continue;
            }
            if (c < 0x20 && c != '\t') {
                continue;
            }
            b.append(c);
        }
        return b.toString();
    }

    // ------------------------------------------------------------------ outbound builders

    public static String nickLine(String nick) {
        return "NICK " + clean(nick).replace(' ', '_');
    }

    public static String userLine(String nick) {
        return "USER " + clean(nick).replace(' ', '_') + " 0 * :" + REALNAME;
    }

    public static String joinLine(String channel) {
        return "JOIN " + clean(channel).replace(' ', '_');
    }

    public static String privmsgLine(String target, String text) {
        return "PRIVMSG " + clean(target).replace(' ', '_') + " :" + clean(text);
    }

    public static String actionLine(String target, String text) {
        // StringBuilder, not '+': javac's indy string concat recipe uses 0x01 as its
        // argument marker, which TeaVM 0.10's StringConcatFactory substitutor misreads.
        StringBuilder b = new StringBuilder();
        b.append(CTCP).append("ACTION ").append(clean(text)).append(CTCP);
        return privmsgLine(target, b.toString());
    }

    public static String pongLine(String token) {
        return "PONG :" + clean(token);
    }

    public static String quitLine(String reason) {
        return "QUIT :" + clean(reason);
    }

    // ------------------------------------------------------------------ parsing

    /** One parsed IRC line: {@code [@tags] [:prefix] COMMAND params… [:trailing]}. */
    public static final class Message {
        public final String tags;
        public final String prefix;
        public final String command;
        /** Middle params and the trailing param (last), in order. */
        public final List<String> params;

        Message(String tags, String prefix, String command, List<String> params) {
            this.tags = tags;
            this.prefix = prefix;
            this.command = command;
            this.params = Collections.unmodifiableList(params);
        }

        /** Nick part of the prefix ({@code nick!user@host} → nick), or the server name. */
        public String nick() {
            if (prefix == null) {
                return "";
            }
            int bang = prefix.indexOf('!');
            return bang >= 0 ? prefix.substring(0, bang) : prefix;
        }

        public String param(int i) {
            return i >= 0 && i < params.size() ? params.get(i) : "";
        }

        public String last() {
            return params.isEmpty() ? "" : params.get(params.size() - 1);
        }
    }

    /** Parse one line (CR/LF stripped); null for blank or command-less input. */
    public static Message parse(String raw) {
        if (raw == null) {
            return null;
        }
        String s = raw;
        while (s.endsWith("\r") || s.endsWith("\n")) {
            s = s.substring(0, s.length() - 1);
        }
        int i = 0;
        int n = s.length();
        String tags = null;
        String prefix = null;
        if (i < n && s.charAt(i) == '@') {
            int sp = s.indexOf(' ', i);
            if (sp < 0) {
                return null;
            }
            tags = s.substring(i + 1, sp);
            i = skipSpaces(s, sp);
        }
        if (i < n && s.charAt(i) == ':') {
            int sp = s.indexOf(' ', i);
            if (sp < 0) {
                return null;
            }
            prefix = s.substring(i + 1, sp);
            i = skipSpaces(s, sp);
        }
        int sp = s.indexOf(' ', i);
        String command = sp < 0 ? s.substring(i) : s.substring(i, sp);
        if (command.isEmpty()) {
            return null;
        }
        List<String> params = new ArrayList<>();
        i = sp < 0 ? n : skipSpaces(s, sp);
        while (i < n) {
            if (s.charAt(i) == ':') {
                params.add(s.substring(i + 1));
                break;
            }
            int next = s.indexOf(' ', i);
            if (next < 0) {
                params.add(s.substring(i));
                break;
            }
            params.add(s.substring(i, next));
            i = skipSpaces(s, next);
        }
        return new Message(tags, prefix, command.toUpperCase(), params);
    }

    private static int skipSpaces(String s, int i) {
        while (i < s.length() && s.charAt(i) == ' ') {
            i++;
        }
        return i;
    }

    /** Split one WebSocket frame into IRC lines (frames are normally one line each). */
    public static List<String> splitFrame(String frame) {
        List<String> out = new ArrayList<>();
        if (frame == null) {
            return out;
        }
        int start = 0;
        for (int i = 0; i <= frame.length(); i++) {
            if (i == frame.length() || frame.charAt(i) == '\n' || frame.charAt(i) == '\r') {
                if (i > start) {
                    out.add(frame.substring(start, i));
                }
                start = i + 1;
            }
        }
        return out;
    }

    private static String abbreviate(String s) {
        String one = clean(s);
        return one.length() <= 60 ? one : one.substring(0, 57) + "...";
    }
}
