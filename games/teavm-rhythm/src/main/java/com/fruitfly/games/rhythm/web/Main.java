package com.fruitfly.games.rhythm.web;

import com.fruitfly.games.rhythm.logic.ChartJson;
import com.fruitfly.games.rhythm.logic.ClickTrack;
import com.fruitfly.games.rhythm.logic.Judgement;
import com.fruitfly.games.rhythm.logic.LifAutoplayer;
import com.fruitfly.games.rhythm.logic.LoadedChart;
import com.fruitfly.games.rhythm.logic.Note;
import com.fruitfly.games.rhythm.logic.NoteChart;
import com.fruitfly.games.rhythm.logic.RhythmGame;
import com.fruitfly.games.rhythm.logic.SongClock;
import org.teavm.jso.ajax.XMLHttpRequest;
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
 * URL options: ?seed=N picks a generated chart. ?chart=URL loads a JSON
 * chart (see ChartJson); its audio is ?audio=URL, else metadata.audio, else
 * a synthesised click track at the chart's bpm. ?audio=none disables audio.
 * With audio, song time is audio.currentTime * 1000 + offset_ms, read every
 * frame; without it (or if it fails) the original frame clock is used.
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
    private static double lastStamp;
    private static SongClock clock = new SongClock(0);
    private static LoadedChart loaded;
    private static AudioSync audio;
    private static String audioParam;
    private static String status = "";
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
        audioParam = param(q, "audio");
        String chartUrl = param(q, "chart");
        if (chartUrl == null && audioParam != null && !"none".equals(audioParam)) {
            audio = new AudioSync(audioParam); // generated chart, audio clock, offset 0
        }
        reset();
        if (chartUrl != null) {
            loadChart(chartUrl);
        }
        doc.addEventListener("keydown", evt -> onKey((KeyboardEvent) evt));
        Window.requestAnimationFrame(Main::frame);
    }

    /** Fetch and parse a JSON chart. On any failure the generated chart stays and the error is shown. */
    private static void loadChart(String url) {
        status = "Loading chart...";
        XMLHttpRequest xhr = XMLHttpRequest.create();
        xhr.open("GET", url);
        xhr.onComplete(() -> {
            int code = xhr.getStatus();
            String text = xhr.getResponseText();
            // file:// pages report status 0 with the body.
            if (code != 200 && !(code == 0 && text != null && !text.isEmpty())) {
                status = "Chart load failed (HTTP " + code + ")";
                return;
            }
            try {
                applyChart(ChartJson.parse(text), url);
            } catch (IllegalArgumentException e) {
                status = "Bad chart: " + e.getMessage();
            }
        });
        xhr.send();
    }

    private static void applyChart(LoadedChart c, String chartUrl) {
        if (running) {
            running = false;
        }
        if (audio != null) {
            audio.stop();
        }
        loaded = c;
        String src;
        if ("none".equals(audioParam)) {
            src = null;
        } else if (audioParam != null) {
            src = audioParam;
        } else if (c.audio() != null) {
            src = resolve(chartUrl, c.audio());
        } else {
            src = ClickTrack.dataUri(c.bpm(), ClickTrack.durationFor(c));
        }
        audio = src == null ? null : new AudioSync(src);
        status = "";
        reset();
    }

    /** metadata.audio is relative to the chart file unless it's absolute. */
    static String resolve(String chartUrl, String ref) {
        if (ref.startsWith("/") || ref.contains(":")) {
            return ref;
        }
        int slash = chartUrl.lastIndexOf('/');
        return slash < 0 ? ref : chartUrl.substring(0, slash + 1) + ref;
    }

    /** Value of {@code name} in a "?a=1&b=2" query, %-decoded; null if absent or empty. */
    static String param(String search, String name) {
        if (search == null || search.isEmpty()) {
            return null;
        }
        String q = search.charAt(0) == '?' ? search.substring(1) : search;
        for (String part : q.split("&")) {
            int eq = part.indexOf('=');
            String k = eq < 0 ? part : part.substring(0, eq);
            if (k.equals(name)) {
                String v = eq < 0 ? "" : decode(part.substring(eq + 1));
                return v.isEmpty() ? null : v;
            }
        }
        return null;
    }

    private static String decode(String v) {
        StringBuilder b = new StringBuilder();
        for (int i = 0; i < v.length(); i++) {
            char c = v.charAt(i);
            if (c == '+') {
                b.append(' ');
            } else if (c == '%' && i + 2 < v.length()
                    && Character.digit(v.charAt(i + 1), 16) >= 0 && Character.digit(v.charAt(i + 2), 16) >= 0) {
                b.append((char) Integer.parseInt(v.substring(i + 1, i + 3), 16));
                i += 2;
            } else {
                b.append(c);
            }
        }
        return b.toString();
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
        NoteChart chart = loaded != null ? loaded.chart().fresh()
                : NoteChart.generate(seed, NOTE_COUNT, BPM, LEAD_IN_MS);
        game = new RhythmGame(chart);
        brain = new LifAutoplayer(game);
        running = false;
        if (audio != null) {
            audio.stop();
        }
        clock = new SongClock(loaded != null ? loaded.offsetMs() : 0);
    }

    /** Re-read the clock at frame time {@code stamp}: audio position when audio is live, else the frame clock. */
    private static long sampleSongTime(double stamp) {
        boolean ok = audio != null && audio.isOk();
        clock.sample(stamp, ok, ok ? audio.positionMs() : 0.0);
        return clock.nowMs();
    }

    private static long songTime() {
        return clock.nowMs();
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
                clock.start(lastStamp, audio != null && audio.isOk());
                if (audio != null) {
                    audio.play();
                }
                e.preventDefault();
            } else if ("n".equalsIgnoreCase(key) && loaded == null) {
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
        Judgement j = game.press(lane, sampleSongTime(lastStamp)); // fresh audio position at the key press
        if (j != null) {
            banner = j.name();
            bannerUntil = lastStamp + 400;
        }
    }

    private static void frame(double stamp) {
        lastStamp = stamp;
        if (running) {
            sampleSongTime(stamp);
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
                if (audio != null) {
                    audio.stop();
                }
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
        ctx.fillText(loaded != null ? loaded.title() : "seed " + seed, WIDTH - 10, 24);
        ctx.fillText(autoplay ? "LIF autoplay ON" : "autoplay off", WIDTH - 10, 46);
        if (autoplay) {
            ctx.fillText("spikes " + brain.spikeCount(), WIDTH - 10, 68);
        }
        if (loaded != null || audio != null) {
            ctx.setTextAlign("left");
            boolean audioClock = running ? clock.isAudioMode() : audio != null && audio.isOk();
            ctx.fillText(audioClock ? "clock audio" : "clock frame", 10, 90);
        }
        if (!status.isEmpty()) {
            ctx.setTextAlign("center");
            ctx.setFont("12px monospace");
            ctx.setFillStyle("#ffb86b");
            ctx.fillText(status.length() > 60 ? status.substring(0, 57) + "..." : status, WIDTH / 2.0, 140);
            ctx.setFont("16px monospace");
            ctx.setFillStyle("#ffffff");
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
                if (loaded != null) {
                    ctx.fillText(loaded.artist() + " · " + game.chart().notes().size() + " notes", WIDTH / 2.0, 200);
                }
                ctx.fillText(loaded != null ? "D F J K hit · R restart" : "D F J K hit · R restart · N new seed",
                        WIDTH / 2.0, 280);
                ctx.fillText("B toggles the LIF autoplayer", WIDTH / 2.0, 305);
            }
        }
    }
}
