package com.fruitfly.games.rhythm.web;

import com.fruitfly.games.rhythm.logic.BrainStage;
import com.fruitfly.games.rhythm.logic.Circuit;
import com.fruitfly.games.rhythm.logic.PhantomBlocks;
import com.fruitfly.games.rhythm.logic.SaberRig;
import com.fruitfly.games.rhythm.logic.Scene3D;
import com.fruitfly.games.rhythm.logic.StageLayout;
import org.teavm.jso.canvas.CanvasRenderingContext2D;

/**
 * Draws the environment that holds the 3D objects, all through the fixed
 * stage camera (StageLayout.camera(): level, vanishing point at mid-height):
 * a perspective floor grid, the highlighted centre tile at the bottom
 * middle, the toy fly standing on it with the shrunk fly-brain object above
 * it (spinning about its own vertical axis), the two sabers, and the phantom
 * blocks, painter-sorted by depth. Display only.
 *
 * Decoupled from RhythmGame: the only inputs are song time, the circuit and
 * spike recency (brain flashes), and the PhantomBlocks / SaberRig state.
 * All coordinates are logical CSS px (the caller applied the DPR transform).
 */
final class StageRenderer {
    static final double FLASH_MS = 140;
    static final String TOY_CAPTION = "TOY circuit \u00b7 not real anatomy or the fly connectome";

    private StageRenderer() {
    }

    static void draw(CanvasRenderingContext2D ctx, StageLayout l, Theme th, double songTimeMs, Circuit circuit,
                     double[] msSinceSpike, PhantomBlocks blocks, SaberRig rig) {
        Scene3D cam = l.camera();
        double ui = l.uiScale;
        floor(ctx, cam, th);
        tile(ctx, cam, th, ui);

        // Painter's order: blocks farther than the fly, then fly + brain + sabers, then nearer blocks.
        double flyDepth = cam.toCamera(0, 0.6, 0)[2];
        int[] order = blocks == null ? new int[0] : blocks.depthOrder(cam, songTimeMs);
        int k = 0;
        while (k < order.length && depth(cam, blocks.view(order[k], songTimeMs)) > flyDepth) {
            block(ctx, cam, th, blocks.view(order[k], songTimeMs));
            k++;
        }
        fly(ctx, cam, th);
        brain(ctx, cam, th, ui, songTimeMs, circuit, msSinceSpike);
        if (rig != null) {
            for (int side = 0; side < 2; side++) {
                saber(ctx, cam, th, side, rig.segment(side, songTimeMs));
            }
        }
        for (; k < order.length; k++) {
            block(ctx, cam, th, blocks.view(order[k], songTimeMs));
        }
        ctx.setTextAlign("center");
        ctx.setFont(Math.round(10 * ui) + "px monospace");
        ctx.setFillStyle(th.caption);
        ctx.fillText(TOY_CAPTION, l.width / 2.0, l.horizonY - 10 * ui);
    }

    private static double depth(Scene3D cam, double[] v) {
        return cam.toCamera(v[0], v[1], v[2])[2];
    }

    /** Ground grid y = 0 on odd coordinates, so the centre tile [-1, 1]^2 is exactly one cell. */
    private static void floor(CanvasRenderingContext2D ctx, Scene3D cam, Theme th) {
        ctx.setStrokeStyle(th.light ? th.floorLine : th.gridMinor);
        ctx.setLineWidth(th.light ? 0.75 : 1);
        for (int i = -41; i <= 41; i += 2) {
            line(ctx, cam, new double[] {i, 0, 3.9}, new double[] {i, 0, -400});
        }
        for (int z = 3; z >= -121; z -= 2) {
            line(ctx, cam, new double[] {-60, 0, z}, new double[] {60, 0, z});
        }
    }

    private static void tile(CanvasRenderingContext2D ctx, Scene3D cam, Theme th, double ui) {
        double[][] c = {{-1, 0, -1}, {1, 0, -1}, {1, 0, 1}, {-1, 0, 1}};
        if (!poly(ctx, cam, c)) {
            return;
        }
        ctx.setFillStyle(th.tileFill);
        ctx.fill();
        ctx.setStrokeStyle(th.tileEdge);
        ctx.setLineWidth(1.5);
        ctx.stroke();
        double[] front = cam.project(0, 0, 1);
        if (front != null) {
            ctx.setFillStyle(th.origin);
            ctx.setFont(Math.round(9 * ui) + "px monospace");
            ctx.setTextAlign("center");
            ctx.fillText("origin", front[0], front[1] + 12 * ui);
        }
        ctx.setStrokeStyle(th.origin);
        ctx.setLineWidth(1);
        double[] prev = null;
        for (int k = 0; k <= 24; k++) {
            double a = 2 * Math.PI * k / 24;
            double[] pt = {0.15 * Math.cos(a), 0, 0.15 * Math.sin(a)};
            if (prev != null) {
                line(ctx, cam, prev, pt);
            }
            prev = pt;
        }
    }

