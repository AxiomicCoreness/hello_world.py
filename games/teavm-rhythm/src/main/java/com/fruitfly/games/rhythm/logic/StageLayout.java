package com.fruitfly.games.rhythm.logic;

/**
 * Screen layout of the play field for a given canvas size in CSS px, from
 * back to front: background (image or camera), the 3D stage (ground grid,
 * origin anchor, fly-brain object), the four lanes, then the HUD.
 *
 * Sized for an iPhone 12 (A14 Bionic: 390 x 844 CSS px at devicePixelRatio
 * 3, a 1170 x 2532 backing canvas) and scales to desktop sizes. The stage
 * sits in the upper part of the screen so the hit line stays clear.
 */
public final class StageLayout {
    /** iPhone 12 / 12 Pro viewport, CSS px, and its device pixel ratio. */
    public static final int IPHONE12_W = 390;
    public static final int IPHONE12_H = 844;
    public static final int IPHONE12_DPR = 3;
    /** Default desktop / headless size (unchanged from the original game). */
    public static final int DEFAULT_W = 400;
    public static final int DEFAULT_H = 600;

    public final int width;
    public final int height;
    public final int hitY;
    public final double laneWidth;
    /** Stage camera: fixed, level (pitch 0), so the floor's vanishing point sits at mid-height. */
    public static final double CAMERA_DISTANCE = 6.0;
    public static final double FOV_Y = Math.toRadians(45);
    /** Screen height fraction where the centre tile's middle (the origin) lands. */
    public static final double TILE_SCREEN_Y = 0.74;
    public final double horizonY;
    public final double tileY;
    /** Centre tile half-size (world units): the fly stands on [-TILE_HALF, TILE_HALF]^2. */
    public static final double TILE_HALF = 0.6;
    /** Font scale for HUD text: 1 at 400 px wide. */
    public final double uiScale;

    private StageLayout(int width, int height) {
        this.width = width;
        this.height = height;
        this.hitY = height - Math.max(80, (int) Math.round(height * 2.0 / 15.0));
        this.laneWidth = width / (double) RhythmGame.LANES;
        this.horizonY = height * 0.5;
        this.tileY = height * TILE_SCREEN_Y;
        this.uiScale = Math.max(0.9, Math.min(1.6, width / 400.0));
    }

    /**
     * The fixed stage camera: eye at (0, E, D) looking level at (0, E, 0),
     * with E chosen so the origin (centre of the floor tile) projects to
     * {@link #tileY}. The ground's vanishing point is (width/2, horizonY).
     */
    public Scene3D camera() {
        double f = Scene3D.focalForFov(FOV_Y, height);
        double eyeY = (tileY - horizonY) * CAMERA_DISTANCE / f;
        return new Scene3D(0, 0, CAMERA_DISTANCE, f, width / 2.0, horizonY, eyeY);
    }

    /** HUD overlay text (#hud-l / #hud-r): top offset, font px and line height (index.html), and its most lines (left column). */
    public static final double HUD_TOP = 8;
    public static final double HUD_FONT_PX = 16;
    public static final double HUD_LINE = 1.4;
    public static final int HUD_MAX_LINES = 5;
    /** On-screen AUTOPLAY button: at least the 44 CSS px touch-target size; label font px (monospace, ~0.6 em per char). */
    public static final double BUTTON_MIN_TAP = 44;
    public static final double BUTTON_FONT_PX = 13;
    public static final double BUTTON_GAP = 4;
    /** Gap between the button and the centre text block (#hud-c) below it. */
    public static final double CENTER_GAP = 6;

    /** Bottom of the corner HUD text at its tallest (5 lines). */
    public double hudBottom() {
        return HUD_TOP + HUD_MAX_LINES * HUD_FONT_PX * HUD_LINE;
    }

    /**
     * The AUTOPLAY button rectangle {x, y, w, h} in CSS px: a centred strip
     * just under the corner HUD, above the centre text (title prompt / judgement
     * banner) and far above the horizon, lanes, hit line, key labels and caption.
     */
    public double[] autoplayButton() {
        double h = BUTTON_MIN_TAP;
        double fit = ControlMode.longestButtonLabel() * 0.62 * BUTTON_FONT_PX + 24;
        double w = Math.floor(Math.min(width - 20, Math.max(fit, 220)));
        return new double[] {Math.round((width - w) / 2.0), hudBottom() + BUTTON_GAP, w, h};
    }

    /** Top of the centre text block (#hud-c), just under the AUTOPLAY button. */
    public double centerTextTop() {
        double[] b = autoplayButton();
        return b[1] + b[3] + CENTER_GAP;
    }

    /** Song picker row: label font px and the gap between its buttons. */
    public static final double PICKER_FONT_PX = 12;
    public static final double PICKER_GAP = 6;

    /**
     * The song-picker row under the AUTOPLAY button: same horizontal span,
     * one 44 px tall tap target per weight (widths proportional to the
     * weights, {@link #PICKER_GAP} apart). Returns {x, y, w, h} per button.
     */
    public double[][] pickerRow(double... weights) {
        double[] a = autoplayButton();
        double sum = 0;
        for (double w : weights) {
            sum += w;
        }
        double free = a[2] - PICKER_GAP * (weights.length - 1);
        double[][] out = new double[weights.length][];
        double x = a[0];
        for (int i = 0; i < weights.length; i++) {
            double w = i == weights.length - 1 ? a[0] + a[2] - x : Math.floor(free * weights[i] / sum);
            out[i] = new double[] {x, a[1] + a[3] + BUTTON_GAP, w, BUTTON_MIN_TAP};
            x += w + PICKER_GAP;
        }
        return out;
    }

    /** Top of the centre text when the picker row is shown. */
    public double centerTextTopBelowPickers() {
        double[] a = autoplayButton();
        return a[1] + a[3] + BUTTON_GAP + BUTTON_MIN_TAP + CENTER_GAP;
    }

    /** Baseline of the TOY caption: the bottom strip, below the key labels, clear of the HUD title text. */
    public double captionY() {
        return height - 8 * uiScale;
    }

    public static StageLayout of(int width, int height) {
        if (width < 200 || height < 300) {
            throw new IllegalArgumentException("canvas too small: " + width + "x" + height);
        }
        return new StageLayout(width, height);
    }

    /**
     * Pick the canvas size (CSS px). {@code device} "iphone12" forces 390x844.
     * A narrow viewport (&lt; 600 px, i.e. a phone) fills the screen. A desktop
     * viewport gets a phone-shaped field as tall as fits, 600..960 px. With
     * no viewport info (0, e.g. headless smoke test) the 400x600 default.
     */
    public static StageLayout choose(String device, int viewportW, int viewportH) {
        if ("iphone12".equals(device)) {
            return of(IPHONE12_W, IPHONE12_H);
        }
        if (viewportW <= 0 || viewportH <= 0) {
            return of(DEFAULT_W, DEFAULT_H);
        }
        if (viewportW < 600) {
            return of(Math.max(200, viewportW), Math.max(300, viewportH));
        }
        int h = Math.max(DEFAULT_H, Math.min(960, viewportH - 32));
        int w = Math.max(DEFAULT_W, (int) Math.round(h * IPHONE12_W / (double) IPHONE12_H * 1.15));
        return of(w, h);
    }

    /** Backing-store pixels for a device pixel ratio (NaN / &lt; 1 treated as 1, capped at 4). */
    public static int backing(int cssPx, double dpr) {
        double d = dpr >= 1.0 && dpr <= 4.0 ? dpr : (dpr > 4.0 ? 4.0 : 1.0);
        return (int) Math.round(cssPx * d);
    }
}
