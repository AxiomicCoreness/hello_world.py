package com.fruitfly.games.rhythm.web;

import com.fruitfly.games.rhythm.logic.Judgement;
import com.fruitfly.games.rhythm.logic.LifAutoplayer;
import com.fruitfly.games.rhythm.logic.Note;
import com.fruitfly.games.rhythm.logic.NoteChart;
import com.fruitfly.games.rhythm.logic.RhythmGame;
import org.teavm.jso.browser.Window;
import org.teavm.jso.canvas.CanvasRenderingContext2D;
import org.teavm.jso.dom.events.KeyboardEvent;
import org.teavm.jso.dom.html.HTMLCanvasElement;
import org.teavm.jso.dom.html.HTMLDocument;

/**
 * Browser layer only: canvas drawing, keyboard input and the
 * requestAnimationFrame loop. All rules live in the logic package.
 *
 * Controls: Space/Enter start, D F J K hit lanes, B toggle the LIF
 * autoplayer, R restart, N new seed.
 *
 * The lane names (antennal lobe, mushroom body, lateral horn, lobula) are
 * display labels only. The lanes aren't wired to those regions or to the
 * connectome; the autoplayer is four independent LIF neurons.
 */
public final class Main {
    static final int WIDTH = 400;
    static final int HEIGHT = 600;
    static final int HIT_Y = 520;
    static final double PX_PER_MS = 0.35;
    static final int NOTE_COUNT = 64;
    static final int BPM = 120;
    static final long LEAD_IN_MS = 2000;
    static final long FLASH_MS = 120;
    /** Display-only lane labels, left to right. Not anatomical wiring. */
    static final String[] REGION_LABELS = {"antennal lobe", "mushroom body", "lateral horn", "lobula"};

    private static CanvasRenderingContext2D ctx;
    private static long seed = 2026L;
    private static RhythmGame game;
    private static LifAutoplayer brain;
    private static boolean autoplay;
    private static boolean running;
    private static double startStamp = -1;
    private static double lastStamp;
    private static final double[] laneFlashUntil = new double[RhythmGame.LANES];
    private static String banner = "";
    private static double bannerUntil;

    private Main() {
    }

    public static void main(String[] args) {
        HTMLDocument doc = HTMLDocument.current();
        HTMLCanvasElement canvas = (HTMLCanvasElement) doc.getElementById("game");
        canvas.setWidth(WIDTH);
        canvas.setHeight(HEIGHT);
        ctx = (CanvasRenderingContext2D) canvas.getContext("2d");
        String q = Window.current().getLocation().getSearch();
        Long fromUrl = parseSeed(q);
        if (fromUrl != null) {
            seed = fromUrl;
        }
        reset();
        doc.addEventListener("keydown", evt -> onKey((KeyboardEvent) evt));
        Window.requestAnimationFrame(Main::frame);
    }

    /** "?seed=123" -> 123; anything else -> null. */
    static Long parseSeed(String search) {
        if (search == null) {
            return null;
        }
        int i = search.indexOf("seed=");
        if (i < 0) {
            return null;
        }
        int j = i + 5;
        int end = j;
        while (end < search.length() && (Character.isDigit(search.charAt(end)) || (end == j && search.charAt(end) == '-'))) {
            end++;
        }
        if (end == j) {
            return null;
        }
        try {
            return Long.parseLong(search.substring(j, end));
        } catch (NumberFormatException e) {
            return null;
        }
    }

    private static void reset() {
        game = new RhythmGame(NoteChart.generate(seed, NOTE_COUNT, BPM, LEAD_IN_MS));
        brain = new LifAutoplayer(game);
        running = false;
        startStamp = -1;
    }

    private static long songTime() {
        return startStamp < 0 ? 0 : (long) (lastStamp - startStamp);
    }

    private static void onKey(KeyboardEvent e) {
        String key = e.getKey();
        String code = e.getCode();
        if ("b".equalsIgnoreCase(key) || "KeyB".equals(code)) {
            // Only switchable between songs, so a score is all-brain or all-human.
            if (!running) {
                autoplay = !autoplay;
            }
            return;
        }
        if (!running) {
            if (" ".equals(key) || "Enter".equals(key)) {
                if (game.isFinished()) {
                    reset();
                }
                running = true;
                startStamp = lastStamp;
                e.preventDefault();
            } else if ("n".equalsIgnoreCase(key)) {
                seed = seed * 31 + 7;
                reset();
            }
            return;
        }
        if ("r".equalsIgnoreCase(key)) {
            reset();
            return;
        }
        if (e.isRepeat() || autoplay) {
            return;
        }
        int lane = RhythmGame.laneForKey(code != null && !code.isEmpty() ? code : key);
        if (lane < 0) {
            return;
        }
        e.preventDefault();
        laneFlashUntil[lane] = lastStamp + FLASH_MS;
        Judgement j = game.press(lane, songTime());
        if (j != null) {
            banner = j.name();
            bannerUntil = lastStamp + 400;
        }
    }

