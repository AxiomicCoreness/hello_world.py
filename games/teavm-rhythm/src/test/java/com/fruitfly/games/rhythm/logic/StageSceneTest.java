package com.fruitfly.games.rhythm.logic;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

/** Stage camera, sabers (pivot arc), phantom blocks (paths, 3D hits, respawn). */
class StageSceneTest {
    private static final double EPS = 1e-9;
    private static final StageLayout PHONE = StageLayout.of(390, 844);

    @Test
    void stageCameraPutsVanishingPointMidHeightAndTileBottomCentre() {
        for (StageLayout l : new StageLayout[] {PHONE, StageLayout.of(510, 960), StageLayout.of(400, 600)}) {
            Scene3D cam = l.camera();
            double[] o = cam.project(0, 0, 0);
            assertEquals(l.width / 2.0, o[0], EPS);
            assertEquals(l.tileY, o[1], 1e-6);
            double[] far = cam.project(3, 0, -1e7);
            assertEquals(l.width / 2.0, far[0], 1e-3);
            assertEquals(l.horizonY, far[1], 1e-3, "ground converges to the mid-height vanishing point");
            for (double[] c : new double[][] {{-1, 0, -1}, {1, 0, -1}, {-1, 0, 1}, {1, 0, 1}}) {
                double[] p = cam.project(c[0], c[1], c[2]);
                assertTrue(p[0] > 0 && p[0] < l.width && p[1] > l.horizonY && p[1] < l.hitY, "tile corner on screen");
            }
        }
    }

    @Test
    void brainIsShrunkAndSeatedAboveTheTile() {
        double[] top = BrainStage.place(BrainStage.regionPosition(BrainStage.regionIndex("medulla")), 0.7);
        double[] low = BrainStage.place(BrainStage.regionPosition(BrainStage.regionIndex("lamina")), 2.1);
        assertTrue(top[1] < 1.4 && low[1] > BrainStage.BASE_Y);
        for (int r = 0; r < BrainStage.REGIONS.length; r++) {
            double[] p = BrainStage.place(BrainStage.regionPosition(r), 1.3);
            assertTrue(Math.abs(p[0]) < 0.35 && Math.abs(p[2]) < 0.35, "within the tile");
        }
    }

    // ---- sabers ----

    @Test
    void saberPivotsAboutTheHandAndNeverTranslates() {
        SaberRig rig = new SaberRig();
        rig.trigger(0, 1000);
        rig.trigger(1, 1200);
        for (double t = 0; t < 2000; t += 3.7) {
            for (int side = 0; side < 2; side++) {
                double[][] seg = rig.segment(side, t);
                assertArrayEquals(SaberRig.HANDS[side], seg[0], 0.0, "base is the hand at t=" + t);
                double len = Math.sqrt(Math.pow(seg[1][0] - seg[0][0], 2) + Math.pow(seg[1][1] - seg[0][1], 2)
                        + Math.pow(seg[1][2] - seg[0][2], 2));
                assertEquals(SaberRig.LENGTH, len, 1e-12, "rigid length");
            }
        }
    }

    @Test
    void swingArcIsIdleOutwardFastInwardThenRecovery() {
        assertEquals(SaberRig.IDLE, SaberRig.angleAt(-1), 0.0);
        assertEquals(SaberRig.IDLE, SaberRig.angleAt(0), EPS);
        assertEquals(SaberRig.STRIKE, SaberRig.angleAt(SaberRig.SWING_MS), EPS);
        assertEquals(SaberRig.IDLE, SaberRig.angleAt(SaberRig.SWING_MS + SaberRig.RECOVER_MS), 0.0);
        double prev = SaberRig.IDLE;
        for (double t = 1; t <= SaberRig.SWING_MS; t++) {
            double a = SaberRig.angleAt(t);
            assertTrue(a < prev, "inward during the arc");
            prev = a;
        }
        for (double t = SaberRig.SWING_MS + 1; t < SaberRig.SWING_MS + SaberRig.RECOVER_MS; t++) {
            double a = SaberRig.angleAt(t);
            assertTrue(a > prev, "outward during recovery");
            prev = a;
        }
        // Arc is fast, recovery slower: average angular speed ratio.
        assertTrue(SaberRig.SWING_MS * 2 < SaberRig.RECOVER_MS);
        // Idle points outward: left tip left of its hand, right tip right of its hand.
        SaberRig rig = new SaberRig();
        assertTrue(rig.segment(0, 0)[1][0] < SaberRig.HANDS[0][0]);
        assertTrue(rig.segment(1, 0)[1][0] > SaberRig.HANDS[1][0]);
        // Mid-swing (strike) the left saber crosses inward past its hand.
        rig.trigger(0, 500);
        assertTrue(rig.segment(0, 590)[1][0] > SaberRig.HANDS[0][0]);
        assertEquals(rig.angle(0, 590), SaberRig.angleAt(90), 0.0, "pure function of song time");
    }

