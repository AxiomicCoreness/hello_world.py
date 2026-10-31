// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT

package com.fruitfly.games.rhythm.client.irc;

import com.fruitfly.games.rhythm.client.CliLines;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Socket-free state machine for the chatbox's direct IRC-over-WebSocket mode.
 * {@code CliClient} feeds it socket events and user lines; it returns the IRC
 * lines to send (one per WebSocket frame) and the chat-history lines to show.
 *
 * <ul>
 *   <li>open → {@code NICK} + {@code USER}</li>
 *   <li>{@code 001} → {@code JOIN <channel>}; {@code 433} nick in use → retry with a suffix</li>
 *   <li>{@code PING} → {@code PONG} (same token)</li>
 *   <li>{@code PRIVMSG}/{@code NOTICE}/{@code JOIN}/{@code PART}/{@code QUIT}/{@code NICK}/{@code KICK},
 *       topic, names and join-error numerics → history lines tagged {@code [IRC]}</li>
 *   <li>user text → {@code PRIVMSG <channel>}; {@code /me}, {@code /nick}, {@code /join},
 *       {@code /msg}, {@code /names}, {@code /quit}; {@code /llm <text>} goes to the channel
 *       for the IRC LLM bot. No raw-line passthrough.</li>
 * </ul>
 */
public final class IrcWsSession {
    public static final String KIND_IRC = "IRC";
    static final int MAX_NICK_RETRIES = 5;

    /** Lines to send and lines to display for one event. */
    public static final class Step {
        public final List<String> send;
        public final List<String> show;

        Step(List<String> send, List<String> show) {
            this.send = Collections.unmodifiableList(send);
            this.show = Collections.unmodifiableList(show);
        }
    }

    private final IrcWsProtocol.Config config;
    private String nick;
    private String channel;
    private boolean registered;
    private boolean joined;
    private int nickRetries;

    public IrcWsSession(IrcWsProtocol.Config config) {
        if (config == null || !config.enabled()) {
            throw new IllegalArgumentException("IrcWsSession needs an enabled Config");
        }
        this.config = config;
        this.nick = config.nick;
        this.channel = config.channel;
    }

    public String nick() {
        return nick;
    }

    public String channel() {
        return channel;
    }

    public boolean registered() {
        return registered;
    }

    public boolean joined() {
        return joined;
    }

    public String url() {
        return config.url;
    }

    /** Socket opened: register. */
    public Step onOpen() {
        List<String> send = new ArrayList<>();
        List<String> show = new ArrayList<>();
        send.add(IrcWsProtocol.nickLine(nick));
        send.add(IrcWsProtocol.userLine(nick));
        show.add(sys("connected " + config.url + " · registering as " + nick));
        return new Step(send, show);
    }

    /** Socket closed / errored: drop state (caller decides on reconnect). */
    public void onClosed() {
        registered = false;
        joined = false;
    }

    /** One WebSocket text frame from the server. */
    public Step onFrame(String frame) {
        List<String> send = new ArrayList<>();
        List<String> show = new ArrayList<>();
        for (String line : IrcWsProtocol.splitFrame(frame)) {
            handle(IrcWsProtocol.parse(line), send, show);
        }
        return new Step(send, show);
    }

