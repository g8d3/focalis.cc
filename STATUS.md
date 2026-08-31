# focalis.cc — Build Status (2026-04-14 — while you sleep)

## ✅ Finished (5/5 agents)

| Agent | Output | Status |
|-------|--------|--------|
| Design Research | REQUIREMENTS.md + CONCEPTS.md | ✅ Done |
| Variant A — Studio | variants/variant-a-studio/ (8 pages) | ✅ Done |
| Variant B — Labs | variants/variant-b-labs/ (8 pages) | ✅ Done |
| Variant C — Systems | variants/variant-c-systems/ (8 pages) | ✅ Done |
| Infra — Docker + Caddy + Spaceship | docker-compose.yml + Caddyfile + scripts | ✅ Healthy |

## 🔍 Preview Right Now (local, no DNS needed)
```bash
curl http://127.0.0.1:80/          # Studio (default at /)
curl http://127.0.0.1:80/studio/   # Studio variant
curl http://127.0.0.1:80/labs/     # Labs variant
curl http://127.0.0.1:80/systems/  # Systems variant
# Or browser: http://192.168.0.93/studio/ etc
docker compose -f /home/vuos/code/p4/sites/focalis.cc/docker-compose.yml ps
```

## ⏳ Pending for Public HTTPS (needs 2 min when you wake)
1. Point DNS to this machine: `cd sites/focalis.cc && ./scripts/update-dns.sh` (sets @ A → 186.87.104.116)
2. Router: forward TCP 80/443 + UDP 443 → 192.168.0.93
3. `sudo ufw allow 80,443/tcp && sudo ufw allow 443/udp` if UFW active
4. Wait 2-5 min → Caddy auto-issues Let's Encrypt certs → https://focalis.cc live

See INFRA.md for full details.
