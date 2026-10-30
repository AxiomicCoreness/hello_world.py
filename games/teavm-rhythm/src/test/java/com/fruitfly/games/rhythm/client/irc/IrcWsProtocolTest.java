// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT

package com.fruitfly.games.rhythm.client.irc;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fruitfly.games.rhythm.client.CliLines;
import java.util.Arrays;
import java.util.List;
import org.junit.jupiter.api.Test;

/** Offline: parsing, sanitizing and URL-param resolution for direct IRC-over-WebSocket. */
class IrcWsProtocolTest {

    @Test
    void defaultsAreLiberaChannelAndGuestNick() {
        IrcWsProtocol.Config c = IrcWsProtocol.resolve(null, null, null, "48151");
        assertTrue(c.enabled());
        assertEquals("wss://web.libera.chat/webirc/websocket/", c.url);
        assertEquals("#axiomiccoreness", c.channel);
        assertEquals("Guest48151", c.nick);
        assertTrue(c.notes.isEmpty());
        assertEquals("Guest00000", IrcWsProtocol.guestNick(null));
    }

    @Test
    void urlParamsOverrideEverything() {
        IrcWsProtocol.Config c = IrcWsProtocol.resolve(
                "wss://irc.example.org:8097/", "tutor", "Clarke_T", "1");
        assertEquals("wss://irc.example.org:8097/", c.url);
        assertEquals("#tutor", c.channel);
        assertEquals("Clarke_T", c.nick);
        assertFalse(IrcWsProtocol.resolve("off", null, null, "1").enabled());
        assertFalse(IrcWsProtocol.resolve("OFF", null, null, "1").enabled());
    }

    @Test
    void badOverridesFallBackWithNotes() {
        IrcWsProtocol.Config c = IrcWsProtocol.resolve(
                "javascript:alert(1)", "#bad chan", "9lives", "12345");
        assertEquals(IrcWsProtocol.DEFAULT_URL, c.url);
        assertEquals(IrcWsProtocol.DEFAULT_CHANNEL, c.channel);
        assertEquals("Guest12345", c.nick);
        assertEquals(3, c.notes.size());
    }

    @Test
    void urlValidation() {
        assertTrue(IrcWsProtocol.isValidIrcWsUrl("wss://web.libera.chat/webirc/websocket/"));
        assertTrue(IrcWsProtocol.isValidIrcWsUrl("wss://irc.abjects.net:6680/"));
        assertTrue(IrcWsProtocol.isValidIrcWsUrl("ws://127.0.0.1:8067/"));
        assertFalse(IrcWsProtocol.isValidIrcWsUrl("ws://irc.example.org:8000/"), "plain ws only to loopback");
        assertFalse(IrcWsProtocol.isValidIrcWsUrl("wss://0.0.0.0:443/"));
        assertFalse(IrcWsProtocol.isValidIrcWsUrl("wss://user:pw@host/"));
        assertFalse(IrcWsProtocol.isValidIrcWsUrl("wss://host:99x/"));
        assertFalse(IrcWsProtocol.isValidIrcWsUrl("wss://host/\r\nQUIT"));
        assertFalse(IrcWsProtocol.isValidIrcWsUrl("https://web.libera.chat/"));
        assertFalse(IrcWsProtocol.isValidIrcWsUrl(""));
        assertFalse(IrcWsProtocol.isValidIrcWsUrl(null));
    }

    @Test
    void nickAndChannelValidation() {
        assertTrue(IrcWsProtocol.isValidNick("Guest12345"));
        assertTrue(IrcWsProtocol.isValidNick("[tea]`_^{|}-9"));
        assertFalse(IrcWsProtocol.isValidNick("9abc"));
        assertFalse(IrcWsProtocol.isValidNick("-abc"));
        assertFalse(IrcWsProtocol.isValidNick("has space"));
        assertFalse(IrcWsProtocol.isValidNick("a\r\nQUIT"));
        assertFalse(IrcWsProtocol.isValidNick("abcdefghijklmnopq"));
        assertTrue(IrcWsProtocol.isValidChannel("#axiomiccoreness"));
        assertTrue(IrcWsProtocol.isValidChannel("##chat"));
        assertFalse(IrcWsProtocol.isValidChannel("#a,#b"));
        assertFalse(IrcWsProtocol.isValidChannel("#a\u0007"));
        assertFalse(IrcWsProtocol.isValidChannel("#"));
        assertFalse(IrcWsProtocol.isValidChannel("nochan"));
    }

