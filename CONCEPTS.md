# focalis.cc — Three Brand Concepts

> Design Research agent — 2026-08-31
> Domain: `focalis.cc` · Tech emprendimiento · Generic/abstract positioning (no p4/p3/p2/p1 mentions)

All three variants share the **same compliance skeleton** (see §4 Site Maps). Differentiation is in tokens, voice, and product framing. Any single variant can be built and submitted to Dodo Payments as-is.

---

## Variant A — Focalis Studio

> **Tagline:** `Tools that stay out of the way.`
> **Positioning:** Minimal premium tech studio — the Linear.app / Vercel lineage. Quiet, precise, crafted. Sells automation tools & workflows to founders, solo builders, and small teams who value speed and restraint.

### Personality

Calm, exacting, opinionated about simplicity. Speaks in short sentences. No hype. The kind of studio that ships a changelog, not a manifesto. Audience: developers, designers, indie hackers who already know what they want and just want it to work.

**Voice:** understated, verbs-first, second-person sparingly. Example: *"Automate the busywork. Keep the craft."*

**Mood board:** Linear home + Vercel docs + Stripe Sessions stage design. Lots of whitespace, hairline borders, a single violet accent that only appears when it means something.

### Color Palette

| Token | Hex | Usage |
|-------|-----|-------|
| `bg` | `#0A0A0B` | Page background (dark default) |
| `surface` | `#141416` | Cards, sections |
| `surface-2` | `#1C1C1F` | Hover / elevated |
| `border` | `#232326` | Hairlines, dividers |
| `text` | `#F4F4F5` | Primary text |
| `muted` | `#9F9FA9` | Secondary, labels |
| `faint` | `#71717B` | Tertiary, metadata |
| `accent` | `#7C5CFF` | CTA, link, focus |
| `accent-2` | `#A78BFA` | Accent hover / highlight |
| `success` | `#10B981` | Checkmarks, badges |
| `light-bg` (toggle) | `#FCFCF9` | Light mode background |
| `light-text` | `#18181B` | Light mode text |

Tailwind mapping: `zinc` base + `violet` accent. Radius: `12px` cards, `8px` buttons. Shadow: almost none — border does the work.

### Typography

- **Display / Headings:** `Geist Sans` (or `Inter` fallback) — weight 600-700, tracking `-0.03em`, leading `0.95–1.1`. Hero 56-64px desktop.
- **Body:** `Inter` 15-16px, leading `1.6`, color `muted` for long copy, `text` for emphasis.
- **Mono / Labels:** `Geist Mono` (or `JetBrains Mono`) — 12-13px, uppercase, tracking `0.08em` for section labels ("PRODUCTS", "PRICING").
- **Scale:** 12 / 14 / 16 / 20 / 28 / 40 / 56 px.

### Visual Language

- Grid: 12-col, max `1120px`, generous gutters (32-48px). Bento cards, 1px border, no drop shadows.
- Imagery: abstract line diagrams, monochrome screenshots with violet highlight, subtle grain (`opacity 0.03`) behind hero.
- Iconography: `lucide` outline, 18px, stroke 1.5.
- Motion: fade-up 180ms, blur 4px → 0, stagger 40ms on card grids. No parallax.
- Photography: none. If a face is needed, use abstract avatar or keep it typographic.

### Products (generic but sellable, automation & workflows)

| Product | Description (Dodo one-sentence) | Deliverable |
|---------|----------------------------------|-------------|
| **Flow Kit — Starter** | Prebuilt automation workflows for solo founders (content → publish pipelines). | Notion + scripts + video walkthrough, single license |
| **Flow Kit — Pro** | Extended workflow library with scheduling, webhooks, and API connectors. | Above + private repo access + updates 12 mo |
| **Inbox Zero System** | Email triage and drafting automation pack (rules, templates, filters). | Templates + setup guide + 30-min onboarding call |
| **Publish Pipeline** | Markdown → site → social scheduling kit (static site + queue). | Boilerplate + scripts + docs |
| **Studio Pass (bundle)** | All workflow kits + future drops for 12 months. | Subscription, monthly |

