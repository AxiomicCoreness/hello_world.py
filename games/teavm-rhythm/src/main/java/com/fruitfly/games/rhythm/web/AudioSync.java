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

    /** Pause mid-song (tab hidden); the position is kept for {@link #resume()}. */
    void pause() {
        audio.pause();
    }

    /**
     * Continue from the paused position. Unlike {@link #play()} this does not
     * rewind to 0, so a song paused while the tab was hidden picks up where
     * it stopped.
     */
    void resume() {
        if (failed || audio.isEnded()) {
            return;
        }
        playSafe(audio, () -> fail("audio play() was refused"));
    }

    /**
     * Still a valid clock: loaded, not failed, not ended. Deliberately not
     * false while buffering: SongClock leaves audio mode for good when this
     * turns false, so a short stall would hand the song to the frame clock
     * and drift from the audio. A stall holds song time instead (the audio
     * position stops) and {@link #isBuffering()} says so on the HUD.
     */
    boolean isOk() {
        return !failed && !audio.isEnded();
    }

    /** Playing but without enough data to advance (readyState below HAVE_FUTURE_DATA). */
    boolean isBuffering() {
        return !failed && !audio.isEnded() && buffering(audio);
    }

    @JSBody(params = {"a"}, script = "return !a.paused && typeof a.readyState === 'number' && a.readyState < 3;")
    private static native boolean buffering(HTMLAudioElement a);

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
