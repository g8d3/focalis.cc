#!/usr/bin/env python3
"""Capture + measure one round of the taste loop (playwright, real Chrome).

Serves the variant directory over 127.0.0.1 in-process (no leftover server), loads the
page at 390x844 and 1280x900, and records what a critic is allowed to see: screenshots,
the rendered text, the interaction (tab) log, and the measured metrics.

    python3 tools/capture.py --round 0
"""
from __future__ import annotations

import argparse
import functools
import json
import re
import sys
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
CLAIMS = Path("/tmp/night/sales/CLAIMS.md")
LANDING = Path("/tmp/night/sales/landing.md")
BAD_WORDS = re.compile(r"\blorem\b|\bipsum\b|\bplaceholder\b|\bcoming soon\b|\btbd\b|\bxxx+\b|«|»", re.I)
ALLOWED_HREFS = {
    "/", "/audit/", "/audit/routes/", "/audit/preview/", "/audit/sample/", "/audit/intake/",
    "/tps/", "/company", "/terms", "/privacy", "/refunds", "/contact",
    "https://github.com/g8d3/transcript-tax",
    "https://github.com/g8d3/pi-web-tps-monitor",
    "mailto:hello@focalis.cc?subject=TAX",
}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *a, **k):  # quiet
        pass


def serve(directory: Path):
    handler = functools.partial(QuietHandler, directory=str(directory))
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd, port


def measure(browser, url: str, width: int, height: int, tag: str, outdir: Path) -> dict:
    ctx = browser.new_context(viewport={"width": width, "height": height},
                              device_scale_factor=2 if width < 500 else 1,
                              is_mobile=width < 500, has_touch=width < 500)
    page = ctx.new_page()
    reqs: list[dict] = []
    page.on("request", lambda r: reqs.append({"url": r.url, "type": r.resource_type}))
    t0 = time.perf_counter()
    resp = page.goto(url, wait_until="load")
    wall_ms = (time.perf_counter() - t0) * 1000
    page.wait_for_timeout(250)

    nav = page.evaluate("""() => {
      const n = performance.getEntriesByType('navigation')[0] || {};
      const rs = performance.getEntriesByType('resource').map(r => r.name);
      return {ttfb: n.responseStart, dcl: n.domContentLoadedEventEnd, load: n.loadEventEnd,
              transferSize: n.transferSize, encodedBodySize: n.encodedBodySize, resources: rs};
    }""")
    geom = page.evaluate("""() => {
      const de = document.documentElement;
      const interactive = [...document.querySelectorAll('a,button')].filter(e => {
        const r = e.getBoundingClientRect(); const s = getComputedStyle(e);
        return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none';
      }).map(e => {
        const r = e.getBoundingClientRect();
        return {tag: e.tagName.toLowerCase(), id: e.id || null, text: (e.innerText || '').trim().slice(0, 80),
                href: e.getAttribute('href'), w: +r.width.toFixed(1), h: +r.height.toFixed(1),
                top: +r.top.toFixed(1), bottom: +r.bottom.toFixed(1), above_fold: r.bottom <= innerHeight};
      });
      const cta = document.getElementById('hero-cta');
      const cr = cta ? cta.getBoundingClientRect() : null;
      return {scrollW: de.scrollWidth, clientW: de.clientWidth, innerW: innerWidth, innerH: innerHeight,
              bodyScrollW: document.body.scrollWidth,
              h1: [...document.querySelectorAll('h1')].map(h => h.innerText),
              h2count: document.querySelectorAll('h2').length,
              interactive, cta: cr ? {top: +cr.top.toFixed(1), bottom: +cr.bottom.toFixed(1),
                                      above_fold: cr.bottom <= innerHeight, w: +cr.width.toFixed(1), h: +cr.height.toFixed(1)} : null};
    }""")

    # interaction log: the real keyboard path through the page, then a hover on the CTA
    tab_order = []
    page.evaluate("document.body.focus()")
    for _ in range(12):
        page.keyboard.press("Tab")
        tab_order.append(page.evaluate("""() => {
          const a = document.activeElement; if (!a) return null;
          const r = a.getBoundingClientRect();
          return {tag: a.tagName.toLowerCase(), text: (a.innerText||'').trim().slice(0,60),
                  href: a.getAttribute && a.getAttribute('href'), top: Math.round(r.top), h: Math.round(r.height)};
        }"""))
    page.evaluate("window.scrollTo(0,0)")
    if page.locator("#hero-cta").count():
        page.locator("#hero-cta").hover()

    shots = {}
    for name, full in (("fold", False), ("full", True)):
        p = outdir / f"{tag}-{name}.png"
        page.screenshot(path=str(p), full_page=full)
        shots[f"{tag}-{name}"] = str(p)

    # viewport strips: what a critic actually sees while scrolling (small enough to attach)
    page.evaluate("window.scrollTo(0,0)")
    max_scroll = page.evaluate("document.documentElement.scrollHeight - innerHeight")
    stops = [0] if max_scroll <= 40 else [0, round(max_scroll * 0.45), max_scroll]
    for i, y in enumerate(stops, 1):
        page.evaluate(f"window.scrollTo(0,{y})")
        page.wait_for_timeout(120)
        p = outdir / f"{tag}-s{i}.png"
        page.screenshot(path=str(p))
        shots[f"{tag}-s{i}"] = str(p)
    page.evaluate("window.scrollTo(0,0)")

    text = page.inner_text("body")
    anchors = [a.get_attribute("href") for a in page.query_selector_all("a")]
    ctx.close()

    overflow = geom["scrollW"] - geom["innerW"]
    small = [i for i in geom["interactive"] if i["h"] < 44 or i["w"] < 44]
    small48 = [i for i in geom["interactive"] if i["h"] < 48 or i["w"] < 48]
    external = [r for r in reqs if "127.0.0.1" not in r["url"] and not r["url"].startswith("data:")]
    return {
        "viewport": f"{width}x{height}",
        "status": resp.status if resp else None,
        "wall_ms": round(wall_ms, 1),
        "nav_timing": {k: (round(v, 1) if isinstance(v, (int, float)) else v) for k, v in nav.items()},
        "requests": reqs,
        "request_count": len(reqs),
        "external_requests": external,
        "overflow_px": overflow,
        "scrollW": geom["scrollW"], "clientW": geom["clientW"],
        "h1_count": len(geom["h1"]), "h1": geom["h1"], "h2_count": geom["h2count"],
        "cta": geom["cta"],
        "interactive_count": len(geom["interactive"]),
        "tap_targets_under_44": small,
        "min_tap_h": min([i["h"] for i in geom["interactive"]], default=None),
        "min_tap_w": min([i["w"] for i in geom["interactive"]], default=None),
        "above_fold_interactive": [i for i in geom["interactive"] if i["above_fold"]],
        "interactive": geom["interactive"],
        "tap_targets_under_48": small48,
        "tab_order": tab_order,
        "anchors": [a for a in anchors if a],
        "bad_words": BAD_WORDS.findall(text),
        "shots": shots,
        "text": text,
    }


