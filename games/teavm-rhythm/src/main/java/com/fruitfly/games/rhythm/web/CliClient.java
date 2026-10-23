package com.fruitfly.games.rhythm.web;

import com.fruitfly.games.rhythm.irc.CliLines;
import com.fruitfly.games.rhythm.irc.IrcBridgeConfig;
import org.teavm.jso.dom.events.Event;
import org.teavm.jso.dom.events.MessageEvent;
import org.teavm.jso.dom.html.HTMLDocument;
import org.teavm.jso.dom.html.HTMLElement;
import org.teavm.jso.dom.html.HTMLInputElement;
import org.teavm.jso.websocket.CloseEvent;
import org.teavm.jso.websocket.WebSocket;

/**
 * Left-column TeaVM CLI. Dials {@link CliLines#LOOPBACK_WS}
 * ({@code ws://127.0.0.1:6669/cli}) only — Cosmic Alignment loopback.
 * Remote IRC {@code irc.abjects.net:6669} is behind the bridge, never a
 * browser-direct socket from Pages.
 *
 * <p>Enter sends; history lines are tagged System / Engine / User.
 */
public final class CliClient {
    private final String wsUrl;
    private HTMLElement history;
    private HTMLInputElement input;
    private WebSocket socket;
    private boolean open;

    public CliClient() {
        this(CliLines.LOOPBACK_WS);
    }

    public CliClient(String wsUrl) {
        if (!CliLines.isLoopbackCliUrl(wsUrl)) {
            throw new IllegalArgumentException(
                    "CliClient requires loopback ws://127.0.0.1:6669/…, got: " + wsUrl);
        }
        this.wsUrl = wsUrl;
    }

    public String wsUrl() {
        return wsUrl;
    }

    public boolean isOpen() {
        return open;
    }

    /**
     * Bind DOM ({@code #cli-column}, {@code #chat-history}, {@code #chat-input})
     * and open the loopback WebSocket. No-op if markup missing.
     */
    public void mount(HTMLDocument doc) {
        HTMLElement col = (HTMLElement) doc.getElementById("cli-column");
        if (col == null) {
            return;
        }
        history = (HTMLElement) doc.getElementById("chat-history");
        HTMLElement raw = (HTMLElement) doc.getElementById("chat-input");
        if (history == null || raw == null) {
            return;
        }
        input = (HTMLInputElement) raw;
        clearAndBoot();
        HTMLElement form = (HTMLElement) doc.getElementById("cli-form");
        if (form != null) {
            form.addEventListener("submit", this::onSubmit);
        }
        input.addEventListener("keydown", evt -> evt.stopPropagation());
        connect();
    }

    private void clearAndBoot() {
        history.setTextContent("");
        appendRaw(CliLines.bootSystemLine());
        appendRaw(CliLines.format(CliLines.KIND_SYSTEM,
                "remote behind bridge: " + CliLines.REMOTE_IRC
                        + " · host " + IrcBridgeConfig.LOOPBACK_CLI_HOST
                        + ":" + IrcBridgeConfig.LOOPBACK_CLI_PORT));
        appendRaw(CliLines.pagesHttpsHint());
    }

    private void connect() {
        if (!WebSocket.isSupported()) {
            append(CliLines.KIND_SYSTEM, "WebSocket unsupported in this browser");
            return;
        }
        append(CliLines.KIND_SYSTEM, "dialing " + wsUrl + " …");
        try {
            socket = WebSocket.create(wsUrl);
        } catch (Throwable t) {
            append(CliLines.KIND_SYSTEM, "dial failed: " + t);
            appendRaw(CliLines.pagesHttpsHint());
            return;
        }
        socket.onOpen(evt -> {
            open = true;
            append(CliLines.KIND_SYSTEM, "connected " + wsUrl);
            append(CliLines.KIND_ENGINE, "loopback up · path → " + CliLines.REMOTE_IRC);
        });
        socket.onMessage(evt -> {
            MessageEvent me = (MessageEvent) evt;
            String data = me.getDataAsString();
            if (data == null) {
                data = String.valueOf(me.getData());
            }
            if (data.startsWith("[") && data.contains("] ")) {
                appendRaw(data);
            } else {
                append(CliLines.KIND_ENGINE, data);
            }
        });
        socket.onError(evt -> {
            open = false;
            append(CliLines.KIND_SYSTEM, "WS error (is loopback bridge on 127.0.0.1:6669?)");
            appendRaw(CliLines.pagesHttpsHint());
        });
        socket.onClose(evt -> {
            open = false;
            CloseEvent ce = (CloseEvent) evt;
            append(CliLines.KIND_SYSTEM,
                    "closed code=" + ce.getCode() + " · " + nullToEmpty(ce.getReason()));
        });
    }

    private static String nullToEmpty(String s) {
        return s == null ? "" : s;
    }

    private void onSubmit(Event evt) {
        evt.preventDefault();
        if (input == null) {
            return;
        }
        String line = input.getValue();
        if (line == null) {
            return;
        }
        line = line.trim();
        input.setValue("");
        if (line.isEmpty()) {
            return;
        }
        sendUser(line);
    }

    /** Append a User line and send over the loopback WS when open. */
    public void sendUser(String text) {
        append(CliLines.KIND_USER, text);
        if (socket != null && open) {
            try {
                socket.send(text);
            } catch (Throwable t) {
                append(CliLines.KIND_SYSTEM, "send failed: " + t);
            }
        } else {
            append(CliLines.KIND_SYSTEM, "not connected — start bridge on 127.0.0.1:6669 (/cli)");
        }
        scrollToEnd();
    }

    public void append(String kind, String body) {
        appendRaw(CliLines.format(kind, body));
    }

    private void appendRaw(String line) {
        if (history == null) {
            return;
        }
        String cur = history.getTextContent();
        if (cur == null || cur.isEmpty()) {
            history.setTextContent(line);
        } else {
            history.setTextContent(cur + "\n" + line);
        }
        scrollToEnd();
    }

    private void scrollToEnd() {
        if (history != null) {
            Dom.scrollTopMax(history);
        }
    }

    /** True when the chat input holds focus (Main skips game keys). */
    public boolean inputFocused() {
        return input != null && Dom.isActive(input);
    }
}
