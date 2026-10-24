package com.fruitfly.games.rhythm.web;

import org.teavm.jso.JSBody;
import org.teavm.jso.JSObject;
import org.teavm.jso.canvas.CanvasRenderingContext2D;
import org.teavm.jso.dom.html.HTMLCanvasElement;
import org.teavm.jso.dom.html.HTMLElement;

/**
 * Small guarded JS helpers for the stage: viewport size, device pixel ratio,
 * canvas backing size, the background image and the optional camera feed.
 * Every helper tolerates a missing API (headless smoke test, old browsers)
 * and returns 0 / null instead of throwing.
 */
public final class Dom {
    private Dom() {
    }

    @JSBody(script = "return (typeof window !== 'undefined' && window.innerWidth) ? window.innerWidth|0 : 0;")
    static native int innerWidth();

    @JSBody(script = "return (typeof window !== 'undefined' && window.innerHeight) ? window.innerHeight|0 : 0;")
    static native int innerHeight();

    @JSBody(script = "return (typeof window !== 'undefined' && window.devicePixelRatio) ? +window.devicePixelRatio : 1;")
    static native double devicePixelRatio();

    /**
     * {@code window.location.hostname}, or empty when unavailable (JVM / headless).
     * Used by {@code CliClient} Option B URL selection.
     */
    @JSBody(script = "if (typeof window === 'undefined' || !window.location) return '';"
            + "return String(window.location.hostname || '');")
    public static native String locationHostname();

    /** {@code window.location.protocol} (e.g. {@code "https:"}, {@code "file:"}), or empty. */
    @JSBody(script = "if (typeof window === 'undefined' || !window.location) return '';"
            + "return String(window.location.protocol || '');")
    public static native String locationProtocol();

    /** Value of query param {@code name} in {@code window.location.search}, or empty. */
    @JSBody(params = {"name"}, script = "try { if (typeof window === 'undefined' || !window.location"
            + " || typeof URLSearchParams === 'undefined') return '';"
            + "var v = new URLSearchParams(window.location.search || '').get(name);"
            + "return v == null ? '' : String(v); } catch (e) { return ''; }")
    public static native String locationQueryParam(String name);

    /** {@code content} of the first {@code <meta name=...>} with this name, or empty. */
    @JSBody(params = {"name"}, script = "try { if (typeof document === 'undefined'"
            + " || typeof document.getElementsByName !== 'function') return '';"
            + "var els = document.getElementsByName(name);"
            + "for (var i = 0; i < els.length; i++) { var el = els[i];"
            + " if (el && String(el.tagName || '').toLowerCase() === 'meta') return String(el.content || ''); }"
            + "return ''; } catch (e) { return ''; }")
    public static native String metaContent(String name);

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

    /** Absolutely position an overlay element (CSS px, relative to .stage). */
    @JSBody(params = {"el", "x", "y", "w", "h"}, script = "if (el && el.style) { el.style.left = x + 'px';"
            + " el.style.top = y + 'px'; el.style.width = w + 'px'; el.style.height = h + 'px'; }")
    static native void place(HTMLElement el, double x, double y, double w, double h);

    @JSBody(params = {"el", "y"}, script = "if (el && el.style) { el.style.top = y + 'px'; }")
    static native void top(HTMLElement el, double y);

    @JSBody(params = {"el", "cls"}, script = "if (el && el.className !== cls) { el.className = cls; }")
    static native void setClass(HTMLElement el, String cls);

    @JSBody(params = {"el"}, script = "if (el && typeof el.blur === 'function') { el.blur(); }")
    static native void blur(HTMLElement el);

    @JSBody(params = {"el", "t"}, script = "if (el && el.title !== t) { el.title = t; if (el.setAttribute) { el.setAttribute('aria-label', el.textContent || t); } }")
    static native void setTitle(HTMLElement el, String t);

    /** UIEvent.detail of a click: 0 for keyboard-synthesised activation; a missing detail counts as a pointer click (1). */
    @JSBody(params = {"e"}, script = "return (e && typeof e.detail === 'number') ? e.detail|0 : 1;")
    static native int clickDetail(org.teavm.jso.dom.events.Event e);

    @org.teavm.jso.JSFunctor
    interface FileCallback extends JSObject {
        void picked(String name, String binary);
    }

    @org.teavm.jso.JSFunctor
    interface ErrorCallback extends JSObject {
        void failed(String why);
    }

