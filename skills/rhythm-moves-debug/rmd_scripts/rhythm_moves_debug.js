/*
 * rhythm-moves-debug v1.0.0: read-only overlay for the teavm-rhythm moves list.
 *
 * Reads window.__rhythmDebug only (moves(), verify(), mode(), count()). It does
 * not rewrite any game element, makes no network request and sends nothing:
 * it adds one overlay element of its own (#rmd-overlay) and removes it again.
 * Run once to open (refreshes about 4 times a second), run again or press the
 * close button to remove it. Without window.__rhythmDebug it says so and stops.
 *
 * Source rules for the builder: every statement ends with a semicolon, no regex
 * literals, no template literals, no division, block comments only.
 */
(function () {
  'use strict';
  var ID = 'rmd-overlay';
  var COLS = ['#', 't', 'key', 'delta', 'who', 'dt', 'judge', 'V', 'th', 'margin', 'fired', 'lat', 'chain', 'value', 'hash'];

  function f3(v) {
    return v === null || v === undefined ? '-' : Number(v).toFixed(3);
  }

  function s(v) {
    return v === null || v === undefined ? '-' : String(v);
  }

  /* One table row's cells, from one moves() row. */
  function cells(r) {
    return [s(r.i), s(r.t), s(r.key), s(r.delta), s(r.who), s(r.dt), s(r.judge), f3(r.V), f3(r.th),
      r.kind === 'margin' ? f3(r.margin) : 'score ' + f3(r.d),
      r.fired === null || r.fired === undefined ? '-' : r.fired ? 'yes' : 'no', s(r.lat), s(r.chain), f3(r.value),
      String(r.hash || '').slice(0, 8)];
  }

  /* Status line: chain indicator from verify(), mode and row count. */
  function status(d) {
    var v = d.verify();
    var ok = v && v.ok === true;
    return {ok: ok, text: (ok ? 'chain OK' : 'chain BAD at #' + v.firstBad) + ' | ' + d.mode() + ' | ' + d.count() + ' rows'};
  }

  function el(doc, tag, css, text) {
    var e = doc.createElement(tag);
    if (css) { e.style.cssText = css; }
    if (text !== undefined) { e.textContent = text; }
    return e;
  }

  function render(win, box) {
    var d = win.__rhythmDebug;
    var doc = win.document;
    var rows = d.moves();
    var st = status(d);
    var key = st.text + ':' + (rows.length ? rows[rows.length - 1].hash : '');
    if (box.rmdKey === key) { return false; }
    box.rmdKey = key;
    box.rmdStatus.textContent = st.text;
    box.rmdStatus.style.color = st.ok ? '#0a7d32' : '#c0152f';
    var tb = box.rmdBody;
    var wrap = box.rmdWrap;
    var atEnd = wrap.scrollTop + wrap.clientHeight + 4 >= wrap.scrollHeight;
    while (tb.firstChild) { tb.removeChild(tb.firstChild); }
    for (var i = 0; i < rows.length; i++) {
      var tr = el(doc, 'tr', rows[i].judge === 'MISS' ? 'color:#c0152f' : '');
      var c = cells(rows[i]);
      for (var k = 0; k < c.length; k++) { tr.appendChild(el(doc, 'td', 'padding:0 4px;text-align:right', c[k])); }
      tb.appendChild(tr);
    }
    if (atEnd) { wrap.scrollTop = wrap.scrollHeight; }
    return true;
  }

  function close(win) {
    var box = win.document.getElementById(ID);
    if (!box) { return false; }
    if (box.rmdTimer) { win.clearInterval(box.rmdTimer); }
    box.parentNode.removeChild(box);
    return true;
  }

  function open(win) {
    var doc = win.document;
    var box = el(doc, 'div', 'position:fixed;left:0;right:0;top:0;max-height:60vh;z-index:2147483647;background:rgba(255,255,255,.95);' +
      'color:#111;font:11px monospace;border-bottom:2px solid #333;box-shadow:0 2px 8px rgba(0,0,0,.3);display:flex;flex-direction:column');
    box.id = ID;
    box.setAttribute('role', 'dialog');
    box.setAttribute('aria-label', 'rhythm moves (read-only)');
    var head = el(doc, 'div', 'display:flex;gap:8px;align-items:center;padding:4px 6px;border-bottom:1px solid #ccc');
    head.appendChild(el(doc, 'b', '', 'rhythm moves (read-only)'));
    var st = el(doc, 'span', 'flex:1', '');
    head.appendChild(st);
    var x = el(doc, 'button', 'font:14px monospace;min-width:32px;min-height:32px', '\u00d7');
    x.type = 'button';
    x.title = 'close';
    x.setAttribute('aria-label', 'close');
    x.addEventListener('click', function () { close(win); });
    head.appendChild(x);
    box.appendChild(head);
    box.rmdStatus = st;
    var d = win.__rhythmDebug;
    if (!d || typeof d.moves !== 'function' || typeof d.verify !== 'function') {
      st.textContent = 'window.__rhythmDebug not found: open the teavm-rhythm game page, then run this again.';
      st.style.color = '#c0152f';
      doc.body.appendChild(box);
      return box;
    }
    var wrap = el(doc, 'div', 'overflow:auto;-webkit-overflow-scrolling:touch');
    var table = el(doc, 'table', 'border-collapse:collapse;white-space:nowrap');
    var hr = el(doc, 'tr', 'position:sticky;top:0;background:#eee');
    for (var i = 0; i < COLS.length; i++) { hr.appendChild(el(doc, 'th', 'padding:0 4px;text-align:right', COLS[i])); }
    var th = el(doc, 'thead');
    th.appendChild(hr);
    table.appendChild(th);
    var tb = el(doc, 'tbody');
    table.appendChild(tb);
    wrap.appendChild(table);
    box.appendChild(wrap);
    box.rmdBody = tb;
    box.rmdWrap = wrap;
    doc.body.appendChild(box);
    render(win, box);
    box.rmdTimer = win.setInterval(function () {
      if (!doc.getElementById(ID)) { win.clearInterval(box.rmdTimer); return; }
      render(win, box);
    }, 250);
    return box;
  }

  /* Second run closes. */
  function toggle(win) {
    return close(win) ? null : open(win);
  }

  var api = {ID: ID, COLS: COLS, cells: cells, status: status, render: render, open: open, close: close, toggle: toggle};
  if (typeof window === 'undefined' && typeof module === 'object' && module && module.exports) {
    module.exports = api;
  } else {
    toggle(window);
  }
})();