### Pricing Tiers

| Tier | Price (USD) | Model | Includes |
|------|-------------|-------|----------|
| **Starter** | $49 | One-time | 1 kit of choice, docs, community access |
| **Pro** | $129 | One-time | Any 2 kits, private repo, 12 mo updates |
| **Studio Pass** | $19/mo or $149/yr | Subscription | All kits, all future drops, priority support |
| **Team** | $39/mo (up to 5 seats) | Subscription | Studio Pass + seat sharing + onboarding call |

Fulfillment: instant license via email + private link after payment (Dodo checkout). Refund: 14 days if not activated / downloaded (see Refund page).

### Site Map

```
Home          → hero + social strip + 3 featured products + pricing teaser + FAQ + footer
Products      → full catalog (cards with what's included, requirements, screenshots)
Pricing       → tier comparison table + FAQ + CTA
About         → studio story, principles, who it's for, not who it's not
Contact       → email + form + response time
Privacy       → data, cookies, MoR disclosure
Terms         → license, subscription renewal, fair use
Refund        → window, process, digital-goods clause
404           → minimal, on-brand, back to home
```

---

## Variant B — Focalis Labs

> **Tagline:** `Experiments you can ship.`
> **Positioning:** Bold experimental lab — optimistic, slightly chaotic, builder-joy energy. Sells AI tools, browser automation, and video generation kits to creators, AI tinkerers, and small agencies who want an edge, not a suite.

### Personality

Curious, generous, a little irreverent. Ships in public, documents the mess, celebrates the demo. Audience: AI-curious developers, video creators, automation nerds, agency owners stitching stacks together.

**Voice:** energetic, first-person plural, concrete nouns. Example: *"We break browsers so you don't have to — then we box the fix and ship it."*

**Mood board:** Perplexity lab notes + Vercel's bright accent moments + 2026 "warm tech" palette (cream, amber, charcoal). Editorial, collage-friendly, not corporate.

### Color Palette

| Token | Hex | Usage |
|-------|-----|-------|
| `bg` | `#FFF9F0` | Page background (warm light default) |
| `surface` | `#FFFFFF` | Cards |
| `surface-2` | `#F5EFE6` | Subtle section bg |
| `border` | `#E8DDD0` | Hairlines |
| `ink` | `#1A1A1E` | Primary text |
| `muted` | `#6B6570` | Secondary |
| `accent` | `#FF4D00` | CTA, highlight (signal orange) |
| `accent-2` | `#FFB800` | Amber accent, badges |
| `accent-3` | `#7C5CFF` | Violet for code / AI tags |
| `dark-bg` (toggle) | `#111113` | Dark mode bg |
| `dark-surface` | `#1A1A1E` | Dark cards |
| `dark-border` | `#2A2A2E` | Dark hairlines |
| `dark-text` | `#FFF9F0` | Dark primary |

Tailwind mapping: warm `stone/amber` base + `orange` primary + `violet` secondary. Radius: `16px` cards, `9999px` pills for tags. More playful than Studio.

### Typography

- **Display / Headings:** `Sora` or `General Sans` (or `Syne`) — weight 700-800, tracking `-0.02em`, slightly wider than Studio. Hero 56-72px with a rotated accent word.
- **Body:** `Instrument Sans` or `Inter` 16px, leading `1.65`, ink on cream.
- **Mono / Labels:** `JetBrains Mono` 12px uppercase for lab tags ("EXPERIMENT 04 — BROWSER", "KIT · VIDEO").
- **Scale:** 12 / 14 / 16 / 20 / 30 / 44 / 64 px. More contrast than Studio.

### Visual Language

