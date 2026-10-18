# Email setup —_pending

> Estado: documentado 2026-08-31, pendiente de activar reenvío + buzón.
> Destino deseado: `CHANGEME@gmail.com` (usuario confirmó)
> Dominio ya en Cloudflare (NS: addilyn / coby) — listo para Email Routing.

## Qué falta (cuando retomes)

1. **Cloudflare Email Routing** (entrante, gratis):
   - Dashboard → focalis.cc → Email → Email Routing → Enable
   - Destination address → `CHANGEME@gmail.com` (verificar vía código que llega a Gmail)
   - Routing rules:
     - `hello@focalis.cc` → `CHANGEME@gmail.com`
     - `contact@focalis.cc` → `CHANGEME@gmail.com`
     - Catch-all → `CHANGEME@gmail.com` (opcional)
   - Verificar que `MX`, `SPF`, `DMARC` queden en `Managed` (Cloudflare lo pone solo).

   Alternativa API (si das token `Zone:DNS:Edit` + `Zone:Email Routing:Edit`):
   ```bash
   curl -X POST https://api.cloudflare.com/client/v4/zones/<zone_id>/email/routing/enable -H "Authorization: Bearer <token>"
   curl -X POST https://api.cloudflare.com/client/v4/zones/<zone_id>/email/routing/addresses -H "Authorization: Bearer <token>" -d '{"email":"CHANGEME@gmail.com"}'
   curl -X POST https://api.cloudflare.com/client/v4/zones/<zone_id>/email/routing/rules -H "Authorization: Bearer <token>" -d '{"matchers":[{"type":"literal","field":"to","value":"hello@focalis.cc"}],"actions":[{"type":"forward","value":["CHANGEME@gmail.com"]}]}'
   ```

2. **Gmail “Enviar como”** (saliente):
   - Gmail → Ajustes (⚙️) → Ver todos los ajustes → Cuentas e importación → `Enviar como` → Añadir otra dirección
   - Nombre: `Focalis` / Email: `hello@focalis.cc` → Desmarcar “Tratar como alias”
   - SMTP: deja que Gmail envíe vía `smtp.gmail.com` con tu cuenta, o pon SMTP de Cloudflare si usas custom
   - Te llega código a `hello@focalis.cc` → lo recibes en `CHANGEME@gmail.com` vía reenvío → verificar
   - Desde entonces puedes elegir “De: hello@focalis.cc” o “De: CHANGEME@gmail.com”.

3. **Conectar formulario** (ya hecho):
   - `contact.html` → `POST /api/contact` → guarda en `logs/contact.jsonl` + intenta SMTP si `SMTP_HOST` está seteado
   - Para que el formulario también te notifique por email, setear en `docker-compose.yml` env para `admin`:
     ```
     - SMTP_HOST=smtp.gmail.com  # o smtp.migadu.com / smtp.zoho.com si usas otro buzón
     - SMTP_PORT=587
     - SMTP_USER=hello@focalis.cc
     - SMTP_PASS=<app-password>
     - SMTP_FROM=hello@focalis.cc
     - CONTACT_TO=CHANGEME@gmail.com
     ```
   - `docker compose restart admin` y probar `curl -X POST http://127.0.0.1:80/api/contact -H "Content-Type: application/json" -d '{"name":"test","email":"t@t.com","message":"hello long enough"}'`

4. **Verificación**:
   - Envía email a `hello@focalis.cc` desde otro Gmail → debe llegar a `CHANGEME@gmail.com` en segundos
   - Responde desde Gmail eligiendo `hello@focalis.cc` → el destinatario ve `hello@focalis.cc`
   - Envía formulario desde `https://focalis.cc/contact.html` → debe llegar notificación (si SMTP) y quedar en `/admin/contacts` (vista privada del admin)

## Estado actual (sin buzón)
- `POST /api/contact` funciona (log + rate limit + honeypot, sin SMTP → solo log)
- Caddy ya proxea `/api/*` → `admin:8788`
- `logs/contact.jsonl` y `/admin/contacts` (requiere login) operativos
- `hello@focalis.cc` aún no recibe email externo (hasta activar Email Routing o comprar buzón)

## Alternativas si no quieres Cloudflare Routing
- **Migadu Mini ($19/año)**: buzón real, mejor entregabilidad que Gmail alias. Requiere cambiar `MX` en Cloudflare a `aspmx1.migadu.com` etc.
- **Zoho Mail (gratis)**: similar, `MX` → `mx.zoho.com`
- Ambos dan SMTP directo para el formulario.

---
Cuando quieras retomar, dame un token Cloudflare con `Zone:DNS:Edit` + `Zone:Email Routing:Edit` para `focalis.cc` y lo dejo reenviando en <2 min.
