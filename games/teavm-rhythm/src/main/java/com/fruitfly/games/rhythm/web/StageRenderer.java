package com.fruitfly.games.rhythm.web;

import com.fruitfly.games.rhythm.logic.BrainStage;
import com.fruitfly.games.rhythm.logic.Circuit;
import com.fruitfly.games.rhythm.logic.Judgement;
import com.fruitfly.games.rhythm.logic.Note;
import com.fruitfly.games.rhythm.logic.NoteBlocks;
import com.fruitfly.games.rhythm.logic.NoteChart;
import com.fruitfly.games.rhythm.logic.SaberRig;
import com.fruitfly.games.rhythm.logic.Scene3D;
import com.fruitfly.games.rhythm.logic.StageGeometry;
import com.fruitfly.games.rhythm.logic.StageLayout;
import org.teavm.jso.canvas.CanvasRenderingContext2D;

/**
 * Draws the Beat-Saber-style stage through the fixed, level stage camera
 * (StageLayout.camera(): no orbit, horizontal horizon, one central vanishing
 * point at mid-height): a perspective floor grid converging to that point,
 * the four lane strips, the hit plane, the centre tile with the toy fly and
 * its shrunk fly-brain object, the two sabers, and the chart's note blocks
 * (NoteBlocks), painter-sorted by depth. Display only.
 *
 * Decoupled from RhythmGame's scoring: the inputs are song time, the chart's
 * notes (read only), the SaberRig, the circuit and spike recency.
 * All coordinates are logical CSS px (the caller applied the DPR transform).
 */
final class StageRenderer {
    static final double FLASH_MS = 140;
    static final String TOY_CAPTION = "TOY circuit \u00b7 not real anatomy or the fly connectome";

    private StageRenderer() {
    }

    static void draw(CanvasRenderingContext2D ctx, StageLayout l, Theme th, double t, Circuit circuit,
                     double[] msSinceSpike, NoteChart chart, SaberRig rig, boolean[] laneFlash) {
        Scene3D cam = l.camera();
        double ui = l.uiScale;
        floor(ctx, cam, th);
        lanes(ctx, cam, th, laneFlash);
        tile(ctx, cam, th, ui);

        // Visible blocks, sorted far -> near by camera depth (insertion sort; a few dozen at most).
        java.util.List<Note> notes = chart.notes();
        int[] vis = new int[notes.size()];
        double[] dep = new double[notes.size()];
        int nv = 0;
        for (int i = 0; i < notes.size(); i++) {
            Note n = notes.get(i);
            int st = NoteBlocks.state(n, t);
            if (st == NoteBlocks.HIDDEN) {
                if (n.timeMs() - NoteBlocks.APPROACH_MS > t) {
                    break; // sorted by time: the rest are not spawned yet
                }
                continue;
            }
            double[] c = NoteBlocks.centre(n, t);
            double d = cam.toCamera(c[0], c[1], c[2])[2];
            int j = nv++;
            while (j > 0 && dep[j - 1] < d) {
                vis[j] = vis[j - 1];
                dep[j] = dep[j - 1];
                j--;
            }
            vis[j] = i;
            dep[j] = d;
        }
        double flyDepth = cam.toCamera(0, 0.6, 0)[2];
        int k = 0;
        while (k < nv && dep[k] > flyDepth) {
            noteBlock(ctx, cam, th, notes.get(vis[k]), t);
            k++;
        }
        // Fly + brain are see-through so the centre lanes' blocks behind them stay readable.
        ctx.setGlobalAlpha(0.6);
        fly(ctx, cam, th);
        brain(ctx, cam, th, ui, t, circuit, msSinceSpike);
        ctx.setGlobalAlpha(1);
        if (rig != null) {
            for (int side = 0; side < 2; side++) {
                saber(ctx, cam, th, side, rig.segment(side, t));
            }
        }
        for (; k < nv; k++) {
            noteBlock(ctx, cam, th, notes.get(vis[k]), t);
        }
        // Judgement text over each slicing block.
        ctx.setTextAlign("center");
        ctx.setFont("bold " + Math.round(11 * ui) + "px monospace");
        for (int q = 0; q < nv; q++) {
            Note n = notes.get(vis[q]);
            int st = NoteBlocks.state(n, t);
            if (st == NoteBlocks.SLICED || st == NoteBlocks.HELD) {
                double[] h = NoteBlocks.hitCentre(n.lane());
                double[] p = cam.project(h[0], h[1] + NoteBlocks.SIZE * 0.9, h[2]);
                if (p != null) {
                    ctx.setFillStyle("rgba(" + th.judgeRgb + "," + Math.max(0, NoteBlocks.alpha(n, t)) + ")");
                    ctx.fillText(n.result().name(), p[0], p[1]);
                }
            }
        }
        ctx.setFont(Math.round(10 * ui) + "px monospace");
        ctx.setFillStyle(th.caption);
        ctx.fillText(TOY_CAPTION, l.width / 2.0, l.captionY());
    }

