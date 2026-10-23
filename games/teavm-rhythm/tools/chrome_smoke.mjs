// Real headless Chrome check of a served build (CDP over WebSocket; node >= 20 with
// --experimental-websocket, or >= 22). Usage:
//   node --experimental-websocket tools/chrome_smoke.mjs http://127.0.0.1:8092/ [port]
// Checks window.__rhythmDebug and ?debug=notes (connectome fly, bembe @90), the pause on a
// hidden tab, and the per-frame clock jitter with audio.currentTime quantised to 40 ms
// (Safari-like), ?clock=raw vs the default smoothed clock. Prints PASS/FAIL lines,
// the first 10 moves rows, and exits 0 only if everything passed.
import { spawn } from 'node:child_process';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const base = process.argv[2] || 'http://127.0.0.1:8092/';
const port = +(process.argv[3] || 9347);
const profile = mkdtempSync(join(tmpdir(), 'rhythm-chrome-'));
const chrome = spawn('google-chrome', ['--headless=new', '--no-sandbox', '--disable-gpu', `--remote-debugging-port=${port}`,
  `--user-data-dir=${profile}`, '--no-first-run', '--autoplay-policy=no-user-gesture-required', 'about:blank'], { stdio: 'ignore' });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fail = 0;
const expect = (name, cond, got) => { console.log((cond ? 'PASS ' : 'FAIL ') + name + (got !== undefined ? '  [' + got + ']' : '')); if (!cond) fail++; };

async function connect(wsUrl) {
  const ws = new WebSocket(wsUrl);
  await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
  let id = 0; const pend = new Map(); const events = [];
  ws.onmessage = (e) => { const m = JSON.parse(e.data); if (m.id && pend.has(m.id)) { pend.get(m.id)(m.result || { error: m.error }); pend.delete(m.id); } else if (m.method) events.push(m); };
  const send = (method, params = {}) => new Promise((r) => { const i = ++id; pend.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
  const ev = async (x) => { const r = await send('Runtime.evaluate', { expression: x, returnByValue: true, awaitPromise: true }); return r.result ? r.result.value : r; };
  const key = async (k, code, kc) => { for (const t of ['keyDown', 'keyUp']) await send('Input.dispatchKeyEvent', { type: t, key: k, code, windowsVirtualKeyCode: kc, text: t === 'keyDown' && k.length === 1 ? k : undefined }); };
  return { ws, send, ev, key, events };
}

async function page(url, init) {
  const t = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, { method: 'PUT' })).json();
  const p = await connect(t.webSocketDebuggerUrl);
  p.targetId = t.id;
  await p.send('Page.enable'); await p.send('Runtime.enable');
  await p.send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 3, mobile: true });
  if (init) await p.send('Page.addScriptToEvaluateOnNewDocument', { source: init });
  await p.send('Page.navigate', { url });
  for (let i = 0; i < 50; i++) { if (await p.ev('!!(window.__rhythmDebug && document.getElementById("hud-l").textContent)')) break; await sleep(200); }
  return p;
}

