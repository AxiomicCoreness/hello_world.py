// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT

package com.fruitfly.games.rhythm.client.transport;

import com.fruitfly.games.rhythm.client.CliLines;
import com.fruitfly.games.rhythm.client.ide.PythonIdeCli;
import com.fruitfly.games.rhythm.client.ide.TracebackFeedback;
import com.fruitfly.games.rhythm.client.irc.IrcWsProtocol;
import com.fruitfly.games.rhythm.client.irc.IrcWsSession;
import com.fruitfly.games.rhythm.client.llm.LlmCli;
import com.fruitfly.games.rhythm.web.Dom;
import java.util.Collections;
import java.util.function.Supplier;
import org.teavm.jso.dom.events.Event;
import org.teavm.jso.dom.events.MessageEvent;
import org.teavm.jso.dom.html.HTMLDocument;
import org.teavm.jso.dom.html.HTMLElement;
import org.teavm.jso.dom.html.HTMLInputElement;
import org.teavm.jso.websocket.CloseEvent;
import org.teavm.jso.websocket.WebSocket;

/**
 * Left-column TeaVM CLI. Bridge URL ({@link CliLines#resolveBridge}), in order:
 * <ol>
 *   <li>{@code ?bridge=ws(s)://…} or {@code <meta name="cli-bridge" content="ws(s)://…">}</li>
 *   <li>loopback page / {@code file:} → {@link CliLines#LOOPBACK_WS}</li>
 *   <li>otherwise (e.g. GitHub Pages) <b>direct IRC-over-WebSocket</b> via
 *       {@link IrcWsSession}: default {@link IrcWsProtocol#DEFAULT_URL} (abjects),
 *       {@link IrcWsProtocol#DEFAULT_CHANNEL}, nick {@code Guest<digits>}; overridable by
 *       {@code ?irc=wss://…&channel=…&nick=…}. An explicit {@code ?irc=} also wins over the
 *       loopback default; {@code ?irc=off} restores {@link CliLines#REMOTE_NOT_CONFIGURED}.</li>
 * </ol>
 * In bridge mode remote IRC {@code irc.abjects.net:6669} stays behind the bridge. In direct
 * mode the browser speaks IRC to the network's own wss:// gateway (never {@code 0.0.0.0}).
 *
 * <p>Enter sends; history lines are tagged System / Engine / User / Traceback.
 * Clicking the column focuses {@code #chat-input}; Main skips game keys while
 * a typing target is focused. {@code /py} / {@code /ide} lines hit
 * {@link PythonIdeCli} offline and the bridge toolkit when the socket is open.
 */
public final class CliClient {
    /** Resolved dial URL, or null when no bridge is configured (stay disconnected). */
    private final String wsUrl;
    /** Rejected-override / mixed-content notes, printed once at boot (may be null). */
    private final String rejectedNote;
    private final String warningNote;
    private HTMLElement history;
    private HTMLInputElement input;
    private HTMLElement column;
    private WebSocket socket;
    private boolean open;
    /** Recent traceback reports — the /llm feedback signal. */
    private final TracebackFeedback feedback = new TracebackFeedback();
    /** Live neuron snapshot JSON from Main (null until wired). */
    private Supplier<String> neuronSnapshot;
    /** Direct IRC-over-WebSocket mode (null = bridge mode). */
    private final IrcWsSession irc;
    private final java.util.List<String> ircNotes;

    /** Resolve dial URL from the page: ?bridge= / meta override, loopback, else none. */
    public CliClient() {
        this(CliLines.resolveBridge(
                Dom.locationProtocol(),
                Dom.locationHostname(),
                Dom.locationQueryParam(CliLines.BRIDGE_QUERY_PARAM),
                Dom.metaContent(CliLines.BRIDGE_META_NAME)),
                Dom.locationQueryParam(IrcWsProtocol.QUERY_URL),
                IrcWsProtocol.resolve(
                        Dom.locationQueryParam(IrcWsProtocol.QUERY_URL),
                        Dom.locationQueryParam(IrcWsProtocol.QUERY_CHANNEL),
                        Dom.locationQueryParam(IrcWsProtocol.QUERY_NICK),
                        String.valueOf(10000 + (int) (Math.random() * 90000))));
    }

    private CliClient(CliLines.BridgeResolution r, String ircParam, IrcWsProtocol.Config c) {
        boolean direct = IrcWsProtocol.useDirect(r.source, r.url != null, ircParam, c);
        this.wsUrl = direct ? null : r.url;
        this.rejectedNote = r.rejected;
        this.warningNote = direct ? null : r.warning;
        this.irc = direct ? new IrcWsSession(c) : null;
        this.ircNotes = c == null ? java.util.Collections.<String>emptyList() : c.notes;
        if (r.rejected != null) {
            Dom.log("[CliClient] " + r.rejected);
        }
    }

