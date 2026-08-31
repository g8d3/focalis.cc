#!/usr/bin/env bash
# update-dns.sh — Point focalis.cc (@ A) to this machine's public IPv4 via Spaceship API
# Usage: ./update-dns.sh [--dry-run] [--ip 1.2.3.4] [--ttl 3600] [--domain focalis.cc]
# Requires: SPACESHIP_API_KEY + SPACESHIP_API_SECRET (env or .env)
# Detects public IP via api.ipify.org -> ifconfig.me -> icanhazip.com fallback
set -euo pipefail

DIR="$(cd "$(dirname "$0")/.." && pwd)"
if [[ -f "$DIR/.env" ]]; then set -a; source "$DIR/.env"; set +a; fi

DOMAIN="${DOMAIN:-focalis.cc}"
TTL="${TTL:-3600}"
DRY_RUN=0
MANUAL_IP="${MANUAL_IP:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --ip) MANUAL_IP="$2"; shift 2 ;;
    --ttl) TTL="$2"; shift 2 ;;
    --domain) DOMAIN="$2"; shift 2 ;;
    *) echo "Unknown arg $1" >&2; exit 1 ;;
  esac
done

BASE="https://spaceship.dev/api/v1"

if [[ -z "${SPACESHIP_API_KEY:-}" || -z "${SPACESHIP_API_SECRET:-}" ]]; then
  echo "[error] Missing SPACESHIP_API_KEY / SPACESHIP_API_SECRET" >&2
  echo "Set in $DIR/.env or export in shell (see .env.example)" >&2
  exit 1
fi

