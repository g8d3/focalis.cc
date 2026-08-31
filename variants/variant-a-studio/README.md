# Focalis Studio — Variant A (Minimal Premium)

**Dodo Payments-ready static site variant for focalis.cc**

Dark, minimal, Linear/Vercel-inspired marketing site. Charcoal `#0A0A0B` + electric blue `#3B82F6`, Inter + JetBrains Mono, huge typography, subtle grid, and restrained motion. Built as pure static HTML/CSS/JS (no build step) so it can be deployed anywhere and passes payment-processor review.

## Quick start

```bash
# serve locally (any static server)
npx serve .
# or
python3 -m http.server 8000
# then open http://localhost:8000
```

No install, no build. Tailwind is loaded via CDN + `assets/css/style.css` and `assets/js/main.js`.

## Pages (all 8 required for Dodo)

| Page | File | Purpose |
|------|------|---------|
| Home | `index.html` | Hero, featured 3 products, principles, social proof |
| Products | `products.html` | 6 products with price, description, features, Buy with Dodo |
| Pricing | `pricing.html` | Pricing grid, comparison table, bundle, FAQ |
| About | `about.html` | Studio story, principles, timeline, legal identity |
| Contact | `contact.html` | Form + direct emails, response SLA, business details |
| Privacy | `privacy.html` | GDPR/Colombia Law 1581-aware privacy policy |
| Terms | `terms.html` | EULA/license, purchase, liability, Colombia governing law |
| Refund | `refund.html` | 14-day no-questions-asked refunds via Dodo |

All pages share the same nav/footer, legal identity, and Dodo merchant-of-record disclosure.

## Design system

- **Background** `#0A0A0B`, card `#141416`, border `#1E1E22`, muted `#9A9AA0`, accent `#3B82F6` / hover `#2563EB`
- **Type** Inter (body/headings), JetBrains Mono (labels/meta)
- **Layout** 1120px max-width, 80px grid, rounded 16–24px cards, pill buttons
- **Motion** `fadeUp` on hero, `reveal` on scroll via IntersectionObserver, hover lift on cards
- **Mobile-first** — nav collapses to hamburger, grids stack, tables scroll horizontally

## Products & pricing (fictional, Dodo placeholders)

| Product | Price | Positioning |
|---------|-------|-------------|
| Flow Engine | $149 | Visual + code workflow automation |
| Capture Kit | $79 | 4K screen/browser capture toolkit |
| Sync Layer | $99 | E2E encrypted bidirectional sync |
| Frame Foundry | $299 | Programmatic video composition engine |
| Signal Desk | $49 | Monitoring + alerts dashboard |
| Vault Core | $19 | Templates & presets starter pack |
| Studio Bundle | $554 | All six (save $140 vs $694) |

Every product card has: name, description, price, “Buy with Dodo” button (currently `alert()` placeholder — replace `href` with your Dodo checkout URL), feature bullets, and license notes. Search for `Buy with Dodo` to wire real URLs.

## Merchant of record

Checkout, VAT/GST, and invoicing are disclosed as handled by **Dodo Payments** everywhere it matters: hero, pricing, product cards, footer, and legal pages. This is intentional for processor review — it shows customers know who charges them and who issues the invoice.

## Legal identity

- **Focalis S.A.S.**, NIT 900.XXX.XXX-1, Bogotá, D.C., Colombia
- Emails: `hello@focalis.cc` · `support@focalis.cc` · `privacy@focalis.cc`
- Legal pages are coherent, non-lorem, and reference Colombia + Dodo + digital-goods delivery. Not legal advice — have counsel review before production.

## Structure

```
variant-a-studio/
├── index.html
├── products.html
├── pricing.html
├── about.html
├── contact.html
├── privacy.html
├── terms.html
├── refund.html
├── assets/
│   ├── css/style.css   # grid, animations, card & button styles
│   └── js/main.js      # mobile menu, reveal-on-scroll, form demo
└── README.md
```

## Customization checklist before launch

- [ ] Replace every “Buy with Dodo” `alert()` with real Dodo checkout links (and bundle)
- [ ] Update NIT, full street address (legal pages + footer + contact), and support hours if needed
- [ ] Wire `contact.html` form to your email/helpdesk (currently local demo confirmation)
- [ ] Add real analytics if desired (update Privacy §6) and favicon/OG image
- [ ] Have legal counsel review Privacy/Terms/Refund for your exact obligations
- [ ] Set up Dodo webhook to deliver license keys (currently described as email delivery)

## Validation

```bash
find . -type f | sort
ls -R
# open each html file and check: nav, footer, Buy buttons, legal links, responsiveness
```

All HTML is static and hand-checked for well-formedness. No build step means no hidden dependencies.

## Variant positioning

Variant A = **Minimal Premium** — the “Linear” option. If you need testing against other directions, Variant B/C could explore editorial/warm or playful/illustrated styles against this baseline.

---

© 2026 Focalis S.A.S. · Built for Dodo Payments review.
