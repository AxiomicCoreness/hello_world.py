// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT

package com.fruitfly.games.rhythm.client.llm;

/**
 * {@code /v3t} chat in the TeaVM CLI: ClarkeYoursaTee-2B-v3t through the authenticated
 * bridge route ({@code sovereign-irc-bridge/src/v3t_route.py}). Single-user: one owner token,
 * shared with the iPhone, kept only in this browser's {@code localStorage}
 * ({@link #TOKEN_KEY}); it is never baked into the build. History is server-side (shared
 * SQLite) and only shown in the chat column, never written into Pages assets.
 *
 * <pre>
 * /v3t &lt;text&gt;        chat (continues the current conversation)
 * /v3t token &lt;tok&gt;   save owner token in localStorage (never echoed)
 * /v3t forget        remove the token from localStorage
 * /v3t history       list shared conversations
 * /v3t open &lt;id&gt;     load a conversation and continue it
 * /v3t new           start a new conversation
 * </pre>
 * Base URL: {@code ?v3t=} override (https://, or http:// loopback), else loopback page →
 * {@link #LOOPBACK_BASE}, else (GitHub Pages) {@link #PAGES_BASE}.
 */
public final class V3tCli {
    public static final String VERB = "/v3t";
    public static final String TOKEN_KEY = "clarkeyoursatee.v3t.ownerToken";
    public static final String LOOPBACK_BASE = "http://127.0.0.1:8087";
    public static final String PAGES_BASE = "https://bridge.axiomiccoreness.com";
    public static final String CHAT_PATH = "/llm/v1/chat/completions";
    public static final String HISTORY_PATH = "/llm/history";

    public enum Kind { CHAT, TOKEN, FORGET, HISTORY, OPEN, NEW, HELP }

    /** Parsed {@code /v3t} line. */
    public static final class Command {
        public final Kind kind;
        public final String arg;

        Command(Kind kind, String arg) {
            this.kind = kind;
            this.arg = arg;
        }
    }

    private V3tCli() {
    }

    public static boolean isV3tLine(String raw) {
        if (raw == null) {
            return false;
        }
        String t = raw.trim().toLowerCase();
        return t.equals(VERB) || t.startsWith(VERB + " ");
    }

    public static Command parse(String raw) {
        String t = raw == null ? "" : raw.trim();
        t = t.length() >= VERB.length() ? t.substring(VERB.length()).trim() : "";
        if (t.isEmpty()) {
            return new Command(Kind.HELP, "");
        }
        int sp = t.indexOf(' ');
        String head = (sp < 0 ? t : t.substring(0, sp)).toLowerCase();
        String rest = sp < 0 ? "" : t.substring(sp + 1).trim();
        switch (head) {
            case "token": return new Command(Kind.TOKEN, rest);
            case "forget": return new Command(Kind.FORGET, "");
            case "history": return new Command(Kind.HISTORY, "");
            case "open": return new Command(Kind.OPEN, rest);
            case "new": return new Command(Kind.NEW, "");
            case "help": return new Command(Kind.HELP, "");
            default: return new Command(Kind.CHAT, t);
        }
    }

    /** True for user lines that must never be echoed into the chat column (they carry the token). */
    public static boolean isSecretLine(String raw) {
        return isV3tLine(raw) && parse(raw).kind == Kind.TOKEN;
    }

    public static boolean validToken(String tok) {
        if (tok == null || !tok.startsWith("cyt_") || tok.length() > 200) {
            return false;
        }
        for (int i = 0; i < tok.length(); i++) {
            char c = tok.charAt(i);
            if (!(Character.isLetterOrDigit(c) || c == '_' || c == '-')) {
                return false;
            }
        }
        return true;
    }

    public static boolean validConversationId(String id) {
        if (id == null || id.isEmpty() || id.length() > 64) {
            return false;
        }
        for (int i = 0; i < id.length(); i++) {
            char c = id.charAt(i);
            if (!(c < 128 && (Character.isLetterOrDigit(c) || c == '_' || c == '-'))) {
                return false;
            }
        }
        return true;
    }

    /** Resolve the route base URL for this page. Never 0.0.0.0; remote must be https. */
    public static String resolveBase(String hostname, String override) {
        if (override != null && !override.trim().isEmpty()) {
            String o = override.trim();
            String lower = o.toLowerCase();
            boolean ok = lower.startsWith("https://")
                    || lower.startsWith("http://127.0.0.1") || lower.startsWith("http://localhost");
            if (ok && !lower.contains("0.0.0.0") && !lower.contains("@") && o.length() < 256) {
                return o.endsWith("/") ? o.substring(0, o.length() - 1) : o;
            }
        }
        String h = hostname == null ? "" : hostname.trim().toLowerCase();
        if (h.isEmpty() || h.equals("127.0.0.1") || h.equals("localhost") || h.equals("::1") || h.equals("[::1]")) {
            return LOOPBACK_BASE;
        }
        return PAGES_BASE;
    }

    /** JSON body for one chat turn (conversation id omitted when null). */
    public static String chatBody(String message, String conversationId) {
        StringBuilder b = new StringBuilder("{\"message\":").append(jsonString(message))
                .append(",\"max_tokens\":512");
        if (conversationId != null && validConversationId(conversationId)) {
            b.append(",\"conversation_id\":").append(jsonString(conversationId));
        }
        return b.append('}').toString();
    }

    static String jsonString(String s) {
        StringBuilder b = new StringBuilder("\"");
        String v = s == null ? "" : s;
        for (int i = 0; i < v.length(); i++) {
            char c = v.charAt(i);
            switch (c) {
                case '"': b.append("\\\""); break;
                case '\\': b.append("\\\\"); break;
                case '\n': b.append("\\n"); break;
                case '\r': b.append("\\r"); break;
                case '\t': b.append("\\t"); break;
                default:
                    if (c < 0x20) {
                        b.append(String.format("\\u%04x", (int) c));
                    } else {
                        b.append(c);
                    }
            }
        }
        return b.append('"').toString();
    }

    public static String helpLine() {
        return "v3t: /v3t <text> · /v3t token <owner token> (kept in this browser only) · /v3t history"
                + " · /v3t open <id> · /v3t new · /v3t forget";
    }
}