detect_ip() {
  if [[ -n "$MANUAL_IP" ]]; then echo "$MANUAL_IP"; return; fi
  local ip
  for url in "https://api.ipify.org" "https://ifconfig.me" "https://icanhazip.com" "https://api.ip2host.com/ip"; do
    ip=$(curl -4 -s --max-time 8 "$url" 2>/dev/null | tr -d ' \n\r' | grep -E '^[0-9]{1,3}(\.[0-9]{1,3}){3}$' || true)
    if [[ -n "$ip" ]]; then echo "$ip"; return; fi
  done
  # last try without -4 (may return ipv6, filter only v4)
  ip=$(curl -s --max-time 8 https://api.ipify.org 2>/dev/null | tr -d ' \n\r' | grep -E '^[0-9]{1,3}(\.[0-9]{1,3}){3}$' || true)
  if [[ -n "$ip" ]]; then echo "$ip"; return; fi
  echo ""
}

PUBLIC_IP="$(detect_ip)"
if [[ -z "$PUBLIC_IP" ]]; then
  echo "[error] Could not detect public IPv4. Use --ip 1.2.3.4" >&2
  exit 1
fi
if ! [[ "$PUBLIC_IP" =~ ^[0-9]{1,3}(\.[0-9]{1,3}){3}$ ]]; then
  echo "[error] Detected IP doesn't look like IPv4: $PUBLIC_IP" >&2
  exit 1
fi

echo "[info] Domain: $DOMAIN"
echo "[info] Public IPv4: $PUBLIC_IP"
echo "[info] TTL: $TTL"

# Fetch current records
TMP_CUR=$(mktemp)
curl -s --max-time 15 -H "X-API-Key: $SPACESHIP_API_KEY" -H "X-API-Secret: $SPACESHIP_API_SECRET" \
  "$BASE/dns/records/$DOMAIN?take=100&skip=0" -o "$TMP_CUR"

echo "[info] Current records:"
python3 -m json.tool "$TMP_CUR" | sed 's/^/  /' || cat "$TMP_CUR"

# Build desired items: keep all non-@-A records, replace @ A with PUBLIC_IP
# Spaceship API PUT replaces entire list, so we must reconstruct.
TMP_NEW=$(mktemp)
python3 - "$TMP_CUR" "$PUBLIC_IP" "$TTL" "$TMP_NEW" <<'PY'
import json, sys
cur_path, public_ip, ttl, out_path = sys.argv[1:5]
ttl = int(ttl)
with open(cur_path) as f:
    data = json.load(f)
items = data.get("items", [])
# keep everything except @ A records
kept = [r for r in items if not (r.get("type")=="A" and r.get("name")=="@")]
# add the single @ A we want
kept.append({"type":"A","name":"@","address": public_ip, "ttl": ttl})
# spaceship API expects each item with type,name,address,ttl
# Remove group/other server-added fields if present, keep only allowed keys
clean = []
for r in kept:
    entry = {"type": r["type"], "name": r["name"], "address": r["address"], "ttl": int(r.get("ttl", ttl))}
    # preserve optional group? not needed on PUT
    if r.get("type") in ("CNAME","MX","TXT","AAAA","NS","SRV","CAA"):
        # for non-A, keep address/value shape: spaceship uses address for all
        pass
    clean.append(entry)
with open(out_path, "w") as out:
    json.dump({"items": clean}, out, indent=2)
print(json.dumps({"kept_non_A": len(kept)-1, "total": len(clean)}, indent=2))
PY

echo "[info] Desired records (PUT payload):"
cat "$TMP_NEW" | python3 -m json.tool | sed 's/^/  /'

# Check if already up to date
if python3 -c "
import json
with open('$TMP_CUR') as f: cur=json.load(f)
with open('$TMP_NEW') as f: new=json.load(f)
# normalize for comparison
def key(r): return (r['type'],r['name'],r['address'])
cur_set=set(key(r) for r in cur.get('items',[]) if r['type']=='A' and r['name']=='@')
new_set=set(key(r) for r in new['items'] if r['type']=='A' and r['name']=='@')
import sys; sys.exit(0 if cur_set==new_set else 1)
"; then
  echo "[info] DNS already points @ A -> $PUBLIC_IP — nothing to do."
  rm -f "$TMP_CUR" "$TMP_NEW"
  exit 0
fi

if [[ "$DRY_RUN" == "1" ]]; then
  echo "[dry-run] Would PUT above payload to $BASE/dns/records/$DOMAIN"
  rm -f "$TMP_CUR" "$TMP_NEW"
  exit 0
fi

echo "[info] Updating DNS via PUT $BASE/dns/records/$DOMAIN ..."
HTTP_CODE=$(curl -s -o /tmp/spaceship_put_resp.json -w "%{http_code}" --max-time 15 \
  -X PUT -H "X-API-Key: $SPACESHIP_API_KEY" -H "X-API-Secret: $SPACESHIP_API_SECRET" \
  -H "Content-Type: application/json" \
  -d @"$TMP_NEW" \
  "$BASE/dns/records/$DOMAIN" || true)

echo "[info] HTTP $HTTP_CODE"
cat /tmp/spaceship_put_resp.json 2>/dev/null | python3 -m json.tool 2>/dev/null | sed 's/^/  /' || cat /tmp/spaceship_put_resp.json 2>/dev/null | sed 's/^/  /' || true

if [[ "$HTTP_CODE" != "204" && "$HTTP_CODE" != "200" ]]; then
  echo "[error] PUT failed (HTTP $HTTP_CODE). Response above." >&2
  rm -f "$TMP_CUR" "$TMP_NEW"
  exit 1
fi

echo "[info] PUT accepted (HTTP $HTTP_CODE). Waiting 2s then verifying..."
sleep 2
curl -s --max-time 15 -H "X-API-Key: $SPACESHIP_API_KEY" -H "X-API-Secret: $SPACESHIP_API_SECRET" \
  "$BASE/dns/records/$DOMAIN?take=100&skip=0" | python3 -m json.tool | sed 's/^/  /'

echo ""
echo "[info] Checking propagation (dig @launch1.spaceship.net, @8.8.8.8)..."
sleep 1
dig +short "$DOMAIN" @launch1.spaceship.net 2>&1 | sed 's/^/  auth: /' || true
dig +short "$DOMAIN" @8.8.8.8 2>&1 | sed 's/^/  google: /' || true
echo "[info] Done. Allow up to TTL ($TTL s) for full propagation. If using LE, ensure ports 80/443 are forwarded."

rm -f "$TMP_CUR" "$TMP_NEW"
