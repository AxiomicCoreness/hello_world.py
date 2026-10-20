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
