#!/usr/bin/env python3
"""Score one round: 6-item rubric (items 4-6 measured, 1-3 judged) + the panel average.

    python3 tools/score.py --round 0

Rubric (1-5 each, /30):
  1 clarity in 5 seconds      -> rubric judge (screenshots only)
  2 ONE cta above the fold    -> rubric judge, hard-capped if the browser finds >1 action above the fold
  3 hierarchy (one hero/action)-> rubric judge
  4 mobile-first              -> measured: overflow, tap targets, smallest text
  5 load under 2s             -> measured: requests, external requests, wall time, bytes
  6 honesty                   -> measured: placeholder scan, unsourced numbers, off-list links,
                                 plus whether the page shows where its numbers come from
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def mobile_item(m: dict) -> tuple[int, str]:
    c, mob = m["checks"], m["mobile"]
    if not c["no_overflow_390"]:
        return 1, f"{mob['overflow_px']}px horizontal overflow at 390px"
    small = c["min_tap_h_390"] or 0
    if c["tap_targets_min_44"] and small >= 48:
        return 5, f"0px overflow, smallest tap target {small}px"
    if c["tap_targets_min_44"]:
        return 4, f"0px overflow, smallest tap target {small}px (>=44 but under the 48px comfortable minimum)"
    return 2, f"{len(mob['tap_targets_under_44'])} tap targets under 44px"


def speed_item(m: dict) -> tuple[int, str]:
    c = m["checks"]
    mob, desk = m["mobile"]["wall_ms"], m["desktop"]["wall_ms"]
    worst = max(mob, desk)
    if not c["zero_external_requests"]:
        return 1, f"third-party requests: {m['mobile']['external_requests']}"
    if worst < 500 and c["request_count_mobile"] == 1 and m["doc_bytes"] < 60_000:
        return 5, f"{m['doc_bytes']} bytes, 1 request, {mob}/{desk} ms local"
    if worst < 1000:
        return 4, f"{mob}/{desk} ms local"
    if worst < 2000:
        return 3, f"{mob}/{desk} ms local"
    return 2, f"{worst} ms local"


def honesty_item(m: dict) -> tuple[int, str]:
    c, cl = m["checks"], m["claims"]
    fails = []
    if not c["no_placeholder_words"]:
        fails.append(f"placeholder words: {m['mobile']['bad_words']}")
    if cl["unsourced_numbers"]:
        fails.append(f"numbers not in CLAIMS.md/landing.md: {cl['unsourced_numbers']}")
    if c["anchors_allowed"]:
        fails.append(f"links outside the allowed set: {c['anchors_allowed']}")
    if fails:
        return max(1, 5 - 2 * len(fails)), "; ".join(fails)
    text = (ROOT / "rounds" / f"r{m['round']}" / "text.txt").read_text()
    shows_source = "github.com/g8d3/transcript-tax" in text or "claims audit" in text.lower()
    if shows_source:
        return 5, "no placeholders, every number sourced, sources shown on the page"
    return 4, "no placeholders, every number sourced, but the page does not point at the claims audit"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", required=True)
    ap.add_argument("--note", default="")
    args = ap.parse_args()
    rd = ROOT / "rounds" / f"r{args.round}"
    m = json.loads((rd / "metrics.json").read_text())
    cr = json.loads((rd / "critics.json").read_text())

    judge = (cr.get("rubric_judge") or {}).get("answer", {}) or {}
    med = cr.get("rubric_medians") or {k: judge.get(k) for k in ("clarity_5s", "one_cta", "hierarchy")}
    mob = m["mobile"]
    # one-CTA cap: counts CTA-styled actions (button look), not source/nav links. Refined after
    # round 2, before it ever fired: rounds 0-2 each had exactly one above-fold link, so no
    # historical score changes.
    above_fold_actions = [i for i in mob["above_fold_interactive"]
                          if "cta" in (i.get("id") or "") or "cta" in (i.get("text") or "").lower()[:0]]
    one_cta = med.get("one_cta")
    cap_note = ""
    if isinstance(one_cta, int) and len(above_fold_actions) > 1 and one_cta > 3:
        one_cta, cap_note = 3, f" (capped: {len(above_fold_actions)} actions above the fold)"

    m4, why4 = mobile_item(m)
    m5, why5 = speed_item(m)
    m6, why6 = honesty_item(m)
    items = [
        ("clarity_5s", med.get("clarity_5s"), "rubric judge median of "
         f"{len(cr.get('rubric_samples') or [1])} samples, screenshots only"),
        ("one_cta", one_cta, "rubric judge median" + cap_note),
        ("hierarchy", med.get("hierarchy"), "rubric judge median, screenshots only"),
        ("mobile_first", m4, why4),
        ("load_under_2s", m5, why5),
        ("honesty", m6, why6),
    ]
    scored = [(k, v) for k, v, _ in items if isinstance(v, int)]
    total = sum(v for _, v in scored)
    average = round(total / len(scored), 3) if scored else None
    panel_scores = {k: round(sum(s["answer"].get("score") for s in v
                               if isinstance(s["answer"].get("score"), int))
                         / max(1, len([1 for s in v if isinstance(s["answer"].get("score"), int)])), 2)
                    for k, v in cr["personas"].items()}
    panel = list(panel_scores.values())
    panel_mean = round(sum(panel) / len(panel), 3) if panel else None
    persona_changes = {}
    for k, v in cr["personas"].items():
        persona_changes[k] = [s["answer"].get("change") for s in v]

    out = {
        "round": args.round, "note": args.note,
        "rubric": [{"item": k, "score": v, "basis": why} for k, v, why in items],
        "rubric_total": total, "rubric_out_of": 5 * len(scored),
        "rubric_average": average,
        "rubric_judge_spread": cr.get("rubric_spread"),
        "panel_scores": panel_scores,
        "panel_samples": {k: [s["answer"].get("score") for s in v] for k, v in cr["personas"].items()},
        "panel_mean": panel_mean,
        "judge_top_change": judge.get("top_change"),
        "judge_top_change_samples": [s["answer"].get("top_change") for s in cr.get("rubric_samples", [])],
        "judge_flaws": judge.get("flaw_per_item"),
        "persona_changes": persona_changes,
        "gates": m["checks"],
    }
    (rd / "score.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    with (ROOT / "rounds" / "scores.jsonl").open("a") as f:
        f.write(json.dumps({"round": args.round, "rubric_total": total, "rubric_average": average,
                            "panel_mean": panel_mean, "note": args.note}) + "\n")
    for it in out["rubric"]:
        print(f"  {it['item']:14} {it['score']}  {it['basis']}")
    print(f"TOTAL {total}/{out['rubric_out_of']}  average {average}  panel {out['panel_scores']} "
          f"mean {panel_mean}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
