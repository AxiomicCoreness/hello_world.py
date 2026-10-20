package com.fruitfly.games.rhythm.logic;

/** A chart JSON document that is malformed or breaks a chart rule. The message names the field. */
public final class ChartFormatException extends IllegalArgumentException {
    private static final long serialVersionUID = 1L;

    public ChartFormatException(String message) {
        super(message);
    }
}
