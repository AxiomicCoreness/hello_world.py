// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT

package com.fruitfly.games.rhythm.web;

import org.teavm.jso.JSBody;
import org.teavm.jso.JSFunctor;
import org.teavm.jso.JSObject;

/**
 * Browser side of {@code /v3t}: localStorage for the owner token (this browser only) and
 * fetch() to the bridge route with {@code Authorization: Bearer}. Replies come back already
 * formatted as text lines; nothing is persisted except the token in localStorage.
 */
public final class V3tHttp {
    private V3tHttp() {
    }

    @JSFunctor
    public interface Done extends JSObject {
        /** ok=false → {@code text} is an error message. {@code conv} may be empty. */
        void done(boolean ok, String text, String conv);
    }

    @JSBody(params = {"k"}, script = "try { return String(window.localStorage.getItem(k) || ''); }"
            + " catch (e) { return ''; }")
    public static native String loadToken(String k);

    @JSBody(params = {"k", "v"}, script = "try { if (v) { window.localStorage.setItem(k, v); }"
            + " else { window.localStorage.removeItem(k); } return true; } catch (e) { return false; }")
    public static native boolean storeToken(String k, String v);

    /** {@code ?v3t=} query override, or empty. */
    @JSBody(script = "try { return String(new URLSearchParams(window.location.search).get('v3t') || ''); }"
            + " catch (e) { return ''; }")
    public static native String queryOverride();

    @JSBody(params = {"url", "token", "body", "cb"}, script = ""
            + "var h = {'Authorization': 'Bearer ' + token, 'X-Client': 'teavm'};"
            + "if (body) { h['Content-Type'] = 'application/json'; }"
            + "fetch(url, {method: body ? 'POST' : 'GET', headers: h, body: body || undefined,"
            + "  mode: 'cors', credentials: 'omit', cache: 'no-store'})"
            + ".then(function (r) { return r.text().then(function (t) { return [r.status, t]; }); })"
            + ".then(function (p) {"
            + "  var st = p[0], d = null; try { d = JSON.parse(p[1]); } catch (e) {}"
            + "  if (st === 401) { cb(false, 'v3t: token rejected (401) - /v3t token <owner token>', ''); return; }"
            + "  if (st < 200 || st >= 300 || !d) { cb(false, 'v3t: HTTP ' + st + (d && d.error ? ' ' + d.error : ''), ''); return; }"
            + "  if (d.choices) { cb(true, String(d.choices[0].message.content || ''), String(d.conversation_id || '')); return; }"
            + "  if (d.conversations) { var out = d.conversations.map(function (c) {"
            + "      return c.conversation_id + '  ' + c.updated_at + '  (' + c.messages + ' msgs, '"
            + "        + (c.devices || []).join('+') + ')  ' + c.title; });"
            + "    cb(true, out.length ? out.join('\\n') : '(no shared conversations yet)', ''); return; }"
            + "  if (d.messages) { cb(true, d.messages.map(function (m) {"
            + "      return (m.role === 'user' ? 'Clarke Yoursa Tee' : 'v3t') + ': ' + m.content; }).join('\\n'),"
            + "    String(d.conversation_id || '')); return; }"
            + "  cb(false, 'v3t: unexpected reply', '');"
            + "}).catch(function (e) { cb(false, 'v3t: bridge unreachable (' + url.split('/llm')[0] + '): ' + e, ''); });")
    public static native void call(String url, String token, String body, Done cb);
}
