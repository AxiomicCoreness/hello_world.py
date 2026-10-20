package com.fruitfly.games.rhythm.logic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;

class JudgementTest {

    @ParameterizedTest(name = "offset {0} ms -> {1}")
    @CsvSource({
        "0,PERFECT", "50,PERFECT", "-50,PERFECT",
        "51,GREAT", "-51,GREAT", "100,GREAT", "-100,GREAT",
        "101,GOOD", "-101,GOOD", "150,GOOD", "-150,GOOD"
    })
    void windowBoundariesAreInclusive(long offset, Judgement expected) {
        assertEquals(expected, Judgement.forOffset(offset));
    }

    @Test
    void outsideGoodWindowIsNoHit() {
        assertNull(Judgement.forOffset(151));
        assertNull(Judgement.forOffset(-151));
        assertNull(Judgement.forOffset(10_000));
    }

    @Test
    void baseScoresAreOrdered() {
        assertEquals(300, Judgement.PERFECT.baseScore());
        assertEquals(200, Judgement.GREAT.baseScore());
        assertEquals(100, Judgement.GOOD.baseScore());
        assertEquals(0, Judgement.MISS.baseScore());
        assertEquals(Judgement.GOOD.windowMs(), Judgement.MAX_WINDOW_MS);
    }
}