- Grid: 12-col, max `1200px`, editorial overlaps — hero type bleeds into card grid.
- Imagery: screenshots withBrowser chrome, terminal snippets, video thumbnails, hand-drawn arrows Underlining a headline word.
- Iconography: filled + outline mix, larger (20-22px), amber/orange fills.
- Motion: slightly more — card tilt on hover (2deg), marquee strip for "AI · AUTOMATION · VIDEO · BROWSER" loop.
- Grain: warmer, slightly stronger (`opacity 0.06`), cream paper texture.

### Products (generic but sellable, AI / browser / video kits)

| Product | Description (Dodo one-sentence) | Deliverable |
|---------|----------------------------------|-------------|
| **Browser Kit** | Headless browser automation recipes for scraping, testing, and capture. | Scripts + Docker image + docs, single license |
| **AI Video Kit** | Prompt → render pipeline for short-form video (scripts → frames → export). | Boilerplate + presets + walkthrough |
| **Capture Pack** | Screen/broadcast capture tools with cue overlays and segment control. | CLI + configs + sample project |
| **Agent Inbox** | Inbound automation: trigger → classify → act (email, webhook, chat). | Templates + webhook kit + guide |
| **Labs All-Access** | Every kit + monthly new experiment drop. | Subscription |

### Pricing Tiers

| Tier | Price (USD) | Model | Includes |
|------|-------------|-------|----------|
| **Single Kit** | $59 | One-time | 1 kit, docs, updates 6 mo |
| **Two Kits** | $99 | One-time | Any 2 kits, updates 12 mo |
| **All-Access** | $29/mo or $199/yr | Subscription | All kits, monthly drops, Discord/priority support |
| **Agency** | $79/mo (up to 10 seats) | Subscription | All-Access + white-label snippets + onboarding |

Fulfillment: instant download + repo invite after payment. Refund: 14 days if not downloaded / repo not accessed.

### Site Map

```
Home          → bold hero (rotated accent) + marquee + featured kits + pricing teaser + lab log (3 recent experiments) + FAQ + footer
Products      → kits catalog with tags (AI · Browser · Video · Automation), difficulty, stack, preview
Pricing       → tier cards + comparison + FAQ
About         → lab story, "how we build", principles, who it's for
Contact       → email + form + response time + lab hours note
Privacy       → same depth as Studio, warm tone but legally identical substance
Terms         → license, sub terms, fair use, redistribution limits
Refund        → window, process, access-based clause
404           → playful, on-brand ("This experiment hasn't been run yet.")
```

---

## Variant C — Focalis Systems

> **Tagline:** `Infrastructure you can trust.`
> **Positioning:** Enterprise-trustworthy — calm, credible, built for buyers who need to brief their boss. Sells consulting, integration services, and SaaS to startups graduating to scale and SMEs buying outcomes, not tools.

### Personality

Steady, expert, low-ego. Speaks in outcomes and service levels. Assumes the reader is smart and busy. Audience: founders hiring integration help, ops leads, teams that want a vendor with a phone number and an SLA.

**Voice:** third-person / institutional, measured. Example: *"We integrate, automate, and support the systems your business already runs on."*

**Mood board:** Stripe enterprise + Linear "Enterprise" page + Wise (fintech trust) — navy, white, restrained blue accent, data-dense but calm. Lots of proof: process steps, SLAs, scope tables.

### Color Palette

| Token | Hex | Usage |
|-------|-----|-------|
| `bg` | `#FFFFFF` | Page background (light default) |
| `surface` | `#F8F9FB` | Subtle section bg |
| `surface-2` | `#EEF1F6` | Cards, table header |
| `border` | `#DFE3EA` | Hairlines, table borders |
| `ink` | `#0F1A2E` | Primary text (navy, not black) |
| `muted` | `#5B6B85` | Secondary |
| `accent` | `#0A4DFF` | Primary CTA, links (trust blue) |
| `accent-hover` | `#083CD6` | Hover |
| `accent-soft` | `#EDF2FF` | Accent bg wash |
| `success` | `#0E7C3E` | SLA met, checkmarks |
| `warning` | `#9A6B00` | Limited scope note |
| `dark-bg` (toggle) | `#0F1A2E` | Dark mode bg (navy) |
| `dark-surface` | `#162544` | Dark cards |
| `dark-border` | `#243656` | Dark hairlines |
| `dark-text` | `#F8F9FB` | Dark primary |