    /** Toy fly standing on the tile: abdomen, thorax, head, legs, forelegs up to the saber hands. */
    private static void fly(CanvasRenderingContext2D ctx, Scene3D cam, Theme th) {
        ctx.setStrokeStyle(th.flyLine);
        ctx.setLineWidth(1.5);
        double[] thorax = {0, 0.46, 0.04};
        for (int s = -1; s <= 1; s += 2) {
            line(ctx, cam, thorax, new double[] {0.28 * s, 0, 0.18});
            line(ctx, cam, thorax, new double[] {0.30 * s, 0, -0.08});
            line(ctx, cam, new double[] {0, 0.32, -0.14}, new double[] {0.26 * s, 0, -0.32});
            line(ctx, cam, thorax, SaberRig.HANDS[s < 0 ? 0 : 1]);
        }
        ctx.setFillStyle(th.flyBody);
        ball(ctx, cam, new double[] {0, 0.32, -0.14}, 0.17);
        ball(ctx, cam, thorax, 0.12);
        ball(ctx, cam, new double[] {0, 0.6, 0.1}, 0.085);
    }

    private static void ball(CanvasRenderingContext2D ctx, Scene3D cam, double[] c, double r) {
        double[] p = cam.project(c[0], c[1], c[2]);
        if (p == null) {
            return;
        }
        ctx.beginPath();
        ctx.arc(p[0], p[1], Math.max(1.5, r * p[3]), 0, 2 * Math.PI);
        ctx.fill();
    }

    private static void brain(CanvasRenderingContext2D ctx, Scene3D cam, Theme th, double ui, double songTimeMs,
                              Circuit circuit, double[] msSinceSpike) {
        double yaw = Scene3D.orbitYaw(songTimeMs);
        double[] centre = BrainStage.place(new double[] {0, BrainStage.CENTER_Y, 0}, yaw);
        double[] sc = cam.project(centre[0], centre[1], centre[2]);
        if (circuit != null) {
            for (int i = 0; i < circuit.neuronCount(); i++) {
                double[] a = BrainStage.place(BrainStage.neuronPosition(circuit, i), yaw);
                double since = msSinceSpike == null ? -1 : msSinceSpike[i];
                boolean hot = since >= 0 && since < FLASH_MS;
                for (int k = circuit.rowStart(i); k < circuit.rowEnd(i); k++) {
                    double[] b = BrainStage.place(BrainStage.neuronPosition(circuit, circuit.target(k)), yaw);
                    boolean inhib = circuit.weight(k) < 0;
                    if (hot) {
                        double fade = 1 - since / FLASH_MS;
                        ctx.setStrokeStyle("rgba(" + (inhib ? th.inhibFlashRgb : th.excitFlashRgb) + ","
                                + (0.35 + 0.65 * fade) + ")");
                        ctx.setLineWidth(inhib ? 1.2 : 2.2);
                    } else {
                        ctx.setStrokeStyle(inhib ? th.inhibIdle : th.excitIdle);
                        ctx.setLineWidth(0.8);
                    }
                    line(ctx, cam, a, b);
                }
            }
        }
        // Region nodes; labels pushed out radially from the object's centre with a thin leader.
        ctx.setTextAlign("center");
        for (int r = 0; r < BrainStage.REGIONS.length; r++) {
            double[] p = BrainStage.place(BrainStage.regionPosition(r), yaw);
            double[] s = cam.project(p[0], p[1], p[2]);
            if (s == null || sc == null) {
                continue;
            }
            boolean only = BrainStage.labelOnly(r);
            ctx.setFillStyle(only ? th.regionFillLabelOnly : th.regionFill);
            ctx.beginPath();
            ctx.arc(s[0], s[1], Math.max(3, 0.07 * s[3]), 0, 2 * Math.PI);
            ctx.fill();
            double dx = s[0] - sc[0];
            double dy = s[1] - sc[1];
            double len = Math.max(1e-6, Math.hypot(dx, dy));
            double push = 46 * ui;
            double lx = s[0] + dx / len * push;
            double ly = s[1] + dy / len * push * 0.8;
            ctx.setStrokeStyle(th.leader);
            ctx.setLineWidth(0.75);
            ctx.beginPath();
            ctx.moveTo(s[0], s[1]);
            ctx.lineTo(lx, ly);
            ctx.stroke();
            ctx.setFont(Math.round((only ? 8 : 9) * ui) + "px monospace");
            ctx.setFillStyle(only ? th.regionTextLabelOnly : th.regionText);
            ctx.fillText(BrainStage.REGIONS[r] + (only ? " (label)" : ""), lx, ly - 2);
        }
        if (circuit != null) {
            for (int i = 0; i < circuit.neuronCount(); i++) {
                double[] p = BrainStage.place(BrainStage.neuronPosition(circuit, i), yaw);
                double[] s = cam.project(p[0], p[1], p[2]);
                if (s == null) {
                    continue;
                }
                double since = msSinceSpike == null ? -1 : msSinceSpike[i];
                boolean hot = since >= 0 && since < FLASH_MS;
                ctx.setFillStyle(hot ? th.neuronHot : th.neuron);
                ctx.beginPath();
                ctx.arc(s[0], s[1], Math.max(1.5, (hot ? 0.03 : 0.018) * s[3]), 0, 2 * Math.PI);
                ctx.fill();
            }
        }
    }