    private void handle(IrcWsProtocol.Message m, List<String> send, List<String> show) {
        if (m == null) {
            return;
        }
        String cmd = m.command;
        switch (cmd) {
            case "PING":
                send.add(IrcWsProtocol.pongLine(m.last()));
                return;
            case "001":
                registered = true;
                if (!m.param(0).isEmpty()) {
                    nick = m.param(0);
                }
                show.add(sys("welcome · " + IrcWsProtocol.stripFormatting(m.last())));
                send.add(IrcWsProtocol.joinLine(channel));
                show.add(sys("joining " + channel + " …"));
                return;
            case "433": // ERR_NICKNAMEINUSE
            case "432": // ERR_ERRONEUSNICKNAME
                if (!registered && nickRetries < MAX_NICK_RETRIES) {
                    nickRetries++;
                    String base = nick.length() >= IrcWsProtocol.MAX_NICK ? nick.substring(0, IrcWsProtocol.MAX_NICK - 1) : nick;
                    nick = cmd.equals("432") ? IrcWsProtocol.guestNick(String.valueOf(10000 + nickRetries * 7919))
                            : base + "_";
                    show.add(sys("nick unavailable · trying " + nick));
                    send.add(IrcWsProtocol.nickLine(nick));
                } else {
                    show.add(sys(cmd + " " + IrcWsProtocol.stripFormatting(m.last())));
                }
                return;
            case "PRIVMSG":
            case "NOTICE":
                showMessage(m, show);
                return;
            case "JOIN": {
                String ch = m.param(0);
                if (m.nick().equalsIgnoreCase(nick)) {
                    joined = true;
                    channel = ch;
                    show.add(sys("joined " + ch + " as " + nick + " · type to chat · /llm <text> asks the bot"));
                } else {
                    show.add(irc("→ " + m.nick() + " joined " + ch));
                }
                return;
            }
            case "PART":
                if (m.nick().equalsIgnoreCase(nick) && m.param(0).equalsIgnoreCase(channel)) {
                    joined = false;
                }
                show.add(irc("← " + m.nick() + " left " + m.param(0)));
                return;
            case "QUIT":
                show.add(irc("← " + m.nick() + " quit (" + IrcWsProtocol.stripFormatting(m.last()) + ")"));
                return;
            case "NICK":
                if (m.nick().equalsIgnoreCase(nick)) {
                    nick = m.last();
                }
                show.add(irc(m.nick() + " is now " + m.last()));
                return;
            case "KICK":
                if (m.param(1).equalsIgnoreCase(nick)) {
                    joined = false;
                }
                show.add(irc(m.param(1) + " was kicked from " + m.param(0) + " by " + m.nick()
                        + " (" + IrcWsProtocol.stripFormatting(m.last()) + ")"));
                return;
            case "332": // RPL_TOPIC
                show.add(irc("topic " + m.param(1) + ": " + IrcWsProtocol.stripFormatting(m.last())));
                return;
            case "353": // RPL_NAMREPLY
                show.add(irc("users " + m.param(2) + ": " + m.last()));
                return;
            case "403": case "404": case "405": case "471": case "473": case "474":
            case "475": case "477": case "489": case "520":
                // join / send refused (e.g. 477: channel needs a registered nick)
                show.add(sys(cmd + " " + m.param(1) + ": " + IrcWsProtocol.stripFormatting(m.last())));
                return;
            case "ERROR":
                show.add(sys("server ERROR: " + IrcWsProtocol.stripFormatting(m.last())));
                return;
            default:
                // Other numerics (MOTD, ISUPPORT, …) stay out of the chat history.
                return;
        }
    }

    private void showMessage(IrcWsProtocol.Message m, List<String> show) {
        String target = m.param(0);
        String text = m.last();
        String from = m.nick();
        boolean notice = "NOTICE".equals(m.command);
        if (!notice && text.length() > 1 && text.charAt(0) == 0x01) {
            String ctcp = text.substring(1, text.endsWith("\u0001") ? text.length() - 1 : text.length());
            if (ctcp.startsWith("ACTION ")) {
                show.add(irc(where(target) + "* " + from + " " + IrcWsProtocol.stripFormatting(ctcp.substring(7))));
            }
            return; // other CTCP (VERSION, …) ignored
        }
        String body = IrcWsProtocol.stripFormatting(text);
        if (notice) {
            show.add(irc(where(target) + "-" + from + "- " + body));
        } else {
            show.add(irc(where(target) + "<" + from + "> " + body));
        }
    }

