# Focalis — variant-d-world (World)

> Single source of truth for personal values: `site.config.json` + `assets/js/site-config.js`

## Personal values — edit here, not scattered

All personal data is centralized in **one variable**:

- **JSON** (for tooling/docs): `site.config.json`
- **JS** (for runtime): `assets/js/site-config.js` → `window.FOCALIS_CONFIG`

```json
{
  "contact": {
    "primaryEmail": "hello@focalis.cc",   // ← change once
    "supportEmail": "contact@focalis.cc"
  },
  "company": {
    "legalName": "Focalis S.A.S.",
    "location": "Bogotá, Colombia"
  },
  "private": {
    "forwardTo": "CHANGEME@gmail.com"   // ← never injected to HTML, only backend
  }
}
```

### How it updates HTML

Every email/company in HTML has a fallback *and* a `data-config` attribute:

```html
<a href="mailto:hello@focalis.cc" data-config="contact.primaryEmail" data-config-href="contact.primaryEmail">hello@focalis.cc</a>
<span data-config="company.legalName">Focalis S.A.S.</span>
```

- **Crawlers** (Dodo, Google) see the fallback text without JS — still passes verification.
- **Browsers** load `site-config.js` before `main.js` and auto-replace `textContent`/`href` from `window.FOCALIS_CONFIG`.
- Change `site.config.json` → copy values to `site-config.js` → reload page (or run sync below to update fallback text for no-JS crawlers).

### Sync fallback text (optional, for perfect no-JS)

If you change the email and want the *fallback* HTML text to also update (so crawlers see new value even without JS):

```bash
cd variants/variant-d-world
node assets/js/site-config.js --sync   # shows JSON
# or manual: edit HTML fallback text to match new email
```

Or use the helper:

```bash
../../scripts/sync-config.sh variant-d-world
```

### What was extracted

- `hello@focalis.cc` (8→ now via `contact.primaryEmail`)
- `contact@focalis.cc` (4→ via `contact.supportEmail`)
- `CHANGEME@gmail.com` (private, only in `private.forwardTo`, never in HTML)
- `Focalis S.A.S.` + `Bogotá, Colombia` (via `company.legalName` / `company.location`)
- `Caddyfile: email hello@focalis.cc` — still separate (Let's Encrypt account). Change there + in config if you change domain email.

### Files

- `site.config.json` — source of truth
- `assets/js/site-config.js` — runtime variable + auto-injector
- `assets/css/style.css` — enhanced 3D/video/images
- `index.html` — hero with visible Three.js (Torus, Knot, Icosahedron, particles) + video-hero 380px + large image stories
- `EMAIL_TODO.md` at `sites/focalis.cc/EMAIL_TODO.md` — pending Cloudflare Email Routing steps
