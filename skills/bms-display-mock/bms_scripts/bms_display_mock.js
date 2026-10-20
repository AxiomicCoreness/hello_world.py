/*
 * BMS DISPLAY MOCK v1.0.0 -- FOR DEMOS AND SCREENSHOTS ONLY.
 *
 * What it does: rewrites the text of BMS-style readout elements on the page you
 * are looking at (voltage, current, temperature, state of charge) with numbers
 * you type in, and shows a "DISPLAY MOCK" banner on the page.
 *
 * What it does NOT do: it reads no battery, talks to no BMS, sends nothing and
 * changes no real data anywhere. Everything happens in this tab's local DOM and
 * disappears on reload or on revert.
 *
 * Do not use it to represent real readings to anyone. Screenshots made with it
 * must be labelled as mock-ups (the on-page banner is there for that reason).
 *
 * Run it once to apply; run it again (or call window.__bmsDisplayMock.revert())
 * to restore the original text and remove the injected style and banner.
 *
 * Optional config, set before running:
 *   window.BMS_MOCK_CONFIG = {
 *     selectors: { voltage: '#my-volts' },   merged over DEFAULT_SELECTORS
 *     hideChrome: true | false,              skip the confirm() question
 *     hideBettingChrome: true                also hide betting-site panels
 *   };
 *
 * Source rules (the Python builder relies on them): every statement ends with a
 * semicolon, no regex literals, no template literals, comments only in block
 * form or on their own line.
 */
