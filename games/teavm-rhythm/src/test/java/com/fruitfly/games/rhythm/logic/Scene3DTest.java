package com.fruitfly.games.rhythm.logic;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

class Scene3DTest {
    private static final double EPS = 1e-9;

    @Test
    void targetProjectsToScreenCentreForAnyOrbitAngle() {
        for (double yaw = -7; yaw <= 7; yaw += 0.37) {
            for (double pitch : new double[] {-0.6, 0, 0.3, 1.2}) {
                Scene3D s = new Scene3D(yaw, pitch, 4.0, 500, 195, 300, 0.95);
                double[] p = s.project(0, 0.95, 0);
                assertEquals(195, p[0], EPS, "yaw " + yaw);
                assertEquals(300, p[1], EPS, "yaw " + yaw);
                assertEquals(4.0, p[2], EPS);
                assertEquals(125, p[3], EPS);
            }
        }
    }

    @Test
    void basisIsOrthonormalAndUprightWhileOrbiting() {
        for (double yaw = 0; yaw < 6.3; yaw += 0.5) {
            Scene3D s = new Scene3D(yaw, 0.35, 4.0, 400, 0, 0, 1.0);
            // A point straight above the target stays straight above on screen (no roll).
            double[] above = s.project(0, 2.0, 0);
            assertEquals(0, above[0], 1e-9, "no roll at yaw " + yaw);
            assertTrue(above[1] < 0, "up is up");
            // Distances are preserved by the rotation: |toCamera(p) - toCamera(q)| == |p - q|.
            double[] a = s.toCamera(0.3, 0.8, -0.4);
            double[] b = s.toCamera(-1.1, 0.2, 0.9);
            double d = Math.sqrt(Math.pow(a[0] - b[0], 2) + Math.pow(a[1] - b[1], 2) + Math.pow(a[2] - b[2], 2));
            assertEquals(Math.sqrt(1.4 * 1.4 + 0.6 * 0.6 + 1.3 * 1.3), d, 1e-12);
        }
    }

    @Test
    void orbitingIsRotationNotTranslation() {
        // The eye circles the target at constant distance; the same world point is seen from different sides.
        Scene3D front = new Scene3D(0, 0, 4.0, 400, 0, 0, 0);
        Scene3D side = new Scene3D(Math.PI / 2, 0, 4.0, 400, 0, 0, 0);
        assertArrayEquals(new double[] {0, 0, 4}, front.eye(), EPS);
        assertArrayEquals(new double[] {4, 0, 0}, side.eye(), EPS);
        // From the front, +x is screen right; from the +x side, +x is towards the camera (centre, nearer).
        assertEquals(100, front.project(1, 0, 0)[0], EPS);
        double[] p = side.project(1, 0, 0);
        assertEquals(0, p[0], EPS);
        assertEquals(3.0, p[2], EPS);
        // ...and +z (towards the front camera) appears on screen left from the +x side.
        assertTrue(side.project(0, 0, 1)[0] < 0);
    }

    @Test
    void behindCameraCulledAndSegmentsClipped() {
        Scene3D s = new Scene3D(0, 0, 4.0, 400, 0, 0, 0);
        assertNull(s.project(0, 0, 4.0));    // at the eye
        assertNull(s.project(0, 0, 9.0));    // behind it
        assertNull(s.project(5, 1, 4.02));   // inside the near plane
        assertNull(s.projectSegment(new double[] {0, 0, 5}, new double[] {1, 1, 6}));
        // Crossing the near plane: kept, clipped end is far off-screen but finite, other end exact.
        double[] seg = s.projectSegment(new double[] {1, 0, 0}, new double[] {1, 0, 8});
        assertTrue(seg != null);
        assertEquals(100, seg[0], EPS);
        assertEquals(0, seg[1], EPS);
        assertTrue(Double.isFinite(seg[2]) && seg[2] > 1000, "clipped end " + seg[2]);
        double[] whole = s.projectSegment(new double[] {1, 0, 0}, new double[] {-1, 0, 0});
        assertArrayEquals(new double[] {100, 0, -100, 0}, whole, EPS);
    }

