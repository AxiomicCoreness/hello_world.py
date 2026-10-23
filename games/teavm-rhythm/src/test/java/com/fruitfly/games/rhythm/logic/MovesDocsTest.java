package com.fruitfly.games.rhythm.logic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import org.junit.jupiter.api.Test;

/** README.md "Moves list" examples are what the implementation produces. */
class MovesDocsTest {
    static String example() throws Exception {
        String r = new String(Files.readAllBytes(Paths.get("README.md")), StandardCharsets.UTF_8);
        int a = r.indexOf("<!-- moves-example -->");
        int b = r.indexOf("<!-- /moves-example -->");
        assertTrue(a >= 0 && b > a, "README moves-example markers");
        return r.substring(a, b);
    }

    @Test
    void bembeRowZeroExampleMatches() throws Exception {
        String doc = example();
        Move m = MovesLogTest.play(MovesLogTest.bembe90(), ControlMode.CONNECTOME).first20().get(0);
        assertTrue(doc.contains("\n" + m.mathOrigin + "\n"), m.mathOrigin);
        assertTrue(doc.contains("\n" + Move.preimage(m, m.prev) + "\n"), Move.preimage(m, m.prev));
        assertTrue(doc.contains("\nhash=" + m.hash + "\n"), m.hash);
        assertTrue(doc.contains("value =\nround(" + m.dMilli + " * " + m.fTenths + " / 10) = " + m.valueMilli + " thousandths"));
    }

    @Test
    void humanTimingExampleMatches() throws Exception {
        Move h = new Move(0, 2000, 2, Move.NA, "you", 1988, -12, "PERFECT", Move.NA, Move.NA, Move.NA, Move.NA,
            Move.KIND_TIMING, Move.timingScoreMilli(-12), 3, MovesLog.GENESIS);
        assertEquals(920, h.dMilli);
        assertEquals(1196, h.valueMilli);
        assertTrue(example().contains("`" + h.mathOrigin + "`"), h.mathOrigin);
    }

    @Test
    void formulaIsDocumented() throws Exception {
        String r = new String(Files.readAllBytes(Paths.get("README.md")), StandardCharsets.UTF_8);
        for (String s : new String[] {"`chain_n = chain_(n-1) + 1` on a hit, `0` on a MISS", "`f(chain) = 1 + min(chain, 10) / 10`",
            "`value = d * f(chain)`", "`d = margin = V_peak - th`", "`d = (150 - |dt|) / 150`", "first row's prev is 64 zeros",
            "goes to lane `p mod 4`"}) {
            assertTrue(r.contains(s), s);
        }
    }
}
