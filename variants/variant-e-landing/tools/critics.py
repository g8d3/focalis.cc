#!/usr/bin/env python3
"""Critic panel + rubric judge for one round (OpenRouter, deepseek-v4.1-flash).

Four personas see ONLY screenshots plus the interaction log and the measured metrics —
never our code, never our intent. Each returns a score (1-5) and EXACTLY ONE concrete
change. A rubric judge scores items 1-3 of the rubric (clarity, one CTA, hierarchy) from
the same evidence; items 4-6 are measured mechanically by capture.py.

    python3 tools/critics.py --round 0
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL = "deepseek/deepseek-v4.1-flash"          # the four personas (cheap, multimodal)
MODEL_JUDGE = "openai/gpt-6-luna"               # rubric judge (different model family = independent)
API = "https://openrouter.ai/api/v1/chat/completions"
KEY = os.environ.get("OPENROUTER_API_KEY", "")

PERSONAS = {
    "mobile-skimmer-8s": {
        "who": "You are a 32-year-old technical lead who opened this link on a phone during a commute. "
               "You spend 8 seconds on it. You scroll with your thumb once. You do not read paragraphs. "
               "You cannot see any code, only what is on the screen.",
        "wants": "To know in one glance what this company does, whether it is for someone like you, and "
                 "whether there is one obvious thing to tap. If the first screen is a wall of text, or you "
                 "cannot tell what is being sold, you leave.",
    },
    "skeptical-cto": {
        "who": "You are a CTO with 40 engineers and a token bill you cannot explain. You have been sold "
               "'AI observability' four times. You read the fine print and you check the numbers. "
               "You only see what is rendered on the page.",
        "wants": "Evidence: a real measured number with a sample size, a way to verify it yourself, and "
                 "no unsourced marketing arithmetic. A claim you cannot check is a reason to leave.",
    },
    "impatient-gamer": {
        "who": "You are a 19-year-old who clicked a link out of curiosity. You have the attention span of "
               "a TikTok session. Layout, motion and a fast obvious action matter to you; long prose does not.",
        "wants": "Something to do NOW: a button that looks like it does something, a page that responds "
                 "instantly, no dead space, no 'read more'. A wall of text or a slow/boring first screen "
                 "makes you close the tab.",
    },
    "buyer-afraid-of-paying": {
        "who": "You are a founder with a fixed budget who has been burned by agencies. You are afraid of "
               "being charged for something vague, of a hidden retainer, of a sales call you cannot escape.",
        "wants": "To see the price before committing, to know exactly what happens after you tap, to see "
                 "that terms/refunds/privacy exist, and to find a step that costs nothing and commits to nothing.",
    },
}

RUBRIC = {
    "clarity_5s": "In 5 seconds, does the page say what is sold, to whom, and why it matters? 5 = unmistakable, 1 = opaque.",
    "one_cta": "Exactly ONE call to action above the fold (one obvious action; navigation links do not count as the action). 5 = a single unambiguous action, 1 = none or a crowd of competing buttons.",
    "hierarchy": "One hero, one action, one visual path down the page. 5 = clean single column of attention, 1 = competing headlines/sections of equal weight.",
}

CHANGE_SEP = "\n"


def data_uri(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


def call(messages: list[dict], model: str, max_tokens: int = 1600) -> dict:
    body = json.dumps({"model": model, "messages": messages, "max_tokens": max_tokens,
                       "reasoning": {"exclude": True}, "temperature": 0.2}).encode()
    req = urllib.request.Request(API, data=body, headers={
        "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read())


def parse_json(text: str) -> dict:
    t = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    try:
        return json.loads(t)
    except Exception:
        m = re.search(r"\{.*\}", t, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
    return {"_raw": text}


def evidence(metrics: dict) -> str:
    c = metrics["checks"]
    mob, desk = metrics["mobile"], metrics["desktop"]
    return (
        "MEASURED EVIDENCE (this is what a browser really did with the page; you may trust it):\n"
        f"- the delivered page is one self-contained file, {metrics['doc_bytes']} bytes, "
        f"{c['request_count_mobile']} network request(s), zero third-party requests.\n"
        f"- load time: {mob['wall_ms']} ms at 390x844, {desk['wall_ms']} ms at 1280x900 (localhost).\n"
        f"- horizontal overflow at 390x844: {mob['overflow_px']} px. Every a/button is at least "
        f"{c['min_tap_h_390']}x{c['min_tap_w_390']} px, {len(mob['tap_targets_under_44'])} under 44 px.\n"
        f"- the primary CTA (#hero-cta) bottom edge sits at {mob['cta']['bottom']} px on a 844 px-tall "
        f"phone screen: {'visible without scrolling' if c['cta_above_fold_390'] else 'NOT visible without scrolling'}.\n"
        f"- headings: {mob['h1_count']} h1, {mob['h2_count']} h2. Places to tap: {mob['interactive_count']}.\n"
        f"- unsourced numbers found on the page: {metrics['claims']['unsourced_numbers'] or 'none'}.\n"
        "INTERACTION LOG (keyboard order of the first 6 stops on mobile, then what each one is):\n"
        + "\n".join(f"  {i+1}. <{s['tag']}> {s['text']!r} -> {s['href']}"
                    for i, s in enumerate(mob["tab_order"][:6]) if s)
        + "\nLIST OF TAPPABLE THINGS ON THE FIRST SCREEN:\n"
        + "\n".join(f"  - {x['text']!r} -> {x['href']} ({x['w']}x{x['h']} px)"
                    for x in mob["above_fold_interactive"])
    )


def images(round_dir: Path, metrics: dict, which: str) -> list[dict]:
    parts = []
    for rel in metrics["critic_images"][which]:
        p = ROOT / rel
        parts.append({"type": "image_url", "image_url": {"url": data_uri(p)}})
    return parts


def persona_messages(name: str, p: dict, metrics: dict, round_dir: Path) -> list[dict]:
    shots = images(round_dir, metrics, "mobile") + images(round_dir, metrics, "desktop")
    labels = [{"type": "text", "text": "Screenshots of the page, in this order: "
               "first = phone screen as opened, then phone scrolled to the middle, then phone scrolled to "
               "the bottom, then the desktop first screen, then desktop scrolled down."}]
    asks = (
        f"\nYOUR ONE CONCRETE CHANGE must be a single edit a developer can make in one sitting "
        f"(add/remove/replace ONE thing). Write it as an imperative sentence naming the exact element. "
        f"Do not list options. Do not say 'consider'. One change.\n"
    )
    body = (f"Who you are:\n{p['who']}\n\nWhat you want:\n{p['wants']}\n\n"
            f"{evidence(metrics)}\n{RUBRIC['clarity_5s']}\n\n{asks}\n"
            "Answer with STRICT JSON only, no prose outside it:\n"
            '{"score": <1-5 integer>, "what_i_saw": "<one sentence>", "complaint": "<the single worst thing>", '
            '"change": "<the ONE concrete change>", "why_it_helps": "<one sentence>"}')
    return [{"role": "system", "content": "You are a harsh but fair product critic. You only judge what you can "
             "see in the screenshots and the measured evidence. You never invent facts. Strict JSON output."},
            {"role": "user", "content": labels + shots + [{"type": "text", "text": body}]}]


def rubric_messages(metrics: dict, round_dir: Path) -> list[dict]:
    shots = images(round_dir, metrics, "mobile") + images(round_dir, metrics, "desktop")
    items = "\n".join(f'- "{k}": {v}' for k, v in RUBRIC.items())
    body = (f"{evidence(metrics)}\n\nScore these three rubric items 1-5 from the screenshots only:\n{items}\n\n"
            "Calibration — do not hand out free 5s. A 5 means a stranger with no context gets it instantly and you "
            "cannot name a single flaw. For EVERY item you must name the concrete flaw that stops it being a 5; "
            "if you truly cannot name one, say so explicitly. If you score two items 5 and one 5, your review is "
            "only believable with three named near-misses. Judge what is on the screen, not what the copy intends.\n"
            "Also name the single highest-leverage change (one edit, one element), as an imperative sentence "
            "naming the exact element.\n"
            "Answer with STRICT JSON only:\n"
            '{"clarity_5s": <1-5>, "one_cta": <1-5>, "hierarchy": <1-5>, '
            '"flaw_per_item": {"clarity_5s": "...", "one_cta": "...", "hierarchy": "..."}, '
            '"top_change": "<one concrete edit>"}')
    return [{"role": "system", "content": "You are a demanding landing-page design judge who has reviewed a "
             "thousand first screens and is hard to impress. Judge only what the screenshots show. "
             "Strict JSON output, no markdown."},
            {"role": "user", "content": [{"type": "text", "text": "Screenshots: phone first screen, phone middle, "
                                         "phone bottom, desktop first screen, desktop scrolled."}] + shots
             + [{"type": "text", "text": body}]}]


def run(key: str, messages: list[dict], model: str, required: tuple[str, ...] = ("score",)) -> dict:
    attempts = []
    for attempt in range(2):
        msgs = messages if attempt == 0 else messages + [
            {"role": "user", "content": "Your previous answer was empty or missing fields. "
             "Reply with the STRICT JSON object only, no prose, no markdown fences."}]
        raw = call(msgs, model)
        content = raw["choices"][0]["message"].get("content") or ""
        ans = parse_json(content)
        attempts.append({"raw_text": content, "answer": ans, "usage": raw.get("usage"),
                         "model": raw.get("model"), "provider": raw.get("provider")})
        if content.strip() and all(k in ans and ans[k] not in (None, "") for k in required):
            break
    out = attempts[-1]
    out["attempts"] = len(attempts)
    out["first_attempt_raw"] = attempts[0]["raw_text"] if len(attempts) > 1 else None
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", required=True)
    ap.add_argument("--persona-samples", type=int, default=3)
    ap.add_argument("--judge-samples", type=int, default=5)
    args = ap.parse_args()
    round_dir = ROOT / "rounds" / f"r{args.round}"
    metrics = json.loads((round_dir / "metrics.json").read_text())

    out: dict = {"model_personas": MODEL, "model_judge": MODEL_JUDGE,
                 "persona_samples": args.persona_samples, "judge_samples": args.judge_samples,
                 "personas": {}, "rubric_judge": None, "rubric_samples": [], "errors": []}
    jobs = {}
    with ThreadPoolExecutor(max_workers=12) as ex:
        for name, p in PERSONAS.items():
            for i in range(args.persona_samples):
                jobs[("persona", name, i)] = ex.submit(
                    run, name, persona_messages(name, p, metrics, round_dir), MODEL, ("score", "change"))
        for i in range(args.judge_samples):
            jobs[("rubric", "judge", i)] = ex.submit(
                run, "rubric", rubric_messages(metrics, round_dir), MODEL_JUDGE,
                ("clarity_5s", "one_cta", "hierarchy", "top_change"))
        for (kind, name, i), fut in sorted(jobs.items()):
            try:
                res = fut.result()
            except Exception as e:  # noqa: BLE001
                out["errors"].append(f"{kind}:{name}:{i}: {e}")
                continue
            if kind == "persona":
                out["personas"].setdefault(name, []).append(res)
            else:
                out["rubric_samples"].append(res)

    def median(vals):
        v = sorted(x for x in vals if isinstance(x, int))
        return v[len(v) // 2] if v else None

    out["rubric_judge"] = out["rubric_samples"][0] if out["rubric_samples"] else None
    out["rubric_medians"] = {k: median([s["answer"].get(k) for s in out["rubric_samples"]])
                             for k in RUBRIC}
    out["rubric_spread"] = {k: sorted([s["answer"].get(k) for s in out["rubric_samples"]])
                            for k in RUBRIC}
    (round_dir / "critics.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    for name, samples in out["personas"].items():
        scores = [s["answer"].get("score") for s in samples]
        print(f"{name}: scores={scores} change={samples[0]['answer'].get('change')!r}")
    print("rubric medians:", out["rubric_medians"], "spread:", out["rubric_spread"])
    print("judge top_change:", out["rubric_medians"] and [s["answer"].get("top_change") for s in out["rubric_samples"]][0])
    if out["errors"]:
        print("ERRORS:", out["errors"], file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
