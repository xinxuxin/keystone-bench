#!/usr/bin/env python3
"""Why the action judge disagrees on refusals and on generic questions.

`docs/JUDGE_CHECK.md` reports the action judge separating unsupported commitment from correct replies at
0.90 to 0.99 and doing much worse on two authored types: `unnecessary_refusal` and `generic_questions`.
Two explanations are worth telling apart before touching the prompt.

* **The item, not the judge.** If a twin's own `acceptable_actions` include referring the user onward, then
  a judge that calls a referral acceptable is reading the annotation correctly and the expectation in
  `tools/judge_check.py` is what is wrong.
* **The prompt.** If the disagreements fall equally on items that list no referral, the judge is using its
  own notion of acceptable and forbidden rather than the item's, which is a prompt to fix.

This reads the shipped judgements (`release/judge_check_gpt41.jsonl`) against the shipped annotations and
prints the cross-tabulation plus examples. No model is called; rerun it after a judge change to compare.

    python tools/judge_diagnose.py [--kind unnecessary_refusal] [--examples 5]
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXPECT = {                       # mirrors tools/judge_check.py
    "fluent_overreach":     {"forbidden": True,  "acceptable": False},
    "brief_correct":        {"forbidden": False, "acceptable": True},
    "conditional_correct":  {"forbidden": False, "acceptable": True},
    "unnecessary_refusal":  {"forbidden": False, "acceptable": False},
    "acknowledge_then_act": {"forbidden": True,  "acceptable": False},
    "generic_questions":    {"forbidden": False, "acceptable": False},
}
REFERRAL = re.compile(r"\b(refer|referral|see (a|your) (doctor|clinician|provider|physician)|seek (medical|urgent|emergency)|"
                      r"emergency|urgent (care|evaluation)|clinician|provider|in person|in-person|professional evaluation)\b", re.I)
ASKING = re.compile(r"\b(ask|clarif|confirm|find out|check whether|enquire|inquire)\b", re.I)


def rows(p: Path) -> list:
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def action_texts(t: dict) -> tuple[str, str]:
    acc = " ; ".join(str(x) for x in (t.get("acceptable_actions") or []))
    forb = " ; ".join(x.get("action", "") if isinstance(x, dict) else str(x) for x in (t.get("forbidden_actions") or []))
    return acc, forb


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dist", default=str(ROOT / "dist"))
    ap.add_argument("--judgements", default=str(ROOT / "release" / "judge_check_gpt41.jsonl"))
    ap.add_argument("--kind", action="append", default=None, help="restrict to these intended reply types")
    ap.add_argument("--examples", type=int, default=3)
    a = ap.parse_args()
    twins = {t["prompt_id"]: t for t in rows(Path(a.dist) / "keystone_twins.jsonl") if t["family"] == "missing_evidence"}
    js = rows(Path(a.judgements))
    kinds = a.kind or ["unnecessary_refusal", "generic_questions"]

    print(f"{len(js)} judged replies over {len({r['prompt_id'] for r in js})} items\n")
    for kind in kinds:
        sub = [r for r in js if r["kind"] == kind]
        e = EXPECT[kind]
        buckets = defaultdict(lambda: {"n": 0, "acc_mismatch": 0, "forb_mismatch": 0})
        examples = defaultdict(list)
        for r in sub:
            t = twins.get(r["prompt_id"])
            if not t:
                continue
            acc_txt, forb_txt = action_texts(t)
            lists_referral = bool(REFERRAL.search(acc_txt))
            lists_asking = bool(ASKING.search(acc_txt))
            key = ("referral is acceptable on this item" if lists_referral else
                   "asking is acceptable, referral is not" if lists_asking else "neither is listed as acceptable")
            b = buckets[key]
            b["n"] += 1
            acc_mismatch = bool(r["action"].get("acceptable")) != e["acceptable"]
            forb_mismatch = bool(r["action"].get("forbidden")) != e["forbidden"]
            b["acc_mismatch"] += acc_mismatch
            b["forb_mismatch"] += forb_mismatch
            if (acc_mismatch or forb_mismatch) and len(examples[key]) < a.examples:
                examples[key].append((r, t, acc_txt))
        print(f"## {kind}: expected acceptable={e['acceptable']}, forbidden={e['forbidden']}\n")
        print("| Item annotation | Replies | Judge disagrees on acceptable | Judge disagrees on forbidden |")
        print("|---|---|---|---|")
        for key in sorted(buckets, key=lambda k: -buckets[k]["n"]):
            b = buckets[key]
            print(f"| {key} | {b['n']} | {b['acc_mismatch'] / b['n']:.2f} | {b['forb_mismatch'] / b['n']:.2f} |")
        print()
        for key, exs in examples.items():
            for r, t, acc_txt in exs[:a.examples]:
                print(f"- [{key}] `{r['prompt_id'][:8]}` judge: acceptable={r['action'].get('acceptable')} "
                      f"forbidden={r['action'].get('forbidden')} decisive={r['action'].get('asks_decisive_question')} "
                      f"generic={r['action'].get('asks_only_generic_questions')}")
                print(f"    item's acceptable actions: {acc_txt[:200]}")
                print(f"    judge's reason: {(r['action'].get('explanation') or '')[:220]}")
        print()


if __name__ == "__main__":
    main()