    /**
     * Explicit URL ctor. Accepts loopback CLI URLs or a valid ws:// / wss:// override.
     */
    public CliClient(String wsUrl) {
        if (!CliLines.isAllowedCliUrl(wsUrl)) {
            throw new IllegalArgumentException(
                    "CliClient requires loopback ws://127.0.0.1:6680/… or a ws:// / wss:// "
                            + "bridge URL, got: " + wsUrl);
        }
        this.wsUrl = wsUrl.trim();
        this.rejectedNote = null;
        this.warningNote = null;
        this.irc = null;
        this.ircNotes = java.util.Collections.<String>emptyList();
    }

    /** Bridge dial URL, or null when no bridge is configured (or in direct IRC mode). */
    public String wsUrl() {
        return wsUrl;
    }

    /** True when the chatbox speaks IRC directly over the network's wss:// gateway. */
    public boolean directIrc() {
        return irc != null;
    }

    /** Main wires the live LIF-RK4 spike snapshot used by {@code /llm}. */
    public void setNeuronSnapshot(Supplier<String> supplier) {
        this.neuronSnapshot = supplier;
    }

    public boolean isOpen() {
        return open;
    }

    /**
     * Bind DOM ({@code #cli-column}, {@code #chat-history}, {@code #chat-input})
     * and open the resolved CLI WebSocket (override or loopback; none → stay disconnected).
     * No-op if markup missing.
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
        if (irc != null) {
            HTMLElement title = (HTMLElement) doc.querySelector(".cli-title");
            if (title != null) {
                title.setTextContent("CLI \u00b7 IRC " + irc.channel() + " \u00b7 /llm \u00b7 /py");
            }
        }
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
        if (irc != null) {
            appendRaw(CliLines.format(CliLines.KIND_SYSTEM, "TeaVM CLI → IRC " + irc.url()
                    + " · " + irc.channel() + " · nick " + irc.nick()));
            appendRaw(CliLines.format(CliLines.KIND_SYSTEM,
                    "override: ?irc=wss://…&channel=…&nick=… · ?irc=off · ?bridge=wss://…/cli for the bridge"));
            appendRaw(CliLines.format(CliLines.KIND_SYSTEM, IrcWsSession.helpLine()));
            appendRaw(CliLines.format(CliLines.KIND_SYSTEM,
                    "pythonIDE: /py help · /py list · /py pointer (offline in IRC mode)"));
            return;
        }
        appendRaw(CliLines.bootSystemLine());
        appendRaw(CliLines.format(CliLines.KIND_SYSTEM,
                "remote behind bridge: " + CliLines.REMOTE_IRC
                        + " · host " + IrcBridgeConfig.LOOPBACK_CLI_HOST
                        + ":" + IrcBridgeConfig.LOOPBACK_CLI_PORT));
        appendRaw(CliLines.format(CliLines.KIND_SYSTEM,
                "pythonIDE: /py help · /py list · /py call <cap> · /py pointer"));
        appendRaw(CliLines.format(CliLines.KIND_SYSTEM,
                "demos: /py deepinfer · /py katex (KaTeXMacroSetTest) · Traceback on fail"));
        appendRaw(LlmCli.helpLine());
        appendRaw(CliLines.pagesHttpsHint());
    }

    private void connect() {
        if (rejectedNote != null) {
            append(CliLines.KIND_SYSTEM, rejectedNote);
        }
        for (String note : ircNotes) {
            append(CliLines.KIND_SYSTEM, note);
        }
        if (irc != null) {
            connectIrc();
            return;
        }
        if (wsUrl == null) {
            append(CliLines.KIND_SYSTEM, CliLines.REMOTE_NOT_CONFIGURED);
            return;
        }
        if (warningNote != null) {
            append(CliLines.KIND_SYSTEM, warningNote);
        }
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
            append(CliLines.KIND_ENGINE, (CliLines.isLoopbackCliUrl(wsUrl) ? "loopback" : "bridge")
                    + " up · path → " + CliLines.REMOTE_IRC);
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
            append(CliLines.KIND_SYSTEM, CliLines.isLoopbackCliUrl(wsUrl)
                    ? "WS error (is loopback bridge on 127.0.0.1:6680?)"
                    : "WS error (is the bridge at " + wsUrl + " up?)");
            appendRaw(CliLines.pagesHttpsHint());
        });
        socket.onClose(evt -> {
            open = false;
            CloseEvent ce = (CloseEvent) evt;
            append(CliLines.KIND_SYSTEM,
                    "closed code=" + ce.getCode() + " · " + nullToEmpty(ce.getReason()));
        });
    }

    /** Direct mode: dial the IRC network's wss:// gateway and run {@link IrcWsSession}. */
    private void connectIrc() {
        if (!WebSocket.isSupported()) {
            append(CliLines.KIND_SYSTEM, "WebSocket unsupported in this browser");
            return;
        }
        append(CliLines.KIND_SYSTEM, "dialing " + irc.url() + " …");
        try {
            socket = WebSocket.create(irc.url());
        } catch (Throwable t) {
            append(CliLines.KIND_SYSTEM, "dial failed: " + t);
            return;
        }
        final WebSocket mine = socket;
        socket.onOpen(evt -> {
            open = true;
            apply(irc.onOpen());
        });
        socket.onMessage(evt -> {
            MessageEvent me = (MessageEvent) evt;
            String data = me.getDataAsString();
            if (data == null) {
                data = String.valueOf(me.getData());
            }
            apply(irc.onFrame(data));
        });
        socket.onError(evt -> {
            append(CliLines.KIND_SYSTEM, "IRC WebSocket error (" + irc.url()
                    + ") · /reconnect to retry · or try ?irc=wss://…");
        });
        socket.onClose(evt -> {
            if (socket != mine) {
                return;
            }
            open = false;
            irc.onClosed();
            CloseEvent ce = (CloseEvent) evt;
            append(CliLines.KIND_SYSTEM, "IRC closed code=" + ce.getCode() + " · "
                    + nullToEmpty(ce.getReason()) + " · /reconnect to dial again");
        });
    }

