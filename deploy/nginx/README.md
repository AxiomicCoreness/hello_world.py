# nginx config for bridge.axiomiccoreness.com

`bridge.axiomiccoreness.com.conf` terminates TLS for the public bridge
host and passes the `/cli` WebSocket through to the local bridge.

Nothing in this repo deploys it automatically. The host admin does these steps:

1. Issue the certificate, for example `certbot certonly -d bridge.axiomiccoreness.com`.
   Adjust the `ssl_certificate` paths in the conf if certbot puts them somewhere else.
2. Add this map block inside the `http {}` block of `nginx.conf`:

   ```nginx
   map $http_upgrade $connection_upgrade {
       default upgrade;
       ''      close;
   }
   ```

3. Install the conf, for example into `/etc/nginx/conf.d/`, then run
   `nginx -t` and reload with `nginx -s reload` or `systemctl reload nginx`.

## What stays where

- The bridge stays bound to `127.0.0.1:6680` (Cosmic Alignment, never `0.0.0.0`).
  nginx on 443 is the only public listener.
- The Pages client already dials `wss://bridge.axiomiccoreness.com/cli`
  (see `irc/CliLines.java`). Local play still uses `ws://127.0.0.1:6680/cli`.
- `/llm` is a chat command sent over the `/cli` socket, so it has no `location` of its own.
- cors-anywhere (`127.0.0.1:8080`) stays internal on purpose. Publishing it
  would make the host an open relay.

## Note on `http2`

The conf uses `listen 443 ssl;` plus `http2 on;` rather than
`listen 443 ssl http2;`. nginx 1.25.1 and later warn that the `http2`
listen parameter is deprecated. On nginx older than 1.25.1, `http2 on;` is not
recognised; use `listen 443 ssl http2;` there instead.

## Checked on

nginx 1.26.3: `nginx -t` passed with the map block and self-signed stand-in certs.
A WebSocket upgrade through `/cli` to the live bridge on 127.0.0.1:6680 returned
`101 Switching Protocols`.
