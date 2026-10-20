package com.fruitfly.games.rhythm.web;

import org.teavm.jso.JSBody;
import org.teavm.jso.JSFunctor;
import org.teavm.jso.JSObject;
import org.teavm.jso.dom.html.HTMLAudioElement;
import org.teavm.jso.dom.html.HTMLDocument;

/**
 * Wraps one HTML5 {@code <audio>} element as a clock source. The game reads
 * {@link #positionMs()} (currentTime * 1000, a double) every frame and feeds it
 * to {@link com.fruitfly.games.rhythm.logic.SongClock}. If the audio can't load,
 * play() is refused, or it ends, {@link #isOk()} turns false and the clock
 * falls back to the frame timer.
 */
final class AudioSync {
    @JSFunctor
    interface Callback extends JSObject {
        void call();
    }

    private final HTMLAudioElement audio;
    private boolean failed;
    private String failure = "";

    AudioSync(String url) {
        audio = (HTMLAudioElement) HTMLDocument.current().createElement("audio");
        audio.setPreload("auto");
        audio.addEventListener("error", evt -> fail("audio failed to load"));
        audio.setSrc(url);
    }

    /** Restart from 0. A refused play() (e.g. autoplay policy) marks the audio failed. */
    void play() {
        if (failed) {
            return;
        }
        audio.setCurrentTime(0);
        playSafe(audio, () -> fail("audio play() was refused"));
    }

    void stop() {
        audio.pause();
    }

    boolean isOk() {
        return !failed && !audio.isEnded();
    }

    double positionMs() {
        return audio.getCurrentTime() * 1000.0;
    }

    String failure() {
        return failure;
    }

    private void fail(String why) {
        failed = true;
        failure = why;
    }

    /** audio.play() returns a Promise in browsers; a rejection would otherwise go unnoticed. */
    @JSBody(params = {"a", "onFail"}, script = "var p = a.play();"
            + " if (p && typeof p.then === 'function') { p.then(null, function () { onFail(); }); }")
    private static native void playSafe(HTMLAudioElement a, Callback onFail);
}