    @Test
    void outboundLinesCannotInjectCommands() {
        String line = IrcWsProtocol.privmsgLine("#axiomiccoreness", "hi\r\nQUIT :pwned\u0000x");
        assertEquals("PRIVMSG #axiomiccoreness :hi  QUIT :pwned x", line);
        assertFalse(line.contains("\r") || line.contains("\n") || line.contains("\u0000"));
        assertEquals("NICK a_b", IrcWsProtocol.nickLine("a\nb"));
        assertEquals("JOIN #x__JOIN_#y", IrcWsProtocol.joinLine("#x\r\nJOIN #y"));
        assertEquals("PONG :tok", IrcWsProtocol.pongLine("tok"));
        assertEquals("USER Guest1 0 * :" + IrcWsProtocol.REALNAME, IrcWsProtocol.userLine("Guest1"));
        StringBuilder big = new StringBuilder();
        for (int i = 0; i < 1000; i++) {
            big.append('x');
        }
        assertEquals(IrcWsProtocol.MAX_TEXT, IrcWsProtocol.clean(big.toString()).length());
    }

    @Test
    void parsesTagsPrefixParamsTrailing() {
        IrcWsProtocol.Message m = IrcWsProtocol.parse(
                "@time=2026-10-30T19:10:00.000Z :tea!~t@user/tea PRIVMSG #axiomiccoreness :hello :) there\r\n");
        assertEquals("time=2026-10-30T19:10:00.000Z", m.tags);
        assertEquals("tea!~t@user/tea", m.prefix);
        assertEquals("tea", m.nick());
        assertEquals("PRIVMSG", m.command);
        assertEquals(Arrays.asList("#axiomiccoreness", "hello :) there"), m.params);
        IrcWsProtocol.Message ping = IrcWsProtocol.parse("PING :lithium.libera.chat");
        assertEquals("PING", ping.command);
        assertEquals("lithium.libera.chat", ping.last());
        IrcWsProtocol.Message num = IrcWsProtocol.parse(":srv 001 Guest1 :Welcome to the Libera.Chat Internet Relay Chat Network Guest1");
        assertEquals("001", num.command);
        assertEquals("Guest1", num.param(0));
        assertEquals("srv", num.nick());
        assertEquals("", num.param(9));
        IrcWsProtocol.Message bare = IrcWsProtocol.parse("join #x");
        assertEquals("JOIN", bare.command);
        assertNull(IrcWsProtocol.parse(""));
        assertNull(IrcWsProtocol.parse(":onlyprefix"));
        assertNull(IrcWsProtocol.parse(null));
    }

    @Test
    void splitsFramesAndStripsFormatting() {
        List<String> lines = IrcWsProtocol.splitFrame("PING :a\r\n:s 001 n :hi\n\r\n");
        assertEquals(Arrays.asList("PING :a", ":s 001 n :hi"), lines);
        assertEquals("bold red plain", IrcWsProtocol.stripFormatting("\u0002bold\u0002 \u000304,01red\u000f plain"));
        assertEquals("apples", IrcWsProtocol.stripFormatting("\u00035apples"), "colour digits are consumed");
        assertEquals("ok", IrcWsProtocol.stripFormatting("\u0003ok\u0016\u001d\u001f"));
        assertEquals("", IrcWsProtocol.stripFormatting(null));
    }

    @Test
    void modeChoiceKeepsBridgePathsWorking() {
        IrcWsProtocol.Config on = IrcWsProtocol.resolve(null, null, null, "1");
        IrcWsProtocol.Config off = IrcWsProtocol.resolve("off", null, null, "1");
        String q = CliLines.BridgeResolution.SOURCE_QUERY;
        String meta = CliLines.BridgeResolution.SOURCE_META;
        String loop = CliLines.BridgeResolution.SOURCE_LOOPBACK;
        String none = CliLines.BridgeResolution.SOURCE_NONE;
        // GitHub Pages, no overrides → direct IRC.
        assertTrue(IrcWsProtocol.useDirect(none, false, null, on));
        // ?irc=off → old "remote bridge not configured".
        assertFalse(IrcWsProtocol.useDirect(none, false, "off", off));
        // ?bridge= / meta → existing /llm bridge path, even with ?irc=.
        assertFalse(IrcWsProtocol.useDirect(q, true, null, on));
        assertFalse(IrcWsProtocol.useDirect(meta, true, "wss://x/", on));
        // Loopback page → bridge unless ?irc= is explicit.
        assertFalse(IrcWsProtocol.useDirect(loop, true, null, on));
        assertTrue(IrcWsProtocol.useDirect(loop, true, "wss://web.libera.chat/webirc/websocket/", on));
        assertFalse(IrcWsProtocol.useDirect(none, false, null, null));
    }
}
