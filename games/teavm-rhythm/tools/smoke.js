// Headless smoke test for the TeaVM output: stubs just enough DOM (canvas 2D
// context, keydown listener, requestAnimationFrame, location.search) to boot
// classes.js under Node, play the first notes of seed 2026 and read the HUD,
// then let the LIF autoplayer (key B) play the whole song. Part 2 boots fresh
// copies with ?chart=charts/sample_chart.json and a stub <audio> element to
// check the JSON chart loader, the audio clock and the frame-clock fallback.
// Part 3 boots with the HTML HUD overlay, an iPhone 12 viewport (390x844 at
// devicePixelRatio 3) and an Image stub, then checks the stage layers, the
// connectome autoplayer (key C), assist mode and ?camera / ?connectome, and
// the on-screen AUTOPLAY button (same cycle as C, never a lane press), its
// visible mid-song lock, the Euclidean songs and the music-source picker
// (Euclidean / MIDI file built in-test / TTS voice with a speechSynthesis stub).
// Usage: node tools/smoke.js [path/to/classes.js]
'use strict';
const fs = require('fs');
const vm = require('vm');
const path = process.argv[2] || 'target/webapp/classes.js';

const texts = [];
let rects = 0;
let pathFills = 0;
const ctx = new Proxy({}, {
  get(t, k) {
    if (k === 'fillText') return (s) => texts.push(String(s));
    if (k === 'fillRect') return () => { rects++; };
    if (k === 'fill') return () => { pathFills++; };
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
expect('region lane labels drawn', ['antennal lobe', 'mushroom body', 'lateral horn', 'lobula'].every((l) => texts.includes(l)));
expect('autoplay off by default', texts.includes('autoplay off'));
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
expect('note blocks drawn (3D faces filled)', pathFills > 10, pathFills);
frame(60000);                   // let the rest of the song lapse
expect('song complete screen', texts.includes('Song complete'));

// LIF autoplayer: toggle with B between songs, then play seed 2026 at ~60 fps.
key('b', 'KeyB');
frame(60016);
expect('autoplay toggled on', texts.includes('LIF autoplay ON'));
key(' ');                       // finished -> reset, start a new run at stamp 60016
let t = 60016;
let done = false;
let lastScore = '';
for (let i = 0; i < 4000 && !done; i++) {
  t += 16;
  frame(t);
  lastScore = hud('Score ') || lastScore;
  done = texts.includes('Song complete');
}
expect('autoplay finished the song', done);
expect('autoplay score 58800 (64/64 PERFECT)', hud('Score ') === 'Score 58800', hud('Score '));
expect('autoplay no misses', hud('Miss ') === 'Miss 0', hud('Miss '));
expect('autoplay spikes 64', hud('spikes ') === 'spikes 64', hud('spikes '));

// ---------------------------------------------------------------------------
// Part 2: JSON chart loader + audio clock. Each boot() is a fresh page.
const webDir = require('path').dirname(path);
function boot(search, opts) {
  opts = opts || {};
  const b = { fills: [], texts: [], canvasTexts: [], key: null, raf: null, xhrs: [], audios: [], images: [], draws: 0, transforms: [], strokes: 0 };
  const c2d = new Proxy({}, {
    get(t, k) {
      if (k === 'fillText') return (s) => { b.texts.push(String(s)); b.canvasTexts.push(String(s)); };
      if (k === 'drawImage') return () => { b.draws++; };
      if (k === 'fillRect') return () => { b.fills.push(t.fillStyle); };
      if (k === 'setTransform') return (...a) => { b.transforms.push(a); };
      if (k === 'stroke') return () => { b.strokes++; };
      if (k in t) return t[k]; return () => {};
    },
    set(t, k, v) { t[k] = v; return true; }
  });
  const cv = { width: 0, height: 0, style: {}, getContext: (kind) => (kind === '2d' ? c2d : null) };
  const huds = {};
  if (opts.hud) {
    for (const id of ['hud-l', 'hud-r', 'hud-c']) huds[id] = { id, textContent: '', style: {} };
    // #autoplay-btn (and the picker buttons): records listeners, focus/blur and default-prevented pointer events.
    const makeBtn = (bid, label) => {
    const btn = { id: bid, textContent: label, className: '', title: '', style: {}, handlers: {}, blurs: 0, prevented: 0 };
    btn.addEventListener = (type, fn) => { (btn.handlers[type] = btn.handlers[type] || []).push(fn); };
    btn.blur = () => { btn.blurs++; };
    btn.fire = (type, extra) => {
      const ev = { type, detail: 1, defaultPrevented: false, stopped: false, ...(extra || {}),
        preventDefault() { this.defaultPrevented = true; }, stopPropagation() { this.stopped = true; } };
      (btn.handlers[type] || []).forEach((fn) => fn(ev));
      if (ev.defaultPrevented) btn.prevented++;
      return ev;
    };
    btn.tap = () => { const d = btn.fire('pointerdown'); btn.fire('mousedown'); const c = btn.fire('click'); return d.defaultPrevented && c.stopped; };
    return btn;
    };
    huds['autoplay-btn'] = makeBtn('autoplay-btn', 'AUTOPLAY: OFF');
    huds['moves-list'] = { id: 'moves-list', textContent: '', style: { display: 'none' } };
    if (!opts.noPickers) {
      huds['rhythm-btn'] = makeBtn('rhythm-btn', 'LAYERED x4');
      huds['bpm-btn'] = makeBtn('bpm-btn', '120 BPM');
      if (!opts.noSource) {
        huds['source-btn'] = makeBtn('source-btn', 'EUCLID');
        // #midi-file: a file input; click() is counted, the test sets .files and fires 'change'.
        const fi = { id: 'midi-file', files: [], value: '', clicks: 0, handlers: {}, style: {} };
        fi.addEventListener = (type, fn) => { (fi.handlers[type] = fi.handlers[type] || []).push(fn); };
        fi.click = () => { fi.clicks++; };
        fi.pick = (name, bytes) => { fi.files = [{ name, bytes }]; (fi.handlers.change || []).forEach((fn) => fn({ type: 'change' })); };
        huds['midi-file'] = fi;
      }
    }
  }
  b.huds = huds;
  b.btn = huds['autoplay-btn'];
  b.rhythmBtn = huds['rhythm-btn'];
  b.bpmBtn = huds['bpm-btn'];
  b.sourceBtn = huds['source-btn'];
  b.midiInput = huds['midi-file'];
  b.spoken = [];
  class FakeXHR {
    constructor() { this.readyState = 0; this.status = 0; this.responseText = ''; this.listeners = {}; b.xhrs.push(this); }
    open(m, url) { this.method = m; this.url = url; this.readyState = 1; }
    addEventListener(type, fn) { (this.listeners[type] = this.listeners[type] || []).push(fn); }
    send() { this.sent = true; }
    respond() { // called by the test, like a network response arriving later
      if (opts.chartText !== undefined) { this.status = 200; this.responseText = opts.chartText; }
      else {
        const f = require('path').join(webDir, this.url);
        if (fs.existsSync(f)) { this.status = 200; this.responseText = fs.readFileSync(f, 'utf8'); }
        else { this.status = 404; this.responseText = 'not found'; }
      }
      this.readyState = 4;
      (this.listeners.readystatechange || []).forEach((fn) => fn.call(this, { type: 'readystatechange' }));
    }
  }
  function makeAudio() {
    const a = { src: '', preload: '', currentTime: 0, paused: true, ended: false, error: null, plays: 0, handlers: {} };
    a.addEventListener = (type, fn) => { (a.handlers[type] = a.handlers[type] || []).push(fn); };
    a.play = () => { a.plays++; if (opts.rejectPlay) return Promise.reject(new Error('NotAllowedError')); a.paused = false; return Promise.resolve(); };
    a.pause = () => { a.paused = true; };
    a.fail = () => { (a.handlers.error || []).forEach((fn) => fn({ type: 'error' })); };
    b.audios.push(a);
    return a;
  }
  const doc = {
    body: { className: '' },
    getElementById: (id) => (id === 'game' ? cv : (huds[id] || null)),
    visibilityState: 'visible',
    addEventListener: (type, fn) => { if (type === 'keydown') b.key = fn; if (type === 'visibilitychange') b.vis = fn; },
    createElement: (tag) => (tag === 'audio' ? makeAudio() : {}),
  };
  b.logs = [];
  const con = opts.captureLog ? { log: (s) => b.logs.push(String(s)), error: console.error, warn: console.warn } : console;
  const sb = { console: con, document: doc, location: { search }, XMLHttpRequest: FakeXHR,
    requestAnimationFrame: (cb) => { b.raf = cb; return 1; }, setTimeout, clearTimeout };
  if (opts.vw) { sb.innerWidth = opts.vw; sb.innerHeight = opts.vh; sb.devicePixelRatio = opts.dpr || 1; }
  if (opts.image) { sb.Image = class { constructor() { this.src = ''; this.naturalWidth = 0; this.naturalHeight = 0; b.images.push(this); } }; }
  if (opts.navigator) sb.navigator = opts.navigator;
  // FileReader: reads the stub file's bytes synchronously-ish (next tick), like a local file.
  sb.FileReader = class { readAsArrayBuffer(f) { setImmediate(() => { const u = Uint8Array.from(f.bytes); this.result = u.buffer; this.onload(); }); } };
  if (opts.speech) {
    sb.SpeechSynthesisUtterance = class { constructor(t) { this.text = t; } };
    sb.speechSynthesis = { speak: (u) => { b.spoken.push([u.text, b.lastSong]); }, cancel: () => { b.cancels = (b.cancels || 0) + 1; } };
  }
  b.cv = cv;
  b.doc = doc;
  b.sb = sb;
  b.hide = (hidden) => { doc.visibilityState = hidden ? 'hidden' : 'visible'; if (b.vis) b.vis({ type: 'visibilitychange' }); };
  sb.window = sb; sb.self = sb;
  vm.createContext(sb);
  vm.runInContext(fs.readFileSync(path, 'utf8'), sb, { filename: path });
  sb.main();
  b.frame = (t) => {
    const cb = b.raf; b.raf = null; b.texts.length = 0; b.canvasTexts.length = 0; b.fills.length = 0; b.strokes = 0; cb(t);
    for (const id of ['hud-l', 'hud-r', 'hud-c']) if (huds[id] && huds[id].textContent) b.texts.push(...huds[id].textContent.split('\n'));
  };
  b.press = (k, code) => b.key({ key: k, code: code || '', repeat: false, preventDefault() {} });
  b.hud = (prefix) => b.texts.find((s) => s.startsWith(prefix));
  b.has = (s) => b.texts.includes(s);
  return b;
}
const tick = () => new Promise((r) => setImmediate(r));
const CHART = '?chart=charts/sample_chart.json';

(async () => {
  // A: loader + audio clock + fallback when the audio errors mid-song.
  let p = boot(CHART);
  p.frame(0);
  expect('chart: XHR GET charts/sample_chart.json', p.xhrs.length === 1 && p.xhrs[0].url === 'charts/sample_chart.json' && p.xhrs[0].sent);
  expect('chart: loading status shown', p.has('Loading chart...'));
  p.xhrs[0].respond();
  p.frame(16);
  expect('chart: title in HUD', p.hud('Fruit Fly') === 'Fruit Fly Heartbeat', p.hud('Fruit Fly'));
  expect('chart: artist + 6 notes', p.has('LIF Autoplayer \u00b7 6 notes'));
  const au = p.audios[0];
  const wavB64 = au ? au.src.replace('data:audio/wav;base64,', '') : '';
  const wav = Buffer.from(wavB64, 'base64');
  expect('chart: click-track WAV data URI', !!au && au.src.startsWith('data:audio/wav;base64,') && wav.slice(0, 4).toString() === 'RIFF' && wav.slice(8, 12).toString() === 'WAVE', wav.length + ' bytes');
  expect('chart: WAV is 4.5 s mono 16-bit 8 kHz', wav.length === 44 + 4500 * 8 * 2 && wav.readUInt16LE(22) === 1 && wav.readUInt32LE(24) === 8000 && wav.readUInt16LE(34) === 16, wav.length);
  expect('chart: clock audio before start', p.has('clock audio'));
  au.currentTime = 7.5;
  p.press(' ');
  expect('audio: play() from 0 on Space', au.plays === 1 && au.currentTime === 0);
  // frame stamps deliberately far from audio time: the audio position must win
  au.currentTime = 1.0; p.frame(50000); p.press('d', 'KeyD');
  au.currentTime = 1.56; p.frame(50016); p.press('d', 'KeyD');
  p.frame(50032);
  expect('audio clock: PERFECT + GREAT = 500', p.hud('Score ') === 'Score 500', p.hud('Score '));
  expect('audio clock: no misses despite stamp 50 s', p.hud('Miss ') === 'Miss 0', p.hud('Miss '));
  au.currentTime = 1.6; p.frame(60000);   // last good reading: song 1600 at stamp 60000
  au.fail();                              // audio error -> frame clock from 1600
  p.frame(60500);                         // song 2100: notes at 2000 still in window
  expect('fallback: clock frame after audio error', p.has('clock frame'));
  expect('fallback: no miss at song 2100', p.hud('Miss ') === 'Miss 0', p.hud('Miss '));
  p.frame(60560);                         // song 2160 > 2000+150: both 2000 notes missed
  expect('fallback: continues from last audio time (Miss 2 at 2160)', p.hud('Miss ') === 'Miss 2', p.hud('Miss '));
  p.frame(70000);
  expect('fallback: song completes', p.has('Song complete'));

  // B: LIF autoplayer driven by the audio clock (stamps advance at a different rate).
  p = boot(CHART);
  p.frame(0); p.xhrs[0].respond(); p.press('b', 'KeyB'); p.frame(16);
  expect('autoplay+audio: toggled on', p.has('LIF autoplay ON'));
  const a2 = p.audios[0];
  p.press(' ');
  let st = 16, done = false;
  for (let i = 0; i < 1000 && !done; i++) { a2.currentTime += 0.016; st += 33; p.frame(st); done = p.has('Song complete'); }
  expect('autoplay+audio: finished', done);
  expect('autoplay+audio: 6/6 PERFECT = 1800', p.hud('Score ') === 'Score 1800' && p.has('P 6  Gr 0  Go 0  M 0'), p.hud('Score '));
  expect('autoplay+audio: spikes 6', p.hud('spikes ') === 'spikes 6', p.hud('spikes '));
  expect('autoplay+audio: audio paused at end', a2.paused === true);

  // C: play() refused (autoplay policy) -> frame clock; autoplayer still plays.
  p = boot(CHART, { rejectPlay: true });
  p.frame(0); p.xhrs[0].respond(); p.press('b', 'KeyB'); p.frame(16);
  p.press(' ');
  await tick();                            // let the rejected play() promise settle
  st = 16; done = false;
  for (let i = 0; i < 1000 && !done; i++) { st += 16; p.frame(st); done = p.has('Song complete'); }
  expect('refused play(): frame clock fallback', p.has('clock frame'));
  expect('refused play(): autoplay 1800, no misses', done && p.hud('Score ') === 'Score 1800' && p.hud('Miss ') === 'Miss 0', p.hud('Score '));

  // D: ?audio=none -> no audio element, frame clock.
  p = boot(CHART + '&audio=none');
  p.frame(0); p.xhrs[0].respond(); p.frame(16);
  expect('audio=none: no <audio>, clock frame', p.audios.length === 0 && p.has('clock frame'));

  // E: missing chart -> error shown, generated seed chart still playable.
  p = boot('?chart=charts/missing.json&seed=2026');
  p.frame(0); p.xhrs[0].respond(); p.frame(16);
  expect('missing chart: HTTP 404 shown', p.has('Chart load failed (HTTP 404)'));
  expect('missing chart: falls back to seed chart', p.hud('seed ') === 'seed 2026' && p.audios.length === 0, p.hud('seed '));
  p.press(' '); p.frame(2000); p.press('j', 'KeyJ'); p.frame(2016);
  expect('missing chart: seed game plays (PERFECT 300)', p.hud('Score ') === 'Score 300', p.hud('Score '));

  // F: malformed chart -> the parser's message is shown.
  p = boot(CHART, { chartText: '{"metadata":{"title":"x","artist":"y","bpm":120,"offset_ms":0},"notes":[{"time_ms":5,"lane":9}]}' });
  p.frame(0); p.xhrs[0].respond(); p.frame(16);
  expect('bad chart: lane error shown', p.has('Bad chart: notes[0].lane: must be an integer 0..3, got 9'),
    p.texts.find((s) => s.startsWith('Bad')));


  // ---------------------------------------------------------------------------
  // Part 3: stage, HUD overlay, connectome autoplayer, assist mode.
  const IPHONE = { hud: true, image: true, vw: 390, vh: 844, dpr: 3 };
  // G: iPhone 12 layout, DPR backing store, HTML HUD, light default stage, 3D stage.
  p = boot('?seed=2026', IPHONE);
  p.frame(0);
  expect('stage: canvas 1170x2532 backing at DPR 3, CSS 390x844', p.cv.width === 1170 && p.cv.height === 2532
    && p.cv.style.width === '390px' && p.cv.style.height === '844px', p.cv.width + 'x' + p.cv.height + ' ' + p.cv.style.width);
  expect('stage: setTransform(3,0,0,3,0,0) every frame', p.transforms.length >= 1 && p.transforms[p.transforms.length - 1].join(',') === '3,0,0,3,0,0');
  expect('light stage: default, no image loaded', p.images.length === 0 && p.draws === 0 && p.doc.body.className === 'theme-light', p.doc.body.className);
  expect('light stage: #f7f6f3 backdrop fill first', p.fills[0] === '#f7f6f3', p.fills[0]);
  expect('light stage: procedural floor (many thin strokes)', p.strokes > 100, p.strokes);
  expect('light stage: dark lane keys / labels', p.fills.includes('#2b2f3a'));
  expect('HUD overlay: Score/mode in HTML, not canvas', p.huds['hud-l'].textContent.startsWith('Score 0')
    && p.huds['hud-r'].textContent.includes('autoplay off') && !p.canvasTexts.some((t) => t.startsWith('Score ')));
  expect('HUD overlay: title prompt in #hud-c', p.huds['hud-c'].textContent.includes('Press Space to start'));
  expect('stage: region labels incl. label-only ones', ['medulla (label)', 'lamina (label)', 'central complex (label)', 'mushroom body'].every((l) => p.canvasTexts.includes(l)));
  expect('stage: toy caption shown', p.canvasTexts.some((t) => t.startsWith('TOY circuit')));
  expect('stage: origin anchor label', p.canvasTexts.includes('origin'));
  expect('stage: blocks cut 0 on the title screen (song time frozen)', p.hud('blocks cut ') === 'blocks cut 0', p.hud('blocks cut '));
  // G2: ?bg=ar keeps the AR photo option.
  const pa = boot('?seed=2026&bg=ar', IPHONE);
  const img = pa.images[0];
  pa.frame(0);
  expect('?bg=ar: AR image requested, dark theme', !!img && img.src === 'assets/ar_brain_bg.jpg' && pa.doc.body.className === 'theme-ar', img && img.src);
  expect('?bg=ar: no drawImage before the image has loaded', pa.draws === 0);
  img.naturalWidth = 1170; img.naturalHeight = 2533; pa.frame(16);
  expect('?bg=ar: photo drawn once loaded, then dimmed', pa.draws === 1 && pa.fills[0] === 'rgba(5,7,13,0.7)', pa.draws + ' ' + pa.fills[0]);
  expect('?bg=ar: orbit grid + brain strokes drawn', pa.strokes > 20, pa.strokes);

  // H: connectome autoplayer, seed 2026, cycled with C (off -> LIF -> connectome).
  p.press('c', 'KeyC'); p.frame(32);
  expect('mode C#1: LIF', p.has('LIF autoplay ON'));
  p.press('c', 'KeyC'); p.frame(48);
  expect('mode C#2: connectome', p.has('connectome autoplay ON'));
  expect('connectome: toy circuit 12 neurons in HUD', p.has('circuit toy (12 neurons)'));
  expect('connectome: lane labels from toy region attribute', ['antennal lobe', 'mushroom body', 'lateral horn', 'lobula'].every((l) => p.canvasTexts.includes(l)));
  p.press(' ');
  st = 48; done = false;
  let flashSeen = false;
  let sliceLabel = false;
  for (let i = 0; i < 5000 && !done; i++) {
    st += 16; p.frame(st); done = p.has('Song complete');
    sliceLabel = sliceLabel || p.canvasTexts.includes('PERFECT'); // judgement drawn over the sliced block
  }
  expect('connectome: seed 2026 finished', done);
  expect('stage: judgement text drawn over sliced blocks (canvas)', sliceLabel);
  expect('connectome: 64/64 PERFECT = 58800', p.hud('Score ') === 'Score 58800' && p.has('P 64  Gr 0  Go 0  M 0'), p.hud('Score '));
  expect('connectome: spikes 192 (in+inter+out) and 64 key presses', p.hud('spikes ') === 'spikes 192 \u00b7 keys 64', p.hud('spikes '));
  expect('stage: blocks cut = judged hits (64)', p.hud('blocks cut ') === 'blocks cut 64', p.hud('blocks cut '));
  expect('stage: blocks never touch the rhythm score', p.hud('Score ') === 'Score 58800');
  p.press('c', 'KeyC'); p.frame(st + 16);
  expect('mode C#3: assist (LIF fly)', p.has('assist ON (LIF fly)'));
  p.press('c', 'KeyC'); p.press('c', 'KeyC'); p.press('c', 'KeyC'); p.frame(st + 32);
  expect('mode C cycles back via off to LIF', p.has('LIF autoplay ON'));

  // I: sample chart, connectome autoplay, frame clock; C ignored mid-song.
  p = boot(CHART + '&audio=none', IPHONE);
  p.frame(0); p.xhrs[0].respond(); p.press('c', 'KeyC'); p.press('c', 'KeyC'); p.frame(16);
  p.press(' ');
  p.frame(500); p.press('c', 'KeyC'); p.frame(516);
  expect('mode key ignored while playing', p.has('connectome autoplay ON'));
  st = 516; done = false;
  for (let i = 0; i < 1000 && !done; i++) { st += 16; p.frame(st); done = p.has('Song complete'); }
  expect('connectome: sample chart 6/6 PERFECT = 1800', p.hud('Score ') === 'Score 1800' && p.has('P 6  Gr 0  Go 0  M 0'), p.hud('Score '));

  // J: assist mode: human hits notes 1000 (D), 2000 (J) and 2500 (F); the fly covers 1500, 2000 lane 3 and 3000.
  for (const [presses, label] of [[3, 'LIF fly'], [4, 'connectome fly']]) {
    p = boot(CHART + '&audio=none', IPHONE);
    p.frame(0); p.xhrs[0].respond();
    for (let k = 0; k < presses; k++) p.press('c', 'KeyC');
    p.frame(16);
    expect('assist: mode ' + label, p.has('assist ON (' + label + ')'));
    p.press(' ');                         // frame clock starts at stamp 16 -> song = stamp - 16
    const human = { 1000: ['d', 'KeyD'], 2000: ['j', 'KeyJ'], 2500: ['f', 'KeyF'] };
    done = false;
    for (let song = 16; song < 6000 && !done; song += 16) {
      p.frame(song + 16);
      for (const t of Object.keys(human)) {   // press on the first frame at/after the note (< 16 ms late)
        if (song >= +t && !human[t].done) { p.press(human[t][0], human[t][1]); human[t].done = true; }
      }
      done = p.has('Song complete');
    }
    // human presses 0-15 ms late: 3 PERFECT by you; 3 GREAT covers by the fly (95 ms late).
    expect('assist (' + label + '): you 3 · fly 3', p.hud('you ') === 'you 3 \u00b7 fly 3', p.hud('you '));
    expect('assist (' + label + '): 3 PERFECT + 3 GREAT, no miss, 1500', p.has('P 3  Gr 3  Go 0  M 0') && p.hud('Score ') === 'Score 1500', p.hud('Score '));
  }

  // K: ?camera=1 without getUserMedia -> screenshot fallback, said so in the HUD.
  p = boot('?seed=2026&camera=1', IPHONE);
  p.frame(0);
  expect('camera: unavailable -> screenshot fallback status', p.has('camera unavailable: using screenshot'));
  expect('camera: falls back to the AR screenshot (dark theme)', p.images.length === 1 && p.images[0].src === 'assets/ar_brain_bg.jpg' && p.doc.body.className === 'theme-ar');

  // L: ?connectome=URL: a good file loads, a bad one shows the parser error and keeps the toy circuit.
  p = boot('?seed=2026&connectome=connectomes/toy_lane_circuit.xml', IPHONE);
  p.frame(0); p.xhrs[0].respond(); p.press('c', 'KeyC'); p.press('c', 'KeyC'); p.frame(16);
  expect('?connectome: file loaded', p.has('circuit connectomes/toy_lane_circuit.xml (12 neurons)'));
  p = boot('?seed=2026&connectome=x.xml', Object.assign({ chartText: '<hemibrain><neuron id="A"/></hemibrain>' }, IPHONE));
  p.frame(0); p.xhrs[0].respond(); p.press('c', 'KeyC'); p.press('c', 'KeyC'); p.frame(16);
  expect('?connectome: bad file -> error, toy kept', p.has("Bad connectome: connectome has no input neuron 'lane0.in'") && p.has('circuit toy (12 neurons)'),
    p.texts.find((t) => t.startsWith('Bad')));

  // M: desktop viewport scales up (phone-shaped field, DPR 2).
  p = boot('?seed=2026', { hud: true, image: true, vw: 1920, vh: 1080, dpr: 2 });
  p.frame(0);
  expect('desktop: 510x960 CSS at DPR 2 -> 1020x1920 backing', p.cv.width === 1020 && p.cv.height === 1920 && p.cv.style.width === '510px', p.cv.width + 'x' + p.cv.height);

  // N: on-screen AUTOPLAY button (iPhone layout): rendered, cycles like C, stays in sync, never presses a lane.
  p = boot('?seed=2026', IPHONE);
  p.frame(0);
  const btn = p.btn;
  const px = (v) => parseFloat(v);
  expect('button: rendered with label AUTOPLAY: OFF', btn.textContent === 'AUTOPLAY: OFF', btn.textContent);
  expect('button: placed >= 44x44 CSS px, inside the 390 px stage', px(btn.style.width) >= 44 && px(btn.style.height) >= 44
    && px(btn.style.left) >= 0 && px(btn.style.left) + px(btn.style.width) <= 390, [btn.style.left, btn.style.top, btn.style.width, btn.style.height].join(' '));
  expect('button: below the corner HUD (5 lines), title text moved under it', px(btn.style.top) >= 120
    && px(p.huds['hud-c'].style.top) >= px(btn.style.top) + px(btn.style.height), btn.style.top + ' / hud-c ' + p.huds['hud-c'].style.top);
  expect('button: click + touch (pointer) listeners', !!(btn.handlers.click && btn.handlers.pointerdown));
  expect('button: title prompt mentions it', p.has('C or AUTOPLAY button: change mode'));
  const tapOk = btn.tap(); p.frame(16);
  expect('button: tap -> LIF fly (HUD + label)', p.has('LIF autoplay ON') && btn.textContent === 'AUTOPLAY: LIF FLY', btn.textContent);
  expect('button: no focus steal (pointerdown default prevented, blurred, click not propagated)', tapOk && btn.blurs >= 1);
  btn.tap(); p.frame(32);
  expect('button: tap -> connectome fly', p.has('connectome autoplay ON') && btn.textContent === 'AUTOPLAY: CONNECTOME FLY', btn.textContent);
  p.press('c', 'KeyC'); p.frame(48);
  expect('button: label follows key C (assist LIF fly)', p.has('assist ON (LIF fly)') && btn.textContent === 'AUTOPLAY: ASSIST \u00b7 LIF FLY', btn.textContent);
  btn.tap(); p.frame(64);
  expect('button: tap -> assist connectome fly', btn.textContent === 'AUTOPLAY: ASSIST \u00b7 CONNECTOME FLY' && p.has('assist ON (connectome fly)'), btn.textContent);
  btn.tap(); p.frame(80);
  expect('button: wraps to off', btn.textContent === 'AUTOPLAY: OFF' && p.has('autoplay off'), btn.textContent);
  p.press('b', 'KeyB'); p.frame(96);
  expect('button: label follows key B', btn.textContent === 'AUTOPLAY: LIF FLY', btn.textContent);
  p.press('b', 'KeyB'); p.frame(112);
  p.press(' ');                              // human play, mode off, frame clock starts at stamp 112
  p.frame(112 + 2000); btn.tap(); p.frame(112 + 2016);   // note 2@2000: a tap must not hit it
  expect('button: locked mid-song (mode unchanged, dimmed, LOCKED label)', btn.textContent === 'LOCKED: OFF' && btn.className === 'locked' && p.has('autoplay off'), btn.textContent + ' ' + btn.className);
  expect('lock: tap mid-song shows the lock hint', p.has('Autoplay locked during song - press R to restart'));
  expect('lock: tooltip says locked', /^Locked during song/.test(btn.title), btn.title);
  p.frame(112 + 2200);
  expect('button: tap never presses a lane (note missed, score 0)', p.hud('Score ') === 'Score 0' && p.hud('Miss ') === 'Miss 1', p.hud('Score ') + ' ' + p.hud('Miss '));
  // desktop: same rules
  p = boot('?seed=2026', { hud: true, image: true, vw: 1920, vh: 1080, dpr: 1 });
  p.frame(0); p.btn.tap(); p.btn.tap(); p.frame(16);
  expect('button (desktop 1920x1080): placed, two taps -> connectome fly', px(p.btn.style.height) >= 44 && px(p.btn.style.left) + px(p.btn.style.width) <= 510
    && p.btn.textContent === 'AUTOPLAY: CONNECTOME FLY' && p.has('connectome autoplay ON'), p.btn.textContent);

  // O: lock feedback for key C, and Space never steps the mode (fix for the live-site report).
  p = boot('?seed=2026', IPHONE);
  p.frame(0); p.btn.tap(); p.btn.tap(); p.frame(16);
  expect('O: two taps -> CONNECTOME FLY, idle tooltip', p.btn.textContent === 'AUTOPLAY: CONNECTOME FLY' && /^Autoplay mode/.test(p.btn.title), p.btn.textContent);
  const kd = p.btn.fire('keydown', { key: ' ', code: 'Space' });
  const ku = p.btn.fire('keyup', { key: ' ', code: 'Space' });
  expect('O: Space on the button: its default (activation) cancelled', kd.defaultPrevented && ku.defaultPrevented);
  const ke = p.btn.fire('keydown', { key: 'Enter', code: 'Enter' });
  expect('O: Enter on the button: default cancelled', ke.defaultPrevented);
  const kx = p.btn.fire('keydown', { key: 'd', code: 'KeyD' });
  expect('O: other keys on the button untouched', !kx.defaultPrevented);
  p.btn.fire('click', { detail: 0 }); p.frame(32);   // keyboard-synthesised click while idle
  expect('O: keyboard-synthesised click (detail 0) ignored', p.btn.textContent === 'AUTOPLAY: CONNECTOME FLY' && p.has('connectome autoplay ON'), p.btn.textContent);
  let spaceEv = { key: ' ', code: 'Space', repeat: false, prevented: false, preventDefault() { this.prevented = true; } };
  p.key(spaceEv); p.btn.fire('click', { detail: 0 }); p.frame(48);
  expect('O: Space starts the song with the chosen mode (CONNECTOME FLY, not ASSIST)', p.has('connectome autoplay ON') && p.btn.textContent === 'LOCKED: CONNECTOME FLY' && spaceEv.prevented, p.btn.textContent);
  expect('O: no lock hint until a mode input', !p.has('Autoplay locked during song - press R to restart'));
  p.press('c', 'KeyC'); p.frame(64);
  expect('O: C mid-song -> hint shown, mode kept', p.has('Autoplay locked during song - press R to restart') && p.has('connectome autoplay ON'));
  p.frame(64 + 2300);
  expect('O: hint is transient (gone after ~2.2 s)', !p.has('Autoplay locked during song - press R to restart'));
  p.press('b', 'KeyB'); p.frame(64 + 2316);
  expect('O: B mid-song -> hint too, mode kept', p.has('Autoplay locked during song - press R to restart') && p.has('connectome autoplay ON'));
  spaceEv = { key: ' ', code: 'Space', repeat: false, prevented: false, preventDefault() { this.prevented = true; } };
  p.key(spaceEv); p.frame(64 + 2332);
  expect('O: Space mid-song consumed, mode kept', spaceEv.prevented && p.has('connectome autoplay ON'));
  p.press('r', 'KeyR'); p.frame(64 + 2348);
  expect('O: R restarts: unlocked, hint cleared', p.btn.textContent === 'AUTOPLAY: CONNECTOME FLY' && p.btn.className === '' && !p.has('Autoplay locked during song - press R to restart') && p.has('Press Space to start'), p.btn.textContent);
  p.key({ key: 'c', code: 'KeyC', repeat: false, preventDefault() {} });
  p.key({ key: 'c', code: 'KeyC', repeat: true, preventDefault() {} });
  p.key({ key: 'c', code: 'KeyC', repeat: true, preventDefault() {} }); p.frame(64 + 2364);
  expect('O: held C (auto-repeat) steps once', p.has('assist ON (LIF fly)') && p.btn.textContent === 'AUTOPLAY: ASSIST \u00b7 LIF FLY', p.btn.textContent);

  // P: Euclidean rhythm songs (default song), picker buttons, lock, HUD patterns, synthesised audio, fly modes.
  p = boot('', IPHONE);
  p.frame(0);
  expect('P: default song is Euclidean LAYERED x4 @ 120 BPM', p.rhythmBtn.textContent === 'LAYERED x4' && p.bpmBtn.textContent === '120 BPM'
    && p.hud('Euclid') === 'Euclid \u00b7 LAYERED x4', p.hud('Euclid'));
  expect('P: HUD shows each layer as an x/. string', ['D E(4,16) x...x...x...x...', 'F E(3,8) x..x..x.', 'J E(5,8) x.xx.xx.', 'K E(7,12) x.xx.x.xx.x.'].every((l) => p.has(l)));
  expect('P: 152 notes (19 per bar x 8)', p.has('Bjorklund \u00b7 120 BPM \u00b7 152 notes'));
  const eu = p.audios[p.audios.length - 1];
  const ew = Buffer.from(eu ? eu.src.replace('data:audio/wav;base64,', '') : '', 'base64');
  expect('P: synthesised WAV (16 kHz mono 16-bit), no file fetched', !!eu && eu.src.startsWith('data:audio/wav;base64,') && ew.readUInt32LE(24) === 16000 && ew.readUInt16LE(22) === 1 && p.xhrs.length === 0, ew.length);
  const ePcm = (ms) => ew.readInt16LE(44 + 2 * Math.round(ms * 16));
  let quiet = true; for (let ms = 0; ms < 1990; ms += 5) quiet = quiet && ePcm(ms) === 0;
  let loud = 0; for (let ms = 2000; ms < 2020; ms += 0.0625) loud = Math.max(loud, Math.abs(ePcm(ms)));
  expect('P: silent lead-in, onset at the first note (2000 ms)', quiet && loud > 3000, loud);
  const rr = p.rhythmBtn, br = p.bpmBtn;
  const rx = (v) => parseFloat(v);
  expect('P: picker row: 44 px tap targets inside 390 px, under AUTOPLAY, centre text below', rx(rr.style.height) >= 44 && rx(br.style.height) >= 44
    && rx(br.style.left) + rx(br.style.width) <= 390 && rx(rr.style.top) >= rx(p.btn.style.top) + rx(p.btn.style.height)
    && rx(p.huds['hud-c'].style.top) >= rx(rr.style.top) + rx(rr.style.height), [rr.style.left, rr.style.top, rr.style.width, br.style.width, p.huds['hud-c'].style.top].join(' '));
  rr.tap(); p.frame(16);
  expect('P: tap rhythm -> TRESILLO, DFJK x..x..x. (single pattern spread over the lanes)', rr.textContent === 'TRESILLO E(3,8)' && p.has('DFJK E(3,8) x..x..x.') && p.has('Bjorklund \u00b7 120 BPM \u00b7 24 notes'), rr.textContent);
  br.tap(); p.frame(32);
  expect('P: tap BPM -> 140', br.textContent === '140 BPM' && p.has('Bjorklund \u00b7 140 BPM \u00b7 24 notes'), br.textContent);
  p.press('t', 'KeyT'); p.frame(48);
  expect('P: key T -> 90 BPM', br.textContent === '90 BPM', br.textContent);
  p.press('e', 'KeyE'); p.press('e', 'KeyE'); p.frame(64);
  expect('P: key E x2 -> BEMBE E(7,12)', rr.textContent === 'BEMBE E(7,12)' && p.has('DFJK E(7,12) x.xx.x.xx.x.'), rr.textContent);
  rr.fire('click', { detail: 0 }); p.frame(80);
  expect('P: keyboard-synthesised click on a picker ignored', rr.textContent === 'BEMBE E(7,12)');
  p.press('e', 'KeyE'); p.press('e', 'KeyE'); p.frame(96);
  expect('P: E reaches the seed chart slot (legacy chart, BPM n/a)', rr.textContent === 'SEED CHART' && p.hud('seed ') === 'seed 2026' && br.className === 'picker locked', rr.textContent);
  p.press('e', 'KeyE'); p.frame(112);
  expect('P: and wraps to LAYERED', rr.textContent === 'LAYERED x4');
  // connectome fly plays the layered chart through the audio clock
  p.press('c', 'KeyC'); p.press('c', 'KeyC'); p.frame(128);
  const la = p.audios[p.audios.length - 1];
  p.press(' '); p.frame(144);
  expect('P: Space starts the synthesised audio; pickers locked', la.plays === 1 && rr.className === 'picker locked' && br.className === 'picker locked', rr.className);
  rr.tap(); p.frame(160);
  expect('P: rhythm tap mid-song -> picker lock hint, song unchanged', p.has('Picker locked during song - press R to restart') && rr.textContent === 'LAYERED x4');
  p.press('t', 'KeyT'); p.frame(176);
  expect('P: T mid-song -> locked, tempo unchanged', br.textContent === '90 BPM' && p.has('Picker locked during song - press R to restart'), br.textContent);
  st = 176; done = false;
  for (let i = 0; i < 4000 && !done; i++) { la.currentTime += 0.016; st += 16; p.frame(st); done = p.has('Song complete'); }
  expect('P: connectome fly: layered @90 all 152 PERFECT', done && p.has('P 152  Gr 0  Go 0  M 0'), p.texts.find((t) => t.startsWith('P ')));
  // LIF fly + assist fly on a single-layer preset via the URL
  for (const [presses, label, key] of [[0, 'LIF', 'b'], [3, 'assist LIF', 'c'], [4, 'assist connectome', 'c']]) {
    p = boot('?rhythm=cinquillo&bpm=140&audio=none', IPHONE);
    p.frame(0);
    if (key === 'b') p.press('b', 'KeyB'); else for (let k = 0; k < presses; k++) p.press('c', 'KeyC');
    p.frame(16); p.press(' ');
    st = 16; done = false;
    for (let i = 0; i < 4000 && !done; i++) { st += 16; p.frame(st); done = p.has('Song complete'); }
    expect('P: ?rhythm=cinquillo&bpm=140, ' + label + ' fly: 40 notes, no miss', p.rhythmBtn.textContent === 'CINQUILLO E(5,8)' && p.bpmBtn.textContent === '140 BPM'
      && done && / M 0$/.test(p.texts.find((t) => t.startsWith('P ')) || '') && p.hud('Miss ') === 'Miss 0', p.texts.find((t) => t.startsWith('P ')));
  }

  // Q: music-source picker: Euclidean (default) / MIDI file / TTS voice.
  const vlq = (v) => { const o = [v & 0x7f]; while ((v >>= 7) > 0) o.unshift((v & 0x7f) | 0x80); return o; };
  const smf = (format, division, tracks) => {
    const out = [0x4d, 0x54, 0x68, 0x64, 0, 0, 0, 6, 0, format, 0, tracks.length, division >> 8, division & 0xff];
    for (const t of tracks) out.push(0x4d, 0x54, 0x72, 0x6b, (t.length >>> 24) & 0xff, (t.length >> 16) & 0xff, (t.length >> 8) & 0xff, t.length & 0xff, ...t);
    return out;
  };
  // C-major scale up and down, quarters at 100 BPM (tempo 600000 us), format 0, 480 PPQN; built here, no .mid committed.
  const scaleTrack = [0, 0xff, 0x51, 3, 0x09, 0x27, 0xc0];
  for (const x of [60, 62, 64, 65, 67, 69, 71, 72, 72, 71, 69, 67, 65, 64, 62, 60]) scaleTrack.push(0, 0x90, x, 100, ...vlq(480), 0x80, x, 0);
  scaleTrack.push(0, 0xff, 0x2f, 0);
  const SCALE = smf(0, 480, [scaleTrack]);
  p = boot('', IPHONE);
  p.frame(0);
  const sb3 = p.sourceBtn;
  const row3 = [sb3, p.rhythmBtn, p.bpmBtn].map((x) => [rx(x.style.left), rx(x.style.top), rx(x.style.width), rx(x.style.height)]);
  expect('Q: three picker buttons, 44 px, in order, inside 390 px', row3.every((r) => r[2] >= 44 && r[3] >= 44 && r[1] === row3[0][1])
    && row3[0][0] + row3[0][2] <= row3[1][0] && row3[1][0] + row3[1][2] <= row3[2][0] && row3[2][0] + row3[2][2] <= 390, JSON.stringify(row3));
  expect('Q: default source EUCLID / LAYERED x4 / 120 BPM', sb3.textContent === 'EUCLID' && p.rhythmBtn.textContent === 'LAYERED x4' && p.bpmBtn.textContent === '120 BPM');
  sb3.tap(); p.frame(16);
  expect('Q: tap source -> MIDI, PICK .MID, FILE BPM, prompt', sb3.textContent === 'MIDI' && p.rhythmBtn.textContent === 'PICK .MID' && p.bpmBtn.textContent === 'FILE BPM'
    && p.has('No MIDI file yet: tap PICK .MID (seed chart for now)'), p.rhythmBtn.textContent);
  p.rhythmBtn.tap(); p.frame(32);
  expect('Q: tap PICK .MID opens the file input (in the gesture)', p.midiInput.clicks === 1);
  p.midiInput.pick('notmidi.mid', [0x52, 0x49, 0x46, 0x46, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]); await tick(); p.frame(48);
  expect('Q: non-MIDI file -> parser error shown, nothing loaded', p.has('Bad MIDI: not a MIDI file: no MThd header') && p.rhythmBtn.textContent === 'PICK .MID');
  p.midiInput.pick('scale.mid', SCALE); await tick(); p.frame(64);
  expect('Q: scale.mid parsed: title, tempo, 16 notes', p.rhythmBtn.textContent === 'scale' && p.hud('MIDI') === 'MIDI \u00b7 scale'
    && p.has('format 0 \u00b7 1 track \u00b7 100 BPM \u00b7 16 notes') && !p.has('Bad MIDI: not a MIDI file: no MThd header'), p.hud('MIDI'));
  const ma = p.audios[p.audios.length - 1];
  const mw = Buffer.from(ma.src.replace('data:audio/wav;base64,', ''), 'base64');
  expect('Q: MIDI audio synthesised in-page (11025 Hz WAV)', ma.src.startsWith('data:audio/wav;base64,') && mw.readUInt32LE(24) === 11025, mw.length);
  p.press('c', 'KeyC'); p.press('c', 'KeyC'); p.frame(80); p.press(' '); p.frame(96);
  sb3.tap(); p.frame(112);
  expect('Q: source tap mid-song -> locked hint, source kept', sb3.textContent === 'MIDI' && sb3.className === 'picker locked' && p.has('Picker locked during song - press R to restart'));
  p.press('s', 'KeyS'); p.frame(120);
  expect('Q: key S mid-song -> locked', sb3.textContent === 'MIDI');
  st = 120; done = false;
  for (let i = 0; i < 4000 && !done; i++) { ma.currentTime += 0.016; st += 16; p.frame(st); done = p.has('Song complete'); }
  expect('Q: connectome fly plays the MIDI chart: 16/16 PERFECT', done && p.has('P 16  Gr 0  Go 0  M 0'), p.texts.find((t) => t.startsWith('P ')));
  p.press('s', 'KeyS'); p.frame(st + 16);
  expect('Q: key S -> VOICE; no speechSynthesis -> graceful text-only notice', sb3.textContent === 'VOICE' && p.rhythmBtn.textContent === 'FRUIT FLY'
    && p.has('speechSynthesis unavailable: syllables shown on stage only') && p.has('\u266a fruit fly brain keeps the beat'), p.rhythmBtn.textContent);
  expect('Q: voice chart on the beat grid: 24 notes, click-track clock', p.has('speechSynthesis \u00b7 120 BPM \u00b7 24 notes') && p.audios[p.audios.length - 1].src.startsWith('data:audio/wav;base64,'));
  p.rhythmBtn.tap(); p.frame(st + 32);
  expect('Q: item tap cycles the line (COUNT 1-4)', p.rhythmBtn.textContent === 'COUNT 1-4' && p.has('\u266a one and two and three and four and'));
  p.press('e', 'KeyE'); p.press('e', 'KeyE'); p.frame(st + 48);
  expect('Q: back to FRUIT FLY', p.rhythmBtn.textContent === 'FRUIT FLY');
  p.press(' ');
  const va = p.audios[p.audios.length - 1];
  let t0 = st + 48; done = false; let sawSyl = false;
  for (let i = 0; i < 4000 && !done; i++) { va.currentTime += 0.016; t0 += 16; p.frame(t0); sawSyl = sawSyl || p.has('\u266a brain'); done = p.has('Song complete'); }
  expect('Q: connectome fly plays the voice chart (no speech): 24 notes, no miss; current syllable on stage', done && / M 0$/.test(p.texts.find((t) => t.startsWith('P ')) || '') && sawSyl, p.texts.find((t) => t.startsWith('P ')));
  p.press('s', 'KeyS'); p.frame(t0 + 16);
  expect('Q: S wraps to EUCLID (LAYERED x4 again)', sb3.textContent === 'EUCLID' && p.rhythmBtn.textContent === 'LAYERED x4' && p.has('D E(4,16) x...x...x...x...'));
  // With speechSynthesis: each syllable spoken once, in order, ~60 ms before its note; LIF and assist flies play it.
  for (const [label, keys] of [['LIF', ['b']], ['assist LIF', ['c', 'c', 'c']]]) {
    p = boot('?source=voice&voice=solfege&audio=none', Object.assign({ speech: true }, IPHONE));
    p.frame(0);
    for (const k of keys) p.press(k, 'Key' + k.toUpperCase());
    p.frame(16); p.press(' ');
    st = 16; done = false;
    for (let i = 0; i < 4000 && !done; i++) { st += 16; p.lastSong = st - 16; p.frame(st); done = p.has('Song complete'); }
    const words = p.spoken.map((w) => w[0]);
    const firstAt = p.spoken.length ? p.spoken[0][1] : -1;
    expect('Q: ?source=voice&voice=solfege, ' + label + ' fly: 32 notes, no miss, 32 syllables spoken in order', p.rhythmBtn.textContent === 'DO RE MI'
      && done && / M 0$/.test(p.texts.find((t) => t.startsWith('P ')) || '') && words.length === 32 && words.slice(0, 8).join(' ') === 'do re mi fa sol la ti do'
      && firstAt >= 2000 - 60 - 16 && firstAt <= 2000, words.length + ' first@' + firstAt + ' ' + p.texts.find((t) => t.startsWith('P ')));
  }

  // R: label / HUD written on the input itself, not on the next animation frame (no p.frame() between input and read).
  p = boot('?rhythm=bembe&bpm=90&audio=none', IPHONE);
  p.frame(0);
  const seqR = ['AUTOPLAY: LIF FLY', 'AUTOPLAY: CONNECTOME FLY', 'AUTOPLAY: ASSIST \u00b7 LIF FLY', 'AUTOPLAY: ASSIST \u00b7 CONNECTOME FLY', 'AUTOPLAY: OFF'];
  const hudR = ['LIF autoplay ON', 'connectome autoplay ON', 'assist ON (LIF fly)', 'assist ON (connectome fly)', 'autoplay off'];
  let seqOk = true; const seen = [];
  for (let k = 0; k < 8; k++) {
    p.btn.tap();                                   // no frame: the rAF loop is "paused"
    const mline = p.huds['hud-r'].textContent.split('\n')[1];
    seen.push(p.btn.textContent);
    seqOk = seqOk && p.btn.textContent === seqR[k % 5] && mline === hudR[k % 5];
  }
  expect('R: label + HUD mode right after each of 8 taps (no frame in between)', seqOk, seen.join(' / '));
  p.press('c', 'KeyC');
  expect('R: key C updates label + HUD immediately', p.btn.textContent === seqR[3] && p.huds['hud-r'].textContent.split('\n')[1] === hudR[3], p.btn.textContent);
  p.press(' ');
  expect('R: Space: label LOCKED with the same mode the HUD shows', p.btn.textContent === 'LOCKED: ASSIST \u00b7 CONNECTOME FLY'
    && p.huds['hud-r'].textContent.split('\n')[1] === 'assist ON (connectome fly)' && p.rhythmBtn.className === 'picker locked', p.btn.textContent);
  p.btn.tap();
  expect('R: mid-song tap -> hint shown at once', p.huds['hud-c'].textContent.includes('Autoplay locked during song - press R to restart'));
  // blocks cut == hits on the press itself (bembe @90: first notes D at 2000 and F at 2444 ms, spread over the lanes; frame clock from stamp 0)
  p = boot('?rhythm=bembe&bpm=90&audio=none', IPHONE);
  p.frame(0); p.press(' ');
  const first2 = [2000, 2000 + Math.round(2 * 240000 / 90 / 12)];
  p.frame(first2[0]); p.press('d', 'KeyD');
  const hl1 = p.huds['hud-l'].textContent;
  p.frame(first2[1]); p.press('f', 'KeyF');
  const hl2 = p.huds['hud-l'].textContent;
  expect('R: blocks cut moves with combo on the press (1/1 then 2/2)', /Combo 1 /.test(hl1) && /blocks cut 1/.test(hl1) && /Combo 2 /.test(hl2) && /blocks cut 2/.test(hl2), JSON.stringify([hl1, hl2]));

  // S: moves list, window.__rhythmDebug, ?debug=notes (console + on-stage list). Connectome fly on bembe @90.
  p = boot('?rhythm=bembe&bpm=90&audio=none&debug=notes', Object.assign({ captureLog: true }, IPHONE));
  p.frame(0);
  const dbg = p.sb.__rhythmDebug;
  expect('S: window.__rhythmDebug installed (frozen, read-only)', !!dbg && dbg.version === 'rhythm-moves/1' && Object.isFrozen(dbg)
    && typeof dbg.moves === 'function' && typeof dbg.first20 === 'function' && typeof dbg.verify === 'function', dbg && dbg.version);
  try { p.sb.__rhythmDebug = null; } catch (e) { /* strict-mode TypeError is fine too */ }
  expect('S: __rhythmDebug cannot be overwritten', p.sb.__rhythmDebug === dbg);
  expect('S: ?debug=notes shows the on-stage list', p.huds['moves-list'].style.display === '' && p.huds['moves-list'].textContent.startsWith('  #'));
  p.press('c', 'KeyC'); p.press('c', 'KeyC');
  expect('S: mode() follows the AUTOPLAY cycle', dbg.mode() === 'connectome', dbg.mode());
  p.press(' ');
  st = 0; done = false;
  for (let i = 0; i < 4000 && !done; i++) { st += 16; p.frame(st); done = p.has('Song complete'); }
  const mv = dbg.moves(), f20 = dbg.first20();
  expect('S: 56 rows (bembe 7 x 8 bars), first20 = rows 0..19', done && dbg.count() === 56 && mv.length === 56 && f20.length === 20 && f20[19].i === 19 && mv[55].i === 55, dbg.count());
  expect('S: every row: fly, PERFECT, fired, margin >= 0, value = margin * f(chain)', mv.every((r) => r.who === 'fly' && r.judge === 'PERFECT' && r.fired === true
    && r.kind === 'margin' && r.margin >= 0 && Math.abs(r.value - Math.round(r.margin * 1000 * (10 + Math.min(r.chain, 10)) / 10) / 1000) < 1e-9), JSON.stringify(mv[0]));
  expect('S: single pattern spread: lanes D F J K D ... (pulse mod 4)', mv.every((r, k) => r.lane === k % 4) && mv[1].key === 'F', mv.slice(0, 5).map((r) => r.key).join(''));
  expect('S: chain counts consecutive hits per lane (row 8 is the 3rd D)', mv[0].chain === 1 && mv[4].chain === 2 && mv[8].chain === 3, [mv[0].chain, mv[4].chain, mv[8].chain].join(','));
  expect('S: row 0: genesis prev, delta null, math_origin derived', mv[0].prev === '0'.repeat(64) && mv[0].delta === null && mv[1].delta === mv[1].t - mv[0].t
    && mv[0].math_origin === 'math_origin=Decision(t=2000;lane=0;who=fly;V=' + mv[0].V.toFixed(3) + ';th=-45.000;margin=' + mv[0].margin.toFixed(3) + ';chain=1;f=1.100;value=' + mv[0].value.toFixed(3) + ')', mv[0].math_origin);
  const pre0 = 'rhythm-move/v1|prev=' + mv[0].prev + '|i=0|t=2000|lane=0|delta=na|who=fly|press=' + mv[0].press + '|dt=' + mv[0].dt + '|judge=PERFECT|fired=yes|lat=' + mv[0].lat + '|' + mv[0].math_origin;
  expect('S: row hash = SHA-256(canonical preimage) (node crypto agrees)', require('crypto').createHash('sha256').update(pre0).digest('hex') === mv[0].hash && dbg.sha256(pre0) === mv[0].hash, mv[0].hash.slice(0, 8));
  const vk = dbg.verify();
  expect('S: verify() ok over the kept rows', vk.ok === true && vk.firstBad === null && vk.checked === 56, JSON.stringify(vk));
  const tam = dbg.moves(); tam[5].judge = 'MISS';
  const vt = dbg.verify(tam);
  expect('S: verify(rows) finds a tampered row (judge of row 5)', vt.ok === false && vt.firstBad === 5, JSON.stringify(vt));
  const tam2 = dbg.moves(); tam2[9].hash = tam2[9].hash.replace(/^./, (c) => (c === '0' ? '1' : '0'));
  expect('S: verify(rows) finds a broken link (hash of row 9)', dbg.verify(tam2).firstBad === 9, JSON.stringify(dbg.verify(tam2)));
  expect('S: copies only: tampering did not touch the game', dbg.verify().ok && dbg.moves()[5].judge === 'PERFECT');
  const logs = p.logs.filter((l) => l.startsWith('[moves] '));
  expect('S: ?debug=notes console.logs every row once, in order', logs.length === 56 && logs[0].startsWith('[moves] #0 t=2000 D delta=na fly press=2000 dt=0 PERFECT V=') && logs[55].startsWith('[moves] #55 '), logs[0]);
  const stageRows = p.huds['moves-list'].textContent.split('\n');
  expect('S: on-stage list = header + last 8 rows, each <= 52 chars (390 px stage at 9 px)', stageRows.length === 9 && stageRows.every((r) => r.length <= 52) && stageRows[8].trim().startsWith('55 '), stageRows[8] + ' (' + Math.max(...stageRows.map((r) => r.length)) + ')');
  // without ?debug=notes: the API is there, nothing logged, list hidden
  p = boot('?rhythm=bembe&bpm=90&audio=none', Object.assign({ captureLog: true }, IPHONE));
  p.frame(0); p.press(' ');
  for (let t2 = 16; t2 < 6000; t2 += 16) p.frame(t2);
  expect('S: no ?debug: API present, list hidden, no console rows; human-off rows are timing rows (MISS -> chain 0, score 0)', !!p.sb.__rhythmDebug && p.huds['moves-list'].style.display === 'none'
    && p.logs.filter((l) => l.startsWith('[moves]')).length === 0 && p.sb.__rhythmDebug.moves().length > 0
    && p.sb.__rhythmDebug.moves().every((r) => r.who === 'none' && r.judge === 'MISS' && r.kind === 'timing' && r.d === 0 && r.chain === 0 && r.fired === null && r.V === null), p.sb.__rhythmDebug.moves().length);

  // T: pause when the tab is hidden, resume without rewinding.
  p = boot('?rhythm=bembe&bpm=90', IPHONE);
  p.frame(0); p.press(' ');
  let aT = p.audios[p.audios.length - 1];
  const playsBefore = aT.plays;
  st = 0;
  for (let i = 0; i < 100; i++) { st += 16; aT.currentTime += 0.016; p.frame(st); }
  const songBefore = p.sb.__rhythmDebug.clock();
  p.hide(true);
  expect('T: hidden mid-song -> audio paused, HUD "paused (tab hidden)"', aT.paused === true && p.huds['hud-c'].textContent.includes('paused (tab hidden)'), p.huds['hud-c'].textContent.split('\n')[0]);
  for (let i = 0; i < 20; i++) { st += 500; p.frame(st); }           // throttled frames while hidden: song time must not move
  expect('T: song clock frozen while hidden', p.sb.__rhythmDebug.clock() === songBefore, songBefore + ' -> ' + p.sb.__rhythmDebug.clock());
  const ctAtHide = aT.currentTime;
  p.hide(false);
  expect('T: visible -> audio.play() again, NOT rewound to 0', aT.plays === playsBefore + 1 && aT.paused === false && aT.currentTime === ctAtHide, aT.currentTime);
  st += 16; aT.currentTime += 0.016; p.frame(st);
  const songAfter = p.sb.__rhythmDebug.clock();
  expect('T: continues from the frozen time (no 10 s jump), notes not missed while hidden', songAfter >= songBefore && songAfter - songBefore < 40
    && p.hud('Miss ') === 'Miss 0' && !p.huds['hud-c'].textContent.includes('paused'), (songAfter - songBefore).toFixed(1) + ' ms');
  // frame-clock fallback (no audio): re-anchored on resume
  p = boot('?rhythm=bembe&bpm=90&audio=none', IPHONE);
  p.frame(0); p.press('c', 'KeyC'); p.press(' ');
  for (st = 16; st <= 3000; st += 16) p.frame(st);
  const fb0 = p.sb.__rhythmDebug.clock();
  p.hide(true); p.frame(st + 9000); p.hide(false); p.frame(st + 9016);
  const fb1 = p.sb.__rhythmDebug.clock();
  expect('T: no-audio clock re-anchored: 9 s hidden adds nothing', fb1 >= fb0 && fb1 - fb0 <= 16, fb0 + ' -> ' + fb1);
  for (st = st + 9032; st < 40000; st += 16) p.frame(st);
  expect('T: LIF fly still plays the whole song after the pause (no miss)', p.has('Song complete') && / M 0$/.test(p.texts.find((t) => t.startsWith('P ')) || ''), p.texts.find((t) => t.startsWith('P ')));

  // U: jitter. 60 fps frames, audio.currentTime updated only every 40 ms (Safari-like coarse steps).
  function jitter(search) {
    const q = boot(search, IPHONE);
    q.frame(0); q.press(' ');
    const a = q.audios[q.audios.length - 1];
    const d = []; let prev = null; let mono = true;
    for (let i = 1; i <= 300; i++) {
      const stamp = i * (1000 / 60);
      a.currentTime = Math.floor(stamp / 40) * 0.040;   // true time = stamp, reported in 40 ms steps
      q.frame(stamp);
      const c = q.sb.__rhythmDebug.clock();
      if (prev !== null && i > 30) { d.push(c - prev); if (c < prev) mono = false; }
      prev = c;
    }
    const mean = d.reduce((x, y) => x + y, 0) / d.length;
    const sd = Math.sqrt(d.reduce((x, y) => x + (y - mean) * (y - mean), 0) / d.length);
    return { mean, sd, max: Math.max(...d), min: Math.min(...d), mono, end: prev };
  }
  const jr = jitter('?rhythm=bembe&bpm=90&clock=raw'), js = jitter('?rhythm=bembe&bpm=90');
  const fmtJ = (j) => 'mean ' + j.mean.toFixed(2) + ' sd ' + j.sd.toFixed(2) + ' min ' + j.min.toFixed(1) + ' max ' + j.max.toFixed(1);
  console.log('JITTER raw  (?clock=raw) per-frame song-time delta: ' + fmtJ(jr));
  console.log('JITTER smooth (default)  per-frame song-time delta: ' + fmtJ(js));
  expect('U: raw clock under 40 ms audio steps is jittery (sd > 10 ms, 0 ms frames)', jr.sd > 10 && jr.min === 0, fmtJ(jr));
  expect('U: smoothed clock: monotonic, sd < 1 ms, every step 0.9x..1.1x of 16.7 ms', js.mono && js.sd < 1 && js.min >= 15 && js.max <= 18.4, fmtJ(js));
  expect('U: smoothed clock stays on the audio (within 25 ms of true time at 5 s)', Math.abs(js.end - 300 * 1000 / 60) < 25, (js.end - 5000).toFixed(1));

  console.log(fail === 0 ? 'SMOKE OK' : 'SMOKE FAILED (' + fail + ')');
  process.exit(fail === 0 ? 0 : 1);
})().catch((e) => { console.log('FAIL exception ' + (e && e.stack || e)); process.exit(1); });