    /** Prefix for messages not in the current channel (PMs / other channels). */
    private String where(String target) {
        if (target == null || target.isEmpty() || target.equalsIgnoreCase(channel)) {
            return "";
        }
        if (target.equalsIgnoreCase(nick) || target.equals("*")) {
            return "(private) ";
        }
        return "(" + target + ") ";
    }

    /** One line typed in the chatbox. */
    public Step onUser(String raw) {
        List<String> send = new ArrayList<>();
        List<String> show = new ArrayList<>();
        String text = IrcWsProtocol.clean(raw);
        if (text.isEmpty()) {
            return new Step(send, show);
        }
        if (!registered) {
            show.add(sys("not on IRC yet — still connecting to " + config.url));
            return new Step(send, show);
        }
        String lower = text.toLowerCase();
        if (lower.equals(IrcWsProtocol.LLM_TRIGGER) || lower.startsWith(IrcWsProtocol.LLM_TRIGGER + " ")) {
            sendToChannel(text, send, show);
        } else if (lower.startsWith("/me ")) {
            String act = text.substring(4).trim();
            send.add(IrcWsProtocol.actionLine(channel, act));
            show.add(irc("* " + nick + " " + act));
        } else if (lower.startsWith("/nick ")) {
            String n = text.substring(6).trim();
            if (IrcWsProtocol.isValidNick(n)) {
                send.add(IrcWsProtocol.nickLine(n));
            } else {
                show.add(sys("invalid nick: " + n));
            }
        } else if (lower.startsWith("/join ")) {
            String c = text.substring(6).trim();
            if (!c.startsWith("#") && !c.startsWith("&")) {
                c = "#" + c;
            }
            if (IrcWsProtocol.isValidChannel(c)) {
                channel = c;
                send.add(IrcWsProtocol.joinLine(c));
            } else {
                show.add(sys("invalid channel: " + c));
            }
        } else if (lower.startsWith("/msg ")) {
            String rest = text.substring(5).trim();
            int sp = rest.indexOf(' ');
            if (sp <= 0) {
                show.add(sys("usage: /msg <nick> <text>"));
            } else {
                String to = rest.substring(0, sp);
                String body = rest.substring(sp + 1).trim();
                if (IrcWsProtocol.isValidNick(to) || IrcWsProtocol.isValidChannel(to)) {
                    send.add(IrcWsProtocol.privmsgLine(to, body));
                    show.add(irc("(to " + to + ") <" + nick + "> " + body));
                } else {
                    show.add(sys("invalid target: " + to));
                }
            }
        } else if (lower.equals("/names")) {
            send.add("NAMES " + channel);
        } else if (lower.equals("/quit") || lower.startsWith("/quit ")) {
            String why = text.length() > 5 ? text.substring(5).trim() : "";
            send.add(IrcWsProtocol.quitLine(why.isEmpty() ? "leaving" : why));
        } else if (lower.equals("/irc") || lower.equals("/help")) {
            show.add(sys(helpLine()));
        } else if (text.startsWith("/")) {
            show.add(sys("unknown IRC command (no raw lines): " + text.split(" ")[0] + " · " + helpLine()));
        } else {
            sendToChannel(text, send, show);
        }
        return new Step(send, show);
    }

    private void sendToChannel(String text, List<String> send, List<String> show) {
        if (!joined) {
            show.add(sys("not in " + channel + " yet"));
            return;
        }
        send.add(IrcWsProtocol.privmsgLine(channel, text));
        show.add(irc("<" + nick + "> " + IrcWsProtocol.clean(text)));
    }

    public static String helpLine() {
        return "irc: text → channel · /llm <text> (bot) · /me · /nick · /join · /msg · /names · /quit · /py stays local";
    }

    private static String sys(String body) {
        return CliLines.format(CliLines.KIND_SYSTEM, body);
    }

    private static String irc(String body) {
        return CliLines.format(KIND_IRC, body);
    }
}
