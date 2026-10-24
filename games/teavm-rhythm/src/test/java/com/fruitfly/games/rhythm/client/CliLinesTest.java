package com.fruitfly.games.rhythm.client;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fruitfly.games.rhythm.client.transport.IrcBridgeConfig;
import org.junit.jupiter.api.Test;

class CliLinesTest {
    @Test
    void formatTagsSystemEngineUser() {
        assertEquals("[System] hi", CliLines.format(CliLines.KIND_SYSTEM, "hi"));
        assertEquals("[Engine] pong", CliLines.format(CliLines.KIND_ENGINE, "pong"));
        assertEquals("[User] yo", CliLines.format(CliLines.KIND_USER, "yo"));
        assertEquals("[Traceback] boom", CliLines.format(CliLines.KIND_TRACEBACK, "boom"));
    }

    @Test
    void loopbackUrlContract() {
        assertTrue(CliLines.isLoopbackCliUrl(CliLines.LOOPBACK_WS));
        assertTrue(CliLines.isLoopbackCliUrl("ws://127.0.0.1:6680/cli"));
        assertTrue(CliLines.isLoopbackCliUrl("ws://[::1]:6680/cli"));
        assertFalse(CliLines.isLoopbackCliUrl("ws://0.0.0.0:6680/cli"));
        assertFalse(CliLines.isLoopbackCliUrl("ws://irc.abjects.net:6669/cli"));
        assertFalse(CliLines.isLoopbackCliUrl("wss://example.com/cli"));
        // Pages WSS is allowed but is not loopback (Cosmic Alignment).
        assertFalse(CliLines.isLoopbackCliUrl(CliLines.PAGES_WSS));
    }

    @Test
    void allowedCliUrlsOptionB() {
        assertTrue(CliLines.isAllowedCliUrl(CliLines.LOOPBACK_WS));
        assertTrue(CliLines.isAllowedCliUrl("ws://127.0.0.1:6680/cli"));
        assertTrue(CliLines.isAllowedCliUrl("ws://[::1]:6680/cli"));
        assertTrue(CliLines.isAllowedCliUrl(CliLines.PAGES_WSS));
        assertEquals("wss://bridge.axiomiccoreness.com/cli", CliLines.PAGES_WSS);
        assertFalse(CliLines.isAllowedCliUrl("ws://0.0.0.0:6680/cli"));
        assertFalse(CliLines.isAllowedCliUrl("ws://irc.abjects.net:6669/cli"));
        assertFalse(CliLines.isAllowedCliUrl("wss://irc.abjects.net:6669/cli"));
        assertFalse(CliLines.isAllowedCliUrl("wss://example.com/cli"));
        assertFalse(CliLines.isAllowedCliUrl(null));
    }

    @Test
    void resolveCliWsUrlHostnameSwitch() {
        assertEquals(CliLines.LOOPBACK_WS, CliLines.resolveCliWsUrl("127.0.0.1"));
        assertEquals(CliLines.LOOPBACK_WS, CliLines.resolveCliWsUrl("localhost"));
        assertEquals(CliLines.LOOPBACK_WS, CliLines.resolveCliWsUrl("LOCALHOST"));
        assertEquals(CliLines.LOOPBACK_WS, CliLines.resolveCliWsUrl("::1"));
        assertEquals(CliLines.LOOPBACK_WS, CliLines.resolveCliWsUrl("[::1]"));
        // Null / blank → local-first (JVM / headless without browser location).
        assertEquals(CliLines.LOOPBACK_WS, CliLines.resolveCliWsUrl(null));
        assertEquals(CliLines.LOOPBACK_WS, CliLines.resolveCliWsUrl(""));
        assertEquals(CliLines.LOOPBACK_WS, CliLines.resolveCliWsUrl("  "));
        assertEquals(CliLines.PAGES_WSS, CliLines.resolveCliWsUrl("axiomiccoreness.github.io"));
        assertEquals(CliLines.PAGES_WSS, CliLines.resolveCliWsUrl("bridge.axiomiccoreness.com"));
        assertEquals(CliLines.PAGES_WSS, CliLines.resolveCliWsUrl("example.com"));
    }

    @Test
    void pagesHintNamesPagesWss() {
        String hint = CliLines.pagesHttpsHint();
        assertTrue(hint.contains(CliLines.PAGES_WSS));
        assertTrue(hint.contains(CliLines.LOOPBACK_WS));
    }

    @Test
    void remoteLabelIsAbjects6669() {
        assertEquals("irc.abjects.net:6669", CliLines.REMOTE_IRC);
        assertTrue(CliLines.bootSystemLine().contains("127.0.0.1:6680"));
        assertTrue(CliLines.bootSystemLine().contains("irc.abjects.net:6669"));
    }

    @Test
    void bridgeConfigPointsAtLoopback() {
        assertEquals("127.0.0.1", IrcBridgeConfig.LOOPBACK_CLI_HOST);
        assertEquals(6680, IrcBridgeConfig.LOOPBACK_CLI_PORT);
        assertEquals(CliLines.LOOPBACK_WS, IrcBridgeConfig.LOOPBACK_CLI_WS);
    }

    @Test
    void loopbackPortIsNotBrowserRestricted() {
        // Chrome kRestrictedPorts / Firefox gBadPortList: IRC 6665-6669, 6679 (Firefox), 6697.
        int[] unsafe = {6665, 6666, 6667, 6668, 6669, 6679, 6697};
        for (int p : unsafe) {
            assertNotEquals(p, IrcBridgeConfig.LOOPBACK_CLI_PORT);
        }
        assertTrue(CliLines.LOOPBACK_WS.contains(":" + IrcBridgeConfig.LOOPBACK_CLI_PORT + "/"));
        assertFalse(CliLines.isLoopbackCliUrl("ws://127.0.0.1:6669/cli"));
    }
}
