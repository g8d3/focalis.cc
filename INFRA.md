# focalis.cc — Hosting Infra

> Machine: `vues-hcar5000mi` (192.168.0.93 LAN, 186.87.104.116 public IPv4) — Ubuntu 24.04, Docker 29.6.2
> Domain: `focalis.cc` @ Spaceship (`launch1/2.spaceship.net` NS)
> Stack: **Caddy 2.11 (caddy:2-alpine)** in Docker — auto HTTPS via Let's Encrypt (HTTP-01)
> Variants: `/home/vuos/code/p4/sites/focalis.cc/variants/{variant-a-studio,variant-b-labs,variant-c-systems}`

Last updated: 2026-08-31 04:20 UTC — INFRA agent (focalis.cc infra subsession)

---

## 1. Spaceship API — Docs & Current State

### Discovery
- Base URL: `https://spaceship.dev/api/v1` (not `api.spaceship.com`)
- Auth: `X-API-Key: $SPACESHIP_API_KEY` + `X-API-Secret: $SPACESHIP_API_SECRET`
- OpenAPI not public without auth; validated by probing.
- **List records**: `GET /dns/records/{domain}?take=100&skip=0`
- **Replace all records**: `PUT /dns/records/{domain}` with `{"items": [{"type":"A","name":"@","address":"1.2.3.4","ttl":3600}, ...]}` — returns `204` on success.
- **Delete specific**: `DELETE /dns/records/{domain}` with JSON array body `[{"type":"A","name":"@","address":"1.2.3.4","ttl":3600}]` — returns 204.
- Search & `curl`-validated 2026-08-31 via `bash curl` from this machine.

### Current DNS (2026-08-31 04:19 UTC)
API `GET /dns/records/focalis.cc?take=100&skip=0`:
```json
{
  "items": [
    { "address": "34.216.117.25", "name": "@", "type": "A", "ttl": 3600, "group": { "type": "custom" } },
    { "address": "54.149.79.189", "name": "@", "type": "A", "ttl": 3600, "group": { "type": "custom" } }
  ],
  "total": 2
}
```
- These are Spaceship parking / default A records (AWS). Before first PUT they showed as `items: []` via API but `dig @8.8.8.8` already resolved to the two AWS IPs — so parking IPs are injected at the authoritative NS even when API reports 0.
- `dig @launch1.spaceship.net focalis.cc` and `dig @8.8.8.8 focalis.cc` both return `34.216.117.25` / `54.149.79.189`.
- `GET /domains/focalis.cc` shows: `lifecycle: registered`, `hosts: launch1/2.spaceship.net`, `privacy: high`, `autoRenew: true`, expires `2027-08-31`.
- No CNAME/MX/TXT/AAAA yet. No wildcard. No `www` A record currently (will be covered by apex + `www.focalis.cc` Caddy block once apex points to this machine).

Saved raw dump: `curl -H "X-API-Key: ..." https://spaceship.dev/api/v1/dns/records/focalis.cc?take=100&skip=0 | jq .` — see `scripts/list-dns.sh`.

---

## 2. Caddy-based Docker Setup

### Files
| File | Purpose |
|------|---------|
| `docker-compose.yml` | Caddy service, volumes `caddy_data`/`caddy_config`, network `focalis-net`, ports `80:80 443:443 443/udp` |
| `Caddyfile` | Routing + TLS (see below) |
| `.env.example` | Template for `SPACESHIP_API_KEY/SECRET`, `DOMAIN`, `CADDY_EMAIL` |
| `variants/variant-a-studio/` | Default site (minimal premium) — served at `/` |
| `variants/variant-b-labs/` | Labs (experimental) |
| `variants/variant-c-systems/` | Systems (enterprise) |
| `scripts/list-dns.sh` | Read-only DNS inspector |
| `scripts/update-dns.sh` | Idempotent public-IP → `@ A` updater (detect IP, dry-run, PUT) |

No bare processes: `docker compose up -d` only. Healthcheck via `wget http://127.0.0.1:80/health` inside container.

### Caddyfile design
- Global: `email hello@focalis.cc` (LE account), `admin off`. Uncomment `acme_ca https://acme-staging...` for testing.
- Snippet `(common)` reused in `:80` and `focalis.cc, www.focalis.cc`:
  - `handle /health*` → `200 ok`
  - `handle_path /studio/*` & `/variant-a/*` → `/srv/variant-a-studio` (`file_server`)
  - `handle_path /labs/*` & `/variant-b/*` → `/srv/variant-b-labs`
  - `handle_path /systems/*` & `/variant-c/*` → `/srv/variant-c-systems`
  - `redir /studio /studio/ 308` (and 5 sibling redirects for bare prefix without trailing slash)
  - `handle { root * /srv/variant-a-studio; file_server }` — fallback default