try {
  let ver;
  for (let i = 0; i < 50 && !ver; i++) { try { ver = await (await fetch(`http://127.0.0.1:${port}/json/version`)).json(); } catch { await sleep(200); } }

  // 1: ?debug=notes, connectome fly, bembe @90 (real audio clock)
  let p = await page(base + '?rhythm=bembe&bpm=90&debug=notes');
  const api = await p.ev(`(() => { const d = window.__rhythmDebug; if (!d) return null; let w = false; try { window.__rhythmDebug = 1; } catch (e) {} w = window.__rhythmDebug === d;
    return { v: d.version, frozen: Object.isFrozen(d), kept: w, fns: ['moves','first20','count','mode','clock','verify','sha256'].every((k) => typeof d[k] === 'function') }; })()`);
  expect('chrome: window.__rhythmDebug present, frozen, not overwritable', api && api.v === 'rhythm-moves/1' && api.frozen && api.kept && api.fns, JSON.stringify(api));
  await p.key('c', 'KeyC', 67); await p.key('c', 'KeyC', 67);
  expect('chrome: mode() connectome after C C', (await p.ev('window.__rhythmDebug.mode()')) === 'connectome');
  await p.key(' ', 'Space', 32);
  await sleep(9000);
  const st = await p.ev(`(() => { const d = window.__rhythmDebug, m = d.moves(), t = m.map((r) => Object.assign({}, r)); t[3].dt = 99;
    const el = document.getElementById('moves-list'), r = el.getBoundingClientRect();
    return { n: d.count(), rows: m, v: d.verify(), vt: d.verify(t), shown: getComputedStyle(el).display !== 'none', right: r.right, w: el.scrollWidth, cw: el.clientWidth,
      lines: el.textContent.split('\\n'), clock: el.textContent && d.clock(), hud: document.getElementById('hud-l').textContent.replace(/\\n/g, ' | ') }; })()`);
  const rows = st.rows || [];
  expect('chrome: rows written as the song plays', st.n >= 10 && rows.length === Math.min(64, st.n), st.n + ' rows at song ' + Math.round(st.clock) + ' ms; ' + st.hud);
  expect('chrome: every row fly, PERFECT, fired, margin >= 0', rows.length > 0 && rows.every((r) => r.who === 'fly' && r.judge === 'PERFECT' && r.fired === true && r.margin >= 0));
  expect('chrome: bembe spread over D F J K (pulse mod 4)', rows.every((r, k) => r.lane === k % 4), rows.slice(0, 8).map((r) => r.key).join(''));
  expect('chrome: verify() ok; a tampered copy fails at its row', st.v.ok && st.vt.ok === false && st.vt.firstBad === 3, JSON.stringify([st.v, st.vt]));
  const logs = p.events.filter((e) => e.method === 'Runtime.consoleAPICalled').map((e) => e.params.args.map((a) => a.value).join(' ')).filter((s) => s.startsWith('[moves] '));
  expect('chrome: ?debug=notes console.log one line per row', logs.length === st.n && logs[0].startsWith('[moves] #0 t=2000 D'), logs.length + ' / ' + st.n);
  expect('chrome: on-stage list shown, header + 8 rows, inside the 390 px stage, no overflow', st.shown && st.lines.length === 9 && st.right <= 390 && st.w <= st.cw,
    'right ' + st.right.toFixed(1) + ' px, scroll ' + st.w + '/' + st.cw);
  console.log('FIRST10 i | t | key | delta | who | press | dt | judge | V | th | margin | fired | lat | chain | f | value | hash8');
  for (const r of rows.slice(0, 10)) console.log('FIRST10 ' + [r.i, r.t, r.key, r.delta, r.who, r.press, r.dt, r.judge, r.V.toFixed(3), r.th.toFixed(3), r.margin.toFixed(3), r.fired, r.lat, r.chain, r.f.toFixed(3), r.value.toFixed(3), r.hash.slice(0, 8)].join(' | '));
  p.ws.close();

  // 2: hidden tab pauses audio + clock; visible resumes without rewind
  p = await page(base + '?rhythm=bembe&bpm=90');
  await p.key('c', 'KeyC', 67); await p.key(' ', 'Space', 32);
  await sleep(3000);
  const s0 = await p.ev(`({ c: window.__rhythmDebug.clock(), vis: document.visibilityState })`);
  const other = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, { method: 'PUT' })).json();
  await fetch(`http://127.0.0.1:${port}/json/activate/${other.id}`);
  await sleep(3000);
  const s1 = await p.ev(`({ c: window.__rhythmDebug.clock(), vis: document.visibilityState, hud: document.getElementById('hud-c').textContent })`);
  expect('chrome: other tab in front -> hidden, "paused (tab hidden)", clock frozen', s1.vis === 'hidden' && s1.hud.includes('paused (tab hidden)') && s1.c - s0.c < 400,
    s1.vis + ' clock +' + Math.round(s1.c - s0.c) + ' ms in 3 s');
  await fetch(`http://127.0.0.1:${port}/json/activate/${p.targetId}`);
  await sleep(1500);
  const s2 = await p.ev(`({ c: window.__rhythmDebug.clock(), vis: document.visibilityState, hud: document.getElementById('hud-c').textContent, l: document.getElementById('hud-l').textContent })`);
  expect('chrome: visible again -> resumed from the frozen time (not rewound, hidden time not added), no miss', s2.vis === 'visible' && !s2.hud.includes('paused')
    && s2.c > s1.c && s2.c - s1.c < 2500 && /Miss 0/.test(s2.l), 'clock ' + Math.round(s1.c) + ' -> ' + Math.round(s2.c) + ' ms; ' + s2.l.replace(/\n/g, ' | '));
  p.ws.close();

  // 3: jitter with Safari-like 40 ms currentTime steps: raw vs smoothed
  const QUANT = `(() => { const d = Object.getOwnPropertyDescriptor(HTMLMediaElement.prototype, 'currentTime');
    Object.defineProperty(HTMLMediaElement.prototype, 'currentTime', { configurable: true, get() { return Math.floor(d.get.call(this) / 0.04) * 0.04; }, set(v) { d.set.call(this, v); } }); })();`;
  const measure = async (q) => {
    const pg = await page(base + q, QUANT);
    await pg.key('c', 'KeyC', 67); await pg.key(' ', 'Space', 32);
    await sleep(1500);
    const r = await pg.ev(`new Promise((done) => { const d = []; let prev = null, n = 0;
      function f() { const c = window.__rhythmDebug.clock(); if (prev !== null) d.push(c - prev); prev = c; if (++n < 240) requestAnimationFrame(f); else done(d); }
      requestAnimationFrame(f); })`);
    pg.ws.close();
    const mean = r.reduce((a, b) => a + b, 0) / r.length;
    const sd = Math.sqrt(r.reduce((a, b) => a + (b - mean) ** 2, 0) / r.length);
    return { mean, sd, min: Math.min(...r), max: Math.max(...r), mono: r.every((x) => x >= 0), n: r.length };
  };
  const raw = await measure('?rhythm=bembe&bpm=90&clock=raw');
  const smooth = await measure('?rhythm=bembe&bpm=90');
  const f = (j) => `mean ${j.mean.toFixed(2)} sd ${j.sd.toFixed(2)} min ${j.min.toFixed(1)} max ${j.max.toFixed(1)} (${j.n} frames)`;
  console.log('CHROME-JITTER raw    ' + f(raw));
  console.log('CHROME-JITTER smooth ' + f(smooth));
  expect('chrome: smoothed clock monotonic and much steadier than raw under 40 ms steps', smooth.mono && smooth.sd < raw.sd / 3, f(raw) + ' vs ' + f(smooth));
} catch (e) {
  expect('chrome smoke ran', false, e && e.stack || e);
} finally {
  chrome.kill('SIGKILL');
  await sleep(300);
  try { rmSync(profile, { recursive: true, force: true }); } catch {}
}
console.log(fail === 0 ? 'CHROME SMOKE OK' : 'CHROME SMOKE FAILED (' + fail + ')');
process.exit(fail === 0 ? 0 : 1);