Tailwind mapping: `slate` base + `blue` accent. Radius: `8px` cards, `6px` buttons — more conservative than Labs, sharper than Studio. Shadow: subtle `0 1px 2px rgba(15,26,46,0.06)`.

### Typography

- **Display / Headings:** `Instrument Sans` or `Inter` — weight 600, tracking `-0.02em`, leading `1.05`. Hero 48-56px (smaller than Labs — restraint is the flex).
- **Body:** `Inter` 15px, leading `1.65`, muted for body, ink for headings.
- **Mono / Labels:** `JetBrains Mono` 12px uppercase for meta ("SERVICE · INTEGRATION", "SLA 24H").
- **Scale:** 12 / 14 / 15 / 18 / 24 / 36 / 48 px. Tight, editorial-free.

### Visual Language

- Grid: 12-col, max `1120px`, classic marketing sections (no editorial overlap). Generous vertical padding (80-96px sections).
- Imagery: product screenshots in browser frames, architecture diagrams (clean lines, navy + blue), headshot placeholders (if needed, use initials avatar — no fake faces).
- Iconography: outline, 16-18px, stroke 1.5, blue on light wash circles.
- Motion: minimal — fade only, no tilt/marquee. Feels stable.
- Proof elements: process timeline (01 → 02 → 03), SLA table, scope comparison, testimonial-ready block (empty until real quotes exist — no lorem testimonials).

### Products (generic but sellable, consulting + integration + SaaS)

| Product | Description (Dodo one-sentence) | Deliverable |
|---------|----------------------------------|-------------|
| **Integration Sprint** | 2-week integration of your stack (CRM, payments, automations) scoped and delivered. | Scoping call + build + handover docs, fixed price |
| **Automation Retainer** | Monthly automation maintenance, monitoring, and iteration. | Hours + SLA, subscription |
| **Systems Audit** | Review of current workflows and tooling with prioritized roadmap. | Report + roadmap + call, one-time |
| **Focalis Cloud (SaaS)** | Hosted automation runner with scheduling, logs, and alerts. | SaaS subscription (hosted) |
| **Priority Support** | SLA-backed support for your Focalis deliverables. | Add-on to any tier |

### Pricing Tiers

| Tier | Price (USD) | Model | Includes |
|------|-------------|-------|----------|
| **Audit** | $299 | One-time | Systems audit report + 60-min call + roadmap |
| **Sprint** | $1,200 | One-time (per sprint) | 2-week integration sprint, fixed scope, handover |
| **Cloud Starter** | $29/mo or $290/yr | Subscription | Hosted runner, 5 workflows, email support |
| **Cloud Pro** | $79/mo or $790/yr | Subscription | 20 workflows, priority support, SLA 24h |
| **Retainer** | $600/mo | Subscription | 10h/mo + monitoring + iteration |

For Dodo verification, the SaaS tiers (Cloud Starter/Pro) are the primary "products with clear price" — consulting sprints are also priced transparently so the crawler sees no "contact for pricing" dead end. Fulfillment: audit/sprint = scheduling link after payment; SaaS = account creation within 24h (stated). Refund: 14 days on SaaS if unused; sprints refundable before kickoff, not after work starts (clearly stated).

### Site Map