(function () {
  'use strict';

  var VERSION = '1.0.0';
  var STATE_KEY = '__bmsDisplayMock';
  var STYLE_ID = 'bms-display-mock-style';
  var BANNER_ID = 'bms-display-mock-banner';
  var MOCK_LABEL = 'DISPLAY MOCK';
  var DISCLAIMER = 'Values typed in by hand for a demo/screenshot. ' +
    'No battery was read and no real data was changed. ' +
    'Do not present these as real readings.';

  /* Explicit hooks only: a data attribute, an id or a class per field. */
  var DEFAULT_SELECTORS = {
    voltage: '[data-bms="voltage"], #bms-voltage, .bms-voltage',
    current: '[data-bms="current"], #bms-current, .bms-current',
    temp: '[data-bms="temp"], #bms-temp, .bms-temp',
    soc: '[data-bms="soc"], #bms-soc, .bms-soc'
  };

  var FIELDS = [
    { key: 'voltage', label: 'Voltage (V)', def: '4.2', min: 0, max: 1000, unit: 'V', suffix: '' },
    { key: 'current', label: 'Current (A)', def: '0.5', min: -1000, max: 1000, unit: 'A', suffix: '' },
    { key: 'temp', label: 'Temp (\u00B0C)', def: '25.0', min: -40, max: 125, unit: '\u00B0C', suffix: '' },
    { key: 'soc', label: 'State of Charge (%)', def: '95', min: 0, max: 100, unit: '%', suffix: '%' }
  ];

  /* Generic page chrome: notifications, toasts, alerts, sidebars, chat, header/footer/nav. */
  var CHROME_SELECTORS = [
    '.notification', '.toast', '[class*="notification"]', '[class*="toast"]',
    'div[role="alert"]', '.sidebar', '.chat', '.chat-container',
    'div[class*="Sidebar"]', 'div[class*="Chat"]', 'aside', 'header', 'footer', 'nav'
  ];

  /*
   * Betting-site panels from the original bookmarklet. They have nothing to do
   * with a BMS; kept only behind the hideBettingChrome flag (off by default).
   */
  var BETTING_SELECTORS = [
    '.bet-history', '.leaderboard', '.live-bets',
    'div[class*="BetHistory"]', 'div[class*="Leaderboard"]'
  ];

  /* Plain decimals only: optional sign, digits, at most one dot. No hex, exponent or Infinity. */
  function isPlainDecimal(text) {
    var digits = 0;
    var dots = 0;
    for (var i = 0; i < text.length; i++) {
      var ch = text.charAt(i);
      if ((ch === '-' || ch === '+') && i === 0) {
        continue;
      }
      if (ch === '.') {
        dots++;
        continue;
      }
      if (ch >= '0' && ch <= '9') {
        digits++;
        continue;
      }
      return false;
    }
    return digits > 0 && dots <= 1;
  }

  function parseValue(raw, field) {
    if (raw === null || raw === undefined) {
      return { ok: false, cancelled: true };
    }
    var text = String(raw).trim();
    if (text === '') {
      return { ok: false, error: field.label + ': empty' };
    }
    var n = isPlainDecimal(text) ? Number(text) : NaN;
    if (typeof n !== 'number' || n !== n || n === Infinity || n === -Infinity) {
      return { ok: false, error: field.label + ': not a number (' + text + ')' };
    }
    if (n < field.min || n > field.max) {
      return { ok: false, error: field.label + ': ' + text + ' outside ' + field.min + '..' + field.max };
    }
    return { ok: true, value: n, text: text };
  }

  function mergeSelectors(custom) {
    var out = {};
    var k;
    for (k in DEFAULT_SELECTORS) {
      if (Object.prototype.hasOwnProperty.call(DEFAULT_SELECTORS, k)) {
        out[k] = DEFAULT_SELECTORS[k];
      }
    }
    if (custom && typeof custom === 'object') {
      for (k in custom) {
        if (Object.prototype.hasOwnProperty.call(out, k) && typeof custom[k] === 'string' && custom[k].trim() !== '') {
          out[k] = custom[k];
        }
      }
    }
    return out;
  }

  function hideCss(includeChrome, includeBetting) {
    var list = [];
    if (includeChrome) {
      list = list.concat(CHROME_SELECTORS);
    }
    if (includeBetting) {
      list = list.concat(BETTING_SELECTORS);
    }
    var css = '#' + BANNER_ID + '{display:block!important;position:fixed!important;top:0;left:0;right:0;' +
      'z-index:2147483647;margin:0;padding:6px 10px;background:#b00020;color:#fff;' +
      'font:bold 14px/1.3 sans-serif;text-align:center;}' +
      '[data-bms-mock="1"]{outline:2px dashed #b00020!important;}';
    if (list.length) {
      css = list.join(',') + '{display:none!important}' + css;
    }
    return css;
  }

  function revert(win) {
    var doc = win.document;
    var state = win[STATE_KEY];
    if (state && state.changed) {
      for (var i = state.changed.length - 1; i >= 0; i--) {
        var rec = state.changed[i];
        while (rec.el.firstChild) {
          rec.el.removeChild(rec.el.firstChild);
        }
        for (var j = 0; j < rec.nodes.length; j++) {
          rec.el.appendChild(rec.nodes[j]);
        }
        rec.el.removeAttribute('data-bms-mock');
        if (rec.title === null) {
          rec.el.removeAttribute('title');
        } else {
          rec.el.setAttribute('title', rec.title);
        }
      }
    }
    var style = doc.getElementById(STYLE_ID);
    if (style && style.parentNode) {
      style.parentNode.removeChild(style);
    }
    var banner = doc.getElementById(BANNER_ID);
    if (banner && banner.parentNode) {
      banner.parentNode.removeChild(banner);
    }
    win[STATE_KEY] = { active: false, version: VERSION, revert: function () { revert(win); } };
    return true;
  }

  function apply(win) {
    var doc = win.document;
    var cfg = win.BMS_MOCK_CONFIG || {};
    var selectors = mergeSelectors(cfg.selectors);
    var changed = [];
    var report = [];
    var errors = [];

    var hideChrome = cfg.hideChrome;
    if (typeof hideChrome !== 'boolean') {
      hideChrome = !!win.confirm(MOCK_LABEL + ': also hide page chrome (header, nav, sidebars, toasts) for a cleaner screenshot?');
    }

    var style = doc.createElement('style');
    style.id = STYLE_ID;
    style.textContent = hideCss(hideChrome, cfg.hideBettingChrome === true);
    (doc.head || doc.documentElement).appendChild(style);

    var banner = doc.createElement('div');
    banner.id = BANNER_ID;
    banner.setAttribute('role', 'status');
    banner.setAttribute('data-bms-mock-banner', '1');
    banner.textContent = MOCK_LABEL + ' \u2014 ' + DISCLAIMER;
    (doc.body || doc.documentElement).appendChild(banner);

    for (var f = 0; f < FIELDS.length; f++) {
      var field = FIELDS[f];
      var parsed = parseValue(win.prompt(MOCK_LABEL + ' \u2014 ' + field.label + ' (Cancel = leave unchanged)', field.def), field);
      if (parsed.cancelled) {
        report.push(field.label + ': unchanged (cancelled)');
        continue;
      }
      if (!parsed.ok) {
        errors.push(parsed.error);
        report.push(field.label + ': unchanged (invalid)');
        continue;
      }
      var els;
      try {
        els = doc.querySelectorAll(selectors[field.key]);
      } catch (e) {
        errors.push(field.label + ': bad selector ' + selectors[field.key]);
        continue;
      }
      for (var e2 = 0; e2 < els.length; e2++) {
        var el = els[e2];
        if (el.getAttribute('data-bms-mock') === '1') {
          continue;
        }
        var nodes = [];
        for (var c = 0; c < el.childNodes.length; c++) {
          nodes.push(el.childNodes[c]);
        }
        changed.push({ el: el, nodes: nodes, title: el.getAttribute('title') });
        el.textContent = parsed.text + field.suffix;
        el.setAttribute('data-bms-mock', '1');
        el.setAttribute('title', MOCK_LABEL + ': typed-in demo value, not a real reading');
      }
      report.push(field.label + ': ' + parsed.text + ' ' + field.unit + ' (' + els.length + ' element' + (els.length === 1 ? '' : 's') + ')');
    }

    win[STATE_KEY] = {
      active: true,
      version: VERSION,
      changed: changed,
      errors: errors,
      revert: function () { revert(win); }
    };

    win.alert('\uD83D\uDF01\u2200 BMS ' + MOCK_LABEL + ' (demo/screenshot only).\n' +
      'Only this page\'s display was changed. ' + DISCLAIMER + '\n\n' +
      report.join('\n') +
      (errors.length ? '\n\nRejected: ' + errors.join('; ') : '') +
      '\n\nRun again or call window.' + STATE_KEY + '.revert() to restore.');
    return win[STATE_KEY];
  }

  function toggle(win) {
    var state = win[STATE_KEY];
    if (state && state.active) {
      if (win.confirm(MOCK_LABEL + ' is active on this page. Revert to the original text?')) {
        revert(win);
      }
      return undefined;
    }
    apply(win);
    return undefined;
  }

  var api = {
    VERSION: VERSION,
    DEFAULT_SELECTORS: DEFAULT_SELECTORS,
    FIELDS: FIELDS,
    CHROME_SELECTORS: CHROME_SELECTORS,
    BETTING_SELECTORS: BETTING_SELECTORS,
    isPlainDecimal: isPlainDecimal,
    parseValue: parseValue,
    mergeSelectors: mergeSelectors,
    hideCss: hideCss,
    apply: apply,
    revert: revert,
    toggle: toggle
  };

  if (typeof window === 'undefined' && typeof module === 'object' && module && module.exports) {
    module.exports = api;
  } else {
    toggle(window);
  }
})();
