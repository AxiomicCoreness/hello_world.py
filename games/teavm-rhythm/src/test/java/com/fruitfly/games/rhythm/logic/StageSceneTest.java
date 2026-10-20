package com.fruitfly.games.rhythm.logic;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import org.junit.jupiter.api.Test;

/** Fixed stage camera, note blocks (approach along lanes to the hit plane), saber swings (pivot, 3D contact). */
class StageSceneTest {
    private static final double EPS = 1e-9;
    private static final StageLayout PHONE = StageLayout.of(390, 844);
    private static final StageLayout[] LAYOUTS = {PHONE, StageLayout.of(510, 960), StageLayout.of(400, 600)};

    // ---- camera ----

    @Test
    void fixedLevelCameraHasOneCentralVanishingPointAndHorizontalHorizon() {
        for (StageLayout l : LAYOUTS) {
            Scene3D cam = l.camera();
            double[] o = cam.project(0, 0, 0);
            assertEquals(l.width / 2.0, o[0], EPS);
            assertEquals(l.tileY, o[1], 1e-6);
            // Every floor line along z (any x) converges to the same point (w/2, horizonY).
            for (double x : new double[] {-30, -1.2, 0, 0.6, 7}) {
                double[] far = cam.project(x, 0, -1e12);
                assertEquals(l.width / 2.0, far[0], 1e-3);
                assertEquals(l.horizonY, far[1], 1e-3);
            }
            // Horizon is level: far points at any x share one screen y.
            assertEquals(cam.project(-500, 0, -1e5)[1], cam.project(500, 0, -1e5)[1], 1e-9);
            // Fixed: the camera does not depend on song time (no orbit).
            assertArrayEquals(l.camera().eye(), cam.eye(), 0.0);
            double h = StageLayout.TILE_HALF;
            for (double[] c : new double[][] {{-h, 0, -h}, {h, 0, -h}, {-h, 0, h}, {h, 0, h}}) {
                double[] p = cam.project(c[0], c[1], c[2]);
                assertTrue(p[0] > 0 && p[0] < l.width && p[1] > l.horizonY && p[1] < l.hitY, "tile corner on screen");
            }
            // All four lanes' hit-plane blocks are on screen, left to right, below the horizon.
            double prevX = -1;
            for (int lane = 0; lane < 4; lane++) {
                double[] p = cam.project(NoteBlocks.LANE_X[lane], NoteBlocks.Y, NoteBlocks.Z_HIT);
                assertTrue(p[0] > prevX && p[0] > 0 && p[0] < l.width && p[1] > l.horizonY && p[1] < l.hitY);
                prevX = p[0];
            }
        }
    }

    @Test
    void captionSitsInTheBottomStripClearOfTheTitleText() {
        for (StageLayout l : LAYOUTS) {
            assertTrue(l.captionY() > l.hitY + 54 * l.uiScale, "below the key labels");
            assertTrue(l.captionY() <= l.height);
            // HUD title block (#hud-c at top 21%, <= 5 lines of ~24 px) ends above the horizon.
            assertTrue(l.height * 0.21 + 5 * 24 < l.horizonY);
        }
    }

    @Test
    void brainIsShrunkAndSeatedAboveTheTile() {
        double[] top = BrainStage.place(BrainStage.regionPosition(BrainStage.regionIndex("medulla")), 0.7);
        double[] low = BrainStage.place(BrainStage.regionPosition(BrainStage.regionIndex("lamina")), 2.1);
        assertTrue(top[1] < 1.4 && low[1] > BrainStage.BASE_Y);
        for (int r = 0; r < BrainStage.REGIONS.length; r++) {
            double[] p = BrainStage.place(BrainStage.regionPosition(r), 1.3);
            assertTrue(Math.abs(p[0]) < StageLayout.TILE_HALF && Math.abs(p[2]) < StageLayout.TILE_HALF, "within the tile");
        }
    }

    // ---- note blocks ----

