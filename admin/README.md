# focalis.cc — Admin Panel

> Switch which variant is served at `focalis.cc /` (apex). Selector lives at `/selector/`, previews at `/studio/` `/labs/` `/systems/`. Apex uses symlink `variants/active -> variant-c-systems` (default light Systems theme).

## Access

- URL: `http://focalis.cc/admin/` (or locally `http://127.0.0.1:80/admin/` / `http://192.168.0.93/admin/`). Caddy proxies `/admin/*` → `admin:8788` (Flask).
- Direct: `http://127.0.0.1:8788/admin/` (host loopback, for debug).
- Auth: HTTP Basic Auth **or** form login. Credentials in `admin/.credentials` (600, gitignored — `sites/` is ignored by repo root `/sites/`). File format:
  ```
  ADMIN_USER=admin
  ADMIN_PASS=<from admin/.credentials, 12 chars>
  ```
  Generated on first `docker compose up -d` if missing (`openssl rand -base64 12` → 12 chars). Override via env vars `ADMIN_USER`/`ADMIN_PASS` (compose `environment` takes precedence). Also persisted Flask `secret_key` in `admin/.secret_key` (600) for session cookies.

- Login form: `GET /admin/login` → username/password → sets `session["admin_user"]` + cookie `focalis_admin=1` (Lax, 30d, not HttpOnly so JS can detect). Logout: `GET /admin/logout`.
- Health (no auth): `GET /admin/health` → `ok`, `GET /health` via Caddy.

Find current credentials:

```bash
cat /home/vuos/code/p4/sites/focalis.cc/admin/.credentials
# or if using env override:
grep ADMIN_ /home/vuos/code/p4/sites/focalis.cc/.env 2>/dev/null
docker compose -f /home/vuos/code/p4/sites/focalis.cc/docker-compose.yml logs admin | grep "ADMIN CREDENTIALS"
```

Rotate: edit `admin/.credentials`, then `docker compose restart admin`.

## What switching does

- `ACTIVE` file `/home/vuos/code/p4/sites/focalis.cc/ACTIVE` ← variant name (`variant-a-studio` | `variant-b-labs` | `variant-c-systems`)
- Symlink `variants/active -> <variant>` via `ln -sfn <variant> variants/active` (run inside admin container as `ln -sfn variant /site/variants/active`)
- Caddy serves apex from `root * /srv/active` (`/srv` is `variants` bind mount). `file_server` follows symlink — instant, no `caddy reload` needed (but `docker compose restart caddy` also works).
- Selector and previews keep working: `/selector/` → `variants/selector`, `/studio/` → `variant-a-studio`, `/labs/` → `variant-b-labs`, `/systems/` → `variant-c-systems` (plus aliases `/variant-a`, `/variant-b`, `/variant-c`).

Current active (host):

```bash
cat /home/vuos/code/p4/sites/focalis.cc/ACTIVE
readlink /home/vuos/code/p4/sites/focalis.cc/variants/active
curl -s http://127.0.0.1:80/ | grep -o "<title>.*</title>"
```

## Dashboard (`/admin/`)

Light theme (Tailwind CDN, `bg-[#FCFCF9]`). Shows current `ACTIVE` + symlink target, then 3 cards:

- **Studio** `variant-a-studio` `#7C5CFF` — Minimal premium, iframe `src="/studio/"`
- **Labs** `variant-b-labs` `#FF4D00` — Bold bento, iframe `src="/labs/"`
- **Systems** `variant-c-systems` `#0F2342` — Enterprise light, iframe `src="/systems/"`

Each card has `Preview … ↗` link + `Make Active` POST form → `POST /admin/switch` with `variant=<name>` → 303 `Location: /admin/?msg=Switched…`. Active card shows `● ACTIVE` badge and disabled button.

CLI switch:

```bash
# Basic Auth
PASS=$(awk -F= '/ADMIN_PASS/{print $2}' admin/.credentials)
curl -s -u admin:$PASS -X POST -d "variant=variant-a-studio" http://127.0.0.1:80/admin/switch -v
curl -s http://127.0.0.1:80/ | grep title  # now Studio

# Session cookie (after form login)
curl -c /tmp/c -b /tmp/c -d "username=admin&password=$PASS&next=/admin/" http://127.0.0.1:80/admin/login -L >/dev/null
curl -b /tmp/c -X POST -d "variant=variant-c-systems" http://127.0.0.1:80/admin/switch

# JSON API
curl -s -u admin:pass -H "Accept: application/json" -X POST -d "variant=variant-b-labs" http://127.0.0.1:80/admin/switch
```