- `:80` block — matches any Host not more specifically matched (localhost, 127.0.0.1, 192.168.0.93, 192.168.1.x). `encode zstd gzip`, `log stdout console`. No TLS.
- `focalis.cc, www.focalis.cc` — same `import common` plus security headers (`X-Frame-Options`, `X-Content-Type-Options`, etc.), auto-HTTPS (LE HTTP-01). `encode zstd gzip`.
- Subdomains (each own LE cert via HTTP-01, no wildcard/DNS-01 needed):
  - `studio.focalis.cc` → `variant-a-studio`
  - `labs.focalis.cc` → `variant-b-labs`
  - `systems.focalis.cc` → `variant-c-systems`

**Why no `*.focalis.cc` wildcard:** wildcard needs DNS-01 challenge; explicit host list gets separate HTTP-01 certs, simpler with Spaceship API (no DNS-01 plugin). Add more subdomains as separate blocks if needed.

Volumes: `variants` mounted `:ro` at `/srv`; `caddy_data` (`/data`) holds LE certs (`/data/caddy/acme/...`), `caddy_config` (`/config`) holds autosave.

### Start / stop
```bash
cd /home/vuos/code/p4/sites/focalis.cc
docker compose up -d        # start / create
docker compose ps           # status (should be healthy)
docker compose logs -f      # tail
docker compose restart      # reload after Caddyfile edit
docker compose down         # stop (preserves volumes)
docker compose down -v      # stop + wipe certs (forces re-issue)
```

---

## 3. Local Test — 2026-08-31 04:20 UTC

All via Docker, no bare `caddy` binary.

```
curl -s http://127.0.0.1:80/health          → 200 ok
curl -s http://127.0.0.1:80/                → 200 <title>Focalis Studio — Tools for makers who ship</title> (variant-a-studio)
curl -s http://127.0.0.1:80/studio/         → 200 Studio
curl -s http://127.0.0.1:80/variant-a/      → 200 Studio (alias)
curl -s http://127.0.0.1:80/labs/            → 200 <title>Focalis Labs — We build tools for builders</title>
curl -s http://127.0.0.1:80/variant-b/products.html → 200 <title>Products — Focalis Labs</title>
curl -s http://127.0.0.1:80/systems/         → 200 <title>Focalis Systems — Infrastructure for Ambitious Teams</title>
curl -s http://127.0.0.1:80/systems/products.html → 200 <title>Products — Focalis Systems</title>
curl -s -i http://127.0.0.1:80/studio       → 308 Location: /studio/ → follow → 200 (slash redirect fixed)
curl -s http://192.168.0.93/health         → 200 ok (LAN)
curl -s http://192.168.0.93/               → 200 Studio
curl -H "Host: focalis.cc" http://127.0.0.1:80/ → 308 Location: https://focalis.cc/ (expected http→https for prod domain)

docker inspect Health: "healthy" (wget spider /health)
```

Caddy adapted config valid: `caddy validate` passes (via `docker run --rm -v Caddyfile... caddy validate`).
Startup logs: `logs/caddy-startup.log` (~100 lines) — TLS obtain attempts for 5 identifiers (`focalis.cc www studio labs systems`) via `acme-v02...` then `acme.zerossl...`. Expected failures until DNS + port-forward are ready:
- `focalis.cc`: `connection timeout` to `34.216.117.25` (parking IP, firewall)
- `www/labs/systems/studio.focalis.cc`: `NXDOMAIN` (no A yet)

Once DNS points to `186.87.104.116` and `80/443` are forwarded, LE will succeed on next retry (Caddy retries automatically; or `docker compose restart`).

---

## 4. DNS Update Script — `scripts/update-dns.sh`

Idempotent, preserves non-`@ A` records.

```bash
# dry-run (what would change):
./scripts/update-dns.sh --dry-run
# live (auto-detect public IP via api.ipify.org/ifconfig.me/icanhazip):
./scripts/update-dns.sh
# force specific IP or TTL or domain:
./scripts/update-dns.sh --ip 186.87.104.116 --ttl 600 --domain focalis.cc
```