    /** Ground grid y = 0: lines along z on the lane boundaries (every LANE_WIDTH), cross lines every 2 lanes. */
    private static void floor(CanvasRenderingContext2D ctx, Scene3D cam, Theme th) {
        ctx.setStrokeStyle(th.light ? th.floorLine : th.gridMinor);
        ctx.setLineWidth(th.light ? 0.75 : 1);
        double w = NoteBlocks.LANE_WIDTH;
        for (int i = -36; i <= 36; i++) {
            line(ctx, cam, new double[] {i * w, 0, 4.5}, new double[] {i * w, 0, -400});
        }
        for (double z = 4.2; z >= -120; z -= 2 * w) {
            line(ctx, cam, new double[] {-40, 0, z}, new double[] {40, 0, z});
        }
    }

    /** Four lane strips down the floor to the vanishing point, the hit plane frame across them. */
    private static void lanes(CanvasRenderingContext2D ctx, Scene3D cam, Theme th, boolean[] flash) {
        double hw = NoteBlocks.LANE_WIDTH / 2;
        double zNear = NoteBlocks.Z_HIT + 0.35;
        for (int l = 0; l < NoteBlocks.LANE_X.length; l++) {
            double x = NoteBlocks.LANE_X[l];
            double[][] q = {{x - hw, 0, zNear}, {x + hw, 0, zNear}, {x + hw, 0, -200}, {x - hw, 0, -200}};
            if (poly(ctx, cam, q)) {
                boolean on = flash != null && l < flash.length && flash[l];
                ctx.setFillStyle(on ? th.laneFlash : (l % 2 == 0 ? th.laneEven : th.laneOdd));
                ctx.fill();
            }
        }
        double x0 = NoteBlocks.LANE_X[0] - hw;
        double x1 = NoteBlocks.LANE_X[NoteBlocks.LANE_X.length - 1] + hw;
        double zh = NoteBlocks.Z_HIT;
        double top = NoteBlocks.Y + NoteBlocks.SIZE * 0.5 + 0.12;
        ctx.setStrokeStyle(th.hitFrame);
        ctx.setLineWidth(1.4);
        line(ctx, cam, new double[] {x0, 0, zh}, new double[] {x1, 0, zh});
        ctx.setLineWidth(0.8);
        line(ctx, cam, new double[] {x0, 0, zh}, new double[] {x0, top, zh});
        line(ctx, cam, new double[] {x1, 0, zh}, new double[] {x1, top, zh});
        line(ctx, cam, new double[] {x0, top, zh}, new double[] {x1, top, zh});
    }