Aliases accepted: `studio` → `variant-a-studio`, `labs` → `variant-b-labs`, `systems` → `variant-c-systems`, `variant-a/b/c` too.

## Admin bar (WordPress-like, on every page)

All 25 HTML files under `variants/` already contain:

```html
<script src="/admin/bar.js"></script>
```

before `</body>`. `GET /admin/bar.js` is public JS that does `fetch('/admin/status', {credentials:'include'})`. If `authenticated:false` → no bar. If `authenticated:true` (session or Basic), it injects `#focalis-admin-bar`:

- Fixed `height:32px`, `top:0`, `z-index:99999`, `background:#0B0B0F`, `border-bottom:#1F1F23`
- `F focalis.cc Admin` → `/admin/`
- `LIVE: Systems variant-c-systems` with color dot (`#0F2342` for Systems)
- Three pills `Studio`/`Labs`/`Systems` — active filled with its color, click → `POST /admin/switch` via fetch then reload
- Right side: `Preview: /studio/` `/labs/` `/systems/` `Selector` `Dashboard` `Logout`
- Sets `document.body.style.paddingTop='32px'` so content not hidden.

When logged out, bar is invisible. After login (form or Basic Auth cached by browser), bar appears on every frontend page (`/`, `/studio/`, `/labs/`, `/systems/`, `/selector/`, plus products/etc because they also include the script). Behind Cloudflare Tunnel same-origin, so works without extra config.

Status endpoint:

```bash
curl -s http://127.0.0.1:80/admin/status
# {"active":"variant-c-systems","authenticated":false, ...}
curl -s -u admin:pass http://127.0.0.1:80/admin/status
# {"authenticated":true,"active":"variant-c-systems","user":"admin"}
```

## Files

| Path | Notes |
|------|-------|
| `admin/app.py` | Flask app (port 8788). Handles auth, switch, bar.js, status, login/logout, dashboard |
| `admin/.credentials` | `600`, `ADMIN_USER`/`ADMIN_PASS` — not in git (`/sites/` ignored) |
| `admin/.secret_key` | `600`, Flask `secret_key` (generated once, persists sessions across restarts) |
| `ACTIVE` | variant name, `variant-c-systems` default |
| `variants/active` | symlink `-> variant-c-systems` (or current) |
| `Caddyfile` | `:80` + `focalis.cc, www.focalis.cc` both have `handle /admin/* { reverse_proxy admin:8788 }`, `handle_path /selector/*`, `handle /` + fallback `root * /srv/active` |
| `docker-compose.yml` | `admin` service (`python:3.12-slim`, `pip install Flask`, `admin:8788`) + `caddy` `depends_on: admin` |

## Operations

```bash
cd /home/vuos/code/p4/sites/focalis.cc

docker compose ps
docker compose logs -f admin   # shows credential generation / switch logs
docker compose logs -f caddy

# validate Caddyfile
docker run --rm -v $PWD/Caddyfile:/etc/caddy/Caddyfile:ro caddy:2-alpine caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
docker compose restart caddy
docker compose restart admin

# test routes
curl -s http://127.0.0.1:80/health
curl -s http://127.0.0.1:80/ | grep title
curl -s http://127.0.0.1:80/selector/ | grep title
curl -s http://127.0.0.1:80/studio/ | grep title
curl -s http://127.0.0.1:80/admin/health
curl -s http://127.0.0.1:80/admin/bar.js | head -5
curl -s -u admin:$(awk -F= '/ADMIN_PASS/{print $2}' admin/.credentials) http://127.0.0.1:80/admin/ | grep -o ACTIVE
```

Cloudflare Tunnel: point your tunnel `ingress` to `http://focalis-caddy:80` or `http://127.0.0.1:80` on this host. All `/admin/*` paths are same-origin, so bar.js fetch works without CORS.

Security: credentials never committed; `admin/.credentials` is `600` on host and `sites/` is gitignored. To use env secrets instead, set `ADMIN_USER`/`ADMIN_PASS` in host env or `docker-compose.yml` `environment` / `--env-file`.
