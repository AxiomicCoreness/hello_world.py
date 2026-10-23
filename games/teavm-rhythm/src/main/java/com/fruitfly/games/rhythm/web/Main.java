package com.fruitfly.games.rhythm.web;

import com.fruitfly.games.rhythm.logic.AssistArbiter;
import com.fruitfly.games.rhythm.logic.ChartJson;
import com.fruitfly.games.rhythm.logic.Circuit;
import com.fruitfly.games.rhythm.logic.CircuitSim;
import com.fruitfly.games.rhythm.logic.ConnectomeAutoplayer;
import com.fruitfly.games.rhythm.logic.ConnectomeXml;
import com.fruitfly.games.rhythm.logic.ControlMode;
import com.fruitfly.games.rhythm.logic.EuclidSong;
import com.fruitfly.games.rhythm.logic.EuclidTrack;
import com.fruitfly.games.rhythm.logic.Midi;
import com.fruitfly.games.rhythm.logic.MidiSong;
import com.fruitfly.games.rhythm.logic.CueProbe;
import com.fruitfly.games.rhythm.logic.Move;
import com.fruitfly.games.rhythm.logic.MovesLog;
import com.fruitfly.games.rhythm.logic.Sha256;
import com.fruitfly.games.rhythm.logic.SongSource;
import com.fruitfly.games.rhythm.logic.VoiceSong;
import com.fruitfly.games.rhythm.logic.ClickTrack;
import com.fruitfly.games.rhythm.logic.InputRouter;
import com.fruitfly.games.rhythm.logic.Judgement;
import com.fruitfly.games.rhythm.logic.LifAutoplayer;
import com.fruitfly.games.rhythm.logic.LoadedChart;
import com.fruitfly.games.rhythm.logic.Note;
import com.fruitfly.games.rhythm.logic.NoteChart;
import com.fruitfly.games.rhythm.logic.NoteBlocks;
import com.fruitfly.games.rhythm.logic.SaberRig;
import com.fruitfly.games.rhythm.logic.Scene3D;
import com.fruitfly.games.rhythm.logic.RhythmGame;
import com.fruitfly.games.rhythm.logic.SongClock;
import com.fruitfly.games.rhythm.logic.StageLayout;
import com.fruitfly.games.rhythm.logic.ToyCircuitXml;
import org.teavm.jso.JSBody;
import java.util.List;
import org.teavm.jso.JSObject;
import org.teavm.jso.ajax.XMLHttpRequest;
import org.teavm.jso.browser.Window;
import org.teavm.jso.canvas.CanvasRenderingContext2D;
import org.teavm.jso.dom.events.KeyboardEvent;
import org.teavm.jso.dom.html.HTMLCanvasElement;
import org.teavm.jso.dom.html.HTMLDocument;
import org.teavm.jso.dom.html.HTMLElement;

/**
 * Browser layer only: canvas drawing, keyboard input and the
 * requestAnimationFrame loop. All rules live in the logic package.
 *
 * Controls: Space/Enter start, D F J K hit lanes, B toggle the LIF
 * autoplayer, C cycle the control mode (between songs only): off, LIF
 * autoplay, connectome autoplay, assist (LIF fly), assist (connectome fly).
 * The on-screen AUTOPLAY button (#autoplay-btn) runs the same cycle as C
 * and always shows the current mode; it never takes key focus.
 * In assist modes the human plays and the fly only covers notes about to be
 * missed (AssistArbiter). R restart, N new seed.
 *
 * URL options: ?seed=N picks a generated chart. ?chart=URL loads a JSON
 * chart (see ChartJson); its audio is ?audio=URL, else metadata.audio, else
 * a synthesised click track at the chart's bpm. ?audio=none disables audio.
 * With audio, song time is audio.currentTime * 1000 + offset_ms, read every
 * frame; without it (or if it fails) the original frame clock is used.
 *
 * The lane names (antennal lobe, mushroom body, lateral horn, lobula) are
 * display labels only. With the toy circuit they're read from the region
 * attribute of laneN.out (connectomes/toy_lane_circuit.xml, a TOY circuit,
 * not the real fly connectome); ?connectome=URL loads another file.
 *
 * Layers, back to front: background (default: light #f7f6f3 stage with a
 * procedural perspective floor; ?bg=ar: the AR screenshot
 * assets/ar_brain_bg.jpg, dimmed; ?camera=1: live camera, else the AR shot), the 3D stage (StageRenderer:
 * grid, origin anchor, fly-brain object), lanes and notes, then the HUD as
 * an HTML overlay (#hud-l, #hud-r, #hud-c; canvas text if those are absent).
 * Left of the stage: #cli-column (CliClient → ws://127.0.0.1:6669/cli → irc.abjects.net:6669).
 * The canvas is sized by StageLayout (iPhone 12: 390x844 CSS px;
 * ?device=iphone12 forces it) with a devicePixelRatio backing store
 * (1170x2532 at DPR 3).
 */
public final class Main {
    static final String BG_URL = "assets/ar_brain_bg.jpg";
    static final int MODE_OFF = ControlMode.OFF;
    static final int MODE_LIF = ControlMode.LIF;
    static final int MODE_CONNECTOME = ControlMode.CONNECTOME;
    static final int MODE_ASSIST_LIF = ControlMode.ASSIST_LIF;
    static final int MODE_ASSIST_CONNECTOME = ControlMode.ASSIST_CONNECTOME;
    static final double SHAKE_MS = 60;
    static final double SHAKE_PX = 4;
    static final int NOTE_COUNT = 64;
    static final int BPM = 120;
    static final long LEAD_IN_MS = 2000;
    static final long FLASH_MS = 120;
    /** Display-only lane labels, left to right. Not anatomical wiring. */
    static final String[] REGION_LABELS = {"antennal lobe", "mushroom body", "lateral horn", "lobula"};