```
Home          → trust hero + credibility strip (stack logos as text, no fake marks) + services + process (3 steps) + pricing teaser + FAQ + footer
Products/Services → service catalog + scope tables + what happens after payment per item
Pricing       → SaaS tiers + service pricing + SLA table + FAQ
About         → company story, approach, who we serve, location/availability
Contact       → email + form + response SLA + availability note
Privacy       → full, conservative, MoR disclosure prominent
Terms         → service terms, SaaS terms, IP, liability, governing law
Refund        → SaaS + service refund windows, clearly separated, process steps
404           → restrained, helpful, search + back to home
```

---

## 4. Shared Site Maps (Dodo Compliance Skeleton)

### 4.1 Required pages — all variants

Every variant ships **exactly** these pages. No variant omits a required page.

| # | Path | Purpose | Dodo check |
|---|------|---------|------------|
| 1 | `/` (Home) | What you sell + price + CTA + trust | 10-second clarity |
| 2 | `/products` (or `/services` for Systems) | Full catalog, what's included, requirements | Product unambiguity |
| 3 | `/pricing` | Tier table, billing model, FAQ | Pricing visibility |
| 4 | `/about` | Who you are, what you do, why | Credibility / entity coherence |
| 5 | `/contact` | Email + form + response window | Real support contact |
| 6 | `/privacy` | Data, cookies, MoR, rights | Reachable from every page |
| 7 | `/terms` | License/service, renewals, law | Reachable from every page |
| 8 | `/refund` | Window, conditions, process | Specificity test |
| 9 | `/404` | Helpful not-found | Broken-link hygiene |

Footer on **every page** links to: Privacy, Terms, Refund, Contact — plus Contact email in plain text.

### 4.2 Page outlines (copy blocks each page must contain)