    @Test
    void swingsComeFromJudgedHitsBySide() {
        RhythmGame g = new RhythmGame(NoteChart.generate(2026, 64, 120, 2000));
        SaberRig rig = new SaberRig();
        g.press(g.chart().notes().get(0).lane(), g.chart().notes().get(0).timeMs() + 20);
        rig.sync(g.chart());
        rig.sync(g.chart()); // idempotent
        int side = SaberRig.sideFor(g.chart().notes().get(0).lane());
        assertEquals(1, rig.swingCount(side));
        assertEquals(0, rig.swingCount(1 - side));
        assertTrue(rig.swinging(side, g.chart().notes().get(0).timeMs() + 20));
        g.update(1_000_000); // everything else MISSes: no swings for misses
        rig.sync(g.chart());
        assertEquals(1, rig.swingCount(0) + rig.swingCount(1));
    }

    // ---- 3D hits ----

    @Test
    void capsuleCubeBasics() {
        double[] c = {0, 0, 0};
        assertTrue(StageGeometry.capsuleHitsCube(new double[] {-1, 0, 0}, new double[] {1, 0, 0}, 0.01, c, 0.2, 0));
        assertFalse(StageGeometry.capsuleHitsCube(new double[] {-1, 0.5, 0}, new double[] {1, 0.5, 0}, 0.01, c, 0.2, 0));
        assertTrue(StageGeometry.capsuleHitsCube(new double[] {-1, 0.105, 0}, new double[] {1, 0.105, 0}, 0.01, c, 0.2, 0));
        // Rotated 45 deg: the corner reaches 0.1414 along x.
        assertTrue(StageGeometry.capsuleHitsCube(new double[] {0.13, -1, 0}, new double[] {0.13, 1, 0}, 0.0, c, 0.2, Math.PI / 4));
        assertFalse(StageGeometry.capsuleHitsCube(new double[] {0.13, -1, 0}, new double[] {0.13, 1, 0}, 0.0, c, 0.2, 0));
        // Segment ending short of the cube.
        assertFalse(StageGeometry.capsuleHitsCube(new double[] {-1, 0, 0}, new double[] {-0.5, 0, 0}, 0.01, c, 0.2, 0));
    }

    @Test
    void distantBlockOverlappingOnScreenIsNotHitButNearOneIs() {
        Scene3D cam = PHONE.camera();
        SaberRig rig = new SaberRig();
        rig.trigger(1, 0);
        double t = 60;
        double[][] seg = rig.segment(1, t);
        double[] mid = {(seg[0][0] + seg[1][0]) / 2, (seg[0][1] + seg[1][1]) / 2, (seg[0][2] + seg[1][2]) / 2};
        double[] eye = cam.eye();
        // A point 3x as far along the same camera ray: identical screen position, much deeper.
        double[] far = {eye[0] + 3 * (mid[0] - eye[0]), eye[1] + 3 * (mid[1] - eye[1]), eye[2] + 3 * (mid[2] - eye[2])};
        double[] sMid = cam.project(mid[0], mid[1], mid[2]);
        double[] sFar = cam.project(far[0], far[1], far[2]);
        assertEquals(sMid[0], sFar[0], 1e-6);
        assertEquals(sMid[1], sFar[1], 1e-6);
        assertTrue(sFar[2] > sMid[2] * 2.5);
        // The far cube is bigger in world units so it even covers the saber on screen, yet no 3D contact.
        assertFalse(PhantomBlocks.saberHits(seg, far, 0.6, 0.3), "distant block overlapping on screen must not be hit");
        assertTrue(PhantomBlocks.saberHits(seg, mid, 0.2, 0.3), "block at the saber is hit");
    }

    // ---- phantom block field ----

    @Test
    void pathsSpawnHighLandOnTheTileThenSink() {
        PhantomBlocks f = new PhantomBlocks(2026);
        for (int i = 0; i < PhantomBlocks.COUNT; i++) {
            for (int c = 0; c < 3; c++) {
                double[] s = f.spawn(i, c);
                double[] p0 = f.path(i, c, 0);
                assertEquals(s[0], p0[0], EPS);
                assertEquals(s[1], p0[1], EPS);
                assertEquals(s[2], p0[2], EPS);
                assertTrue(s[1] >= 3.2 && s[2] <= -3, "spawns high and far");
                double sz = f.size(i, c);
                double[] land = f.path(i, c, PhantomBlocks.LAND_U - 1e-12);
                assertEquals(sz / 2, land[1], 1e-6, "rests on the tile");
                assertTrue(Math.abs(land[0]) <= PhantomBlocks.TILE_HALF - sz / 2 && Math.abs(land[2]) <= PhantomBlocks.TILE_HALF - sz / 2);
                double[] sunk = f.path(i, c, 0.999);
                assertTrue(sunk[1] < 0 && sunk[4] < 0.01, "sinks into the tile and fades");
                double[][] k = PhantomBlocks.corners(new double[] {land[0], land[1], land[2]}, sz, land[3]);
                for (int[] e : PhantomBlocks.EDGES) {
                    double d = Math.sqrt(Math.pow(k[e[0]][0] - k[e[1]][0], 2) + Math.pow(k[e[0]][1] - k[e[1]][1], 2)
                            + Math.pow(k[e[0]][2] - k[e[1]][2], 2));
                    assertEquals(sz, d, 1e-12, "cube edge");
                }
            }
        }
    }

