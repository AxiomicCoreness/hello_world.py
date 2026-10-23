package com.fruitfly.games.rhythm.irc;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

class CliLinesTest {
    @Test
    void formatTagsSystemEngineUser() {
        assertEquals("[System] hi", CliLines.format(CliLines.KIND_SYSTEM, "hi"));
        assertEquals("[Engine] pong", CliLines.format(CliLines.KIND_ENGINE, "pong"));
        assertEquals("[User] yo", CliLines.format(CliLines.KIND_USER, "yo"));
    }

    @Test
    void loopbackUrlContract() {
        assertTrue(CliLines.isLoopbackCliUrl(CliLines.LOOPBACK_WS));
        assertTrue(CliLines.isLoopbackCliUrl("ws://127.0.0.1:6669/cli"));
        assertTrue(CliLines.isLoopbackCliUrl("ws://[::1]:6669/cli"));
        assertFalse(CliLines.isLoopbackCliUrl("ws://0.0.0.0:6669/cli"));
        assertFalse(CliLines.isLoopbackCliUrl("ws://irc.abjects.net:6669/cli"));
        assertFalse(CliLines.isLoopbackCliUrl("wss://example.com/cli"));
    }

    @Test
    void remoteLabelIsAbjects6669() {
        assertEquals("irc.abjects.net:6669", CliLines.REMOTE_IRC);
        assertTrue(CliLines.bootSystemLine().contains("127.0.0.1:6669"));
        assertTrue(CliLines.bootSystemLine().contains("irc.abjects.net:6669"));
    }

    @Test
    void bridgeConfigPointsAtLoopback() {
        assertEquals("127.0.0.1", IrcBridgeConfig.LOOPBACK_CLI_HOST);
        assertEquals(6669, IrcBridgeConfig.LOOPBACK_CLI_PORT);
        assertEquals(CliLines.LOOPBACK_WS, IrcBridgeConfig.LOOPBACK_CLI_WS);
    }
}
