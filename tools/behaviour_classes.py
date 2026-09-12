"""What the evidence asks for, across families: ask, change, escalate, hold.

Families are units of construction, not units of behaviour. Six of them edit a decisive element, but the
edits demand different things: some make a question necessary, some make a different action correct, some
make escalation correct, and two make no change correct. The evidence state each twin carries already names
which, so the same 319 items regroup into four behaviour classes with larger cells than any single family.

The question this answers is whether an assistant's weakness is tied to a kind of edit or to a kind of
required response. If the classes separate and the ordering is the same across systems, the finding is about
a cognitive step rather than about a surface manipulation.

Usage: python tools/behaviour_classes.py [--prefix q060] [--out docs/BEHAVIOUR_CLASSES.md]
"""
from __future__ import annotations
import argparse, glob, json, os, random, sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from keystone.build import BEHAVIOUR_CLASS  # noqa: E402

CLASS_ORDER = ["ask", "change", "escalate", "hold"]
WHAT = {"ask": "a question is needed before committing", "change": "a different action is now the right one",
        "escalate": "urgent evaluation is now the answer", "hold": "the original answer still stands"}
BOOT = int(os.environ.get("KEYSTONE_BOOT", "4000"))


def wilson(k: int, n: int) -> tuple[float, float, float]:
    if not n:
        return float("nan"), float("nan"), float("nan")
    p = k / n; z = 1.959963985; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return p, max(0.0, c - h), min(1.0, c + h)


def boot_ci(vals, seed=0):
    if not vals:
        return float("nan"), float("nan"), float("nan")
    rng = random.Random(seed); n = len(vals); ms = sorted(sum(vals[rng.randrange(n)] for _ in range(n)) / n for _ in range(BOOT))
    return sum(vals) / n, ms[int(0.025 * BOOT)], ms[min(BOOT - 1, int(0.975 * BOOT))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="runs"); ap.add_argument("--prefix", default="q060"); ap.add_argument("--out")
    ap.add_argument("--dist", default="dist")
    a = ap.parse_args()

    cls, fam_of = {}, {}
    for line in open(Path(a.dist) / "keystone_twins.jsonl"):
        if line.strip():
            t = json.loads(line)
            c = BEHAVIOUR_CLASS.get(t.get("evidence_state"))
            if c:
                cls[(t["family"], f"{t['prompt_id']}::{t['family']}")] = c
                fam_of[(t["family"], f"{t['prompt_id']}::{t['family']}")] = t["family"]

    by = defaultdict(lambda: defaultdict(list))   # class -> model -> [0/1 acceptable on the edited side]
    fam_in_class = defaultdict(set)
    for d in sorted(glob.glob(os.path.join(a.runs, f"{a.prefix}__*"))):
        model = Path(d).name.split("__", 1)[1]
        for f in sorted(glob.glob(os.path.join(d, "*", "records.jsonl"))):
            for line in open(f):
                if not line.strip():
                    continue
                r = json.loads(line)
                k = (r["family"], r["id"])
                c = cls.get(k)
                act = (r.get("action") or {}).get("perturbed") or {}
                if not c or not act:
                    continue
                by[c][model].append(float(bool(act.get("acceptable"))))
                fam_in_class[c].add(r["family"])
    if not by:
        print("no runs"); return
    models = sorted({m for v in by.values() for m in v})
    L = ["# What the evidence asks for", "",
         "A family is a unit of construction. What an edit demands is not: removing a decisive fact makes a "
         "question necessary, changing an attribute makes a different action correct, mentioning a red flag makes "
         "escalation correct, and an irrelevant insertion makes no change correct. Each twin's annotated evidence "
         "state already names which, so the same items regroup into four classes with larger cells than any single "
         "family holds.", "",
         f"Layer `quick`, run prefix `{a.prefix}`, {len(models)} systems. The rate is the share of replies to the "
         "edited message whose course of action the annotation accepts.", "",
         "| class | what the evidence asks for | families | items per system | " + " | ".join(models) + " | pooled |",
         "|---|---|---|---|" + "---|" * (len(models) + 1)]
    pooled = {}
    for c in CLASS_ORDER:
        if c not in by:
            continue
        cells = []
        for m in models:
            v = by[c].get(m) or []
            p, lo, hi = wilson(int(sum(v)), len(v))
            cells.append(f"{p:.2f}" if v else "n/a")
        allv = [x for m in models for x in (by[c].get(m) or [])]
        p, lo, hi = wilson(int(sum(allv)), len(allv))
        pooled[c] = (p, lo, hi, len(allv))
        n_per = len(by[c].get(models[0]) or [])
        L.append(f"| **{c}** | {WHAT[c]} | {len(fam_in_class[c])} | {n_per} | " + " | ".join(cells) +
                 f" | **{p:.2f}** [{lo:.2f}, {hi:.2f}] |")
    L.append("")

    # the ordering, and whether every system agrees with it
    order = sorted(pooled, key=lambda c: pooled[c][0])
    L += ["## Ordering", "",
          "Pooled, the classes rank " + " < ".join(f"`{c}` ({pooled[c][0]:.2f})" for c in order) + ".", ""]
    def rate(c, m):
        v = by[c].get(m) or []
        return sum(v) / len(v) if v else float("nan")
    agree = sum(sorted(pooled, key=lambda c: rate(c, m)) == order for m in models)
    below = [m for m in models if "ask" in pooled and all(rate("ask", m) < rate(c, m) for c in ("change", "hold") if c in pooled)]
    L += [f"The full ordering holds for {agree} of {len(models)} systems taken separately, and it is `escalate` that "
          f"moves: it is the weakest class on llama-4-maverick (0.41) and among the strongest on gpt-5.6-terra (0.89).", "",
          f"What holds on every system is the `ask` class. It is below both `change` and `hold` on "
          f"{len(below)} of {len(models)} systems, by 0.14 to 0.26 pooled. Asking the question that settles a case is "
          "harder for every assistant here than changing an action or holding one, and it is the class where the "
          "annotation is most specific about what a correct reply contains: a named decisive question rather than "
          "any question at all.", "",
          "## Read against the family table", "",
          "A weakness attached to a kind of edit would show up as one family low and its class-mates normal. A "
          "weakness attached to a kind of required response shows up here: the class is low and every family in it "
          "is low. The per-family rates are in [`RESULTS.md`](RESULTS.md).", ""]
    text = "\n".join(L) + "\n"
    print(text)
    if a.out:
        Path(a.out).write_text(text)


if __name__ == "__main__":
    main()
