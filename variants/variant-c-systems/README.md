# Focalis Systems — Variant C (Enterprise Trust)

**Location:** `sites/focalis.cc/variants/variant-c-systems/`
**Positioning:** B2B systems integrator — *Infrastructure for ambitious teams*
**Goal:** Pass [Dodo Payments](https://dodopayments.com) merchant review on first submission.

---

## Why this variant is the most "approvable"

Dodo (and similar merchants of record) approve sites that look like real businesses with real products, clear pricing, reachable support, and honest legal pages. Variant C is deliberately conservative and boring — in the way procurement teams and payment reviewers like:

- **Real products, real prices, real commitments** — every product has a name, what it does, who it is for, a price in USD, an SLA, seats/volume limits, and a "Buy with Dodo" checkout placeholder.
- **Pricing is explicit** — $49 / $199 / $349 / $499 and Enterprise from $999, with monthly and annual, overage rates, and a comparison matrix. Taxes noted as "calculated at checkout by Dodo Payments."
- **Dodo Payments is named as merchant of record** in the footer, product cards, pricing table, and in three legal pages — reviewers can see the invoicing path without hunting.
- **Contact is reachable** — legal entity, Paris address, three email addresses, phone with hours, support response targets, and a contact form. No anonymous operation.
- **Legal pages are enterprise-grade** — Privacy (with DPA, sub-processors, SCCs, retention, 14-day sub-processor notice), Terms (license vs. service, SLA with credits, billing via Dodo), and Refund (14-day on new licenses, clearly scoped, with examples).
- **Design is enterprise-credible** — light mode, navy #0F2342 + teal #14B8A6 + warm stone, IBM Plex Sans/Serif/Mono, whitespace, trust strips, live-status-style table, and testimonial placeholders that do not pretend to be more than they are.

No lorem ipsum. No p4/p3 references. No hype.

---

## Pages (all required for Dodo)

| File | Purpose |
|---|---|
| `index.html` | Hero, live-status table, trust strip, 3 product previews, How it works, testimonials, compliance + sub-processor summary, FAQ, CTA |
| `products.html` | Full detail for Data Pipeline / Automation Suite / Integration Layer — capability tables, volumes, SLAs, feature lists, Buy with Dodo, comparison matrix, Enterprise banner |
| `pricing.html` | Monthly/annual toggle, 4 plan cards, feature matrix, Enterprise custom scope, billing FAQ (tax, cancellation, overage, refunds, wire) |
| `about.html` | Positioning, at-a-glance entity facts, principles, timeline, team (no stock photos), careers |
| `contact.html` | Form (demo handler), direct channels (contact@ / support@ / legal@ / phone + hours), support response table, billing/MoR note, registered address |
| `privacy.html` | Controller + processor roles, data categories, lawful bases, sharing, **sub-processor table**, DPA (SCCs), transfers, retention, security, rights (GDPR), changes |
| `terms.html` | Licensed-software grant, products & pricing table, accounts/acceptable use, **Dodo as MoR**, subscription/overage/taxes, delivery/SLA with credits, IP/confidentiality |
| `refund.html` | 14-day on new licenses (with example), renewals/annual/overage, Enterprise terms, how to request, processing/timing, cancellation vs. refund, statutory rights |

Plus shared `assets/css/style.css` and `assets/js/main.js`.

---

## Products

| Product | Plan | Price (USD) | SLA | Volume included | Overage | Seats |
|---|---|---|---|---|---|---|
| **Data Pipeline** | Team | $199 / mo | 99.9% | 50M events | $0.18 / 1k | 12 |
| **Automation Suite** | Business | $349 / mo | 99.9% | 500k runs | $0.12 / 1k | 25 |
| **Integration Layer** | Starter | $49 / mo | 99.5% | 100k API calls | $0.08 / 1k | 5 |
| **Integration Layer** | Pro | $499 / mo | 99.9% | 1M API calls | $0.08 / 1k | 12 |
| Any | **Enterprise** | From $999 / mo | 99.95% | Custom | Custom | Custom |

- Single-product or suite purchase. Annual saves ~17% (two months free).
- Each product card: name, who it is for, description, price, `Buy with Dodo` button (`data-dodo-checkout`), SLA, support target, seats, and feature list.
- Overage is capped; taxes calculated at checkout by Dodo Payments.

---

## Legal entity and merchant of record

- **Legal entity:** Focalis Technologies S.A.S. — 12 Rue de la Paix, 75002 Paris, France — `contact@focalis.cc` · `support@focalis.cc` · `legal@focalis.cc` · +33 1 23 45 67 89 — VAT FR12345678901 (example; replace with real when live).
- **Merchant of record:** **Dodo Payments** — handles checkout, payment, VAT/GST, invoicing, and refund processing. Called out in footer, pricing, product cards, and legal pages. Billing portal linked from receipts.
- **Sub-processors:** Dodo Payments (MoR), cloud hosting (EU Frankfurt primary, US Virginia optional), email delivery (EU), error monitoring (EU), support desk (EU) — with 14-day change notice and DPA/SCCs.
- **Refund:** 14 calendar days from initial purchase for new licenses; renewals not individually refundable; annual refund is whole-year within 14 days; Enterprise per order form (default 30-day acceptance with pro-rata).

Effective date on legal pages: **1 March 2026**.

---

## Design system

- **Mode:** Light, paper-like (`#FAF9F7` background, white cards, `#E8E4DE` borders).
- **Palette:** Navy `#0F2342` (primary), Teal `#14B8A6` (accent, CTAs, badges), Warm stone (`#FAF9F7 / #F5F3EF / #E8E4DE / #D6D0C4`), Ink `#1A1E2A` / muted `#5B6476`.
- **Typography:** IBM Plex Sans (body/UI), IBM Plex Serif (headlines), IBM Plex Mono (prices, data tables) — via Google Fonts.
- **Framework:** Tailwind CDN + `assets/css/style.css` (cards, buttons, badges, tables, legal prose, form). No build step.
- **Traits:** Sticky blurred header, hero gradient, data tables (uptime, plan matrix), trust strip (EU residency, GDPR, Dodo, 14-day refund), metric cards, and reveal-on-scroll.

---

## Tech

- **Stack:** Static HTML/CSS/JS only. Tailwind CDN, no bundler, no backend required.
- **Responsive:** Mobile-first; hamburger menu at `lg` breakpoint, stacked cards on mobile.
- **JS:** `assets/js/main.js` — mobile menu, reveal-on-scroll, pricing toggle (monthly/annual), FAQ accordion, contact form demo handler, Dodo checkout placeholder toast (no real redirect yet).
- **Checkout placeholder:** Every `Buy with Dodo` button has `data-dodo-checkout` + `data-product` — wired to a toast. Replace with the real Dodo Payments checkout URL / SDK when ready (search `data-dodo-checkout` in each HTML file).
- **No external dependencies at runtime** beyond Tailwind CDN and Google Fonts — both replaceable with vendored files for air-gapped review.

---

## Running locally

```bash
# from the variant root
python3 -m http.server 8000
# then open http://localhost:8000/
# or
npx serve .
```

All links are relative — works from any static host (Cloudflare Pages, Vercel, S3, etc.) or file:// (with minor font/CDN caveats).

---

## Before Dodo submission — checklist

- [ ] Replace example VAT / phone / SIREN with real values where you have them.
- [ ] Wire each `data-dodo-checkout` button to the real Dodo Payments checkout link or SDK (one link per product/plan).
- [ ] Host at `focalis.cc` with HTTPS and confirm every nav/footer link resolves (no 404s — payment reviewers click them).
- [ ] Add real product docs / changelog links if you have them (placeholder: "documentation" is referenced throughout).
- [ ] If you add analytics or non-essential cookies, add a consent banner — current static variant sets none.
- [ ] Set `Effective` / `Last updated` dates to your actual go-live date if different from 1 March 2026.

---

## File map

```
variant-c-systems/
├── index.html
├── products.html
├── pricing.html
├── about.html
├── contact.html
├── privacy.html
├── terms.html
├── refund.html
├── README.md
└── assets/
    ├── css/style.css
    └── js/main.js
```