Logic:
1. Detects public IPv4 via `curl -4 https://api.ipify.org` → fallbacks `ifconfig.me`, `icanhazip.com`. Honors `MANUAL_IP` / `--ip`.
2. GET current items, filters out any `@ A`, appends desired `{type:A,name:@,address:$IP,ttl:$TTL}`, cleans to `{type,name,address,ttl}` shape.
3. Compares current `@ A` set vs desired; exits early if already pointing.
4. PUT new list to `/dns/records/{domain}` (HTTP 204 = success).
5. Verifies via GET + `dig @launch1.spaceship.net` / `@8.8.8.8`. TTL = 3600 default.

Also see `scripts/list-dns.sh` for read-only inspect + dig + public IP echo.

**Safety:** test with `--dry-run` first. PUT replaces *all* records, so script reconstructs full list from GET instead of blind overwrite — keeps TXT/CNAME/MX if you later add them. Test run 2026-08-31 dry-run correctly showed payload `{"address":"186.87.104.116"}` replacing the two parking IPs.

No Cloudflare involved — direct Spaceship authoritative NS.

---

## 5. What's Pending (manual)

### Required for public HTTPS
- [ ] **DNS cutover**: run `./scripts/update-dns.sh` (or `--dry-run` then live). Sets `@ A → 186.87.104.116`. Wait `TTL 3600` for propagation; `dig @8.8.8.8 focalis.cc` should then return `186.87.104.116` instead of parking IPs. Optionally add `www A → same IP` (same script covers apex only; `www` will be served via `www.focalis.cc` Caddy block once apex A exists — but you may want explicit `www A` or CNAME; current script keeps non-`@` records, so add `www` separately if desired: PUT payload already supports it).
- [ ] **Port forwarding**: router must forward `TCP 80` and `TCP 443` (and `UDP 443` for HTTP/3) to `192.168.0.93` (this machine, eno1). Check via `https://canyouseeme.org` or `curl -v http://186.87.104.116 --connect-timeout 5` from outside, or `nmap`. ISP CGNAT: `186.87.104.116` is public — verify it's not behind carrier NAT. If CGNAT, need tunnel (Cloudflare Tunnel, Tailscale Funnel, or VPS reverse proxy).
- [ ] **Firewall**: `sudo ufw allow 80/tcp && sudo ufw allow 443/tcp && sudo ufw allow 443/udp` if UFW enabled (`ss -tlnp` currently shows no host firewall blocking; Docker's iptables handles mapping, but host UFW can still block).
- [ ] **Let's Encrypt issuance**: Caddy will auto-retry; once DNS + forwarding are live, wait 1-2 min then `docker compose logs | grep tls.obtain`. On success, `curl -vk https://focalis.cc` should return 200 with valid cert for `focalis.cc` (+ subdomains). If `NXDOMAIN` for subdomains, add `A` records for `studio/labs/systems` or use only subpath routing (Caddy will still try to issue but fail until DNS exists — not fatal for apex). Alternative: remove subdomain blocks until needed.
- [ ] **Public IP volatility**: ISP `186.87.104.116` (AS10620 Telmex Colombia) is dynamic. Schedule `update-dns.sh` via cron or systemd timer: e.g. `*/30 * * * * /home/vuos/code/p4/sites/focalis.cc/scripts/update-dns.sh >> /home/vuos/code/p4/sites/focalis.cc/logs/dns-update.log 2>&1`. Script is idempotent.
- [ ] **HTTPS redirect & HSTS**: Caddy auto redirects `http://focalis.cc → https://focalis.cc`. After first successful cert, uncomment `Strict-Transport-Security` header in `Caddyfile` and `docker compose restart`.
- [ ] **IPv6**: machine has `2800:484:aa74:1900:...` global. If you want AAAA, set via API similarly (script currently handles only A; extend to AAAA by detecting `curl -6` and adding `{"type":"AAAA","name":"@","address":"<ipv6>"}`).

### Optional / nice-to-have
- Staging CA for tests: uncomment `acme_ca https://acme-staging-v02...` to avoid rate limits while iterating.
- `www` redirect: current `focalis.cc, www.focalis.cc` serves same content on both. Could add `www.focalis.cc { redir https://focalis.cc{uri} }` to canonicalize.
- Logs retention: `logs/` is git-ignored? If not, add.
- Backups: `caddy_data` volume holds certs — `docker volume inspect focalis-caddy-data`.
- Variants alias: `variant-a` / `variant-b` / `variant-c` are legacy empty dirs — routing uses `variant-a-studio` etc. Keep or remove empty dirs to avoid confusion.

### Verified not needed
- Cloudflare proxy: **no** — direct.
- Bare `caddy` install: **no** — Docker only per requirements.

---

## 6. Quick Cheat Sheet

```bash
cd /home/vuos/code/p4/sites/focalis.cc

# inspect
./scripts/list-dns.sh
cat Caddyfile
docker compose ps; docker compose logs --tail 50
curl -s http://localhost/health; curl -s http://localhost/labs/ | grep title
curl -s http://192.168.0.93/health
dig @8.8.8.8 focalis.cc +short
curl -4 -s https://api.ipify.org; echo

# update DNS (dry then live)
./scripts/update-dns.sh --dry-run
./scripts/update-dns.sh

# after public cutover, verify TLS
curl -vk https://focalis.cc/ 2>&1 | head -20
curl -vk https://studio.focalis.cc/ 2>&1 | head -20
docker compose logs | grep -E "tls.obtain|certificate"

# Caddyfile edit cycle
$EDITOR Caddyfile
docker run --rm -v $PWD/Caddyfile:/etc/caddy/Caddyfile -v $PWD/variants:/srv caddy:2-alpine caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
docker compose restart && sleep 3 && curl -s http://127.0.0.1:80/health
```

---

## 7. Artifacts & Logs (saved)

- `docker-compose.yml` (765 B) + `Caddyfile` (3.3 KB) — created 2026-08-31
- `scripts/list-dns.sh` + `scripts/update-dns.sh` (executable, `chmod +x`)
- `.env.example`
- `logs/caddy-startup.log` — first startup with TLS challenge failures (expected pre-cutover)
- `curl -s http://127.0.0.1/...` HTML dumps: `/tmp/local_test_{root,studio,labs,systems}.html` (17–42 KB)
- API probes performed via `curl` with `X-API-Key/Secret` headers — responses saved inline above

---

## 8. Security Notes

- `SPACESHIP_API_KEY/SECRET` in env only, never committed. `docker-compose.yml` does not embed secrets.
- Caddy runs as `caddy` user inside Alpine container, non-root mapped ports via Docker.
- `admin off` disables Caddy admin API on `:2019` exposure (still bound internally but not forwarded).
- Headers: `X-Frame-Options SAMEORIGIN`, `nosniff`, strict referrer, disable geolocation/mic/camera.
- Keep `variants` read-only mount (`:ro`) to container.

---

## 9. Next Agent / Human Actions

1. Run `./scripts/update-dns.sh` when ready to go live (ensure `SPACESHIP_API_KEY/SECRET` exported or in `.env`).
2. Forward `80/443` on router to `192.168.0.93` (eno1). Verify via external `curl http://186.87.104.116` or port checker.
3. Restart Caddy and watch cert issuance: `docker compose restart && docker compose logs -f | grep tls`.
4. Add `www`, `studio`, `labs`, `systems` A records if subdomains needed, or remove subdomain blocks until DNS exists to silence LE NXDOMAIN retries.
5. Once HTTPS works, update `STATUS.md` checklist and mark Infra done.

---

## 10. Admin Panel — Live Variant Switcher (2026-08-31)

> Added per user request: Cloudflare Tunnel compatible, all 3 variants stay alive, admin UI picks the apex.

### 10.1 Switch mechanism
- File `ACTIVE` at `/home/vuos/code/p4/sites/focalis.cc/ACTIVE` contains active variant name (default `variant-c-systems`, the light Systems theme user chose).
- Symlink `variants/active -> variant-c-systems` created with `ln -sfn variant-c-systems variants/active`. Caddy mounts `variants` at `/srv` so inside container it appears as `/srv/active -> variant-c-systems`. `file_server` follows symlink, no Caddy reload needed.
- Caddy `handle /` and fallback `handle` now both use `root * /srv/active` (previously `/srv/selector`). Selector moved to `/selector/` via `handle_path /selector/* { root * /srv/selector }` + `redir /selector /selector/ 308`.
- Previews unchanged: `/studio/*` → `variant-a-studio`, `/labs/*` → `variant-b-labs`, `/systems/*` → `variant-c-systems` (plus `/variant-a` `/variant-b` `/variant-c` aliases). Each still serves its full sub-site.
- Admin proxied via `handle /admin/* { reverse_proxy admin:8788 }` + `redir /admin /admin/ 308` in both `:80` and `focalis.cc, www.focalis.cc` blocks. Must be before fallback so it wins. No `basic_auth` in Caddy — auth lives in the app.

Verify:
```bash
cat ACTIVE                              # variant-c-systems
readlink variants/active                # variant-c-systems
curl -s http://127.0.0.1:80/ | grep title          # Systems (apex)
curl -s http://127.0.0.1:80/selector/ | grep title # Chooses version (hub)
curl -s http://127.0.0.1:80/studio/ | grep title   # Studio preview
curl -s http://127.0.0.1:80/labs/ | grep title     # Labs preview
curl -s http://127.0.0.1:80/systems/ | grep title  # Systems preview
```
Switch: `curl -u admin:$PASS -X POST -d "variant=variant-a-studio" http://127.0.0.1:80/admin/switch` writes `ACTIVE` and runs `ln -sfn`. Apex changes instantly.

### 10.2 Admin backend (`admin/app.py`)
- `admin/app.py` — Python 3.12 + Flask on `0.0.0.0:8788` (container `focalis-admin`, image `python:3.12-slim`).
- Volumes: `./admin:/app`, `./:/site`, `./variants:/srv`. Env: `ACTIVE_FILE=/site/ACTIVE`, `VARIANTS_DIR=/site/variants`, `CREDENTIALS_FILE=/app/.credentials`. Ports `127.0.0.1:8788:8788` (host direct debug) but Caddy proxies via internal DNS `admin:8788` on `focalis-net`.
- Auth: **HTTP Basic Auth + session cookie**. Priority: `ADMIN_USER`/`ADMIN_PASS` env if set, else `admin/.credentials` (created if missing: user `admin` + random 12-char `openssl rand -base64 12`, saved as `ADMIN_USER=…`/`ADMIN_PASS=…` with `chmod 600`). Loaded via `hmac.compare_digest`. Form login at `GET /admin/login` → `POST /admin/login` sets `session["admin_user"]` (Flask `secret_key` persisted in `admin/.secret_key`, 600) + plain cookie `focalis_admin=1` (Lax, 30d) for JS bar detection. `GET /admin/logout` clears both. `requires_auth` checks session OR Basic header; if neither, 302 to `/admin/login` (or 401 if Authorization header was sent and wrong). Also supports `ADMIN_USER`/`ADMIN_PASS` override via compose env.
- Routes:
  - `GET /admin/health` → `ok` (no auth, Caddy/compose healthcheck)
  - `GET /admin/status` → JSON `{"authenticated":bool,"active":variant,"user":…}` (checks session or Basic; used by bar.js)
  - `GET /admin/bar.js` → public JS (no auth) — fetches `/admin/status` with `credentials:include`, if authenticated injects WordPress-like top bar
  - `GET /admin/` + `GET /admin` → dashboard (3 cards: Studio `color #7C5CFF`, Labs `#FF4D00`, Systems `#0F2342`, each with iframe preview `src="/studio/"` etc + `Make Active` POST form). Shows current `ACTIVE` and symlink target.
  - `POST /admin/switch` → validates `variant` against allowlist (`variant-a-studio`, `variant-b-labs`, `variant-c-systems` plus aliases `studio`/`labs`/`systems`/`variant-a`…), writes `ACTIVE`, runs `ln -sfn`, redirects to `/admin/?msg=…` (or JSON if `Accept: application/json`).
  - `GET /admin/login` / `POST /admin/login` form, `GET/POST /admin/logout`.
- Light theme: Tailwind CDN, `bg-[#FCFCF9]` / `border-zinc-200`, same type scale as variants. Installed on first start via `pip install --no-cache-dir Flask` in container command `bash -c "pip… && python /app/app.py"`.

Healthchecks:
- `caddy`: `wget --spider http://127.0.0.1:80/health`
- `admin`: `python -c "urllib.request.urlopen('http://127.0.0.1:8788/admin/health').read()==b'ok'"` every 30s, start_period 15s.

Startup: `docker compose up -d` creates `focalis-admin` (pulls `python:3.12-slim` if needed) + `focalis-caddy` (depends_on admin). Logs: `docker compose logs admin` prints generated credentials once (also `cat admin/.credentials`).

### 10.3 Admin bar (WordPress-like)
- Every variant HTML (all 25 files under `variants/{selector,variant-a-studio,variant-b-labs,variant-c-systems}/*.html`) now includes `<script src="/admin/bar.js"></script>` before `</body>` (injected via `sed` on 2026-08-31).
- `/admin/bar.js` is public; it calls `fetch('/admin/status', {credentials:'include'})`. If `authenticated:false` → no bar. If true → injects fixed div `#focalis-admin-bar` `height:32px`, `position:fixed; top:0; z-index:99999; background:#0B0B0F`, `border-bottom:1px solid #1F1F23`, `box-shadow`. Adds `document.body.style.paddingTop='32px'` so layout not shifted.
- Bar contents: `F focalis.cc Admin` link → `/admin/`, `LIVE: Systems variant-c-systems` with color dot matching active, three pill buttons `Studio`/`Labs`/`Systems` (active has filled bg `color`, inactive `border #2A2A2E`), clicking does `fetch('/admin/switch', POST variant=…)` then reload; right side links `Preview: /studio/` `/labs/` `/systems/`, `Selector`, `Dashboard`, `Logout` (`/admin/logout`).
- When not logged in, bar is invisible (status false). After form/Basic login, bar appears on every page without further Caddy config because script is already embedded.
- Caddy `X-Frame-Options SAMEORIGIN` still set for `focalis.cc` host — but bar uses same-origin fetch, and iframe previews on dashboard use `SAMEORIGIN` which is allowed for same host. No extra header needed for bar.

### 10.4 Credentials & git safety
- `admin/.credentials` (`600`, `ADMIN_USER=admin` + `ADMIN_PASS=<random 12 chars, see file>`) and `admin/.secret_key` (`600`) are on host bind mount `./admin:/app`. `sites/` is gitignored via `/sites/` in repo root `.gitignore`, so not tracked. Env override: `ADMIN_USER` / `ADMIN_PASS` in compose `environment` takes precedence (useful for Cloudflare Tunnel secrets or `docker compose --env-file`).
- `ACTIVE` and `variants/active` are also bind-mounted via `./:/site` and `./variants:/srv`, so switch is visible on host immediately.
- No plaintext password committed; only in host file + container logs (first run). Rotate by editing `admin/.credentials` and `docker compose restart admin`.

### 10.5 docker-compose.yml delta
```yaml
services:
  admin:
    image: python:3.12-slim
    container_name: focalis-admin
    volumes: [./admin:/app, ./:/site, ./variants:/srv]
    ports: ["127.0.0.1:8788:8788"]
    environment: [ADMIN_USER, ADMIN_PASS, ACTIVE_FILE, VARIANTS_DIR, CREDENTIALS_FILE]
    command: bash -c "pip install --no-cache-dir Flask && python /app/app.py"
    networks: [focalis-net]
  caddy:
    depends_on: {admin: {condition: service_started}}
    volumes: [./Caddyfile:/etc/caddy/Caddyfile:ro, ./variants:/srv:ro, ...]
```
Local test after change (2026-08-31 05:31 UTC):
```
curl -s http://127.0.0.1:80/                  -> Systems (active)
curl -s http://127.0.0.1:80/selector/        -> Choose your version
curl -s http://127.0.0.1:80/studio/          -> Studio
curl -s http://127.0.0.1:80/labs/            -> Labs
curl -s http://127.0.0.1:80/systems/         -> Systems
curl -s http://127.0.0.1:80/admin/health     -> ok (public)
curl -s -u admin:… http://127.0.0.1:80/admin/  -> dashboard (3 cards)
curl -X POST -u admin:… -d variant=variant-a-studio http://127.0.0.1:80/admin/switch -> 303, ACTIVE=variant-a-studio, / now Studio; switch back -> Systems
curl -s http://127.0.0.1:80/admin/bar.js        -> JS
curl -s http://127.0.0.1:80/admin/status       -> {authenticated:false, active:...}
curl -s -u admin:… http://127.0.0.1:80/admin/status -> {authenticated:true}
# form login
curl -c /tmp/c -b /tmp/c -d "username=admin&password=…" http://127.0.0.1:80/admin/login -> sets focalis_admin + session, bar appears
```

Cloudflare Tunnel: tunnel should point to `http://focalis-caddy:80` or `http://127.0.0.1:80` on this host. All paths (`/`, `/selector/`, `/studio/`, `/labs/`, `/systems/`, `/admin/`, `/admin/bar.js`, `/health`) are same-origin, so bar works behind tunnel too. No extra DNS change needed; `update-dns.sh` still valid if you keep direct IP fallback.

