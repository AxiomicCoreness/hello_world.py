/*
 * DOM tests for the BMS DISPLAY MOCK, run with node + jsdom.
 * Usage: node evals/bms_dom_test.js  (NODE_PATH may point at a node_modules that has jsdom)
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
var SRC = fs.readFileSync(path.join(ROOT, 'bms_scripts', 'bms_display_mock.js'), 'utf8');
var URL_TXT = fs.readFileSync(path.join(ROOT, 'assets', 'bookmarklet.txt'), 'utf8').trim();
var MIN = decodeURIComponent(URL_TXT.slice('javascript:'.length));
var HTML = fs.readFileSync(path.join(ROOT, 'assets', 'demo.html'), 'utf8');

var passed = 0;
var failed = 0;
function check(name, cond, extra) {
  if (cond) { passed++; console.log('PASS ' + name); }
  else { failed++; console.log('FAIL ' + name + (extra ? ' :: ' + extra : '')); }
}

function page(opts) {
  opts = opts || {};
  var dom = new JSDOM(HTML, { runScripts: 'outside-only' });
  var w = dom.window;
  var answers = (opts.answers || ['4.2', '0.5', '25.0', '95']).slice();
  w.prompts = [];
  w.alerts = [];
  w.prompt = function (msg, def) { w.prompts.push([msg, def]); return answers.length ? answers.shift() : def; };
  w.confirm = function () { return opts.confirm === undefined ? false : opts.confirm; };
  w.alert = function (m) { w.alerts.push(m); };
  if (opts.config) { w.BMS_MOCK_CONFIG = opts.config; }
  return w;
}
function txt(w, sel) { return w.document.querySelector(sel).textContent; }
function html(w, sel) { return w.document.querySelector(sel).innerHTML; }

['minified bookmarklet', 'readable source'].forEach(function (label, idx) {
  var code = idx === 0 ? MIN : SRC;
  var w = page({ config: { hideChrome: false } });
  var before = w.document.body.innerHTML;
  w.eval(code);
  var p = label + ': ';
  check(p + 'data-bms voltage set', txt(w, '[data-bms="voltage"]') === '4.2');
  check(p + '#bms-voltage set', txt(w, '#bms-voltage') === '4.2');
  check(p + '.bms-current set', txt(w, '.bms-current') === '0.5');
  check(p + 'temp set', txt(w, '[data-bms="temp"]') === '25.0');
  check(p + 'soc gets % suffix', txt(w, '#bms-soc') === '95%' && txt(w, '.bms-soc') === '95%');
  check(p + 'decoys untouched', txt(w, '#decoy-template') === 'template text' &&
    txt(w, '#decoy-current') === 'page 2 of 5' && txt(w, '#decoy-temperature') === 'outdoor 12 \u00B0C' &&
    txt(w, '#voltage-help') === 'voltage help text' && txt(w, '#decoy-soc') === 'associate');
  var banner = w.document.getElementById('bms-display-mock-banner');
  check(p + 'banner visible and labelled', !!banner && banner.textContent.indexOf('DISPLAY MOCK') === 0 &&
    banner.textContent.indexOf('No battery was read') > 0 && w.getComputedStyle(banner).display !== 'none');
  check(p + 'alert labelled', w.alerts.length === 1 && w.alerts[0].indexOf('DISPLAY MOCK (demo/screenshot only)') > 0 &&
    w.alerts[0].indexOf('Do not present these as real readings') > 0);
  check(p + 'prompts labelled with defaults', w.prompts.length === 4 && w.prompts[0][1] === '4.2' &&
    w.prompts[2][1] === '25.0' && w.prompts[3][1] === '95' && w.prompts[0][0].indexOf('DISPLAY MOCK') === 0);
  var style = w.document.getElementById('bms-display-mock-style');
  check(p + 'no hide CSS when hideChrome=false', !!style && style.textContent.indexOf('display:none') < 0 &&
    w.getComputedStyle(w.document.getElementById('site-header')).display !== 'none');
  check(p + 'changed elements marked', w.document.querySelectorAll('[data-bms-mock="1"]').length === 6);
  w.confirm = function () { return true; };
  w.eval(code);
  check(p + 'second run reverts body exactly', w.document.body.innerHTML === before,
    w.document.body.innerHTML.length + ' vs ' + before.length);
  check(p + 'revert restores child nodes', html(w, '[data-bms="voltage"]') === '3.<b>9</b>8');
  check(p + 'revert restores title', w.document.querySelector('.bms-soc').getAttribute('title') === 'original title' &&
    !w.document.getElementById('bms-voltage').hasAttribute('title'));
  check(p + 'style and banner removed', !w.document.getElementById('bms-display-mock-style') &&
    !w.document.getElementById('bms-display-mock-banner'));
  check(p + 'state inactive', w.__bmsDisplayMock.active === false);
});

(function () {
  var w = page({ answers: [null, '0.7', null, null], config: { hideChrome: false } });
  w.eval(MIN);
  check('cancel per field: voltage unchanged', txt(w, '#bms-voltage') === '3.97');
  check('cancel per field: current applied', txt(w, '.bms-current') === '0.7');
  check('cancel per field: soc unchanged', txt(w, '#bms-soc') === '62%');
  check('cancel reported in alert', w.alerts[0].indexOf('Voltage (V): unchanged (cancelled)') >= 0);
})();

(function () {
  var w = page({ answers: ['abc', 'NaN', '150', ''], config: { hideChrome: false } });
  w.eval(MIN);
  check('invalid: nothing changed', txt(w, '#bms-voltage') === '3.97' && txt(w, '.bms-current') === '1.20' &&
    txt(w, '[data-bms="temp"]') === '31.5' && txt(w, '#bms-soc') === '62%');
  check('invalid: four errors recorded', w.__bmsDisplayMock.errors.length === 4, JSON.stringify(w.__bmsDisplayMock.errors));
  check('invalid: alert lists rejections', w.alerts[0].indexOf('Rejected:') > 0 && w.alerts[0].indexOf('Temp (\u00B0C): 150 outside -40..125') > 0 && w.alerts[0].indexOf('State of Charge (%): empty') > 0);
})();

(function () {
  var w = page({ answers: ['Infinity', '-1000', '-41', '100'], config: { hideChrome: false } });
  w.eval(MIN);
  check('range: Infinity rejected', txt(w, '#bms-voltage') === '3.97');
  check('range: -1000 A accepted at bound', txt(w, '.bms-current') === '-1000');
  check('range: -41 C rejected', txt(w, '[data-bms="temp"]') === '31.5');
  check('range: 100% accepted', txt(w, '#bms-soc') === '100%');
})();

(function () {
  var w = page({ config: { hideChrome: true } });
  w.eval(MIN);
  var d = w.document;
  check('hideChrome: header/nav/aside/toast hidden', ['site-header', 'site-nav', 'side', 'toast', 'site-footer'].every(function (id) {
    return w.getComputedStyle(d.getElementById(id)).display === 'none';
  }));
  check('hideChrome: banner still visible', w.getComputedStyle(d.getElementById('bms-display-mock-banner')).display !== 'none');
  check('hideChrome: betting panel NOT hidden by default', w.getComputedStyle(d.getElementById('leaderboard')).display !== 'none');
})();

(function () {
  var w = page({ config: { hideChrome: false, hideBettingChrome: true } });
  w.eval(MIN);
  check('hideBettingChrome: leaderboard hidden', w.getComputedStyle(w.document.getElementById('leaderboard')).display === 'none');
})();

(function () {
  var w = page({ confirm: true });
  w.eval(MIN);
  check('hideChrome unset: confirm() asked and honoured', w.getComputedStyle(w.document.getElementById('site-header')).display === 'none');
})();

(function () {
  var w = page({ config: { hideChrome: false, selectors: { voltage: '#voltage-help', soc: '   ' } } });
  w.eval(MIN);
  check('custom selector map: voltage remapped', txt(w, '#voltage-help') === '4.2' && txt(w, '#bms-voltage') === '3.97');
  check('custom selector map: blank entry falls back to default', txt(w, '#bms-soc') === '95%');
})();

(function () {
  var w = page({ config: { hideChrome: false, selectors: { voltage: '[[bad' } } });
  w.eval(MIN);
  check('bad custom selector reported, rest applied', w.__bmsDisplayMock.errors.join(' ').indexOf('bad selector') >= 0 &&
    txt(w, '.bms-current') === '0.5');
})();

(function () {
  var api = require(path.join(ROOT, 'bms_scripts', 'bms_display_mock.js'));
  var f = api.FIELDS[3];
  check('module export: parseValue ok', api.parseValue(' 42 ', f).ok && api.parseValue(' 42 ', f).text === '42');
  check('module export: parseValue cancel', api.parseValue(null, f).cancelled === true);
  check('module export: hex, exponent, 1.2.3 and lone sign rejected', ['0x10', '1e2', '1.2.3', '-', '.'].every(function (v) {
    return !api.parseValue(v, f).ok;
  }));
  check('module export: 4.20 / +3 / -0.5 / .5 accepted as typed', api.parseValue('4.20', api.FIELDS[0]).text === '4.20' &&
    api.parseValue('+3', api.FIELDS[1]).ok && api.parseValue('-0.5', api.FIELDS[1]).ok && api.parseValue('.5', f).ok);
  check('module export: no substring selectors', Object.keys(api.DEFAULT_SELECTORS).every(function (k) {
    return api.DEFAULT_SELECTORS[k].indexOf('*=') < 0;
  }));
})();

console.log(passed + ' passed, ' + failed + ' failed');
process.exit(failed ? 1 : 0);
