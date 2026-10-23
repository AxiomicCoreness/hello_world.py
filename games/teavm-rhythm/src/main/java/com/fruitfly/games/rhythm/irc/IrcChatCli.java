package com.fruitfly.games.rhythm.irc;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Pure-logic IRC chatbox CLI for the TeaVM rhythm page. Scrollback + command
 * parsing only — dials go through {@link IrcBridgeClientStub} (plan / dry-run).
 * Default UI target is {@link IrcBridgeConfig#uiEndpoint(int) uiEndpoint(3)}
 * ({@code irc.abjects.net:6669}). No live sockets; unit tests stay offline.
 */
public final class IrcChatCli {
    /** PORTS_UI index for the chatbox default (6669). */
    public static final int TARGET_SLOT = 3;
    public static final int MAX_LINES = 200;

    private final IrcBridgeClientStub bridge;
    private final List<String> lines = new ArrayList<>();
    private final String target;

    public IrcChatCli() {
        this(new IrcBridgeClientStub());
    }

    public IrcChatCli(IrcBridgeClientStub bridge) {
        if (bridge == null) {
            throw new IllegalArgumentException("bridge required");
        }
        this.bridge = bridge;
        this.target = IrcBridgeConfig.uiEndpoint(TARGET_SLOT);
        bootBanner();
    }

    private void bootBanner() {
        append("TeaVM IRC CLI · " + target);
        append("via " + IrcBridgeConfig.BRIDGE_SERVICE + IrcBridgeConfig.WS_PATH
                + " → mTLS " + IrcBridgeConfig.IRC_HOST + ":" + IrcBridgeConfig.PORT_TLS);
        append("stub mode · no live socket until PEMs · /help");
    }

    public String target() {
        return target;
    }

    public IrcBridgeClientStub bridge() {
        return bridge;
    }

    public List<String> lines() {
        return Collections.unmodifiableList(lines);
    }

    public String statusLine() {
        IrcBridgeClientStub.State s = bridge.state();
        switch (s) {
            case PLANNED:
                return "PLANNED · " + target + " (stub dial)";
            case DRY_RUN_MARKED:
                return "DRY-RUN · " + target;
            case IDLE:
            default:
                return "IDLE · " + target + " · /connect";
        }
    }

    /**
     * Handle one prompt line. Returns the lines appended this call (for DOM
     * paint). Empty / whitespace-only input appends nothing.
     */
    public List<String> handle(String raw) {
        List<String> added = new ArrayList<>();
        if (raw == null) {
            return added;
        }
        String line = raw.trim();
        if (line.isEmpty()) {
            return added;
        }
        if (line.startsWith("/")) {
            handleCommand(line, added);
        } else {
            handleSay(line, added);
        }
        return added;
    }

    private void handleCommand(String line, List<String> added) {
        String[] parts = line.split("\\s+", 2);
        String cmd = parts[0].toLowerCase();
        switch (cmd) {
            case "/help":
            case "/?":
                add(added, "commands: /connect /disconnect /mtls /status /clear /help");
                add(added, "target UI port " + target + " · bridge mTLS :" + IrcBridgeConfig.PORT_TLS);
                add(added, "plain text echoes locally after /connect (no live IRC in CI)");
                break;
            case "/connect":
            case "/join":
                add(added, "> " + line);
                add(added, bridge.planDial());
                add(added, "UI channel → " + target + " (label); live TCP is bridge→:"
                        + IrcBridgeConfig.PORT_TLS);
                break;
            case "/disconnect":
            case "/part":
                add(added, "> " + line);
                bridge.reset();
                add(added, "disconnected (local) · " + target);
                break;
            case "/mtls":
                add(added, "> /mtls");
                MtlsToolCall.Result r = bridge.toolCall("/mtls");
                add(added, r.message());
                for (String echo : r.echoLines()) {
                    add(added, echo);
                }
                break;
            case "/status":
                add(added, "> /status");
                add(added, statusLine());
                add(added, "ws=" + bridge.wsUrl() + " state=" + bridge.state());
                if (bridge.lastPlan() != null) {
                    add(added, bridge.lastPlan());
                }
                break;
            case "/clear":
                lines.clear();
                added.clear();
                bootBanner();
                added.addAll(lines);
                break;
            default:
                add(added, "> " + line);
                add(added, "unknown command · /help");
                break;
        }
    }

    private void handleSay(String text, List<String> added) {
        add(added, "› " + text);
        if (bridge.state() == IrcBridgeClientStub.State.PLANNED) {
            add(added, "[" + target + "] (local echo) " + text);
            add(added, "(stub) not sent — bridge has no live WS in this build");
        } else {
            add(added, "not connected · /connect to plan dial to " + target);
        }
    }

    private void add(List<String> added, String s) {
        append(s);
        added.add(s);
    }

    private void append(String s) {
        lines.add(s);
        while (lines.size() > MAX_LINES) {
            lines.remove(0);
        }
    }
}