    private static CanvasRenderingContext2D ctx;
    private static StageLayout layout;
    private static double dpr = 1;
    private static int width;
    private static int height;
    private static int hitY;
    private static JSObject background;
    private static JSObject camera;
    private static Theme theme = Theme.LIGHT;
    private static boolean cameraReported;
    private static HTMLElement hudL;
    private static HTMLElement hudR;
    private static HTMLElement hudC;
    /** On-screen AUTOPLAY button (#autoplay-btn); null on pages without it. Same code path as key C. */
    private static HTMLElement autoplayBtn;
    private static final StringBuilder hl = new StringBuilder();
    private static final StringBuilder hr = new StringBuilder();
    private static final StringBuilder hc = new StringBuilder();
    private static Circuit circuit = ConnectomeXml.parse(ToyCircuitXml.XML);
    private static String circuitName = "toy";
    private static ConnectomeAutoplayer wired;
    private static AssistArbiter arbiter;
    private static LifAutoplayer flyLif;
    private static ConnectomeAutoplayer flyWired;
    private static int mode = MODE_OFF;
    private static SaberRig sabers;
    private static long seed = 2026L;
    private static RhythmGame game;
    private static LifAutoplayer brain;
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
    /** Page time until which the "Autoplay locked during song" hint shows (C / B / button used mid-song). */
    private static double lockHintUntil;
    private static String lockHint = ControlMode.LOCK_HINT;
    /** Song picker: Euclidean presets 0..P-1, P = the seed / ?chart chart (legacy). */
    private static HTMLElement rhythmBtn;
    private static HTMLElement bpmBtn;
    /** Music-source picker (#source-btn) and the hidden MIDI file input (#midi-file). */
    private static HTMLElement sourceBtn;
    private static HTMLElement midiInput;
    private static int source = SongSource.EUCLID;
    private static LoadedChart midiChart;
    private static String midiUri;
    private static String midiName;
    private static int voiceLine;
    /** Index of the last syllable handed to speechSynthesis this run (-1 = none). */
    private static int voiceSpoken = -1;
    private static boolean speechOk;
    private static int rhythmIdx = EuclidSong.PRESETS.length;
    private static int bpmIdx = EuclidSong.DEFAULT_BPM_INDEX;
    /** The seed / ?chart chart and its audio, restored when the picker returns to that slot. */
    private static LoadedChart baseLoaded;
    private static AudioSync baseAudio;
    static final String PICKER_LOCK_HINT = SongSource.LOCK_HINT;
    /** Moves list of the current run (window.__rhythmDebug); a fresh one at every start. */
    private static MovesLog moves;
    /** ?debug=notes: console.log every row and show the last rows on the stage (#moves-list). */
    private static boolean debugNotes;
    private static HTMLElement movesEl;
    static final int STAGE_ROWS = 8;
    /** ?clock=raw: read audio.currentTime as is (the pre-smoothing behaviour, for comparison). */
    private static boolean rawClock;
    /** Song paused because the tab went hidden; resumePending = re-anchor the clock on the next frame. */
    private static boolean pausedHidden;
    private static boolean resumePending;
    static final String PAUSED_TEXT = "paused (tab hidden)";
    /** Left CLI → ws://127.0.0.1:6669/cli (Cosmic Alignment loopback). */
    private static CliClient cliClient;

    private Main() {
    }

