# focalis.cc — Requirements & Research

> Design Research agent output — 2026-08-31
> Domain: `focalis.cc` · Purpose: tech emprendimiento, Dodo Payments verification

---

## 1. Dodo Payments Website Requirements

### 1.1 Source & Method

Attempted live fetch of `dodopayments.com` and `docs.dodopayments.com` via `curl` (2026-08-31). Key sources:

- **Merchant Underwriting Explained** — `dodopayments.com/blogs/merchant-underwriting-explained` (fetched & parsed, full article content extracted)
- **How to Pass Merchant Underwriting on the First Submission** section (same article, checklist at bottom)
- **Dodo Payments homepage & pricing** (fetched, confirmed MoR positioning)
- **Dodo docs `llms.txt`** — confirmed docs structure, no dedicated "business verification" page publicly indexed
- **General MoR / KYB knowledge** — Dodo acts as Merchant of Record (holds acquiring relationship, inherits liability)

> Note: Dodo does not publish a single "website requirements checklist" page. Requirements are inferred from the underwriting article's explicit checklist + standard MoR KYB patterns + Stripe/Paddle/LemonSqueezy analogues + card-network compliance expectations Dodo cites (VAMP, ECM, MATCH).

### 1.2 What Dodo (and its acquirer) actually checks

From the article, verbatim logic:

> *"Publish a site a stranger understands in ten seconds. What is sold, what it costs, what happens after payment. A holding page, waitlist, or 'coming soon' screen is a decline under most policies, including Dodo's."*

**Automated onboarding** uses: document checks, entity lookups, website crawls, sanctions screening. **Manual review** triggers on ambiguity — unclear product, thin registry data, near-restricted category, large projected volume.

Flow: `Sign up → Entity/identity resolve? → Product category unambiguous? → Projected volume within limits? → Approved` — any "No" routes to manual compliance review.

### 1.3 Hard requirements for focalis.cc to pass

| # | Requirement | Detail | Failure mode |
|---|-------------|--------|--------------|
| 1 | **Professional, live business site** | Real domain (`focalis.cc`), no holding page / waitlist / "coming soon", no placeholder. Must look like a real company. | Auto-decline |
| 2 | **Clear product/service description** | One plain sentence per Dodo's advice: e.g. *"AI-assisted automation tools sold as monthly subscriptions"* — not vague puff like "next-gen intelligent platform". Reviewer must know what's sold in 10 seconds. | Manual review → questions → delay |
| 3 | **Pricing visible & specific** | Prices in USD (or clearly stated currency), billing model explicit (one-time vs subscription vs credits), what you get at each tier. No "contact for pricing" hiding everything. | Manual review |
| 4 | **What happens after payment** | Fulfillment description: instant access, license delivery, download, account creation — eliminates delivery-risk ambiguity. SaaS = low risk (immediate grant). | Manual review |
| 5 | **Legal pages reachable from every page** | Footer links on all pages to: Privacy Policy, Terms & Conditions, Refund Policy. Must exist as real pages, not anchors. | Manual review |
| 6 | **Refund policy — specific, not vague** | Must state window (e.g. 14 days), conditions, how to request, processing time. *"Refunds at our discretion"* is explicitly called out as worse than no policy. For digital: clarify when refund is / isn't available (e.g. after license activation). | Reject |
| 7 | **Privacy policy — substantive** | What data is collected, how used, cookies, Dodo as MoR/processor disclosure, contact for data requests. GDPR-aware language helps even if not EU-targeted. | Reject |
| 8 | **Terms & Conditions** | Who the seller is, license/use terms for digital products, subscription renewal/cancellation terms, governing law. | Reject |
| 9 | **Real support contact** | Working email that resolves (e.g. `hello@focalis.cc` or `support@focalis.cc`) + stated response window (e.g. "within 24h business days"). Reduces disputes. No placeholder form-to-nowhere. | Reject |
| 10 | **About page — credible entity** | Who is behind the site, what the studio does, why it exists. Does NOT need to name p4/p3 internals — generic but believable (small tech studio, location, mission). | Trust signal |
| 11 | **Contact page — separate & complete** | Email, response time, optional form. No fake address. If no physical office, don't invent one — just email + jurisdiction disclosure. | Trust signal |
| 12 | **No placeholder / lorem ipsum anywhere** | Every page has real copy. No "Lorem ipsum", no empty product cards, no stock TODO text. Website crawler flags this. | Auto-decline |
| 13 | **Consistent entity details** | If Dodo asks for business entity, the name/address on site must match incorporation docs and payout bank account holder. Keep site copy generic enough not to contradict future filings. | Payout mismatch |
| 14 | **Product category must be unambiguous & allowed** | Avoid restricted buckets Dodo names: adult, gambling, lending/advice, health claims, crypto, multi-vendor marketplace. AI tools / automation / video kits are in the "middle band" — allowed but need disclaimers & demo access. | Decline or enhanced DD |
| 15 | **Supported jurisdiction** | Dodo publishes accepted countries/territories. Confirm before building. Founders without a company can use individual path but site should not claim a fake registration. | Hard block |
| 16 | **No deceptive claims** | No unverifiable revenue promises, no fake testimonials, no "lorem ipsum" social proof. Honest copy. | Trust / dispute risk |

