/*
 * DOM tests for the rhythm-moves-debug bookmarklet, run with node + jsdom against a
 * stub window.__rhythmDebug (no game build needed).
 * Usage: node evals/rmd_dom_test.js  (NODE_PATH may point at a node_modules that has jsdom)
 * Exit 0 all pass, 1 failure, 77 jsdom not installed (pytest turns that into a skip).
 */
'use strict';
var fs = require('fs');
var path = require('path');

var JSDOM;
try {
  JSDOM = require('jsdom').JSDOM;
} catch (e) {
  console.log('SKIP jsdom not installed');
  process.exit(77);
}

var ROOT = path.resolve(__dirname, '..');
var SRC = fs.readFileSync(path.join(ROOT, 'rmd_scripts', 'rhythm_moves_debug.js'), 'utf8');
var URL_TXT = fs.readFileSync(path.join(ROOT, 'assets', 'bookmarklet.txt'), 'utf8').trim();
var MIN = decodeURIComponent(URL_TXT.slice('javascript:'.length));
var GAME = '<!doctype html><html><body><div class="stage"><canvas id="game"></canvas>' +
  '<div id="hud-l" class="hud">Score 7800\nCombo 18  x2</div><button id="autoplay-btn">LOCKED: CONNECTOME FLY</button></div></body></html>';

var passed = 0;
var failed = 0;
function check(name, cond, extra) {
  if (cond) { passed++; console.log('PASS ' + name); }
  else { failed++; console.log('FAIL ' + name + (extra ? ' :: ' + extra : '')); }
}
function sleep(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }

function row(i) {
  return { i: i, t: 2000 + 222 * i, lane: i % 4, key: 'DFJK'[i % 4], delta: i ? 222 : null, who: 'fly', press: 2000 + 222 * i, dt: 0,
    judge: i === 6 ? 'MISS' : 'PERFECT', V: -44.612, th: -45, margin: 0.388, fired: i !== 6, lat: 15, kind: 'margin', d: 0.388,
    chain: 1 + (i >> 2), f: 1.1, value: 0.427, math_origin: 'math_origin=Decision(t=..)', prev: '0'.repeat(64),
    hash: (i.toString(16) + 'abcdef0123456789').slice(0, 16) + '0'.repeat(48) };
}

function page(withApi) {
  var dom = new JSDOM(GAME, { runScripts: 'outside-only' });
  var w = dom.window;
  w.net = [];
  ['fetch', 'XMLHttpRequest', 'WebSocket', 'EventSource'].forEach(function (k) { w[k] = function () { w.net.push(k); throw new Error('network: ' + k); }; });
  w.navigator.sendBeacon = function () { w.net.push('beacon'); return false; };
  w.calls = [];
  w.timers = { set: 0, clear: 0 };
  var si = w.setInterval, ci = w.clearInterval;
  w.setInterval = function (f, ms) { w.timers.set++; w.timers.ms = ms; return si.call(w, f, ms); };
  w.clearInterval = function (h) { w.timers.clear++; return ci.call(w, h); };
  if (withApi) {
    var state = { rows: [0, 1, 2, 3, 4, 5, 6].map(row), bad: null };
    w.stub = state;
    var api = Object.freeze({
      version: 'rhythm-moves/1',
      moves: function () { w.calls.push('moves'); return JSON.parse(JSON.stringify(state.rows)); },
      first20: function () { w.calls.push('first20'); return JSON.parse(JSON.stringify(state.rows.slice(0, 20))); },
      count: function () { w.calls.push('count'); return state.rows.length; },
      mode: function () { w.calls.push('mode'); return 'connectome'; },
      clock: function () { return 0; },
      verify: function () { w.calls.push('verify'); return state.bad === null ? { ok: true, firstBad: null, checked: state.rows.length } : { ok: false, firstBad: state.bad, checked: state.bad }; },
      sha256: function () { return ''; }
    });
    Object.defineProperty(w, '__rhythmDebug', { value: api, writable: false });
  }
  return w;
}

function cellsOf(tr) { return Array.prototype.map.call(tr.children, function (td) { return td.textContent; }); }

