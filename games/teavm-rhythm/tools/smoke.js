// Headless smoke test for the TeaVM output: stubs just enough DOM (canvas 2D
// context, keydown listener, requestAnimationFrame, location.search) to boot
// classes.js under Node, play the first notes of seed 2026 and read the HUD,
// then let the LIF autoplayer (key B) play the whole song. Part 2 boots fresh
// copies with ?chart=charts/sample_chart.json and a stub <audio> element to
// check the JSON chart loader, the audio clock and the frame-clock fallback.
// Part 3 boots with the HTML HUD overlay, an iPhone 12 viewport (390x844 at
// devicePixelRatio 3) and an Image stub, then checks the stage layers, the
// connectome autoplayer (key C), assist mode and ?camera / ?connectome.
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
expect('notes drawn', rects > 10, rects);
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
  if (opts.hud) { for (const id of ['hud-l', 'hud-r', 'hud-c']) huds[id] = { id, textContent: '' }; }
  b.huds = huds;
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
    addEventListener: (type, fn) => { if (type === 'keydown') b.key = fn; },
    createElement: (tag) => (tag === 'audio' ? makeAudio() : {}),
  };
  const sb = { console, document: doc, location: { search }, XMLHttpRequest: FakeXHR,
    requestAnimationFrame: (cb) => { b.raf = cb; return 1; }, setTimeout, clearTimeout };
  if (opts.vw) { sb.innerWidth = opts.vw; sb.innerHeight = opts.vh; sb.devicePixelRatio = opts.dpr || 1; }
  if (opts.image) { sb.Image = class { constructor() { this.src = ''; this.naturalWidth = 0; this.naturalHeight = 0; b.images.push(this); } }; }
  if (opts.navigator) sb.navigator = opts.navigator;
  b.cv = cv;
  b.doc = doc;
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
  for (let i = 0; i < 5000 && !done; i++) { st += 16; p.frame(st); done = p.has('Song complete'); }
  expect('connectome: seed 2026 finished', done);
  expect('connectome: 64/64 PERFECT = 58800', p.hud('Score ') === 'Score 58800' && p.has('P 64  Gr 0  Go 0  M 0'), p.hud('Score '));
  expect('connectome: spikes 192 (in+inter+out) and 64 key presses', p.hud('spikes ') === 'spikes 192 \u00b7 keys 64', p.hud('spikes '));
  expect('stage: sabers cut phantom blocks during the song (HUD)', /^blocks cut [1-9]\d*$/.test(p.hud('blocks cut ') || ''), p.hud('blocks cut '));
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

  console.log(fail === 0 ? 'SMOKE OK' : 'SMOKE FAILED (' + fail + ')');
  process.exit(fail === 0 ? 0 : 1);
})().catch((e) => { console.log('FAIL exception ' + (e && e.stack || e)); process.exit(1); });
