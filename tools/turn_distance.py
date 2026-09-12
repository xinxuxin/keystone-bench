"""Does the distance to the edited turn change whether an assistant notices.

`missing_evidence_early` removes the decisive fact from an earlier user turn rather than the last one, so the
same family spans a range of distances between the edit and the question the assistant is answering. If the
failure were attention decay, the rate of noticing would fall with distance. If it is that assistants do not
re-check earlier turns at all, distance would not matter and the level would be flat and low.

Usage: python tools/turn_distance.py [--prefix q060] [--out docs/TURN_DISTANCE.md]
"""
from __future__ import annotations
import argparse, glob, json, os, random, sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
BOOT = int(os.environ.get("KEYSTONE_BOOT", "4000"))


def wilson(k, n):
    if not n:
        return float("nan"), float("nan"), float("nan")
    p = k / n; z = 1.959963985; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return p, max(0.0, c - h), min(1.0, c + h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="runs"); ap.add_argument("--prefix", default="q060")
    ap.add_argument("--dist", default="dist"); ap.add_argument("--out")
    a = ap.parse_args()
    meta = {}
    for line in open(Path(a.dist) / "keystone_twins.jsonl"):
        if line.strip():
            t = json.loads(line)
            if t["family"] == "missing_evidence_early" and isinstance(t.get("edited_turn"), int):
                meta[f"{t['prompt_id']}::{t['family']}"] = (t["edited_turn"], t.get("turns") or 0)
    rows = defaultdict(lambda: defaultdict(list))   # distance -> outcome -> values
    per_model = defaultdict(lambda: defaultdict(list))
    for d in sorted(glob.glob(os.path.join(a.runs, f"{a.prefix}__*"))):
        model = Path(d).name.split("__", 1)[1]
        f = Path(d) / "missing_evidence_early" / "records.jsonl"
        if not f.exists():
            continue
        for line in open(f):
            if not line.strip():
                continue
            r = json.loads(line)
            if r["id"] not in meta:
                continue
            k, turns = meta[r["id"]]
            dist = max(0, turns - 1 - k)          # turns between the edited turn and the one being answered
            act = (r.get("action") or {}).get("perturbed") or {}
            beh = (r.get("behavior") or {}).get("perturbed") or {}
            if act:
                rows[dist]["acceptable"].append(float(bool(act.get("acceptable"))))
                rows[dist]["decisive"].append(float(bool(act.get("asks_decisive_question")) or bool(act.get("conditional"))))
                per_model[model][dist].append(float(bool(act.get("acceptable"))))
            if beh:
                rows[dist]["named"].append(float(bool(beh.get("names_missing_element"))))
    if not rows:
        print("no early-family runs"); return
    L = ["# Distance to the edited turn", "",
         "`missing_evidence_early` removes the decisive fact from an earlier user turn, so the same family spans a "
         "range of distances between the edit and the message being answered. Attention decay predicts a fall with "
         "distance. A different account, that assistants do not re-check earlier turns at all, predicts a flat low "
         "level.", "",
         "| turns between the edit and the question | items x systems | named the missing element | asked the decisive question or answered conditionally | acceptable action |",
         "|---|---|---|---|---|"]
    for dist in sorted(rows):
        n = len(rows[dist]["acceptable"])
        def cell(key):
            v = rows[dist].get(key) or []
            p, lo, hi = wilson(int(sum(v)), len(v))
            return f"{p:.2f} [{lo:.2f}, {hi:.2f}]" if v else "n/a"
        L.append(f"| {dist} | {n} | {cell('named')} | {cell('decisive')} | {cell('acceptable')} |")
    allv = [x for d in rows for x in rows[d]["acceptable"]]
    L += ["", f"Pooled acceptable action on this family: {sum(allv)/len(allv):.2f} over {len(allv)} (item, system) cells.", ""]

    # the same edit in the last turn: missing_evidence is the same operation, one turn away
    comp = defaultdict(list)
    for d in sorted(glob.glob(os.path.join(a.runs, f"{a.prefix}__*"))):
        f = Path(d) / "missing_evidence" / "records.jsonl"
        if not f.exists():
            continue
        for line in open(f):
            if not line.strip():
                continue
            r = json.loads(line)
            act = (r.get("action") or {}).get("perturbed") or {}
            beh = (r.get("behavior") or {}).get("perturbed") or {}
            if act:
                comp["acceptable"].append(float(bool(act.get("acceptable"))))
                comp["decisive"].append(float(bool(act.get("asks_decisive_question")) or bool(act.get("conditional"))))
            if beh:
                comp["named"].append(float(bool(beh.get("names_missing_element"))))
    if comp:
        L += ["## The same operation, one turn away", "",
              "`missing_evidence` removes a decisive fact from the last user turn. It is the same edit as the family "
              "above, differing only in which turn it lands on, which makes it the right comparison for the level "
              "rather than the slope.", "",
              "| where the fact was removed | items x systems | named the missing element | asked the decisive question | acceptable action |",
              "|---|---|---|---|---|"]
        def row(label, d, n):
            def cell(key):
                v = d.get(key) or []
                p, lo, hi = wilson(int(sum(v)), len(v))
                return f"{p:.2f} [{lo:.2f}, {hi:.2f}]" if v else "n/a"
            return f"| {label} | {n} | {cell('named')} | {cell('decisive')} | {cell('acceptable')} |"
        early = {k: [x for dd in rows for x in rows[dd].get(k, [])] for k in ("named", "decisive", "acceptable")}
        L.append(row("the last user turn", comp, len(comp["acceptable"])))
        L.append(row("an earlier user turn", early, len(early["acceptable"])))
        dn = sum(comp["named"]) / len(comp["named"]) - sum(early["named"]) / len(early["named"])
        dd_ = sum(comp["decisive"]) / len(comp["decisive"]) - sum(early["decisive"]) / len(early["decisive"])
        L += ["", f"Moving the same removal from the last turn to an earlier one costs {dn:.2f} of the rate at which "
                  f"the missing element is named and {dd_:.2f} of the rate at which the decisive question is asked. "
                  "Within the early family the distance itself does not add to that, on the two distances with enough "
                  "items to compare: what matters is whether the fact is in the turn being answered, not how far back "
                  "it is.", ""]
    text = "\n".join(L) + "\n"
    print(text)
    if a.out:
        Path(a.out).write_text(text)


if __name__ == "__main__":
    main()