### 1.4 Dodo vs. typical Stripe/Paddle checklists — differences

- Dodo is **MoR**: you don't apply for your own merchant account, but Dodo still runs KYB on you + beneficial owners and ongoing monitoring. Lighter than direct acquirer pack, but site review is *identical* in strictness.
- Dodo's multi-brand: one verified business can run multiple brands/sites — but each brand's site still gets reviewed.
- Ongoing triggers re-review: dispute spike, volume spike, new product line, refund climb, card-testing traffic. Site must stay compliant post-approval.

### 1.5 SEO / technical hygiene that helps verification (not strictly required but flagged by crawlers)

- Valid `og:image`, favicon, `title`/`description` per page, canonical domain, HTTPS.
- No broken links; all nav/footer links resolve (404 page exists and is helpful).
- Fast LCP, no massive render-blocking — Dodo's own site defers GTM until post-LCP (they care about performance, so should we).

---

## 2. Design Skills & Tooling Inventory

### 2.1 Local skills available (this machine, 2026-08-31)

| Location | Skills found |
|----------|--------------|
| `~/.pi/skills/` | **does not exist** (legacy path) |
| `~/.pi/agent/skills/` | `faceless-explainer`, `hyperframes` (+ animation/audio/cli/core/creative/keyframes/registry/media-use), `orquestador`, `terminal-browser` |
| `~/.claude/skills/` | Same set plus `paperclip`, `para-memory-files` (npm npx installs) |
| `/home/vuos/code/p4/.pi/skills/` | `fish-audio-api`, `fish-audio-sdk` |
| Pipe project skills | `p4/e028-dsh-harness` (cordis), `e033-vuza-playground` (playwright), `e034-motion-design-skill` (motion-design / LottieFiles), `e027-open-design` (Open Design / od daemon + DESIGN.md systems) |

**Relevant design system sources inside this repo:**

- `e027-open-design/upstream/plugins/_official/design-systems/` — templates: `clean`, `energetic`, `tetris`, `elevenlabs`, `wise`, `retro`
- `e027-open-design/upstream/apps/daemon/tests/fixtures/design-systems/` — `runtime-v3/DESIGN.md`, `legacy/DESIGN.md`
- `e034-motion-design-skill/upstream/skills/motion-design/SKILL.md` — motion primitives (used by HyperFrames builds)
- `hyperframes-creative` — brand/pacing/style skill (frame.md / design.md / DESIGN.md spec, palettes, typography, composition patterns)

