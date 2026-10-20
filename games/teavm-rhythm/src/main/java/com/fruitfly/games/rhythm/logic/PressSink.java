package com.fruitfly.games.rhythm.logic;

/** Receives an autoplayer's spike-presses (lane, song time in ms). */
public interface PressSink {
    void press(int lane, long timeMs);
}
