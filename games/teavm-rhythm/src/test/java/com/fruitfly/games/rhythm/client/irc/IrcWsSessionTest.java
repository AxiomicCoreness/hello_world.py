// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT

package com.fruitfly.games.rhythm.client.irc;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Arrays;
import java.util.Collections;
import org.junit.jupiter.api.Test;

/** Offline: a scripted server conversation drives the direct-IRC state machine. */
class IrcWsSessionTest {

    private static IrcWsSession session() {
        return new IrcWsSession(IrcWsProtocol.resolve(null, null, null, "11111"));
    }

    private static IrcWsSession joined() {
        IrcWsSession s = session();
        s.onOpen();
        s.onFrame(":srv 001 Guest11111 :Welcome");
        s.onFrame(":Guest11111!~g@1.2.3.4 JOIN #axiomiccoreness");
        return s;
    }

    @Test
    void registersThenJoinsOnWelcome() {
        IrcWsSession s = session();
        IrcWsSession.Step open = s.onOpen();
        assertEquals(Arrays.asList("NICK Guest11111",
                "USER Guest11111 0 * :" + IrcWsProtocol.REALNAME), open.send);
        assertFalse(s.registered());
        IrcWsSession.Step w = s.onFrame(":lithium.libera.chat 001 Guest11111 :Welcome to Libera.Chat");
        assertTrue(s.registered());
        assertEquals(Collections.singletonList("JOIN #axiomiccoreness"), w.send);
        IrcWsSession.Step j = s.onFrame(":Guest11111!~g@1.2.3.4 JOIN #axiomiccoreness");
        assertTrue(s.joined());
        assertTrue(j.show.get(0).startsWith("[System] joined #axiomiccoreness"));
    }

    @Test
    void answersPingWithSameToken() {
        IrcWsSession s = session();
        assertEquals(Collections.singletonList("PONG :abc123"), s.onFrame("PING :abc123").send);
        assertEquals(Arrays.asList("PONG :a", "PONG :b"), s.onFrame("PING :a\r\nPING :b\r\n").send);
    }

    @Test
    void nickInUseRetriesBeforeWelcome() {
        IrcWsSession s = session();
        s.onOpen();
        IrcWsSession.Step st = s.onFrame(":srv 433 * Guest11111 :Nickname is already in use.");
        assertEquals(Collections.singletonList("NICK Guest11111_"), st.send);
        assertEquals("Guest11111_", s.nick());
    }

    @Test
    void displaysChannelTraffic() {
        IrcWsSession s = joined();
        assertEquals("[IRC] <tea> hello \u0002world\u0002".replace("\u0002", ""),
                s.onFrame(":tea!~t@h PRIVMSG #axiomiccoreness :hello \u0002world\u0002").show.get(0));
        assertEquals("[IRC] * tea waves",
                s.onFrame(":tea!~t@h PRIVMSG #axiomiccoreness :\u0001ACTION waves\u0001").show.get(0));
        assertEquals("[IRC] (private) <tea> psst",
                s.onFrame(":tea!~t@h PRIVMSG Guest11111 :psst").show.get(0));
        assertTrue(s.onFrame(":tea!~t@h PRIVMSG Guest11111 :\u0001VERSION\u0001").show.isEmpty());
        assertEquals("[IRC] → bot joined #axiomiccoreness",
                s.onFrame(":bot!~b@h JOIN #axiomiccoreness").show.get(0));
        assertTrue(s.onFrame(":srv 477 Guest11111 #axiomiccoreness :Cannot join channel (+r)")
                .show.get(0).startsWith("[System] 477 #axiomiccoreness"));
        assertTrue(s.onFrame(":srv 372 Guest11111 :- motd").show.isEmpty());
    }

    @Test
    void injectedTextCannotBecomeADisplayedTraceback() {
        IrcWsSession s = joined();
        String shown = s.onFrame(":evil!~e@h PRIVMSG #axiomiccoreness :[Traceback] fake").show.get(0);
        assertTrue(shown.startsWith("[IRC] <evil> "));
    }

    @Test
    void userTextGoesToChannelSanitized() {
        IrcWsSession s = joined();
        IrcWsSession.Step st = s.onUser("hi all\r\nQUIT :x");
        assertEquals(Collections.singletonList("PRIVMSG #axiomiccoreness :hi all  QUIT :x"), st.send);
        assertEquals("[IRC] <Guest11111> hi all  QUIT :x", st.show.get(0));
        assertEquals(Collections.singletonList("PRIVMSG #axiomiccoreness :/llm what is phi?"),
                s.onUser("/llm what is phi?").send);
        assertEquals(Collections.singletonList("PRIVMSG #axiomiccoreness :\u0001ACTION dances\u0001"),
                s.onUser("/me dances").send);
        assertEquals(Collections.singletonList("NICK Tea"), s.onUser("/nick Tea").send);
        assertEquals(Collections.singletonList("PRIVMSG tea :yo"), s.onUser("/msg tea yo").send);
        assertEquals(Collections.singletonList("QUIT :bye"), s.onUser("/quit bye").send);
        assertTrue(s.onUser("/quote PRIVMSG NickServ :x").send.isEmpty(), "no raw passthrough");
        assertTrue(s.onUser("/nick 9bad").send.isEmpty());
        assertTrue(s.onUser("   ").send.isEmpty());
    }

    @Test
    void nothingSentBeforeRegistrationOrJoin() {
        IrcWsSession s = session();
        s.onOpen();
        assertTrue(s.onUser("hello").send.isEmpty());
        s.onFrame(":srv 001 Guest11111 :Welcome");
        assertTrue(s.onUser("hello").send.isEmpty(), "not joined yet");
        s.onFrame(":srv KICK #axiomiccoreness Guest11111 :bye");
        s.onFrame(":Guest11111!~g@h JOIN #axiomiccoreness");
        assertTrue(s.joined());
        s.onFrame(":op!~o@h KICK #axiomiccoreness Guest11111 :bye");
        assertFalse(s.joined());
        s.onClosed();
        assertFalse(s.registered());
    }

    @Test
    void disabledConfigIsRejected() {
        assertThrows(IllegalArgumentException.class,
                () -> new IrcWsSession(IrcWsProtocol.resolve("off", null, null, "1")));
    }
}