    @Test
    void landingJustRespawnsAndTitleScreenIsStill() {
        PhantomBlocks f = new PhantomBlocks(2026);
        f.advance(0, null);
        double[] a = f.view(3, 0);
        f.advance(0, null);
        assertArrayEquals(a, f.view(3, 0), 0.0, "frozen song time -> frozen scene");
        f.advance(60_000, null);
        assertTrue(f.landedCount() >= PhantomBlocks.COUNT * 5, "landed " + f.landedCount());
        assertEquals(0, f.destroyedCount());
        f.advance(10, null); // rewind (restart) resets to the song-time function
        assertEquals(0, f.landedCount());
    }

    @Test
    void depthOrderIsFarToNearAndAllVisibleBlocksAreInFront() {
        Scene3D cam = PHONE.camera();
        PhantomBlocks f = new PhantomBlocks(2026);
        for (double t = 0; t < 20_000; t += 777) {
            f.advance(t, null);
            int[] order = f.depthOrder(cam, t);
            double prev = Double.POSITIVE_INFINITY;
            for (int i : order) {
                double[] v = f.view(i, t);
                double d = cam.toCamera(v[0], v[1], v[2])[2];
                assertTrue(d <= prev);
                prev = d;
                assertNotNull(cam.project(v[0], v[1], v[2]), "in front of the near plane");
            }
        }
    }

    /** Autoplay seed 2026 with the sabers swinging on every hit; returns {destroyed, landed}. */
    private static int[] sabreRun(long frameMs) {
        RhythmGame g = new RhythmGame(NoteChart.generate(2026, 64, 120, 2000));
        LifAutoplayer p = new LifAutoplayer(g);
        SaberRig rig = new SaberRig();
        PhantomBlocks f = new PhantomBlocks(2026);
        long end = g.chart().lastNoteMs() + 1000;
        for (long t = 0; t <= end; t += frameMs) {
            p.advanceTo(t);
            g.update(t);
            rig.sync(g.chart());
            f.advance(t, rig);
        }
        assertEquals(58_800, g.score(), "blocks never touch the rhythm score");
        return new int[] {f.destroyedCount(), f.landedCount()};
    }

    @Test
    void sabersCutBlocksDeterministically() {
        int[] a = sabreRun(16);
        assertArrayEquals(a, sabreRun(16));
        assertArrayEquals(a, sabreRun(7), "frame-rate independent");
        assertArrayEquals(a, sabreRun(33), "frame-rate independent");
        assertArrayEquals(a, sabreRun(17), "odd frame length, off the 2 ms grid");
        assertArrayEquals(new int[] {12, 12}, a, "seed 2026 autoplay: 12 cut, 12 landed");
        assertTrue(a[0] > 0, "some blocks cut: " + a[0]);
        assertTrue(a[1] > 0, "some blocks landed: " + a[1]);
    }

    @Test
    void cutBlockFlashesExpandsFadesThenRespawns() {
        PhantomBlocks f = new PhantomBlocks(2026);
        SaberRig rig = new SaberRig();
        // Find a time when block 0 sits in the right saber's strike: place a swing so its arc meets it.
        double hitT = -1;
        for (long s = 0; s < 120_000 && hitT < 0; s += 350) {
            PhantomBlocks probe = new PhantomBlocks(2026);
            SaberRig r = new SaberRig();
            r.trigger(1, s);
            probe.advance(Math.max(0, s - 1), null);
            probe.advance(s + 350, r);
            if (probe.destroyedCount() > 0) {
                hitT = s;
            }
        }
        assertTrue(hitT >= 0, "a swing eventually cuts a block");
        rig.trigger(1, (long) hitT);
        f.advance(Math.max(0, hitT - 1), null);
        f.advance(hitT + 350, rig);
        assertEquals(1, f.destroyedCount() >= 1 ? 1 : 0);
        int cut = -1;
        for (int i = 0; i < PhantomBlocks.COUNT; i++) {
            if (f.view(i, hitT + 350)[6] >= 0) {
                cut = i;
            }
        }
        if (cut >= 0) {
            double[] fx = f.view(cut, hitT + 350);
            assertTrue(fx[6] > 0 && fx[5] < 1 && fx[3] > f.size(cut, 0), "expanding, fading");
        }
        f.advance(hitT + 350 + PhantomBlocks.FX_MS + 10, rig);
        for (int i = 0; i < PhantomBlocks.COUNT; i++) {
            assertEquals(-1, f.view(i, hitT + 350 + PhantomBlocks.FX_MS + 10)[6], 0.0, "all respawned");
        }
    }
}
