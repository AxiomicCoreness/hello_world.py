// End-to-end check of the CLI /llm chat in real headless Chrome (CDP). Needs, all on loopback:
//   llama-server -m <any.gguf> --host 127.0.0.1 --port 8081
//   (cd sovereign-irc-bridge && python -m src.cli_loopback)       # ws://127.0.0.1:6669/cli
//   python3 -m http.server 8092 --bind 127.0.0.1 -d target/webapp
// Usage: node tools/llm_chat_e2e.mjs http://127.0.0.1:8092/ [cdpPort]
// Plays bembe with the LIF autoplayer, triggers one real /py traceback, sends /llm and waits for
// the model's reply in #chat-history. Exits 0 only if the reply arrived with a snapshot attached.
import { spawn } from 'node:child_process';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const base = process.argv[2] || 'http://127.0.0.1:8092/';
const port = +(process.argv[3] || 9348);
const profile = mkdtempSync(join(tmpdir(), 'rhythm-llm-'));
const chrome = spawn(process.env.CHROME || 'google-chrome', ['--headless=new', '--no-sandbox', '--disable-gpu',
  `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`, '--no-first-run',
  '--autoplay-policy=no-user-gesture-required',
  // Chrome blocks 6665-6669 (IRC) as unsafe ports; the loopback CLI contract is :6669.
  '--explicitly-allowed-ports=6669', 'about:blank'], { stdio: 'ignore' });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fail = 0;
const expect = (name, cond, got) => { console.log((cond ? 'PASS ' : 'FAIL ') + name + (got !== undefined ? '  [' + got + ']' : '')); if (!cond) fail++; };

try {
  for (let i = 0; i < 50; i++) { try { await (await fetch(`http://127.0.0.1:${port}/json/version`)).json(); break; } catch { await sleep(200); } }
  const t = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, { method: 'PUT' })).json();
  const ws = new WebSocket(t.webSocketDebuggerUrl);
  await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
  let id = 0; const pend = new Map();
  ws.onmessage = (e) => { const m = JSON.parse(e.data); if (m.id && pend.has(m.id)) { pend.get(m.id)(m.result || { error: m.error }); pend.delete(m.id); } };
  const send = (method, params = {}) => new Promise((r) => { const i = ++id; pend.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
  const ev = async (x) => { const r = await send('Runtime.evaluate', { expression: x, returnByValue: true, awaitPromise: true }); return r.result ? r.result.value : r; };
  const key = async (k, code, kc) => { for (const ty of ['keyDown', 'keyUp']) await send('Input.dispatchKeyEvent', { type: ty, key: k, code, windowsVirtualKeyCode: kc, text: ty === 'keyDown' && k.length === 1 ? k : undefined }); };
  const hist = () => ev('document.getElementById("chat-history").textContent');
  const say = (s) => ev(`(() => { const i = document.getElementById('chat-input'); i.value = ${JSON.stringify(s)};
    document.getElementById('cli-form').dispatchEvent(new Event('submit', { cancelable: true })); return true; })()`);
  await send('Page.enable'); await send('Runtime.enable');
  await send('Page.navigate', { url: base + '?rhythm=bembe&bpm=90' });
  for (let i = 0; i < 50; i++) { if (await ev('!!(window.__rhythmDebug && /connected ws:/.test(document.getElementById("chat-history").textContent))')) break; await sleep(200); }
  expect('chat connected to loopback bridge', /connected ws:\/\/127\.0\.0\.1:6669\/cli/.test(await hist()));
  await ev('document.activeElement && document.activeElement.blur()');
  await key('b', 'KeyB', 66);
  expect('LIF autoplayer on', (await ev('window.__rhythmDebug.mode()')) === 'lif');
  await key(' ', 'Space', 32);
  await sleep(6000);
  await say('/py call no_such_capability_zz');
  for (let i = 0; i < 50 && !/\[Traceback\]/.test(await hist()); i++) await sleep(200);
  expect('real /py traceback in history', /\[Traceback\]/.test(await hist()));
  await say('/llm What are the lanes doing, and how do I fix the last error?');
  let h = '';
  const after = (x) => x.slice(Math.max(0, x.lastIndexOf('[User] /llm ')));
  for (let i = 0; i < 600; i++) { h = after(await hist()); if (/\[Engine\] llm: |\[System\] llm offline/.test(h)) break; await sleep(200); }
  await sleep(300);
  h = after(await hist());
  const tail = h.split('\n');
  for (const l of tail) console.log('CHAT ' + l);
  expect('snapshot attached (with neuron snapshot, >=1 traceback report)', /llm → bridge \(with neuron snapshot, [1-9]\d* traceback report/.test(h));
  expect('bridge saw live LIF spikes', /llm ctx: brain=lif mode=lif window=2000ms spikes\[/.test(h));
  expect('model reply shown in chatbox', /\[Engine\] llm: /.test(h));
  ws.close();
} finally {
  chrome.kill();
  await sleep(300);
  try { rmSync(profile, { recursive: true, force: true }); } catch {}
}
console.log(fail ? `LLM E2E FAIL (${fail})` : 'LLM E2E OK');
process.exit(fail ? 1 : 0);
