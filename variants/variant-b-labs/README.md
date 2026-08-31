# Focalis Labs — Variant B (Bold Experimental)

> **We build tools for builders.** A bold, experimental storefront for Focalis Labs — the lab aesthetic variant of focalis.cc, designed to pass Dodo Payments review.

**Live variant:** `/variants/variant-b-labs/`  
**Design direction:** Deep void violet (`#0F0A1E`), neon lime (`#C6FF00`) + magenta (`#FF006E`) + cyan (`#00E5FF`) accents, glass morphism, bento grids, gradient-heavy 2026 lab aesthetic.

---

## Pages (8/8 — all Dodo-required)

| Page | File | Purpose |
|------|------|---------|
| Home | `index.html` | Hero, bento product teaser, stats, CTA |
| Products | `products.html` | 6 kits with full detail + bundle |
| Pricing | `pricing.html` | 3 tiers, comparison table, FAQ |
| About | `about.html` | Story, values, team, legal entity |
| Contact | `contact.html` | Contact info + functional form |
| Privacy Policy | `privacy.html` | GDPR/CCPA-aware, Dodo as MoR disclosed |
| Terms of Service | `terms.html` | License, disclaimers, governing law (DE) |
| Refund Policy | `refund.html` | 14-day no-questions-asked, digital goods |

All pages share a consistent nav/footer and are responsive (mobile-first) with hover states.

## Design System

- **Typography:** `Syne` (headlines, 800) + `Space Grotesk` (body) via Google Fonts
- **Background:** `#0F0A1E` void with radial gradient blobs (violet/magenta/lime)
- **Glass:** `rgba(255,255,255,0.06)` + `backdrop-blur(16px)` + `1px solid rgba(255,255,255,0.09)`
- **Accents:** Lime for primary CTAs, magenta for trading, cyan for voice
- **Layout:** 12-col bento grids, `rounded-[28px]` cards, pill buttons (`rounded-full`)
- **No build step:** Static HTML/CSS/JS only. Tailwind via CDN (`https://cdn.tailwindcss.com`) + inline config

## Products (priced $29–$499)

| Kit | Price | Tagline |
|-----|-------|---------|
| **HyperCapture** | $149 | Browser-native 4K capture & video assembly |
| **Signal Grid** | $299 | Volume-profile S/R with capital redistribution |
| **Voice Forge** | $79 | Studio voices that don't sound like AI |
| **Frame Engine** | $99 | Programmatic video — HTML is your timeline |
| **Prompt Forge** | $29 | Prompt management for production agents |
| **Data Lens** | $49 (was $99) | Turn any API into a live dashboard |
| **Builder Bundle** | $499 | All 6 kits + every new kit in 2026 (save 40%) |

Each product on `products.html` includes: name, description, price, **"Buy with Dodo"** placeholder button, feature list, and use cases. Bundle savings and comparison table on `pricing.html`.

## Copy Principles

- Tagline: *"We build tools for builders"* — no mention of p4/p3 internal names
- Generic, product-led positioning (AI creative & automation kits)
- No lorem ipsum — all copy is real English, written for builders/designers/traders
- Tone: confident, lab-like, slightly irreverent ("A lab, not a store.")

## Legal & Dodo Compliance

- **Entity:** Focalis Labs LLC — 8 The Green STE B, Dover, DE 19901, USA
- **Contact:** `hello@focalis.cc` (sales) / `support@focalis.cc` (support & refunds)
- **Merchant of record:** Dodo Payments disclosed on every page (footer + pricing/terms/privacy/refund)
- **Privacy:** Covers Dodo as MoR, processors, retention, rights (GDPR/CCPA), cookies (essential-only)
- **Terms:** License (perpetual, commercial allowed), acceptable use, no financial advice disclaimer, liability, DE governing law
- **Refund:** 14-day no-questions-asked on digital goods, 48h processing via Dodo, license revocation, tax handling

## Tech

- Static files only — no bundler, no framework, no backend
- Tailwind CDN + custom `<style>` for glass/glow/gradients
- Vanilla JS for mobile menu + contact form (mock success state)
- All internal links are relative (`index.html`, `products.html`, etc.)

## How to Preview

```bash
# from repo root
npx serve sites/focalis.cc/variants/variant-b-labs
# or
python3 -m http.server --directory sites/focalis.cc/variants/variant-b-labs 8000
```

Open `index.html` and navigate via the top nav.

## Distinct from Variant A

Variant B is intentionally maximalist where Variant A is expected to be minimal: bento grids instead of linear lists, glass morphism + neon gradients instead of flat neutrals, `Syne` display type instead of a subdued sans, and a lab/experimental narrative instead of a clean commerce narrative. Same 8-page IA and compliance surface, completely different visual language.
