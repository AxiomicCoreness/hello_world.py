package com.fruitfly.games.rhythm.irc;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Arrays;
import org.junit.jupiter.api.Test;

class TracebackFeedbackTest {

    private static void feedPython(TracebackFeedback f, String type, String msg, int frames) {
        f.accept("[Traceback] Traceback (most recent call last):");
        for (int i = 0; i < frames; i++) {
            f.accept("[Traceback]   File \"/repo/pythonIDE/mod" + i + ".py\", line " + (10 + i) + ", in fn" + i);
            f.accept("[Traceback]     do_thing()");
        }
        f.accept("[Traceback] " + type + ": " + msg);
        f.accept("[Engine] next");
    }

    @Test
    void emptyBlock() {
        assertEquals("{\"kind\":\"traceback\",\"reports\":[],\"dropped\":0}", new TracebackFeedback().toJson());
    }

    @Test
    void parsesTypeMessageAndLastFrames() {
        TracebackFeedback f = new TracebackFeedback();
        feedPython(f, "pythonIDE.toolkit.CapabilityError", "unknown capability 'zz'", 5);
        assertEquals(1, f.size());
        assertEquals("{\"kind\":\"traceback\",\"reports\":[{\"type\":\"pythonIDE.toolkit.CapabilityError\","
                + "\"message\":\"unknown capability 'zz'\",\"origin\":\"cli\",\"frames\":["
                + "\"mod2.py:12 in fn2\",\"mod3.py:13 in fn3\",\"mod4.py:14 in fn4\"]}],\"dropped\":0}",
                f.toJson());
    }

    @Test
    void offlinePythonIdeCliTracebackIsCaptured() {
        TracebackFeedback f = new TracebackFeedback();
        for (String line : PythonIdeCli.formatTraceback("CliClient.sendUser", "SendError", "socket closed")) {
            f.accept(line);
        }
        String json = f.toJson(); // toJson flushes the pending run
        assertTrue(json.contains("\"type\":\"SendError\",\"message\":\"socket closed\""), json);
        assertTrue(json.contains("\"CliClient.sendUser:1 in <cli>\""), json);
    }

    @Test
    void keepsOnlyNewestReports() {
        TracebackFeedback f = new TracebackFeedback();
        for (int i = 0; i < 5; i++) {
            feedPython(f, "ValueError", "bad " + i, 1);
        }
        assertEquals(TracebackFeedback.MAX_REPORTS, f.size());
        assertEquals(5, f.seen());
        String json = f.toJson();
        assertFalse(json.contains("bad 1"));
        assertTrue(json.contains("bad 2") && json.contains("bad 4"));
        assertTrue(json.endsWith("\"dropped\":2}"), json);
    }

    @Test
    void truncatesMessagesAndCapsBlock() {
        TracebackFeedback f = new TracebackFeedback();
        StringBuilder huge = new StringBuilder();
        for (int i = 0; i < 1000; i++) {
            huge.append('x');
        }
        for (int i = 0; i < 3; i++) {
            f.add("RuntimeError", huge.toString() + i,
                    Arrays.asList("a.py:1 in f", "b.py:2 in g", "c.py:3 in h", "d.py:4 in k"), "test");
        }
        String json = f.toJson();
        assertTrue(json.length() <= TracebackFeedback.MAX_JSON, "len " + json.length());
        assertFalse(json.contains("a.py:1"), "only last 3 frames");
        assertTrue(json.contains("…"), "message trimmed with ellipsis");
        assertTrue(json.contains("\"dropped\":"));
        // each report message is capped
        int idx = json.indexOf("\"message\":\"");
        int end = json.indexOf('"', idx + 11);
        assertEquals(TracebackFeedback.MAX_MESSAGE, end - (idx + 11));
    }

    @Test
    void nonTracebackTextIsIgnored() {
        TracebackFeedback f = new TracebackFeedback();
        f.accept("[Engine] ack: hi");
        f.accept("[System] connected");
        f.accept(null);
        assertEquals(0, f.size());
    }
}