    @Test
    void blockReachesTheHitPlaneExactlyAtNoteTimeAndIsFartherSmallerNearerTheVanishingPointBefore() {
        for (StageLayout l : LAYOUTS) {
            Scene3D cam = l.camera();
            double vx = l.width / 2.0;
            double vy = l.horizonY;
            for (int lane = 0; lane < 4; lane++) {
                Note n = new Note(lane, 5000);
                double[] atHit = NoteBlocks.centre(n, 5000);
                assertEquals(NoteBlocks.Z_HIT, atHit[2], 0.0, "on the hit plane at time_ms");
                assertEquals(NoteBlocks.LANE_X[lane], atHit[0], 0.0);
                assertEquals(NoteBlocks.APPROACH, NoteBlocks.state(n, 5000));
                double prevDepth = cam.toCamera(atHit[0], atHit[1], atHit[2])[2];
                double[] pHit = cam.project(atHit[0], atHit[1], atHit[2]);
                double prevScale = pHit[3];
                double prevDist = Math.hypot(pHit[0] - vx, pHit[1] - vy);
                for (double t = 4990; t >= 5000 - NoteBlocks.APPROACH_MS; t -= 10) {
                    double[] c = NoteBlocks.centre(n, t);
                    assertTrue(c[2] < NoteBlocks.Z_HIT, "farther before time_ms");
                    double[] p = cam.project(c[0], c[1], c[2]);
                    assertTrue(p[2] > prevDepth && p[3] < prevScale, "deeper and smaller at t=" + t);
                    double dist = Math.hypot(p[0] - vx, p[1] - vy);
                    assertTrue(dist < prevDist, "closer to the vanishing point at t=" + t);
                    prevDepth = p[2];
                    prevScale = p[3];
                    prevDist = dist;
                }
                // Spawn point: at Z_SPAWN, right next to the vanishing point.
                double[] s = NoteBlocks.centre(n, 5000 - NoteBlocks.APPROACH_MS);
                assertEquals(NoteBlocks.Z_SPAWN, s[2], 1e-9);
                double[] ps = cam.project(s[0], s[1], s[2]);
                assertTrue(Math.hypot(ps[0] - vx, ps[1] - vy) < 0.08 * l.height, "spawns at the horizon point");
                assertEquals(NoteBlocks.HIDDEN, NoteBlocks.state(n, 5000 - NoteBlocks.APPROACH_MS - 1));
            }
        }
    }

    @Test
    void missedBlocksPassByAndFade() {
        RhythmGame g = new RhythmGame(TestCharts.of(1, 3, 1000, 500));
        Note n = g.chart().notes().get(0);
        g.update(1000 + Judgement.MAX_WINDOW_MS + 1);
        assertEquals(Judgement.MISS, n.result());
        double t = 1000 + Judgement.MAX_WINDOW_MS + 1;
        assertEquals(NoteBlocks.PASSED, NoteBlocks.state(n, t));
        assertTrue(NoteBlocks.centre(n, t)[2] > NoteBlocks.Z_HIT, "kept going past the hit plane");
        assertTrue(NoteBlocks.alpha(n, t) < 1 && NoteBlocks.alpha(n, t) > 0, "fading");
        assertEquals(NoteBlocks.HIDDEN, NoteBlocks.state(n, 1000 + NoteBlocks.PASS_FADE_MS));
        assertEquals(0, NoteBlocks.cutCount(g.chart(), 1e9), "a MISS is never cut");
    }

    @Test
    void hitBlockIsHeldThenSlicedIntoTwoSeparatingHalvesThenGone() {
        RhythmGame g = new RhythmGame(TestCharts.of(1, 0, 1000, 500));
        Note n = g.chart().notes().get(0);
        g.press(0, 1020);
        double c = NoteBlocks.contactMs(n);
        assertEquals(1020 + SaberRig.CONTACT_MS, c, 0.0);
        assertEquals(NoteBlocks.APPROACH, NoteBlocks.state(n, 1000));
        assertEquals(NoteBlocks.HELD, NoteBlocks.state(n, 1025));
        assertArrayEquals(NoteBlocks.hitCentre(0), NoteBlocks.centre(n, 1025), 0.0, "held at the hit plane");
        assertEquals(0, NoteBlocks.cutCount(g.chart(), c - 0.5));
        assertEquals(1, NoteBlocks.cutCount(g.chart(), c));
        assertEquals(NoteBlocks.SLICED, NoteBlocks.state(n, c + 1));
        double prevGap = -1;
        for (double s = 0; s <= NoteBlocks.SLICE_MS; s += 30) {
            double[][][] h = NoteBlocks.halves(0, s);
            double[] a = mean(h[0]);
            double[] b = mean(h[1]);
            double gap = StageGeometry.distance(a, b);
            assertTrue(gap > prevGap, "halves separate");
            prevGap = gap;
            // The halves sit on opposite sides of the cut plane, apart along its normal (both share the drift).
            double[] nrm = SaberRig.cutNormal(0);
            assertEquals(2 * (NoteBlocks.SIZE / 4 + NoteBlocks.SPLIT * Math.min(1, s / NoteBlocks.SLICE_MS)),
                    StageGeometry.dot(StageGeometry.sub(b, a), nrm), 1e-9);
        }
        assertTrue(NoteBlocks.alpha(n, c + NoteBlocks.SLICE_MS * 0.5) < 1, "fades");
        assertEquals(NoteBlocks.HIDDEN, NoteBlocks.state(n, c + NoteBlocks.SLICE_MS));
    }