    @Test
    void aspectHandledWithOneFocalLength() {
        // Wide and tall canvases: equal world offsets give equal px offsets in x and y.
        for (int[] wh : new int[][] {{390, 844}, {1920, 1080}}) {
            double f = Scene3D.focalForFov(Math.toRadians(50), wh[1]);
            Scene3D s = new Scene3D(0, 0, 4.0, f, wh[0] / 2.0, wh[1] / 2.0, 0);
            double[] px = s.project(0.5, 0, 0);
            double[] py = s.project(0, 0.5, 0);
            assertEquals(px[0] - wh[0] / 2.0, wh[1] / 2.0 - py[1], 1e-9);
            // Vertical FOV maps tan(fov/2) * depth to the top edge.
            double[] top = s.project(0, Math.tan(Math.toRadians(25)) * 4.0, 0);
            assertEquals(0, top[1], 1e-9);
        }
    }

    @Test
    void orbitYawIsAFunctionOfSongTime() {
        assertEquals(0, Scene3D.orbitYaw(0), EPS);
        assertEquals(Math.PI, Scene3D.orbitYaw(20_000), EPS);
        assertEquals(Math.PI / 2, Scene3D.orbitYaw(50_000), EPS);
        assertEquals(1.5 * Math.PI, Scene3D.orbitYaw(-10_000), EPS);
        assertEquals(Scene3D.orbitYaw(12_345), Scene3D.orbitYaw(12_345), 0.0);
    }

    @Test
    void rejectsBadCamera() {
        assertThrows(IllegalArgumentException.class, () -> new Scene3D(0, 0, 0, 400, 0, 0, 0));
        assertThrows(IllegalArgumentException.class, () -> new Scene3D(0, 0, 4, -1, 0, 0, 0));
        assertThrows(IllegalArgumentException.class, () -> new Scene3D(0, Math.PI / 2, 4, 400, 0, 0, 0));
    }

    @Test
    void iphone12Layout() {
        StageLayout l = StageLayout.choose("iphone12", 1920, 1080);
        assertEquals(390, l.width);
        assertEquals(844, l.height);
        assertEquals(1170, StageLayout.backing(l.width, StageLayout.IPHONE12_DPR));
        assertEquals(2532, StageLayout.backing(l.height, StageLayout.IPHONE12_DPR));
        assertEquals(844 - 113, l.hitY);
        assertEquals(97.5, l.laneWidth, EPS);
        assertTrue(l.tileY < l.hitY - 80, "centre tile above the hit line");
        assertEquals(422, l.horizonY, EPS);
    }

    @Test
    void layoutSelection() {
        StageLayout d = StageLayout.choose(null, 0, 0);
        assertEquals(400, d.width);
        assertEquals(600, d.height);
        assertEquals(520, d.hitY, "original HIT_Y kept at the default size");
        StageLayout phone = StageLayout.choose(null, 390, 844);
        assertEquals(390, phone.width);
        StageLayout desk = StageLayout.choose(null, 1920, 1080);
        assertEquals(960, desk.height);
        assertEquals(510, desk.width);
        assertEquals(1, StageLayout.backing(1, Double.NaN));
        assertEquals(800, StageLayout.backing(200, 9));
    }

    @Test
    void brainStagePositions() {
        Circuit c = ConnectomeXml.parse(ToyCircuitXml.XML);
        for (int i = 0; i < c.neuronCount(); i++) {
            double[] p = BrainStage.neuronPosition(c, i);
            assertTrue(p[1] > 0, "above the ground: " + c.id(i));
        }
        double[] in = BrainStage.neuronPosition(c, c.indexOf("lane1.in"));
        double[] out = BrainStage.neuronPosition(c, c.indexOf("lane1.out"));
        assertTrue(out[1] > in[1]);
        assertEquals(7, BrainStage.REGIONS.length);
        assertTrue(BrainStage.labelOnly(BrainStage.regionIndex("medulla")));
        assertTrue(!BrainStage.labelOnly(BrainStage.regionIndex("lobula")));
        assertEquals(-1, BrainStage.regionIndex("nope"));
        Circuit ring = ConnectomeXml.parse("<hemibrain><neuron id='A'/><neuron id='B'/></hemibrain>");
        assertEquals(BrainStage.CENTER_Y, BrainStage.neuronPosition(ring, 0)[1], EPS);
    }
}
