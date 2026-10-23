'use strict';

/**
 * Private loopback CORS Anywhere — local/dev only.
 *
 * Cosmic Alignment: bind 127.0.0.1 only (never 0.0.0.0 / ::).
 * Not an open proxy: originWhitelist must be non-empty.
 * Do NOT use public cors-anywhere.herokuapp.com.
 * Separate concern from port380 harden-CORS (feat/harden-cors-healthz).
 */

var path = require('path');
var corsAnywhere = require('cors-anywhere');
var createRateLimitChecker = require('cors-anywhere/lib/rate-limit');

/** Default Origins — align with PORT380_ALLOWED_ORIGINS + axiomic / localhost. */
var DEFAULT_WHITELIST = [
  'https://api.sovereign.garden',
  'https://sovereign.garden',
  'http://localhost:380',
  'http://localhost:8080',
  'http://localhost',
  'http://127.0.0.1:380',
  'http://127.0.0.1:8080',
  'http://127.0.0.1',
  'https://axiomiccoreness.com',
  'https://www.axiomiccoreness.com',
  'https://bridge.axiomiccoreness.com',
  'https://axiomiccoreness.github.io',
].join(',');

function parseEnvList(env) {
  if (!env) {
    return [];
  }
  return env.split(',').map(function (s) {
    return s.trim();
  }).filter(Boolean);
}

var hostEnv = (process.env.HOST || process.env.BIND_HOST || '127.0.0.1').trim();
var port = parseInt(process.env.PORT || '8080', 10);

if (!Number.isFinite(port) || port < 1 || port > 65535) {
  console.error('FATAL: PORT must be an integer 1-65535, got ' + JSON.stringify(process.env.PORT));
  process.exit(1);
}

// Cosmic Alignment — refuse anything that is not loopback IPv4.
if (hostEnv === '0.0.0.0' || hostEnv === '::' || hostEnv === '[::]' ||
    hostEnv === '*' || (hostEnv !== '127.0.0.1' && hostEnv !== 'localhost')) {
  console.error(
    'FATAL: Cosmic Alignment — refuse bind host ' + JSON.stringify(hostEnv) +
    '; only 127.0.0.1 (or localhost alias) is allowed.'
  );
  process.exit(1);
}
var host = '127.0.0.1';

var originWhitelist = parseEnvList(
  process.env.CORSANYWHERE_WHITELIST || DEFAULT_WHITELIST
);
if (originWhitelist.length === 0) {
  console.error(
    'FATAL: CORSANYWHERE_WHITELIST is empty — refusing to start as an open proxy. '
    + 'Set a comma-separated Origin allowlist.'
  );
  process.exit(1);
}

var originBlacklist = parseEnvList(process.env.CORSANYWHERE_BLACKLIST);

// Sensible local default: 50 requests per origin per minute.
var rateLimitEnv = process.env.CORSANYWHERE_RATELIMIT || '50 1';
var checkRateLimit = createRateLimitChecker(rateLimitEnv);

var server = corsAnywhere.createServer({
  originBlacklist: originBlacklist,
  originWhitelist: originWhitelist,
  requireHeader: ['Origin', 'X-Requested-With'],
  checkRateLimit: checkRateLimit,
  removeHeaders: [
    'cookie',
    'cookie2',
  ],
  setHeaders: {
    'x-powered-by': 'axiomic-loopback-cors-anywhere',
  },
  redirectSameOrigin: true,
  helpFile: path.join(__dirname, 'help.txt'),
  httpProxyOptions: {
    xfwd: false,
  },
});

server.listen(port, host, function () {
  console.log('Running private CORS Anywhere on http://' + host + ':' + port);
  console.log('Whitelist (' + originWhitelist.length + '): ' + originWhitelist.join(', '));
  console.log('Rate limit: ' + rateLimitEnv);
  console.log('Cosmic Alignment: loopback-only; not herokuapp; cookies stripped.');
});