**Home**
- Nav: logo + Products + Pricing + About + Contact + CTA ("Get started" / "View kits" / "Start audit")
- Hero: headline + subhead (one plain sentence what you sell) + primary CTA + secondary CTA (view pricing) + hero visual (diagram/screenshot)
- Trust/cred strip: 3 metrics or audience labels (no fake logos) — e.g. "For founders · For small teams · For agencies" + build note
- Featured products: 3 cards (name, one-line desc, price, what's included bullets, CTA)
- How it works / After payment: 3 steps ("Choose → Pay via Dodo → Get instant access")
- Pricing teaser: 2-3 tiers inline, link to full pricing
- FAQ: 4-6 items (what's included, fulfillment, refund window, support, license, subscription cancel)
- Footer: links + email + © + Dodo MoR note ("Payments processed by Dodo Payments")

**Products (`/products`)**
- Header: page title + one-line category explainer
- Filters/tags (Labs only; Studio/Systems just list)
- Product cards: name, tagline, bullets (what's included), stack/requirements, price, CTA per product
- Comparison/helper: "Which one for me?" guidance
- CTA to pricing

**Pricing (`/pricing`)**
- Billing toggle (monthly/annual where subscriptions exist)
- Tier cards or table: price, model, every inclusion, CTA per tier
- FAQ below table (refunds, cancel anytime, what happens after payment)
- Contact for custom scope (Systems: enterprise note — but still shows Sprint/Retainer prices)

**About (`/about`)**
- Studio/Lab/Systems story (generic, credible, no p4/p3 names)
- Principles (3-4)
- Who it's for / not for
- Contact CTA

**Contact (`/contact`)**
- Email displayed as text (`hello@focalis.cc`) — crawlable, not image
- Form (name, email, message) — can be non-functional with "or email us directly" fallback for static site
- Response window: "within 24 hours on business days"
- No fake address; optional: jurisdiction line ("Operated from [region]")

**Privacy (`/privacy`)**
- Last updated date
- What we collect, how used, cookies, third parties (Dodo Payments as MoR/processor), data retention, rights, contact for requests

**Terms (`/terms`)**
- Who the seller is, what you're buying (license/service), payment via Dodo, subscription renewal/cancel terms, IP, liability limits, governing law

**Refund (`/refund`)**
- Window: 14 days (standard for digital, defensible)
- Condition: not activated/downloaded/accessed beyond preview (or for SaaS: not used beyond trial; for sprints: before kickoff)
- How to request (email), processing time (5-10 business days), who processes (Dodo)

**404**
- On-brand headline, short help text, button to Home, link to Contact/Pricing

### 4.3 Technical requirements (all variants)

- Static HTML, valid `<title>` + `<meta description>` per page, OG image, favicon.
- All internal links resolve; 404 page exists and is linked.
- HTTPS on deployment; canonical domain `https://focalis.cc`.
- Sitemap `sitemap.xml`, `robots.txt`.
- No lorem ipsum, no "coming soon" tiers, no empty cards.

---

## 5. Variant Comparison at a Glance

| Dimension | Studio (A) | Labs (B) | Systems (C) |
|-----------|------------|----------|-------------|
| **Tagline** | Tools that stay out of the way. | Experiments you can ship. | Infrastructure you can trust. |
| **Aesthetic** | Linear / Vercel — quiet premium | Warm lab — bold, collage, orange | Stripe enterprise — navy, calm, proof |
| **Palette** | Zinc + violet, dark-first | Cream + orange/amber, light-first | White + navy + trust blue, light-first |
| **Type** | Geist/Inter, tight, minimal | Sora/General Sans, expressive, large | Inter/Instrument Sans, conservative |
| **Radius** | 12px / 8px | 16px / pills | 8px / 6px |
| **Motion** | Fade-up only | Tilt + marquee + fade | Fade only |
| **Products** | Workflow kits, publish pipe | Browser/AI/video kits | Sprints, audit, SaaS runner |
| **Top price** | $39/mo Team | $79/mo Agency | $1,200 Sprint / $600/mo Retainer |
| **Audience** | Solo builders, small teams | Creators, tinkerers, agencies | Ops leads, scaling startups, SMEs |
| **Risk for Dodo** | Low (digital kits, instant) | Low-medium (needs disclaimers for AI) | Low (SaaS + scoped services, clear) |
| **Build effort** | Lowest — fewest pages visuals | Medium — more graphic assets | Medium — more copy/table work |

### Recommendation for Dodo submission order

1. **Studio (A)** — safest first submission: lowest perceived risk, simplest product, instant fulfillment, smallest price points. Gets approved fastest.
2. **Systems (C)** — next: SaaS + services is well-understood by underwriters; higher price but SaaS tiers keep average transaction legible. Good if you want to sell retainers.
3. **Labs (B)** — still approvable but lands in Dodo's "enhanced DD middle band" (AI + browser automation) — expect they may ask for demo access / disclaimers before approval. Ship once Studio is verified and reuse the verified entity.

---

## 6. Copy Guardrails (all variants)

- No mention of `p4`, `p3`, `p2`, `p1`, or internal experiment numbers — ever.
- Product names are generic and portable (`Flow Kit`, `Browser Kit`, not internal codenames).
- No fake testimonials, no fake logos, no revenue claims.
- Refund/privacy/terms copy must be **substantively different per variant** in tone but **identical in legal substance** — don't copy-paste a template verbatim; tailor voice.
- All prices include currency (`USD` or `$` with note "billed in USD via Dodo Payments").

---

## 7. Next Steps (for the build agent)

1. Pick one variant (recommend **A** for first pass).
2. Create `DESIGN.md` from that variant's palette + type tokens (frontmatter) + site map.
3. Build static site to `sites/focalis.cc/<variant>/` with the 9 pages above, footer on every page, real copy (no lorem).
4. Add `sitemap.xml` + `robots.txt` + OG image.
5. Deploy preview, then submit Dodo verification with that URL.

*Research agent done — no user input needed. Files: `REQUIREMENTS.md` + `CONCEPTS.md` in `sites/focalis.cc/`.*
