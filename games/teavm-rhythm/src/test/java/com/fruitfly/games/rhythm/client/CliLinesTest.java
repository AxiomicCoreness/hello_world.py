package com.fruitfly.games.rhythm.client;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
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
    }

    @Test
    void allowedCliUrls() {
        assertTrue(CliLines.isAllowedCliUrl(CliLines.LOOPBACK_WS));
        assertTrue(CliLines.isAllowedCliUrl("ws://127.0.0.1:6680/cli"));
        assertTrue(CliLines.isAllowedCliUrl("ws://[::1]:6680/cli"));
        assertTrue(CliLines.isAllowedCliUrl("wss://example.com/cli"));
        assertFalse(CliLines.isAllowedCliUrl("ws://0.0.0.0:6680/cli"));
        assertFalse(CliLines.isAllowedCliUrl("ws://irc.abjects.net:6669/cli"));
        assertFalse(CliLines.isAllowedCliUrl("wss://irc.abjects.net:6669/cli"));
        assertFalse(CliLines.isAllowedCliUrl("https://example.com/cli"));
        assertFalse(CliLines.isAllowedCliUrl(null));
    }

    @Test
    void noDeadBridgeDomainAnywhereInResolution() {
        // axiomiccoreness.com is NXDOMAIN: nothing may resolve to it implicitly.
        for (String host : new String[] {"axiomiccoreness.github.io", "example.com", "user.atomgit.net"}) {
            assertNull(CliLines.resolveCliWsUrl(host), host);
        }
        assertFalse(CliLines.pagesHttpsHint().contains("axiomiccoreness.com"));
        assertFalse(CliLines.REMOTE_NOT_CONFIGURED.contains("axiomiccoreness.com"));
    }

    @Test
    void loopbackPageGivesLoopbackWs() {
        for (String host : new String[] {"127.0.0.1", "localhost", "LOCALHOST", "::1", "[::1]"}) {
            CliLines.BridgeResolution r = CliLines.resolveBridge("http:", host, null, null);
            assertEquals(CliLines.LOOPBACK_WS, r.url, host);
            assertEquals(CliLines.BridgeResolution.SOURCE_LOOPBACK, r.source);
            assertNull(r.rejected);
        }
        assertEquals("ws://127.0.0.1:6680/cli",
                CliLines.resolveBridge("https:", "127.0.0.1", "", "").url);
        // file: pages have an empty hostname.
        assertEquals(CliLines.LOOPBACK_WS, CliLines.resolveBridge("file:", "", null, null).url);
        // JVM / headless: no location → local-first.
        assertEquals(CliLines.LOOPBACK_WS, CliLines.resolveCliWsUrl(null));
        assertEquals(CliLines.LOOPBACK_WS, CliLines.resolveCliWsUrl(""));
        assertEquals(CliLines.LOOPBACK_WS, CliLines.resolveCliWsUrl("  "));
    }

    @Test
    void httpsRemotePageWithoutOverrideStaysDisconnected() {
        CliLines.BridgeResolution r =
                CliLines.resolveBridge("https:", "axiomiccoreness.github.io", null, null);
        assertNull(r.url);
        assertFalse(r.connects());
        assertEquals(CliLines.BridgeResolution.SOURCE_NONE, r.source);
        assertNull(r.rejected);
        // Blank meta / query count as absent.
        assertNull(CliLines.resolveBridge("https:", "user.atomgit.net", "  ", "").url);
        assertEquals("remote bridge not configured \u2013 set ?bridge=wss://\u2026",
                CliLines.REMOTE_NOT_CONFIGURED);
    }

    @Test
    void validWssOverrideIsUsed() {
        CliLines.BridgeResolution q = CliLines.resolveBridge(
                "https:", "axiomiccoreness.github.io", " wss://chat.example.org:8443/cli ", null);
        assertEquals("wss://chat.example.org:8443/cli", q.url);
        assertEquals(CliLines.BridgeResolution.SOURCE_QUERY, q.source);
        assertNull(q.warning);

        CliLines.BridgeResolution m = CliLines.resolveBridge(
                "https:", "user.atomgit.net", null, "wss://bridge.example.net/cli");
        assertEquals("wss://bridge.example.net/cli", m.url);
        assertEquals(CliLines.BridgeResolution.SOURCE_META, m.source);

        // Query param wins over meta.
        assertEquals("wss://q.example/cli", CliLines.resolveBridge(
                "https:", "x.example", "wss://q.example/cli", "wss://m.example/cli").url);
        // Override also wins on a loopback page (e.g. testing a remote bridge locally).
        assertEquals("wss://q.example/cli", CliLines.resolveBridge(
                "http:", "127.0.0.1", "wss://q.example/cli", null).url);
        // IPv6 literal with port.
        assertTrue(CliLines.isValidBridgeOverride("wss://[2001:db8::1]:443/cli"));
    }

    @Test
    void wsOverrideFromHttpsPageWarnsMixedContent() {
        CliLines.BridgeResolution r = CliLines.resolveBridge(
                "https:", "x.example", "ws://bridge.example/cli", null);
        assertEquals("ws://bridge.example/cli", r.url);
        assertNotNull(r.warning);
        assertTrue(r.warning.contains("wss://"));
        // Loopback ws:// from https is fine (127.0.0.1 is potentially trustworthy).
        assertNull(CliLines.resolveBridge("https:", "x.example", "ws://127.0.0.1:6680/cli", null).warning);
        // Plain http page: no warning.
        assertNull(CliLines.resolveBridge("http:", "x.example", "ws://bridge.example/cli", null).warning);
    }

    @Test
    void javascriptOrHttpOverrideIsRejected() {
        String[] bad = {
            "javascript:alert(1)",
            "JavaScript:alert(1)//wss://x",
            "http://bridge.example/cli",
            "https://bridge.example/cli",
            "data:text/html,hi",
            "wss://",
            "wss:///cli",
            "ws://user:pw@bridge.example/cli",
            "wss://bridge.example:notaport/cli",
            "wss://bri dge.example/cli",
            "wss://bridge.example/\"><script>",
            "ws://0.0.0.0:6680/cli",
            "wss://irc.abjects.net:6669/cli",
            "//bridge.example/cli",
        };
        for (String u : bad) {
            assertFalse(CliLines.isValidBridgeOverride(u), u);
        }
        // Remote page: rejected override → disconnected, with a single rejection note.
        CliLines.BridgeResolution r =
                CliLines.resolveBridge("https:", "x.example", "javascript:alert(1)", null);
        assertNull(r.url);
        assertNotNull(r.rejected);
        assertTrue(r.rejected.contains("query"));
        CliLines.BridgeResolution h =
                CliLines.resolveBridge("https:", "x.example", "http://bridge.example/cli", null);
        assertNull(h.url);
        assertNotNull(h.rejected);
        // Bad query falls through to a valid meta; the note still records the rejection.
        CliLines.BridgeResolution f = CliLines.resolveBridge(
                "https:", "x.example", "http://bad/cli", "wss://good.example/cli");
        assertEquals("wss://good.example/cli", f.url);
        assertNotNull(f.rejected);
        // Loopback page: rejected override falls back to the loopback bridge.
        CliLines.BridgeResolution l =
                CliLines.resolveBridge("http:", "localhost", "javascript:alert(1)", null);
        assertEquals(CliLines.LOOPBACK_WS, l.url);
        assertNotNull(l.rejected);
    }

    @Test
    void pagesHintExplainsOverride() {
        String hint = CliLines.pagesHttpsHint();
        assertTrue(hint.contains("?bridge=wss://"));
        assertTrue(hint.contains("cli-bridge"));
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
