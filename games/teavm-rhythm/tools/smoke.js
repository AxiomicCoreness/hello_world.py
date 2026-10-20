// Headless smoke test for the TeaVM output: stubs just enough DOM (canvas 2D
// context, keydown listener, requestAnimationFrame, location.search) to boot
// classes.js under Node, play the first notes of seed 2026 and read the HUD.
// Usage: node tools/smoke.js [path/to/classes.js]
'use strict';
const fs = require('fs');
const vm = require('vm');
const path = process.argv[2] || 'target/webapp/classes.js';

const texts = [];
let rects = 0;
const ctx = new Proxy({}, {
  get(t, k) {
    if (k === 'fillText') return (s) => texts.push(String(s));
    if (k === 'fillRect') return () => { rects++; };
    if (k in t) return t[k];
    return () => {};
  },
  set(t, k, v) { t[k] = v; return true; }
});
const canvas = { width: 0, height: 0, getContext: (kind) => (kind === '2d' ? ctx : null) };
let keyHandler = null;
let rafCb = null;
const document = {
  getElementById: (id) => (id === 'game' ? canvas : null),
  addEventListener: (type, fn) => { if (type === 'keydown') keyHandler = fn; },
};
const sandbox = {
  console, document,
  location: { search: '?seed=2026' },
  requestAnimationFrame: (cb) => { rafCb = cb; return 1; },
  setTimeout, clearTimeout,
};
sandbox.window = sandbox;
sandbox.self = sandbox; // TeaVM UMD wrapper exports main() onto self in browsers
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(path, 'utf8'), sandbox, { filename: path });
sandbox.main();

function frame(t) { const cb = rafCb; rafCb = null; texts.length = 0; cb(t); }
function key(k, code) { keyHandler({ key: k, code: code || '', repeat: false, preventDefault() {} }); }
const hud = (prefix) => texts.find((s) => s.startsWith(prefix));
let fail = 0;
function expect(name, cond, got) { console.log((cond ? 'PASS ' : 'FAIL ') + name + (got !== undefined ? '  [' + got + ']' : '')); if (!cond) fail++; }

expect('canvas sized 400x600', canvas.width === 400 && canvas.height === 600, canvas.width + 'x' + canvas.height);
expect('rAF registered', typeof rafCb === 'function');
frame(0);
expect('title screen', texts.includes('Press Space to start'));
expect('seed from URL', hud('seed ') === 'seed 2026', hud('seed '));
key(' ');                       // start at stamp 0 -> song time = stamp
// seed 2026 chart starts 2@2000, 2@2500, 0@3000 (lanes J, J, D)
frame(2000); key('j', 'KeyJ');  // PERFECT
frame(2560); key('j', 'KeyJ');  // +60 ms -> GREAT
frame(2600);
expect('score after PERFECT+GREAT = 500', hud('Score ') === 'Score 500', hud('Score '));
expect('combo 2', (hud('Combo ') || '').startsWith('Combo 2'), hud('Combo '));
expect('GREAT banner', texts.includes('GREAT'));
frame(3200);                    // note @3000 passes the 150 ms window unhit
expect('miss counted', hud('Miss ') === 'Miss 1', hud('Miss '));
expect('combo reset', (hud('Combo ') || '').startsWith('Combo 0'), hud('Combo '));
expect('notes drawn', rects > 10, rects);
frame(60000);                   // let the rest of the song lapse
expect('song complete screen', texts.includes('Song complete'));
console.log(fail === 0 ? 'SMOKE OK' : 'SMOKE FAILED (' + fail + ')');
process.exit(fail === 0 ? 0 : 1);