    private static void saber(CanvasRenderingContext2D ctx, Scene3D cam, Theme th, int side, double[][] seg) {
        ctx.setStrokeStyle(th.saberGlow[side]);
        ctx.setLineWidth(7);
        line(ctx, cam, seg[0], seg[1]);
        ctx.setStrokeStyle(th.saberCore[side]);
        ctx.setLineWidth(2.2);
        line(ctx, cam, seg[0], seg[1]);
        ctx.setFillStyle(th.flyBody);
        ball(ctx, cam, seg[0], 0.035);
    }

    /** One phantom block: faces far-to-near with a low-alpha fill, thin edges; cut effect flashes and expands. */
    private static void block(CanvasRenderingContext2D ctx, Scene3D cam, Theme th, double[] v) {
        double alpha = Math.max(0, Math.min(1, v[5]));
        if (alpha <= 0.002) {
            return;
        }
        double fx = v[6];
        double[][] c = PhantomBlocks.corners(new double[] {v[0], v[1], v[2]}, v[3], v[4]);
        int[][] faces = PhantomBlocks.FACES;
        double[] fd = new double[faces.length];
        Integer[] idx = new Integer[faces.length];
        for (int f = 0; f < faces.length; f++) {
            idx[f] = f;
            double d = 0;
            for (int q : faces[f]) {
                d += cam.toCamera(c[q][0], c[q][1], c[q][2])[2];
            }
            fd[f] = d;
        }
        java.util.Arrays.sort(idx, (a, b) -> Double.compare(fd[b], fd[a]));
        boolean flash = fx >= 0 && fx < 0.3;
        String rgb = fx >= 0 ? th.flashRgb : th.blockRgb;
        double fillA = (flash ? 0.45 : 0.08) * alpha;
        for (int f : idx) {
            double[][] quad = new double[4][];
            for (int q = 0; q < 4; q++) {
                quad[q] = c[faces[f][q]];
            }
            if (poly(ctx, cam, quad)) {
                ctx.setFillStyle("rgba(" + rgb + "," + fillA + ")");
                ctx.fill();
            }
        }
        ctx.setStrokeStyle("rgba(" + rgb + "," + (0.55 * alpha) + ")");
        ctx.setLineWidth(flash ? 1.6 : 0.9);
        for (int[] e : PhantomBlocks.EDGES) {
            line(ctx, cam, c[e[0]], c[e[1]]);
        }
    }

    /** Path a polygon; false (nothing pathed) if any vertex is behind the near plane. */
    private static boolean poly(CanvasRenderingContext2D ctx, Scene3D cam, double[][] pts) {
        double[][] s = new double[pts.length][];
        for (int i = 0; i < pts.length; i++) {
            s[i] = cam.project(pts[i][0], pts[i][1], pts[i][2]);
            if (s[i] == null) {
                return false;
            }
        }
        ctx.beginPath();
        ctx.moveTo(s[0][0], s[0][1]);
        for (int i = 1; i < s.length; i++) {
            ctx.lineTo(s[i][0], s[i][1]);
        }
        ctx.closePath();
        return true;
    }

    private static void line(CanvasRenderingContext2D ctx, Scene3D cam, double[] a, double[] b) {
        double[] s = cam.projectSegment(a, b);
        if (s == null) {
            return;
        }
        ctx.beginPath();
        ctx.moveTo(s[0], s[1]);
        ctx.lineTo(s[2], s[3]);
        ctx.stroke();
    }
}
