package com.fruitfly.games.rhythm.web;

import org.teavm.jso.JSBody;
import org.teavm.jso.JSObject;
import org.teavm.jso.canvas.CanvasRenderingContext2D;
import org.teavm.jso.dom.html.HTMLCanvasElement;

/**
 * Small guarded JS helpers for the stage: viewport size, device pixel ratio,
 * canvas backing size, the background image and the optional camera feed.
 * Every helper tolerates a missing API (headless smoke test, old browsers)
 * and returns 0 / null instead of throwing.
 */
final class Dom {
    private Dom() {
    }

    @JSBody(script = "return (typeof window !== 'undefined' && window.innerWidth) ? window.innerWidth|0 : 0;")
    static native int innerWidth();

    @JSBody(script = "return (typeof window !== 'undefined' && window.innerHeight) ? window.innerHeight|0 : 0;")
    static native int innerHeight();

    @JSBody(script = "return (typeof window !== 'undefined' && window.devicePixelRatio) ? +window.devicePixelRatio : 1;")
    static native double devicePixelRatio();

    /** CSS size via style (when present); backing store already set by the caller. */
    @JSBody(params = {"c", "w", "h"}, script = "if (c && c.style) { c.style.width = w + 'px'; c.style.height = h + 'px'; }")
    static native void cssSize(HTMLCanvasElement c, int w, int h);

    @JSBody(params = {"cls"}, script = "if (typeof document !== 'undefined' && document.body) { document.body.className = cls; }")
    static native void bodyClass(String cls);

    @JSBody(params = {"url"}, script = "if (typeof Image === 'undefined') return null;"
            + "var i = new Image(); i.decoding = 'async'; i.src = url; return i;")
    static native JSObject loadImage(String url);

    /** Draw an image or video "cover"-fitted to w x h; returns false if it isn't ready. */
    @JSBody(params = {"ctx", "src", "w", "h"}, script = "if (!src) return false;"
            + "var sw = src.videoWidth || src.naturalWidth || 0, sh = src.videoHeight || src.naturalHeight || 0;"
            + "if (!sw || !sh || (src.readyState !== undefined && src.readyState < 2)) return false;"
            + "var s = Math.max(w / sw, h / sh), dw = sw * s, dh = sh * s;"
            + "try { ctx.drawImage(src, (w - dw) / 2, (h - dh) / 2, dw, dh); } catch (e) { return false; }"
            + "return true;")
    static native boolean drawCover(CanvasRenderingContext2D ctx, JSObject src, double w, double h);

    /**
     * Start the rear camera as a live backdrop. Returns a &lt;video&gt; or null
     * when getUserMedia is unavailable; a denied / failed request leaves the
     * video without frames, so drawCover() keeps falling back.
     */
    @JSBody(script = "if (typeof navigator === 'undefined' || !navigator.mediaDevices"
            + " || !navigator.mediaDevices.getUserMedia || typeof document.createElement !== 'function') return null;"
            + "var v = document.createElement('video'); v.muted = true; v.playsInline = true;"
            + "v.setAttribute && v.setAttribute('playsinline', '');"
            + "navigator.mediaDevices.getUserMedia({video: {facingMode: 'environment'}, audio: false})"
            + ".then(function (s) { v.srcObject = s; return v.play(); })"
            + ".catch(function (e) { v.cameraError = String(e && e.name || e); });"
            + "return v;")
    static native JSObject startCamera();

    @JSBody(params = {"v"}, script = "return v && v.cameraError ? v.cameraError : null;")
    static native String cameraError(JSObject v);
}