    private static void tile(CanvasRenderingContext2D ctx, Scene3D cam, Theme th, double ui) {
        double h = StageLayout.TILE_HALF;
        double[][] c = {{-h, 0, -h}, {h, 0, -h}, {h, 0, h}, {-h, 0, h}};
        if (!poly(ctx, cam, c)) {
            return;
        }
        ctx.setFillStyle(th.tileFill);
        ctx.fill();
        ctx.setStrokeStyle(th.tileEdge);
        ctx.setLineWidth(1.5);
        ctx.stroke();
        double[] front = cam.project(0, 0, h);
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
            line(ctx, cam, new double[] {0, 0.32, 0.18}, new double[] {0.26 * s, 0, 0.36});
            line(ctx, cam, thorax, SaberRig.HANDS[s < 0 ? 0 : 1]);
        }
        ctx.setFillStyle(th.flyBody);
        ball(ctx, cam, new double[] {0, 0.30, 0.18}, 0.11);
        ball(ctx, cam, thorax, 0.08);
        ball(ctx, cam, new double[] {0, 0.58, -0.04}, 0.06);
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

    /** One chart note's block: whole (approach / held / passed) or its two sliced halves. */
    private static void noteBlock(CanvasRenderingContext2D ctx, Scene3D cam, Theme th, Note n, double t) {
        double alpha = Math.max(0, Math.min(1, NoteBlocks.alpha(n, t)));
        if (alpha <= 0.002) {
            return;
        }
        int st = NoteBlocks.state(n, t);
        int side = SaberRig.sideFor(n.lane());
        boolean miss = n.result() == Judgement.MISS;
        String rgb = miss ? th.missRgb : th.noteRgb[side];
        if (st == NoteBlocks.SLICED) {
            double since = t - NoteBlocks.contactMs(n);
            boolean flash = since < NoteBlocks.FLASH_MS;
            if (flash) { // flash at the cut: a bright burst at the block centre
                double[] h = NoteBlocks.hitCentre(n.lane());
                double[] p = cam.project(h[0], h[1], h[2]);
                if (p != null) {
                    double f = 1 - since / NoteBlocks.FLASH_MS;
                    ctx.setFillStyle("rgba(" + th.flashRgb + "," + (0.55 * f) + ")");
                    ctx.beginPath();
                    ctx.arc(p[0], p[1], NoteBlocks.SIZE * (0.6 + 0.6 * (1 - f)) * p[3], 0, 2 * Math.PI);
                    ctx.fill();
                }
            }
            double[][][] halves = NoteBlocks.halves(n.lane(), since);
            for (double[][] h : halves) {
                box(ctx, cam, h, flash ? th.flashRgb : rgb, alpha, flash ? 0.6 : 0.42);
            }
            return;
        }
        box(ctx, cam, NoteBlocks.corners(n, t), rgb, alpha, miss ? 0.12 : 0.42);
    }

    /** A box from 8 corners: faces far to near with a fill, then the edges. */
    private static void box(CanvasRenderingContext2D ctx, Scene3D cam, double[][] c, String rgb, double alpha,
                            double fillA) {
        int[][] faces = StageGeometry.FACES;
        double[] fd = new double[faces.length];
        int[] idx = new int[faces.length];
        for (int f = 0; f < faces.length; f++) {
            double d = 0;
            for (int q : faces[f]) {
                d += cam.toCamera(c[q][0], c[q][1], c[q][2])[2];
            }
            int j = f;
            while (j > 0 && fd[j - 1] < d) {
                fd[j] = fd[j - 1];
                idx[j] = idx[j - 1];
                j--;
            }
            fd[j] = d;
            idx[j] = f;
        }
        ctx.setFillStyle("rgba(" + rgb + "," + (fillA * alpha) + ")");
        for (int f : idx) {
            double[][] quad = new double[4][];
            for (int q = 0; q < 4; q++) {
                quad[q] = c[faces[f][q]];
            }
            if (poly(ctx, cam, quad)) {
                ctx.fill();
            }
        }
        ctx.setStrokeStyle("rgba(" + rgb + "," + (0.9 * alpha) + ")");
        ctx.setLineWidth(1.1);
        for (int[] e : StageGeometry.EDGES) {
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