(async function () {
  var labels = ['minified bookmarklet', 'readable source'];
  for (var n = 0; n < 2; n++) {
    var code = n === 0 ? MIN : SRC;
    var p = labels[n] + ': ';
    // absent API
    var w = page(false);
    var before = w.document.body.innerHTML;
    w.eval(code);
    var box = w.document.getElementById('rmd-overlay');
    check(p + 'no __rhythmDebug: overlay says so, no polling', !!box && box.textContent.indexOf('window.__rhythmDebug not found') >= 0 && w.timers.set === 0 && !box.querySelector('table'));
    w.eval(code);
    check(p + 'no __rhythmDebug: second run removes it, page unchanged', !w.document.getElementById('rmd-overlay') && w.document.body.innerHTML === before);

    // with the stub API
    w = page(true);
    before = w.document.body.innerHTML;
    w.eval(code);
    box = w.document.getElementById('rmd-overlay');
    var rows = box ? box.querySelectorAll('tbody tr') : [];
    check(p + 'overlay: fixed, top layer, labelled dialog', !!box && box.style.position === 'fixed' && box.style.zIndex === '2147483647' && box.getAttribute('role') === 'dialog');
    var wrap = box.querySelector('table').parentNode;
    check(p + 'overlay: scrollable table with the columns', wrap.style.overflow === 'auto' &&
      cellsOf(box.querySelector('thead tr')).join(',') === '#,t,key,delta,who,dt,judge,V,th,margin,fired,lat,chain,value,hash');
    check(p + 'one table row per move', rows.length === 7, rows.length);
    var c0 = cellsOf(rows[0]);
    check(p + 'row 0 shows decision values, chain, value and an 8-hex hash', c0.join('|') === '0|2000|D|-|fly|0|PERFECT|-44.612|-45.000|0.388|yes|15|1|0.427|0abcdef0', c0.join('|'));
    check(p + 'MISS row: not fired, highlighted', cellsOf(rows[6])[10] === 'no' && rows[6].style.color !== '');
    var stEl = box.querySelector('span');
    check(p + 'chain OK indicator with mode and count', stEl.textContent === 'chain OK | connectome | 7 rows' && stEl.style.color === 'rgb(10, 125, 50)', stEl.textContent);
    check(p + 'auto-refresh every 250 ms (~4 Hz)', w.timers.set === 1 && w.timers.ms === 250);
    w.stub.rows.push(row(7));
    w.stub.bad = 5;
    await sleep(320);
    rows = box.querySelectorAll('tbody tr');
    check(p + 'refresh picks up new rows and a broken chain', rows.length === 8 && stEl.textContent === 'chain BAD at #5 | connectome | 8 rows' && stEl.style.color === 'rgb(192, 21, 47)', stEl.textContent);
    var used = w.calls.filter(function (c, i, a) { return a.indexOf(c) === i; }).sort().join(',');
    check(p + 'reads only moves / verify / mode / count', used === 'count,mode,moves,verify', used);
    check(p + 'no network, nothing sent', w.net.length === 0, w.net.join(','));
    check(p + 'game DOM untouched (only its own overlay added)', w.document.getElementById('hud-l').textContent === 'Score 7800\nCombo 18  x2' &&
      w.document.getElementById('autoplay-btn').textContent === 'LOCKED: CONNECTOME FLY' && w.document.body.children.length === 2);
    box.querySelector('button').dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
    check(p + 'close button removes it and stops polling', !w.document.getElementById('rmd-overlay') && w.timers.clear === 1 && w.document.body.innerHTML === before);
    w.eval(code);
    check(p + 'run again: opens again', !!w.document.getElementById('rmd-overlay'));
    w.eval(code);
    check(p + 'second run toggles it off, page restored', !w.document.getElementById('rmd-overlay') && w.timers.clear === 2 && w.document.body.innerHTML === before);
  }
  // module mode: exports, does not run
  var mod = { exports: {} };
  new Function('module', 'window', SRC)(mod, undefined);
  check('node: readable source exports its functions without running', typeof mod.exports.toggle === 'function' && mod.exports.ID === 'rmd-overlay' &&
    mod.exports.cells({ i: 1, t: 2, key: 'F', delta: null, who: 'you', dt: -12, judge: 'GOOD', V: null, th: null, kind: 'timing', d: 0.92, fired: null, lat: null, chain: 3, value: 1.196, hash: 'abcdef0123' }).join('|')
      === '1|2|F|-|you|-12|GOOD|-|-|score 0.920|-|-|3|1.196|abcdef01');
  console.log(passed + ' passed, ' + failed + ' failed');
  process.exit(failed === 0 ? 0 : 1);
})();
