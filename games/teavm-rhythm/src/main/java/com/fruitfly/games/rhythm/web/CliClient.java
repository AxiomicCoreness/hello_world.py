package com.fruitfly.games.rhythm.web;

import com.fruitfly.games.rhythm.irc.CliLines;
import com.fruitfly.games.rhythm.irc.IrcBridgeConfig;
import com.fruitfly.games.rhythm.irc.PythonIdeCli;
import org.teavm.jso.dom.events.Event;
import org.teavm.jso.dom.events.MessageEvent;
import org.teavm.jso.dom.html.HTMLDocument;
import org.teavm.jso.dom.html.HTMLElement;
import org.teavm.jso.dom.html.HTMLInputElement;
import org.teavm.jso.websocket.CloseEvent;
import org.teavm.jso.websocket.WebSocket;

/**
 * Left-column TeaVM CLI. Option B hostname switch:
 * <ul>
 *   <li>local / CI ({@code 127.0.0.1}, {@code localhost}) → {@link CliLines#LOOPBACK_WS}</li>
 *   <li>GitHub Pages / production → {@link CliLines#PAGES_WSS}
 *       ({@code wss://bridge.axiomiccoreness.com/cli})</li>
 * </ul>
 * Remote IRC {@code irc.abjects.net:6669} stays behind the bridge; the browser
 * never dials abjects or {@code 0.0.0.0} directly.
 *
 * <p>Enter sends; history lines are tagged System / Engine / User / Traceback.
 * Clicking the column focuses {@code #chat-input}; Main skips game keys while
 * a typing target is focused. {@code /py} / {@code /ide} lines hit
 * {@link PythonIdeCli} offline and the bridge toolkit when the socket is open.
 */
public final class CliClient {
    private final String wsUrl;
    private HTMLElement history;
    private HTMLInputElement input;
    private HTMLElement column;
    private WebSocket socket;
    private boolean open;

    /** Resolve dial URL from browser hostname (Option B). */
    public CliClient() {
        this(CliLines.resolveCliWsUrl(Dom.locationHostname()));
    }

    /**
     * Explicit URL ctor. Accepts loopback CLI URLs or exact {@link CliLines#PAGES_WSS}.
     */
    public CliClient(String wsUrl) {
        if (!CliLines.isAllowedCliUrl(wsUrl)) {
            throw new IllegalArgumentException(
                    "CliClient requires loopback ws://127.0.0.1:6669/… or "
                            + CliLines.PAGES_WSS + ", got: " + wsUrl);
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
     * and open the resolved CLI WebSocket (loopback or Pages WSS). No-op if markup missing.
     */
    public void mount(HTMLDocument doc) {
        column = (HTMLElement) doc.getElementById("cli-column");
        if (column == null) {
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
        // Click anywhere in the column focuses the input (history / title / padding).
        column.addEventListener("mousedown", this::onColumnPointer);
        column.addEventListener("click", this::onColumnPointer);
        // Stop bubble so document game handlers never see chat keystrokes.
        // Main ALSO gates on Dom.isTypingTarget() — do not rely on this alone.
        input.addEventListener("keydown", this::onInputKey);
        input.addEventListener("keyup", this::onInputKey);
        input.addEventListener("keypress", this::onInputKey);
        connect();
        // Defer focus so canvas setup does not immediately steal it back.
        Dom.focus(input);
    }

    private void onColumnPointer(Event evt) {
        if (input == null) {
            return;
        }
        // Keep focus on the text field; do not steal from the input itself mid-edit.
        HTMLElement t = (HTMLElement) evt.getTarget();
        if (t != null && input == t) {
            return;
        }
        Dom.focus(input);
    }

    private void onInputKey(Event evt) {
        evt.stopPropagation();
        // Space / letters must reach the input — never preventDefault here.
    }

    private void clearAndBoot() {
        history.setTextContent("");
        appendRaw(CliLines.bootSystemLine());
        appendRaw(CliLines.format(CliLines.KIND_SYSTEM,
                "remote behind bridge: " + CliLines.REMOTE_IRC
                        + " · host " + IrcBridgeConfig.LOOPBACK_CLI_HOST
                        + ":" + IrcBridgeConfig.LOOPBACK_CLI_PORT));
        appendRaw(CliLines.format(CliLines.KIND_SYSTEM,
                "pythonIDE: /py help · /py list · /py call <cap> · /py pointer"));
        appendRaw(CliLines.format(CliLines.KIND_SYSTEM,
                "demos: /py deepinfer · /py katex (KaTeXMacroSetTest) · Traceback on fail"));
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
            append(CliLines.KIND_ENGINE, "pythonIDE live via bridge · /py call <cap>");
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
        evt.stopPropagation();
        if (input == null) {
            return;
        }
        String line = input.getValue();
        if (line == null) {
            return;
        }
        line = line.trim();
        input.setValue("");
        Dom.focus(input); // keep caret in chat after Enter
        if (line.isEmpty()) {
            return;
        }
        sendUser(line);
    }

    /** Append a User line; IDE commands run offline and/or over the loopback WS. */
    public void sendUser(String text) {
        append(CliLines.KIND_USER, text);
        if (PythonIdeCli.isIdeLine(text)) {
            // Live toolkit + full Python traceback when the bridge is up.
            // Offline: local help/list/pointer + traceback-shaped errors (no duplicate).
            if (socket != null && open) {
                try {
                    socket.send(text);
                } catch (Throwable t) {
                    for (String line : PythonIdeCli.formatTraceback(
                            "CliClient.sendUser", "SendError", String.valueOf(t))) {
                        appendRaw(line);
                    }
                }
            } else {
                for (String line : PythonIdeCli.handleOffline(text)) {
                    appendRaw(line);
                }
            }
            scrollToEnd();
            return;
        }
        if (socket != null && open) {
            try {
                socket.send(text);
            } catch (Throwable t) {
                for (String line : PythonIdeCli.formatTraceback(
                        "CliClient.sendUser", "SendError", String.valueOf(t))) {
                    appendRaw(line);
                }
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
        if (Dom.isTypingTarget()) {
            return true;
        }
        return input != null && Dom.isActive(input);
    }

    /** Re-assert focus on the chat input (e.g. after stage button blur). */
    public void focusInput() {
        if (input != null) {
            Dom.focus(input);
        }
    }
}