def claims_check(text: str) -> dict:
    source = (CLAIMS.read_text() + "\n" + LANDING.read_text())
    src_norm = source.replace(",", "").replace(" ", "")
    nums = set(re.findall(r"\d[\d.,]*", text))
    missing = []
    for n in sorted(nums):
        cand = n.replace(",", "")
        if n in source or cand in src_norm or cand.rstrip(".") in src_norm:
            continue
        missing.append(n)
    return {"number_tokens": sorted(nums), "unsourced_numbers": missing,
            "sourced": not missing}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", required=True)
    ap.add_argument("--html", default="index.html")
    args = ap.parse_args()
    outdir = ROOT / "rounds" / f"r{args.round}"
    outdir.mkdir(parents=True, exist_ok=True)
    src = ROOT / args.html
    snapshot = outdir / "page.html"           # frozen revision: critics always judge this exact file
    if src.resolve() != snapshot.resolve():
        snapshot.write_bytes(src.read_bytes())

    httpd, port = serve(ROOT)
    url = f"http://127.0.0.1:{port}/{args.html}"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            m390 = measure(browser, url, 390, 844, "mobile", outdir)
            m1280 = measure(browser, url, 1280, 900, "desktop", outdir)
            browser.close()
    finally:
        httpd.shutdown()

    f390, f1280 = m390, m1280

    def shot_files(m):
        return [v for k, v in m["shots"].items() if "-s" in k]
    doc_bytes = (ROOT / args.html).stat().st_size
    m = {
        "round": args.round, "html": args.html, "url_served": url,
        "doc_bytes": doc_bytes,
        "mobile": {k: v for k, v in f390.items() if k != "text"},
        "desktop": {k: v for k, v in f1280.items() if k != "text"},
        "checks": {
            "zero_external_requests": not f390["external_requests"] and not f1280["external_requests"],
            "request_count_mobile": f390["request_count"],
            "no_overflow_390": f390["overflow_px"] <= 1,
            "tap_targets_min_44": not f390["tap_targets_under_44"],
            "min_tap_h_390": f390["min_tap_h"], "min_tap_w_390": f390["min_tap_w"],
            "cta_above_fold_390": bool(f390["cta"] and f390["cta"]["above_fold"]),
            "single_h1": f390["h1_count"] == 1,
            "load_under_2s": f390["wall_ms"] < 2000 and f1280["wall_ms"] < 2000,
            "no_placeholder_words": not f390["bad_words"],
            "anchors_allowed": sorted(set(a for a in f390["anchors"] + f1280["anchors"]
                                          if a not in ALLOWED_HREFS)),
        },
        "claims": claims_check(f390["text"]),
        "critic_images": {"mobile": [s.replace(str(ROOT) + "/", "") for s in shot_files(f390)],
                          "desktop": [s.replace(str(ROOT) + "/", "") for s in shot_files(f1280)]},
    }
    (outdir / "metrics.json").write_text(json.dumps(m, indent=2, ensure_ascii=False))
    (outdir / "text.txt").write_text(f390["text"])
    print(json.dumps({k: v for k, v in m["checks"].items()}, indent=2))
    print("unsourced numbers:", m["claims"]["unsourced_numbers"] or "none")
    print("wrote", outdir / "metrics.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