    public static void main(String[] args) {
        HTMLDocument doc = HTMLDocument.current();
        HTMLCanvasElement canvas = (HTMLCanvasElement) doc.getElementById("game");
        String q = Window.current().getLocation().getSearch();
        layout = StageLayout.choose(param(q, "device"), Dom.innerWidth(), Dom.innerHeight());
        width = layout.width;
        height = layout.height;
        hitY = layout.hitY;
        canvas.setWidth(StageLayout.backing(width, Dom.devicePixelRatio()));
        canvas.setHeight(StageLayout.backing(height, Dom.devicePixelRatio()));
        dpr = canvas.getWidth() / (double) width; // backing scale = devicePixelRatio (3 on iPhone 12)
        Dom.cssSize(canvas, width, height);
        ctx = (CanvasRenderingContext2D) canvas.getContext("2d");
        // Cosmic Alignment CLI: loopback WS only (never browser→abjects).
        cliClient = new CliClient();
        cliClient.mount(doc);
        hudL = (HTMLElement) doc.getElementById("hud-l");
        hudR = (HTMLElement) doc.getElementById("hud-r");
        hudC = (HTMLElement) doc.getElementById("hud-c");
        autoplayBtn = (HTMLElement) doc.getElementById("autoplay-btn");
        if (autoplayBtn != null) {
            double[] r = layout.autoplayButton();
            Dom.place(autoplayBtn, r[0], r[1], r[2], r[3]);
            // Never take focus (so Space / Enter / D F J K keep going to the game), never reach the canvas.
            autoplayBtn.addEventListener("pointerdown", evt -> evt.preventDefault());
            autoplayBtn.addEventListener("mousedown", evt -> evt.preventDefault());
            // If it ever does get focus (assistive tech, programmatic focus), Space / Enter must not
            // activate it: cancel the button's own default; the document keydown handler still sees the key.
            autoplayBtn.addEventListener("keydown", evt -> {
                KeyboardEvent k = (KeyboardEvent) evt;
                if (InputRouter.isStartKey(k.getKey(), k.getCode())) {
                    evt.preventDefault();
                }
            });
            autoplayBtn.addEventListener("keyup", evt -> {
                KeyboardEvent k = (KeyboardEvent) evt;
                if (InputRouter.isStartKey(k.getKey(), k.getCode())) {
                    evt.preventDefault();
                }
            });
            autoplayBtn.addEventListener("click", evt -> {
                evt.preventDefault();
                evt.stopPropagation();
                Dom.blur(autoplayBtn);
                // detail 0 = keyboard-synthesised click: ignored, so Space / Enter only start the song.
                applyModeAction(InputRouter.buttonClick(Dom.clickDetail(evt), running), false);
                refreshNow(); // label + HUD show the new mode now, not on the next animation frame
            });
        }
        rhythmBtn = (HTMLElement) doc.getElementById("rhythm-btn");
        bpmBtn = (HTMLElement) doc.getElementById("bpm-btn");
        sourceBtn = (HTMLElement) doc.getElementById("source-btn");
        midiInput = (HTMLElement) doc.getElementById("midi-file");
        boolean pickers = rhythmBtn != null && bpmBtn != null;
        if (pickers) {
            double[][] row = sourceBtn != null ? layout.pickerRow(0.26, 0.48, 0.26) : layout.pickerRow(0.7, 0.3);
            int at = 0;
            if (sourceBtn != null) {
                Dom.place(sourceBtn, row[at][0], row[at][1], row[at][2], row[at][3]);
                wirePicker(sourceBtn, Main::cycleSource);
                at++;
            }
            Dom.place(rhythmBtn, row[at][0], row[at][1], row[at][2], row[at][3]);
            Dom.place(bpmBtn, row[at + 1][0], row[at + 1][1], row[at + 1][2], row[at + 1][3]);
            wirePicker(rhythmBtn, Main::itemTap);
            wirePicker(bpmBtn, Main::cycleBpm);
        }
        if (midiInput != null) {
            Dom.onFilePicked(midiInput, Main::midiPicked, why -> status = "MIDI read failed: " + why);
        }
        if (hudC != null && autoplayBtn != null) {
            // centre text starts under the button (and under the picker row when present)
            Dom.top(hudC, pickers ? layout.centerTextTopBelowPickers() : layout.centerTextTop());
        }
        boolean camParam = "1".equals(param(q, "camera"));
        // Default: light stage with a procedural floor. ?bg=ar (or ?camera=1, which falls back to it) uses the AR photo.
        theme = "ar".equals(param(q, "bg")) || camParam ? Theme.AR : Theme.LIGHT;
        Dom.bodyClass(theme.bodyClass);
        if (!theme.light) {
            background = Dom.loadImage(BG_URL);
        }
        if (camParam) {
            camera = Dom.startCamera();
            if (camera == null) {
                status = "camera unavailable: using screenshot";
            }
        }
        debugNotes = "notes".equals(param(q, "debug"));
        rawClock = "raw".equals(param(q, "clock"));
        movesEl = (HTMLElement) doc.getElementById("moves-list");
        if (movesEl != null) {
            Dom.show(movesEl, debugNotes);
        }
        DebugApi.install(DebugApi.VERSION,
                () -> MovesLog.toJson(moves == null ? new java.util.ArrayList<>() : moves.recent()),
                () -> MovesLog.toJson(moves == null ? new java.util.ArrayList<>() : moves.first20()),
                () -> moves == null ? 0 : moves.size(),
                () -> ControlMode.id(mode),
                () -> clock.now(),
                () -> moves == null ? -1 : moves.verifyKept(),
                Sha256::hex);
        Dom.onVisibilityChange(Main::visibilityChanged);
        String connectomeUrl = param(q, "connectome");
        Long fromUrl = parseSeed(q);
        if (fromUrl != null) {
            seed = fromUrl;
        }
        audioParam = param(q, "audio");
        String chartUrl = param(q, "chart");
        if (chartUrl == null && audioParam != null && !"none".equals(audioParam)) {
            audio = new AudioSync(audioParam); // generated chart, audio clock, offset 0
        }
        baseAudio = audio;
        // Euclidean rhythm is the default song; ?seed= / ?chart= keep the legacy charts; ?rhythm=<id> / ?bpm=N pick one.
        int fromRhythm = EuclidSong.indexOf(param(q, "rhythm"));
        String bpmParam = param(q, "bpm");
        for (int i = 0; i < EuclidSong.BPMS.length; i++) {
            if (String.valueOf(EuclidSong.BPMS[i]).equals(bpmParam)) {
                bpmIdx = i;
            }
        }
        if (fromRhythm >= 0) {
            rhythmIdx = fromRhythm;
        } else if (fromUrl == null && chartUrl == null && pickers) {
            rhythmIdx = 0;
        }
        int fromSource = SongSource.indexOf(param(q, "source"));
        if (fromSource >= 0 && sourceBtn != null) {
            source = fromSource;
        }
        for (int i = 0; i < VoiceSong.LINES.length; i++) {
            if (VoiceSong.LINES[i][0].equals(param(q, "voice"))) {
                voiceLine = i;
            }
        }
        applyRhythm();
        if (chartUrl != null) {
            loadChart(chartUrl);
        }
        if (connectomeUrl != null) {
            loadConnectome(connectomeUrl);
        }
        doc.addEventListener("keydown", evt -> {
            onKey((KeyboardEvent) evt);
            refreshNow();
        });
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

    /** Fetch a connectome XML (connectome.xsd format). On failure the toy circuit stays. */
    private static void loadConnectome(String url) {
        XMLHttpRequest xhr = XMLHttpRequest.create();
        xhr.open("GET", url);
        xhr.onComplete(() -> {
            int code = xhr.getStatus();
            String text = xhr.getResponseText();
            if (code != 200 && !(code == 0 && text != null && !text.isEmpty())) {
                status = "Connectome load failed (HTTP " + code + ")";
                return;
            }
            try {
                Circuit c = ConnectomeXml.parse(text);
                for (int l = 0; l < RhythmGame.LANES; l++) {
                    ConnectomeAutoplayer.measureLatencyMs(c, l); // lane neurons present and reachable
                }
                circuit = c;
                circuitName = url;
                if (!running) {
                    reset();
                }
            } catch (IllegalArgumentException e) {
                status = "Bad connectome: " + e.getMessage();
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
        baseLoaded = c;
        baseAudio = src == null ? null : new AudioSync(src);
        status = "";
        applyRhythm();
    }

    /** Same no-focus rules as the AUTOPLAY button; a tap runs {@code onTap} between songs, shows the lock hint mid-song. */
    private static void wirePicker(HTMLElement btn, Runnable onTap) {
        btn.addEventListener("pointerdown", evt -> evt.preventDefault());
        btn.addEventListener("mousedown", evt -> evt.preventDefault());
        btn.addEventListener("keydown", evt -> {
            KeyboardEvent k = (KeyboardEvent) evt;
            if (InputRouter.isStartKey(k.getKey(), k.getCode())) {
                evt.preventDefault();
            }
        });
        btn.addEventListener("keyup", evt -> {
            KeyboardEvent k = (KeyboardEvent) evt;
            if (InputRouter.isStartKey(k.getKey(), k.getCode())) {
                evt.preventDefault();
            }
        });
        btn.addEventListener("click", evt -> {
            evt.preventDefault();
            evt.stopPropagation();
            Dom.blur(btn);
            int a = InputRouter.buttonClick(Dom.clickDetail(evt), running);
            if (a == InputRouter.LOCKED) {
                showLockHint(PICKER_LOCK_HINT);
            } else if (a == InputRouter.CYCLE_MODE) {
                onTap.run();
            }
            refreshNow();
        });
    }

    /**
     * Render the HUD and button labels right away, from the state the input
     * just changed. Before this, the DOM text was only written by draw() in
     * the requestAnimationFrame loop, so after a click or key the label kept
     * the previous mode until the next frame ran; with frames throttled or
     * paused (background / occluded window, a screenshot racing the frame)
     * it read one step behind the real mode.
     */
    private static void refreshNow() {
        if (ctx != null && game != null) {
            draw(lastStamp);
        }
    }

    private static void showLockHint(String text) {
        lockHint = text;
        lockHintUntil = lastStamp + ControlMode.LOCK_HINT_MS;
    }

    /** S / the source button: Euclidean -> MIDI -> voice (between songs only). */
    private static void cycleSource() {
        if (running) {
            return;
        }
        source = SongSource.next(source, false);
        applyRhythm();
    }

    /** E / the middle button: Euclidean preset, MIDI file picker, or the voice line, by source. */
    private static void itemTap() {
        if (running) {
            return;
        }
        if (source == SongSource.MIDI) {
            if (midiInput != null) {
                Dom.openFilePicker(midiInput); // inside the tap / key gesture, as browsers require
            } else {
                status = "No MIDI file input on this page";
            }
        } else if (source == SongSource.VOICE) {
            voiceLine = (voiceLine + 1) % VoiceSong.LINES.length;
            applyRhythm();
        } else {
            cycleRhythm();
        }
    }

    /** A local .mid was read: parse it (format 0/1, tempo map), build its chart and synthesised audio. */
    private static void midiPicked(String name, String binary) {
        byte[] bytes = new byte[binary.length()];
        for (int i = 0; i < bytes.length; i++) {
            bytes[i] = (byte) binary.charAt(i);
        }
        try {
            Midi.Song song = Midi.parse(bytes);
            LoadedChart c = MidiSong.chart(song, SongSource.midiLabel(name));
            midiUri = "none".equals(audioParam) ? null : MidiSong.dataUri(song);
            midiChart = c;
            midiName = name;
            status = "";
        } catch (IllegalArgumentException e) {
            status = "Bad MIDI: " + e.getMessage();
            refreshNow();
            return;
        }
        if (!running && source == SongSource.MIDI) {
            applyRhythm();
        }
        refreshNow();
    }

    /** E / the rhythm button: next Euclidean preset, then the seed / ?chart chart, then wrap (between songs only). */
    private static void cycleRhythm() {
        if (running) {
            return;
        }
        rhythmIdx = (rhythmIdx + 1) % (EuclidSong.PRESETS.length + 1);
        applyRhythm();
    }

    /** T / the BPM button: next tempo for the Euclidean songs (between songs only). */
    private static void cycleBpm() {
        if (running) {
            return;
        }
        if (source == SongSource.MIDI) {
            return; // a MIDI file keeps its own tempo map
        }
        bpmIdx = (bpmIdx + 1) % EuclidSong.BPMS.length;
        applyRhythm();
    }

    private static boolean euclidActive() {
        return source == SongSource.EUCLID && rhythmIdx < EuclidSong.PRESETS.length;
    }

    /** Load the picked song: a Euclidean preset with its synthesised track, or the base chart and audio. */
    private static void applyRhythm() {
        if (audio != null) {
            audio.stop();
        }
        Dom.cancelSpeech();
        if (status.startsWith("No MIDI") || status.startsWith("speechSynthesis")) {
            status = "";
        }
        int bpm = EuclidSong.BPMS[bpmIdx];
        if (source == SongSource.MIDI && midiChart != null) {
            loaded = midiChart;
            audio = midiUri == null ? null : new AudioSync(midiUri);
        } else if (source == SongSource.MIDI) {
            loaded = baseLoaded;
            audio = baseAudio;
            status = "No MIDI file yet: tap PICK .MID (seed chart for now)";
        } else if (source == SongSource.VOICE) {
            loaded = VoiceSong.chart(voiceLine, bpm);
            // Clock = a synthesised click track; the syllables are spoken over it as their notes come up.
            audio = "none".equals(audioParam) ? null
                    : new AudioSync(ClickTrack.dataUri(bpm, VoiceSong.durationMs(voiceLine, bpm)));
            speechOk = Dom.hasSpeech();
            status = speechOk ? "" : "speechSynthesis unavailable: syllables shown on stage only";
        } else if (euclidActive()) {
            EuclidSong.Preset p = EuclidSong.PRESETS[rhythmIdx];
            loaded = EuclidSong.chart(p, bpm);
            audio = "none".equals(audioParam) ? null : new AudioSync(EuclidTrack.dataUri(p, bpm));
        } else {
            loaded = baseLoaded;
            audio = baseAudio;
        }
        reset();
    }

    private static String rhythmLabel() {
        if (source == SongSource.MIDI) {
            return SongSource.midiLabel(midiName);
        }
        if (source == SongSource.VOICE) {
            return VoiceSong.LINES[voiceLine][1];
        }
        if (euclidActive()) {
            return EuclidSong.PRESETS[rhythmIdx].label;
        }
        return baseLoaded != null ? "JSON CHART" : "SEED CHART";
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
        wired = new ConnectomeAutoplayer(game, circuit);
        arbiter = new AssistArbiter(game);
        flyLif = new LifAutoplayer(game, AssistArbiter.FLY_AIM_MS, arbiter);
        flyWired = new ConnectomeAutoplayer(game, circuit, AssistArbiter.FLY_AIM_MS, arbiter);
        attachFly();
        sabers = new SaberRig();
        running = false;
        lockHintUntil = 0;
        voiceSpoken = -1;
        if (audio != null) {
            audio.stop();
        }
        clock = new SongClock(loaded != null ? loaded.offsetMs() : 0, !rawClock);
        moves = new MovesLog(game, mode, null);
        pausedHidden = false;
        resumePending = false;
        if (movesEl != null && debugNotes) {
            setText(movesEl, Move.stageHeader());
        }
    }

    /** The active fly brain's cue probe for the moves list (null when no fly plays). */
    private static CueProbe probeFor(int m) {
        switch (m) {
            case MODE_LIF: return brain.probe();
            case MODE_CONNECTOME: return wired.probe();
            case MODE_ASSIST_LIF: return flyLif.probe();
            case MODE_ASSIST_CONNECTOME: return flyWired.probe();
            default: return null;
        }
    }

    /**
     * Tab hidden mid-song: requestAnimationFrame stops but an audio element
     * keeps playing, so notes would pass unplayed. Pause audio and clock;
     * on visible, resume the audio where it stopped (no rewind) and re-anchor
     * the clock on the next frame's stamp.
     */
    private static void visibilityChanged(boolean hidden) {
        if (hidden) {
            if (running && !pausedHidden) {
                pausedHidden = true;
                resumePending = false;
                clock.pause();
                if (audio != null) {
                    audio.pause();
                }
                Dom.cancelSpeech();
            }
        } else if (pausedHidden) {
            if (audio != null) {
                audio.resume();
            }
            resumePending = true;
        }
        refreshNow();
    }

    /** Append the rows settled by song time t; with ?debug=notes log each and refresh the stage list. */
    private static void recordMoves(long t) {
        if (moves == null) {
            return;
        }
        List<Move> fresh = moves.update(t);
        if (fresh.isEmpty() || !debugNotes) {
            return;
        }
        for (Move m : fresh) {
            Dom.log(m.logLine());
        }
        if (movesEl != null) {
            StringBuilder b = new StringBuilder(Move.stageHeader());
            for (Move m : moves.tail(STAGE_ROWS)) {
                b.append('\n').append(m.stageLine());
            }
            setText(movesEl, b.toString());
        }
    }

    private static boolean assist() {
        return ControlMode.isAssist(mode);
    }

    /** Key C and the AUTOPLAY button: off -> LIF -> connectome -> assist LIF -> assist connectome (between songs only). */
    private static void cycleMode() {
        mode = ControlMode.cycle(mode, running);
        attachFly();
    }

    /** CYCLE_MODE / TOGGLE_LIF / LOCKED from InputRouter; anything else is ignored. */
    private static void applyModeAction(int action, boolean lifToggle) {
        if (action == InputRouter.LOCKED) {
            showLockHint(ControlMode.LOCK_HINT); // the lock stays; now it says so
        } else if (action == InputRouter.CYCLE_MODE) {
            cycleMode();
        } else if (action == InputRouter.TOGGLE_LIF && lifToggle) {
            mode = ControlMode.toggleLif(mode, running);
            attachFly();
        }
    }

    /** The arbiter advances the selected fly brain before each human press. */
    private static void attachFly() {
        if (mode == MODE_ASSIST_CONNECTOME) {
            arbiter.attachBrain(flyWired::advanceTo);
        } else {
            arbiter.attachBrain(flyLif::advanceTo);
        }
    }

    /** Advance whichever brain the mode uses to song time; its spikes become presses. */
    private static void advanceBrain(long t) {
        switch (mode) {
            case MODE_LIF: brain.advanceTo(t); break;
            case MODE_CONNECTOME: wired.advanceTo(t); break;
            case MODE_ASSIST_LIF: flyLif.advanceTo(t); break;
            case MODE_ASSIST_CONNECTOME: flyWired.advanceTo(t); break;
            default: break;
        }
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
        // Prefer Dom.isTypingTarget(): TeaVM stopPropagation on #chat-input is not enough
        // when the document listener still sees the native keydown.
        if (Dom.isTypingTarget() || (cliClient != null && cliClient.inputFocused())) {
            return; // typing in #chat-input / CLI column — do not steal D F J K / Space
        }
        String key = e.getKey();
        String code = e.getCode();
        int action = InputRouter.key(key, code, e.isRepeat(), running);
        switch (action) {
            case InputRouter.CYCLE_MODE:
            case InputRouter.TOGGLE_LIF:
                // Only switchable between songs, so a score is all-brain or all-human.
                applyModeAction(action, true);
                return;
            case InputRouter.LOCKED:
                boolean songKey = "KeyE".equals(code) || "KeyT".equals(code) || "KeyS".equals(code)
                        || "e".equalsIgnoreCase(key) || "t".equalsIgnoreCase(key) || "s".equalsIgnoreCase(key);
                showLockHint(songKey ? PICKER_LOCK_HINT : ControlMode.LOCK_HINT);
                return;
            case InputRouter.CYCLE_RHYTHM:
                itemTap();
                return;
            case InputRouter.CYCLE_SOURCE:
                cycleSource();
                return;
            case InputRouter.CYCLE_BPM:
                cycleBpm();
                return;
            case InputRouter.START:
                if (game.isFinished()) {
                    reset();
                }
                running = true;
                lockHintUntil = 0;
                moves = new MovesLog(game, mode, probeFor(mode));
                clock.start(lastStamp, audio != null && audio.isOk());
                if (audio != null) {
                    audio.play();
                }
                e.preventDefault();
                return;
            case InputRouter.CONSUME:
                e.preventDefault();
                return;
            case InputRouter.NEW_SEED:
                if (loaded == null) {
                    seed = seed * 31 + 7;
                    reset();
                }
                return;
            case InputRouter.RESTART:
                reset();
                return;
            case InputRouter.LANE:
                if (pausedHidden) {
                    return;
                }
                break;
            default:
                return;
        }
        if (ControlMode.isFullAutoplay(mode)) {
            return;
        }
        int lane = RhythmGame.laneForKey(code != null && !code.isEmpty() ? code : key);
        if (lane < 0) {
            return;
        }
        e.preventDefault();
        laneFlashUntil[lane] = lastStamp + FLASH_MS;
        long pressMs = sampleSongTime(lastStamp); // fresh audio position at the key press
        Judgement j = assist() ? arbiter.human(lane, pressMs) : game.press(lane, pressMs);
        if (j != null) {
            banner = j.name();
            bannerUntil = lastStamp + 400;
        }
    }

    private static void frame(double stamp) {
        lastStamp = stamp;
        if (resumePending) {
            resumePending = false;
            pausedHidden = false;
            clock.resume(stamp); // the hidden time is not added to song time
        }
        if (running && !pausedHidden) {
            sampleSongTime(stamp);
            int missesBefore = game.missCount();
            if (mode != MODE_OFF) {
                int hitsBefore = game.perfectCount() + game.greatCount() + game.goodCount();
                advanceBrain(songTime()); // spikes become presses at their substep times
                if (game.perfectCount() + game.greatCount() + game.goodCount() != hitsBefore) {
                    banner = game.lastJudgement().name();
                    bannerUntil = stamp + 400;
                }
            }
            game.update(songTime());
            if (source == SongSource.VOICE && speechOk) {
                int idx = VoiceSong.currentIndex(voiceLine, EuclidSong.BPMS[bpmIdx], songTime() + VoiceSong.SPEAK_LEAD_MS);
                if (idx > voiceSpoken) {
                    voiceSpoken = idx;
                    speechOk = Dom.speak(VoiceSong.syllableAt(voiceLine, idx)); // false -> degrade to text only
                    if (!speechOk) {
                        status = "speechSynthesis failed: syllables shown on stage only";
                    }
                }
            }
            if (game.missCount() != missesBefore) {
                banner = "MISS";
                bannerUntil = stamp + 400;
            }
            recordMoves(songTime());
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

    private static String laneLabel(int l) {
        String r = ConnectomeAutoplayer.laneLabel(circuit, l);
        return r != null ? r : REGION_LABELS[l];
    }

    /** ms since each neuron's last spike in the connectome autoplayer (-1 = never); null unless that mode is on. */
    private static double[] msSinceSpike() {
        if (mode != MODE_CONNECTOME && mode != MODE_ASSIST_CONNECTOME) {
            return null;
        }
        CircuitSim sim = (mode == MODE_CONNECTOME ? wired : flyWired).sim();
        double[] out = new double[circuit.neuronCount()];
        long now = songTime();
        for (int i = 0; i < out.length; i++) {
            long last = sim.lastSpikeSubstep(i);
            out[i] = last == Long.MIN_VALUE ? -1 : now - last * 1.0;
        }
        return out;
    }

    private static void line(StringBuilder b, String s) {
        if (b.length() > 0) {
            b.append('\n');
        }
        b.append(s);
    }

    @JSBody(params = {"el", "s"}, script = "if (el.textContent !== s) { el.textContent = s; }")
    private static native void setText(HTMLElement el, String s);

    private static void draw(double stamp) {
        // Reset to the DPR transform every frame, then draw in logical CSS px.
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        ctx.setGlobalAlpha(1);
        double ui = layout.uiScale;
        double laneW = layout.laneWidth;

        // 1. Background: live camera (?camera=1), else the AR screenshot, dimmed; else flat.
        if (camera != null && !cameraReported) {
            String err = Dom.cameraError(camera);
            if (err != null) {
                status = "camera unavailable (" + err + "): using screenshot";
                cameraReported = true;
            }
        }
        boolean bg = camera != null && Dom.drawCover(ctx, camera, width, height);
        if (!bg && background != null) {
            bg = Dom.drawCover(ctx, background, width, height);
        }
        ctx.setFillStyle(bg && theme.dim != null ? theme.dim : theme.backdrop);
        ctx.fillRect(0, 0, width, height);
        // 2. The 3D stage (display only). Song time drives everything; frozen on the title screen.
        sabers.sync(game.chart());
        double sinceCut = songTime() - NoteBlocks.lastCutAt(game.chart(), songTime());
        if (sinceCut >= 0 && sinceCut < SHAKE_MS) { // tiny screen shake on a slice: <= 4 CSS px, 60 ms
            double a = SHAKE_PX * (1 - sinceCut / SHAKE_MS);
            ctx.translate(a * Math.sin(sinceCut * 0.9), 0.6 * a * Math.cos(sinceCut * 1.3));
        }
        boolean[] flashing = new boolean[RhythmGame.LANES];
        for (int l = 0; l < RhythmGame.LANES; l++) {
            flashing[l] = laneFlashUntil[l] > stamp;
        }
        StageRenderer.draw(ctx, layout, theme, clock.now(), circuit, msSinceSpike(), game.chart(), sabers, flashing);

        // 3. Key bar: the notes themselves are the 3D blocks; keys sit under their lanes' hit-plane x.
        ctx.setFillStyle(theme.hitLine);
        ctx.fillRect(0, hitY - 1, width, 2);
        Scene3D cam = layout.camera();
        double[] keyX = new double[RhythmGame.LANES];
        for (int l = 0; l < RhythmGame.LANES; l++) {
            double[] p = cam.project(NoteBlocks.LANE_X[l], 0, NoteBlocks.Z_HIT);
            keyX[l] = p != null ? p[0] : l * laneW + laneW / 2.0;
        }

        ctx.setFont("bold " + Math.round(20 * ui) + "px monospace");
        ctx.setTextAlign("center");
        for (int l = 0; l < RhythmGame.LANES; l++) {
            ctx.setFillStyle(theme.laneKey);
            ctx.fillText(RhythmGame.LANE_KEYS[l], keyX[l], hitY + 34 * ui);
        }
        // Labels sit under the projected lanes; shrink the font so the longest fits the lane spacing.
        int longest = 1;
        for (int l = 0; l < RhythmGame.LANES; l++) {
            longest = Math.max(longest, laneLabel(l).length());
        }
        double spacing = (keyX[RhythmGame.LANES - 1] - keyX[0]) / (RhythmGame.LANES - 1);
        ctx.setFont(Math.round(Math.min(11 * ui, 0.92 * spacing / (0.6 * longest))) + "px monospace");
        for (int l = 0; l < RhythmGame.LANES; l++) {
            ctx.setFillStyle(theme.laneLabel);
            ctx.fillText(laneLabel(l), keyX[l], hitY + 54 * ui);
        }

        // 4. HUD (HTML overlay when present).
        hl.setLength(0);
        hr.setLength(0);
        hc.setLength(0);
        line(hl, "Score " + game.score());
        line(hl, "Combo " + game.combo() + "  x" + RhythmGame.multiplierFor(game.combo()));
        line(hl, "Miss " + game.missCount());
        // Counted at the judged press, like score / combo; the split animation follows at blade contact (+41 ms).
        line(hl, "blocks cut " + NoteBlocks.hitCount(game.chart(), songTime()));
        if (loaded != null || audio != null) {
            boolean audioClock = running ? clock.isAudioMode() : audio != null && audio.isOk();
            if (running && audioClock && !pausedHidden && audio != null && audio.isBuffering()) {
                line(hl, "clock: audio buffering");
            } else {
                line(hl, audioClock ? "clock audio" : "clock frame");
            }
        }
        line(hr, loaded != null ? loaded.title() : "seed " + seed);
        line(hr, ControlMode.hudText(mode));
        if (mode == MODE_LIF) {
            line(hr, "spikes " + brain.spikeCount());
        } else if (mode == MODE_CONNECTOME) {
            line(hr, "spikes " + wired.spikeCount() + " \u00b7 keys " + wired.pressCount());
        } else if (assist()) {
            line(hr, "you " + arbiter.humanHits() + " \u00b7 fly " + arbiter.flyHits());
        }
        if (mode == MODE_CONNECTOME || mode == MODE_ASSIST_CONNECTOME) {
            line(hr, "circuit " + circuitName + " (" + circuit.neuronCount() + " neurons)");
        }
        if (!status.isEmpty()) {
            line(hc, status.length() > 60 ? status.substring(0, 57) + "..." : status);
        }
        if (pausedHidden) {
            line(hc, PAUSED_TEXT);
        }
        if (lockHintUntil > stamp && running) {
            line(hc, lockHint);
        }
        if (bannerUntil > stamp && running) {
            line(hc, banner);
        }
        if (euclidActive()) {
            for (String s : EuclidSong.hudLines(EuclidSong.PRESETS[rhythmIdx])) {
                line(hc, s); // the active pattern(s) as x/. strings, one per lane
            }
        }
        if (source == SongSource.VOICE) {
            int at = running ? VoiceSong.currentIndex(voiceLine, EuclidSong.BPMS[bpmIdx], songTime()) : -1;
            line(hc, at >= 0 ? "\u266a " + VoiceSong.syllableAt(voiceLine, at) : "\u266a " + VoiceSong.LINES[voiceLine][2]);
        }
        if (!running) {
            if (game.isFinished()) {
                line(hc, "Song complete");
                line(hc, "P " + game.perfectCount() + "  Gr " + game.greatCount()
                        + "  Go " + game.goodCount() + "  M " + game.missCount());
                line(hc, "Max combo " + game.maxCombo() + "  Acc " + Math.round(game.accuracy() * 1000) / 10.0 + "%");
                line(hc, "Space to play again");
            } else {
                if (loaded != null) {
                    line(hc, loaded.artist() + " \u00b7 " + game.chart().notes().size() + " notes");
                }
                line(hc, "Press Space to start");
                line(hc, loaded != null ? "D F J K hit \u00b7 R restart" : "D F J K hit \u00b7 R restart \u00b7 N new seed");
                if (!euclidActive() && source == SongSource.EUCLID) {
                    line(hc, "B toggles the LIF autoplayer");
                }
                line(hc, autoplayBtn != null ? "C or AUTOPLAY button: change mode" : "C cycles off / LIF / connectome / assist");
            }
        }
        if (autoplayBtn != null) {
            setText(autoplayBtn, ControlMode.buttonLabel(mode, running));
            Dom.setClass(autoplayBtn, running ? "locked" : "");
            Dom.setTitle(autoplayBtn, ControlMode.buttonTitle(running));
        }
        if (rhythmBtn != null && bpmBtn != null) {
            boolean ownTempo = euclidActive() || source == SongSource.VOICE;
            setText(rhythmBtn, rhythmLabel());
            setText(bpmBtn, ownTempo ? EuclidSong.bpmLabel(EuclidSong.BPMS[bpmIdx]) : source == SongSource.MIDI ? "FILE BPM" : "-- BPM");
            Dom.setClass(rhythmBtn, running ? "picker locked" : "picker");
            Dom.setClass(bpmBtn, running || !ownTempo ? "picker locked" : "picker");
            Dom.setTitle(rhythmBtn, running ? PICKER_LOCK_HINT : source == SongSource.MIDI ? "Pick a local .mid file (key E)"
                    : source == SongSource.VOICE ? "Spoken line (key E)" : "Song: Euclidean rhythm preset (key E)");
            Dom.setTitle(bpmBtn, running ? PICKER_LOCK_HINT : "Tempo for Euclidean and voice songs (key T)");
        }
        if (sourceBtn != null) {
            setText(sourceBtn, SongSource.label(source));
            Dom.setClass(sourceBtn, running ? "picker locked" : "picker");
            Dom.setTitle(sourceBtn, running ? PICKER_LOCK_HINT : "Music source: Euclidean / MIDI file / TTS voice (key S)");
        }
        if (hudL != null && hudR != null && hudC != null) {
            setText(hudL, hl.toString());
            setText(hudR, hr.toString());
            setText(hudC, hc.toString());
        } else {
            canvasHud(ui);
        }
    }

    /** Fallback when the page has no HUD overlay elements. */
    private static void canvasHud(double ui) {
        ctx.setFont(Math.round(16 * ui) + "px monospace");
        ctx.setFillStyle(theme.hudText);
        String[][] cols = {hl.toString().split("\n"), hr.toString().split("\n"), hc.toString().split("\n")};
        ctx.setTextAlign("left");
        for (int i = 0; i < cols[0].length; i++) {
            ctx.fillText(cols[0][i], 10, (24 + 22 * i) * ui);
        }
        ctx.setTextAlign("right");
        for (int i = 0; i < cols[1].length; i++) {
            ctx.fillText(cols[1][i], width - 10, (24 + 22 * i) * ui);
        }
        ctx.setTextAlign("center");
        for (int i = 0; i < cols[2].length; i++) {
            if (!cols[2][i].isEmpty()) {
                ctx.fillText(cols[2][i], width / 2.0, height * 0.21 + 26 * ui * i);
            }
        }
    }
}