    private void apply(IrcWsSession.Step step) {
        if (socket != null && open) {
            for (String line : step.send) {
                try {
                    socket.send(line);
                } catch (Throwable t) {
                    append(CliLines.KIND_SYSTEM, "IRC send failed: " + t);
                    break;
                }
            }
        }
        for (String line : step.show) {
            appendRaw(line);
        }
    }

    /** Direct-mode user line: /py stays local, /reconnect redials, the rest goes to IRC. */
    private void sendIrcUser(String text) {
        if (PythonIdeCli.isIdeLine(text)) {
            for (String line : PythonIdeCli.handleOffline(text)) {
                appendRaw(line);
            }
            return;
        }
        if (text.trim().equalsIgnoreCase("/reconnect")) {
            if (socket != null && open) {
                append(CliLines.KIND_SYSTEM, "already connected to " + irc.url());
                return;
            }
            connectIrc();
            return;
        }
        if (socket == null || !open) {
            append(CliLines.KIND_SYSTEM, "not connected to " + irc.url() + " · /reconnect");
            return;
        }
        apply(irc.onUser(text));
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
        if (irc != null) {
            // Chat / IRC commands echo as [IRC] lines from the session; echo local-only ones here.
            if (PythonIdeCli.isIdeLine(text) || text.trim().equalsIgnoreCase("/reconnect")) {
                append(CliLines.KIND_USER, text);
            }
            sendIrcUser(text);
            scrollToEnd();
            return;
        }
        append(CliLines.KIND_USER, text);
        if (LlmCli.isLlmLine(text)) {
            sendLlm(text);
            scrollToEnd();
            return;
        }
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
            append(CliLines.KIND_SYSTEM, wsUrl == null
                    ? CliLines.REMOTE_NOT_CONFIGURED
                    : CliLines.isLoopbackCliUrl(wsUrl)
                            ? "not connected — start bridge on 127.0.0.1:6680 (/cli)"
                            : "not connected — bridge " + wsUrl + " is not open");
        }
        scrollToEnd();
    }

    /** /llm: prompt + live spike snapshot + traceback feedback → bridge → llama-server. */
    private void sendLlm(String text) {
        if (socket == null || !open) {
            appendRaw(LlmCli.offlineLine());
            return;
        }
        String neuro = null;
        if (neuronSnapshot != null) {
            try {
                neuro = neuronSnapshot.get();
            } catch (Throwable t) {
                feedback.add("SnapshotError", String.valueOf(t),
                        Collections.singletonList("CliClient.sendLlm"), "teavm");
            }
        }
        String wire = LlmCli.wire(text, neuro, feedback.toJson());
        try {
            socket.send(wire);
            append(CliLines.KIND_SYSTEM, "llm → bridge (" + (neuro == null ? "no" : "with")
                    + " neuron snapshot, " + feedback.size() + " traceback report(s))");
        } catch (Throwable t) {
            for (String line : PythonIdeCli.formatTraceback(
                    "CliClient.sendLlm", "SendError", String.valueOf(t))) {
                appendRaw(line);
            }
        }
    }

    public void append(String kind, String body) {
        appendRaw(CliLines.format(kind, body));
    }

    private void appendRaw(String line) {
        feedback.accept(line);
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