    /** On a file input's change: read the first file as bytes and hand them over as a binary (latin-1) string. */
    @JSBody(params = {"input", "ok", "bad"}, script = "if (!input || !input.addEventListener) return;"
            + "input.addEventListener('change', function () {"
            + "  var f = input.files && input.files[0]; if (!f) return;"
            + "  if (typeof FileReader === 'undefined') { bad('FileReader unavailable'); return; }"
            + "  var r = new FileReader();"
            + "  r.onload = function () { var u = new Uint8Array(r.result), s = '';"
            + "    for (var i = 0; i < u.length; i += 8192) { s += String.fromCharCode.apply(null, u.subarray(i, i + 8192)); }"
            + "    ok(String(f.name || ''), s); };"
            + "  r.onerror = function () { bad(String(r.error && r.error.name || 'read error')); };"
            + "  r.readAsArrayBuffer(f);"
            + "});")
    static native void onFilePicked(HTMLElement input, FileCallback ok, ErrorCallback bad);

    @JSBody(params = {"input"}, script = "if (input) { try { input.value = ''; } catch (e) {} if (input.click) input.click(); }")
    static native void openFilePicker(HTMLElement input);

    @JSBody(script = "return typeof speechSynthesis !== 'undefined' && typeof SpeechSynthesisUtterance !== 'undefined';")
    static native boolean hasSpeech();

    /** Speak one syllable now (short, fast); false if speech is unavailable or throws. */
    @JSBody(params = {"text"}, script = "try { if (typeof speechSynthesis === 'undefined' || typeof SpeechSynthesisUtterance === 'undefined') return false;"
            + " var u = new SpeechSynthesisUtterance(text); u.rate = 1.5; u.pitch = 1.1; u.volume = 1;"
            + " speechSynthesis.speak(u); return true; } catch (e) { return false; }")
    static native boolean speak(String text);

    @JSBody(script = "try { if (typeof speechSynthesis !== 'undefined') speechSynthesis.cancel(); } catch (e) {}")
    static native void cancelSpeech();

    @org.teavm.jso.JSFunctor
    interface VisibilityCallback extends JSObject {
        void changed(boolean hidden);
    }

    /** document 'visibilitychange' -> hidden yes/no. No-op where the event or document.visibilityState is missing. */
    @JSBody(params = {"cb"}, script = "if (typeof document === 'undefined' || !document.addEventListener) return;"
            + "document.addEventListener('visibilitychange', function () { cb(document.visibilityState === 'hidden'); });")
    static native void onVisibilityChange(VisibilityCallback cb);

    @JSBody(script = "return typeof document !== 'undefined' && document.visibilityState === 'hidden';")
    static native boolean isHidden();

    @JSBody(params = {"s"}, script = "if (typeof console !== 'undefined' && console.log) console.log(s);")
    public static native void log(String s);

    @JSBody(params = {"el", "show"}, script = "if (el && el.style) { var d = show ? '' : 'none'; if (el.style.display !== d) el.style.display = d; }")
    static native void show(HTMLElement el, boolean show);

    /** True when {@code el} is document.activeElement. */
    @JSBody(params = {"el"}, script = "return !!(el && typeof document !== 'undefined' && document.activeElement === el);")
    public static native boolean isActive(HTMLElement el);

    /**
     * True when keyboard focus is in a text field or inside {@code #cli-column}.
     * Prefer this over TeaVM stopPropagation — game keys must not steal chat typing.
     */
    @JSBody(script = "if (typeof document === 'undefined' || !document.activeElement) return false;"
            + "var a = document.activeElement;"
            + "var tag = (a.tagName || '').toUpperCase();"
            + "if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || a.isContentEditable) return true;"
            + "if (a.id === 'chat-input') return true;"
            + "var col = document.getElementById('cli-column');"
            + "return !!(col && typeof col.contains === 'function' && col.contains(a));")
    public static native boolean isTypingTarget();

    /** Focus an element (chat input); swallow focus errors. */
    @JSBody(params = {"el"}, script = "if (!el || typeof el.focus !== 'function') return;"
            + "try { el.focus({preventScroll: true}); } catch (e) { try { el.focus(); } catch (e2) {} }")
    public static native void focus(HTMLElement el);

    /** Scroll an element to its bottom (chat scrollback). */
    @JSBody(params = {"el"}, script = "if (el) { el.scrollTop = el.scrollHeight; }")
    public static native void scrollTopMax(HTMLElement el);
}