    private static double[] mean(double[][] pts) {
        double[] m = new double[3];
        for (double[] p : pts) {
            for (int k = 0; k < 3; k++) {
                m[k] += p[k] / pts.length;
            }
        }
        return m;
    }

    // ---- sabers ----

    @Test
    void saberPivotsAboutTheHandAndNeverTranslates() {
        SaberRig rig = new SaberRig();
        rig.trigger(0, 1000);
        rig.trigger(1, 1030); // overlapping swings on one side chain smoothly
        rig.trigger(3, 1200);
        for (double t = 0; t < 2000; t += 1.7) {
            for (int side = 0; side < 2; side++) {
                double[][] seg = rig.segment(side, t);
                assertArrayEquals(SaberRig.HANDS[side], seg[0], 0.0, "base is the hand at t=" + t);
                assertEquals(SaberRig.LENGTH, StageGeometry.distance(seg[0], seg[1]), 1e-12, "rigid length");
            }
        }
    }

    @Test
    void swingIsContinuousAndIdleOutward() {
        SaberRig rig = new SaberRig();
        assertTrue(rig.segment(0, 0)[1][0] < SaberRig.HANDS[0][0], "left idle points outward");
        assertTrue(rig.segment(1, 0)[1][0] > SaberRig.HANDS[1][0], "right idle points outward");
        rig.trigger(1, 500);
        rig.trigger(0, 500);
        rig.trigger(1, 540); // retrigger mid-strike
        for (int side = 0; side < 2; side++) {
            double[] prev = rig.direction(side, 400);
            for (double t = 400.5; t < 1000; t += 0.5) {
                double[] d = rig.direction(side, t);
                assertTrue(StageGeometry.distance(prev, d) < 0.12, "no jumps at t=" + t + " side " + side);
                prev = d;
            }
            assertArrayEquals(SaberRig.idleDirection(side), rig.direction(side, 2000), 0.0);
        }
        assertTrue(SaberRig.STRIKE_MS < SaberRig.RECOVER_MS, "fast strike, slower recovery");
    }

    /** The core requirement: for every lane, the blade passes through that lane's block at the hit plane. */
    @Test
    void swingCapsuleIntersectsTheLaneBlockAtTheHitPlaneAtContactForAllFourLanes() {
        for (int lane = 0; lane < 4; lane++) {
            int side = SaberRig.sideFor(lane);
            long press = 3000;
            SaberRig rig = new SaberRig();
            rig.trigger(lane, press);
            Note n = new Note(lane, press);
            double[] block = NoteBlocks.centre(n, press);
            assertEquals(NoteBlocks.Z_HIT, block[2], 0.0, "block on the hit plane at hit time");
            double[] aim = SaberRig.aim(lane);
            assertTrue(StageGeometry.distance(SaberRig.HANDS[side], block) < SaberRig.LENGTH - NoteBlocks.SIZE / 2, "in reach");
            double contact = press + SaberRig.CONTACT_MS;
            double[][] seg = rig.segment(side, contact);
            assertArrayEquals(aim, rig.direction(side, contact), 1e-9, "blade points through the block centre");
            assertTrue(StageGeometry.capsuleHitsCube(seg[0], seg[1], SaberRig.RADIUS, block, NoteBlocks.SIZE, 0),
                    "lane " + lane + " blade meets its block at contact");
            // It really passes through: clear of the block when raised and after the follow-through.
            double[][] raised = rig.segment(side, press + SaberRig.LEAD_MS);
            double[][] low = rig.segment(side, press + SaberRig.LEAD_MS + SaberRig.STRIKE_MS);
            assertFalse(StageGeometry.capsuleHitsCube(raised[0], raised[1], SaberRig.RADIUS, block, NoteBlocks.SIZE, 0));
            assertFalse(StageGeometry.capsuleHitsCube(low[0], low[1], SaberRig.RADIUS, block, NoteBlocks.SIZE, 0));
            // The contact pose doesn't touch the other lanes' blocks.
            for (int o = 0; o < 4; o++) {
                if (o != lane) {
                    assertFalse(StageGeometry.capsuleHitsCube(seg[0], seg[1], SaberRig.RADIUS,
                            NoteBlocks.hitCentre(o), NoteBlocks.SIZE, 0), "lane " + lane + " swing vs lane " + o);
                }
            }
        }
    }

