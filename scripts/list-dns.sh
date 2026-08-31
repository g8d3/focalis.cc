#!/usr/bin/env bash
# list-dns.sh — Show current Spaceship DNS records for focalis.cc
# Auth via SPACESHIP_API_KEY + SPACESHIP_API_SECRET env vars (.env or shell)
set -euo pipefail
DIR="$(cd "$(dirname "$0")/.." && pwd)"
if [[ -f "$DIR/.env" ]]; then set -a; source "$DIR/.env"; set +a; fi

DOMAIN="${DOMAIN:-focalis.cc}"
BASE="https://spaceship.dev/api/v1"

if [[ -z "${SPACESHIP_API_KEY:-}" || -z "${SPACESHIP_API_SECRET:-}" ]]; then
  echo "Missing SPACESHIP_API_KEY / SPACESHIP_API_SECRET" >&2
  echo "Set them in $DIR/.env or env" >&2
  exit 1
fi

echo "=== Domain: $DOMAIN ==="
curl -s -H "X-API-Key: $SPACESHIP_API_KEY" -H "X-API-Secret: $SPACESHIP_API_SECRET" \
  "$BASE/domains/$DOMAIN" | python3 -m json.tool || true

echo ""
echo "=== DNS records (GET /dns/records/$DOMAIN?take=100&skip=0) ==="
curl -s -H "X-API-Key: $SPACESHIP_API_KEY" -H "X-API-Secret: $SPACESHIP_API_SECRET" \
  "$BASE/dns/records/$DOMAIN?take=100&skip=0" | python3 -m json.tool

echo ""
echo "=== Public DIG ==="
dig +short "$DOMAIN" @8.8.8.8 2>&1 | sed 's/^/A: /'
dig +short "$DOMAIN" @launch1.spaceship.net 2>&1 | sed 's/^/Auth-A: /' || true
curl -4 -s --max-time 5 https://api.ipify.org 2>&1 | sed 's/^/Public-IPv4: /' || true
curl -6 -s --max-time 5 ifconfig.me 2>&1 | sed 's/^/Public-IPv6: /' || true