    private static void frame(double stamp) {
        lastStamp = stamp;
        if (running) {
            int missesBefore = game.missCount();
            if (autoplay) {
                int hitsBefore = game.perfectCount() + game.greatCount() + game.goodCount();
                brain.advanceTo(songTime()); // spikes become presses at their substep times
                if (game.perfectCount() + game.greatCount() + game.goodCount() != hitsBefore) {
                    banner = game.lastJudgement().name();
                    bannerUntil = stamp + 400;
                }
            }
            game.update(songTime());
            if (game.missCount() != missesBefore) {
                banner = "MISS";
                bannerUntil = stamp + 400;
            }
            if (game.isFinished()) {
                running = false;
            }
        }
        draw(stamp);
        Window.requestAnimationFrame(Main::frame);
    }

    private static void draw(double stamp) {
        int laneW = WIDTH / RhythmGame.LANES;
        ctx.setFillStyle("#0b0f1a");
        ctx.fillRect(0, 0, WIDTH, HEIGHT);
        String[] colors = {"#ff3b6b", "#3bb3ff", "#ff3b6b", "#3bb3ff"};
        for (int l = 0; l < RhythmGame.LANES; l++) {
            ctx.setFillStyle(laneFlashUntil[l] > stamp ? "#26304d" : (l % 2 == 0 ? "#121829" : "#0f1422"));
            ctx.fillRect(l * laneW, 0, laneW, HEIGHT);
        }
        ctx.setFillStyle("#e8e8f0");
        ctx.fillRect(0, HIT_Y - 2, WIDTH, 4);

        long now = songTime();
        for (Note n : game.chart().notes()) {
            if (n.isResolved()) {
                continue;
            }
            double y = HIT_Y - (n.timeMs() - now) * PX_PER_MS;
            if (y < -20) {
                break;
            }
            if (y > HEIGHT + 20) {
                continue;
            }
            ctx.setFillStyle(colors[n.lane()]);
            ctx.fillRect(n.lane() * laneW + 8, y - 10, laneW - 16, 20);
        }

        ctx.setFont("bold 20px monospace");
        ctx.setTextAlign("center");
        for (int l = 0; l < RhythmGame.LANES; l++) {
            ctx.setFillStyle("#8890a8");
            ctx.fillText(RhythmGame.LANE_KEYS[l], l * laneW + laneW / 2.0, HIT_Y + 40);
        }
        ctx.setFont("11px monospace");
        for (int l = 0; l < RhythmGame.LANES; l++) {
            ctx.setFillStyle("#6f7896");
            ctx.fillText(REGION_LABELS[l], l * laneW + laneW / 2.0, HIT_Y + 62);
        }

        ctx.setTextAlign("left");
        ctx.setFont("16px monospace");
        ctx.setFillStyle("#ffffff");
        ctx.fillText("Score " + game.score(), 10, 24);
        ctx.fillText("Combo " + game.combo() + "  x" + RhythmGame.multiplierFor(game.combo()), 10, 46);
        ctx.fillText("Miss " + game.missCount(), 10, 68);
        ctx.setTextAlign("right");
        ctx.fillText("seed " + seed, WIDTH - 10, 24);
        ctx.fillText(autoplay ? "LIF autoplay ON" : "autoplay off", WIDTH - 10, 46);
        if (autoplay) {
            ctx.fillText("spikes " + brain.spikeCount(), WIDTH - 10, 68);
        }

        ctx.setTextAlign("center");
        if (bannerUntil > stamp && running) {
            ctx.setFont("bold 28px monospace");
            ctx.setFillStyle("MISS".equals(banner) ? "#ff5555" : "#ffe066");
            ctx.fillText(banner, WIDTH / 2.0, HIT_Y - 80);
        }
        if (!running) {
            ctx.setFont("bold 22px monospace");
            ctx.setFillStyle("#ffffff");
            if (game.isFinished()) {
                ctx.fillText("Song complete", WIDTH / 2.0, 220);
                ctx.setFont("16px monospace");
                ctx.fillText("P " + game.perfectCount() + "  Gr " + game.greatCount()
                        + "  Go " + game.goodCount() + "  M " + game.missCount(), WIDTH / 2.0, 250);
                ctx.fillText("Max combo " + game.maxCombo() + "  Acc "
                        + Math.round(game.accuracy() * 1000) / 10.0 + "%", WIDTH / 2.0, 275);
                ctx.fillText("Space to play again", WIDTH / 2.0, 310);
            } else {
                ctx.fillText("Press Space to start", WIDTH / 2.0, 250);
                ctx.setFont("16px monospace");
                ctx.fillText("D F J K hit · R restart · N new seed", WIDTH / 2.0, 280);
                ctx.fillText("B toggles the LIF autoplayer", WIDTH / 2.0, 305);
            }
        }
    }
}