**No standalone `open-design` skill installed at `~/.pi/agent/skills/open-design`** — but the `e027-open-design` upstream is available locally and `hyperframes-creative` covers equivalent token needs. For focalis.cc builds, use `hyperframes-creative` + `hyperframes-core` + `media-use`.

### 2.2 Recommended toolchain for focalis.cc variants

- **Stack**: static HTML + Tailwind CDN (or Vite+Tailwind), deployable to any static host (Cloudflare Pages / Vercel / Netlify). No framework lock needed for Dodo verification — static is fastest to crawl.
- **Design spec file**: each variant gets `DESIGN.md` or `frame.md` with frontmatter tokens (colors, fonts, spacing, radius) — consumable by both humans and any future `od` / HyperFrames pipeline.
- **Media**: `media-use` skill to resolve OG images, icons, logos to frozen local files. No external hotlink.
- **Video (if needed)**: HyperFrames — not required for Dodo but useful for product demos on the site.

### 2.3 Web Design Trends 2026 — Tech Studio Sites

Synthesized from observation of `linear.app`, `vercel.com`, `stripe.com`, `paddle.com`, `framer.com`, plus trend reports (Awwwards, Linear's 2025-26 design system updates, Vercel Ship).

**What's in for tech studios / indie SaaS in 2026:**

1. **Quiet luxury / minimal premium** — Linear/Vercel lineage is dominant: near-black or pure-white canvas, single accent, generous whitespace, hairline borders (`border: 1px solid rgba(255,255,255,0.06)`), subtle grid. No gradients-for-the-sake-of-it.
2. **Typography as hero** — Large display sans (Geist, Inter, Instrument Sans, General Sans, Sora, Syne), tight tracking (-0.02em to -0.04em on headlines), oversized hero type (48-72px desktop), mono for meta/labels.
3. **Bento / modular cards** — Product features in bordered cards with small icons, not long sections. 2-3 column grid, rounded 12-16px, hover-lift.
4. **Glass & grain (subtle)** — Very light noise texture or mesh gradient behind hero, not full glassmorphism. A hint of depth, not a frosted panel.
5. **Dark default, light toggle** — Most dev-tool studios ship dark-first in 2026; enterprise variants ship light-first. Both offer toggle.
6. **Motion is restrained** — Fade-up + slight blur on scroll, no parallax. `prefers-reduced-motion` respected. HyperFrames animation maps kept minimal.
7. **Pricing is transparent and interactive** — Toggle monthly/annual, feature comparison inline, FAQ accordion below. No hidden pricing.
8. **Trust strip** — "Built for builders / Used by ..." + small logos or just icon + metric numbers — but no fake logos (Dodo flags fake social proof).
9. **Docs-like clarity** — Stripe Docs influence: left nav on content pages, code blocks / integration snippets even on marketing pages, copy is plain sentences.
10. **Warm accent revival vs. cold tech** — Two competing palettes: cold (zinc + violet/blue) vs. warm (cream + amber/terracotta). Both valid; choice signals personality.
11. **Accessibility & performance as aesthetic** — Lighthouse 95+, semantic HTML, AA contrast — these are now part of the brand, not just compliance.

**What's out:**

- Heavy gradients, neon glows, 2022-style glassmorphism.
- Illustrations as hero (replaced by product screenshots / abstract monospace diagrams).
- Lorem ipsum anywhere (also a Dodo fail condition).
- Cookie-banner dark patterns (ironic for a privacy-page-required site).

---

## 3. Implications for focalis.cc

- All three variants must share the **same compliance skeleton** (pages, footer, legal depth, pricing clarity) so any one can pass Dodo on day one.
- Visual differentiation happens in **tokens** (palette, type, radius, density) and **copy voice**, not in page count — sitemap is identical across variants to keep verification logic simple.
- Generic-but-credible product taxonomy: avoid naming internal p4/p3 projects; instead sell categories that map to real capabilities (automation kits, video pipelines, browser tools) described generically.
- Pricing must be **real numbers** tied to **real deliverables** (license, seats, support window) — not "coming soon" tiers.