    @Test
    void capsuleCubeBasicsAndDepthCorrectness() {
        double[] c = {0, 0, 0};
        assertTrue(StageGeometry.capsuleHitsCube(new double[] {-1, 0, 0}, new double[] {1, 0, 0}, 0.01, c, 0.2, 0));
        assertFalse(StageGeometry.capsuleHitsCube(new double[] {-1, 0.5, 0}, new double[] {1, 0.5, 0}, 0.01, c, 0.2, 0));
        assertTrue(StageGeometry.capsuleHitsCube(new double[] {0.13, -1, 0}, new double[] {0.13, 1, 0}, 0.0, c, 0.2, Math.PI / 4));
        assertFalse(StageGeometry.capsuleHitsCube(new double[] {-1, 0, 0}, new double[] {-0.5, 0, 0}, 0.01, c, 0.2, 0));
        // A block 3x as far along the camera ray overlaps the blade on screen but is not touched in 3D.
        Scene3D cam = PHONE.camera();
        SaberRig rig = new SaberRig();
        rig.trigger(2, 0);
        double[][] seg = rig.segment(1, SaberRig.CONTACT_MS);
        double[] mid = {(seg[0][0] + seg[1][0]) / 2, (seg[0][1] + seg[1][1]) / 2, (seg[0][2] + seg[1][2]) / 2};
        double[] eye = cam.eye();
        double[] far = {eye[0] + 3 * (mid[0] - eye[0]), eye[1] + 3 * (mid[1] - eye[1]), eye[2] + 3 * (mid[2] - eye[2])};
        assertEquals(cam.project(mid[0], mid[1], mid[2])[0], cam.project(far[0], far[1], far[2])[0], 1e-6);
        assertFalse(StageGeometry.capsuleHitsCube(seg[0], seg[1], SaberRig.RADIUS, far, 0.6, 0));
        assertTrue(StageGeometry.capsuleHitsCube(seg[0], seg[1], SaberRig.RADIUS, mid, 0.2, 0));
    }

    @Test
    void cubeCornersAndEdges() {
        double[][] k = StageGeometry.cube(new double[] {1, 2, 3}, 0.4);
        for (int[] e : StageGeometry.EDGES) {
            assertEquals(0.4, StageGeometry.distance(k[e[0]], k[e[1]]), 1e-12);
        }
        for (int[] f : StageGeometry.FACES) {
            assertEquals(0.4, StageGeometry.distance(k[f[0]], k[f[1]]), 1e-12);
            assertEquals(0.4 * Math.sqrt(2), StageGeometry.distance(k[f[0]], k[f[2]]), 1e-12, "quad, not crossed");
        }
    }

    @Test
    void swingsComeFromJudgedHitsBySideAndCutsEqualHits() {
        RhythmGame g = new RhythmGame(NoteChart.generate(2026, 64, 120, 2000));
        LifAutoplayer p = new LifAutoplayer(g);
        SaberRig rig = new SaberRig();
        long end = g.chart().lastNoteMs() + 1000;
        for (long t = 0; t <= end; t += 16) {
            p.advanceTo(t);
            g.update(t);
            rig.sync(g.chart());
            rig.sync(g.chart()); // idempotent
        }
        assertEquals(58_800, g.score(), "rhythm score unchanged");
        int hits = g.perfectCount() + g.greatCount() + g.goodCount();
        assertEquals(64, hits);
        assertEquals(hits, NoteBlocks.cutCount(g.chart(), end));
        int left = 0;
        List<Note> notes = g.chart().notes();
        for (Note n : notes) {
            left += SaberRig.sideFor(n.lane()) == 0 ? 1 : 0;
        }
        assertEquals(left, rig.swingCount(0));
        assertEquals(64 - left, rig.swingCount(1));
        assertNotNull(notes.get(0).result());
    }
}
