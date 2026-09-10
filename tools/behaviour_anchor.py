#!/usr/bin/env python3
"""Criterion validity: does the materiality label predict what models actually do?

The other two anchors compare our labels with physician-written artefacts. This one asks the harder
question, the one a rater-agreement study cannot answer: a twin labelled material is supposed to be a twin
where the original commitment is no longer supported, so **assistants should stop committing on it more often
than on a twin labelled immaterial**. That prediction is about behaviour, and the behaviour is already
measured and shipped: `release/reference_records.jsonl` holds every reply of five assistants on the 80
`missing_evidence` twins of the reference pilot, with its classification.

The design has a built-in discriminant control. Each item also carries a paraphrase-only twin, which changes
the wording and no evidence. Materiality must predict the drop in commitment on the **perturbed** side and
must *not* predict it on the **paraphrase** side: a label that predicts both is measuring how much the text
was disturbed, not whether the evidence still supports the answer. The gap between the two is therefore the
estimate to read, and it is computed per item, so no model contributes more than one observation to it.

Materiality is taken from the two rubric-blind reviewers where they agree (the release's own two-rater rule),
with the three-rater median reported next to it. Rates are aggregated per item first, so five replies to the
same twin cannot act as five independent observations.

    python tools/behaviour_anchor.py            # writes docs/BEHAVIOUR_ANCHOR.md
"""
from __future__ import annotations

import argparse
import json
import os
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "BEHAVIOUR_ANCHOR.md"
BOOT = int(os.environ.get("KEYSTONE_BOOT", 4000))
PERM = int(os.environ.get("KEYSTONE_PERM", 20000))


def rows(p: Path) -> list:
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def blind(t: dict):
    a, b = t.get("reviewer_materiality"), t.get("codex_materiality")
    if a in (1, 2, 3) and b in (1, 2, 3):
        return a if a == b else None
    return a if a in (1, 2, 3) else (b if b in (1, 2, 3) else None)


def stance(rec: dict, cond: str):
    return (rec["behavior"].get(cond) or {}).get("stance")


def mean(v: list):
    return sum(v) / len(v) if v else None


def boot_ci(vals: list, seed: int = 0):
    if not vals:
        return None, (None, None)
    rng = random.Random(seed)
    draws = sorted(mean([vals[rng.randrange(len(vals))] for _ in range(len(vals))]) for _ in range(BOOT))
    return mean(vals), (draws[int(0.025 * BOOT)], draws[int(0.975 * BOOT)])


def spearman_perm(pairs: list, seed: int = 0):
    """Rank correlation with a permutation p, which needs no normality at these item counts."""
    if len(pairs) < 8:
        return None, None
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j + 2) / 2
            i = j + 1
        return r
    def rho(xs, ys):
        rx, ry = rank(xs), rank(ys)
        n = len(xs)
        mx, my = mean(rx), mean(ry)
        num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
        den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
        return num / den if den else 0.0
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    obs = rho(xs, ys)
    rng = random.Random(seed)
    hits = 0
    for _ in range(PERM):
        sh = ys[:]
        rng.shuffle(sh)
        if abs(rho(xs, sh)) >= abs(obs):
            hits += 1
    return obs, (hits + 1) / (PERM + 1)


def fmt(x, nd=3):
    return "n/a" if x is None else f"{x:.{nd}f}"


def ci(t):
    return "" if t is None or t[0] is None else f"[{fmt(t[0])}, {fmt(t[1])}]"


def pfmt(p):
    return "n/a" if p is None else (f"<{1 / (PERM + 1):.1g}" if p <= 1 / (PERM + 1) else f"{p:.2g}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dist", default=str(ROOT / "dist"))
    ap.add_argument("--out", default=str(OUT), help="where to write the report (default: the docs page)")
    ap.add_argument("--records", default=str(ROOT / "release" / "reference_records.jsonl"))
    a = ap.parse_args()
    twins = {t["prompt_id"]: t for t in rows(Path(a.dist) / "keystone_twins.jsonl") if t["family"] == "missing_evidence"}
    recs = [r for r in rows(Path(a.records)) if r["family"] == "missing_evidence"]

    # one observation per (item, model), then collapse to items
    per_item = defaultdict(lambda: defaultdict(list))
    per_model = defaultdict(lambda: defaultdict(list))
    for r in recs:
        t = twins.get(r["source_id"])
        if t is None:
            continue
        o, p, q = stance(r, "original"), stance(r, "perturbed"), stance(r, "paraphrase")
        if o is None:                                   # empty reply: missing data, never a stance
            continue
        committed = o == "definitive"
        names = bool((r["behavior"].get("perturbed") or {}).get("names_missing_element"))
        cells = {"committed_original": float(committed)}
        if committed and p is not None:
            cells["dropped_on_twin"] = float(p != "definitive")
            cells["adaptation_failure"] = float(p == "definitive" and not names)
        if committed and q is not None:
            cells["dropped_on_paraphrase"] = float(q != "definitive")
        if p is not None:
            cells["unsafe_on_twin"] = float(bool((r["behavior"].get("perturbed") or {}).get("unsafe_action")))
        if r.get("rubric") and r["rubric"].get("inapplicable_share") is not None:
            cells["inapplicable_share"] = float(r["rubric"]["inapplicable_share"])
        for k, v in cells.items():
            per_item[r["source_id"]][k].append(v)
            per_model[r["model"]][k].append((r["source_id"], v))

    items = {}
    for sid, d in per_item.items():
        t = twins[sid]
        items[sid] = {"blind": blind(t), "majority": t.get("materiality_majority"),
                      **{k: mean(v) for k, v in d.items()},
                      "n_models": len(d.get("committed_original", []))}

    def table(label_key: str, title: str) -> list:
        lv = defaultdict(list)
        for sid, it in items.items():
            if it[label_key] in (1, 2, 3):
                lv[it[label_key]].append(it)
        L = [f"### {title}", "",
             "| Materiality | Items | Committed on the original | Dropped commitment on the twin | Stayed definitive without naming "
             "the change | Dropped on the paraphrase (control) | Evidence effect, twin minus paraphrase |", "|---|---|---|---|---|---|---|"]
        for k in (3, 2, 1):
            its = lv.get(k, [])
            if not its:
                L.append(f"| {k} | 0 | | | | | |")
                continue
            def col(key):
                v = [i[key] for i in its if i.get(key) is not None]
                m, c = boot_ci(v, seed=k)
                return f"{fmt(m)} {ci(c)}" if m is not None else "n/a"
            gap = [i["dropped_on_twin"] - i["dropped_on_paraphrase"] for i in its
                   if i.get("dropped_on_twin") is not None and i.get("dropped_on_paraphrase") is not None]
            mg, cg = boot_ci(gap, seed=k + 10)
            L.append(f"| {k} | {len(its)} | {col('committed_original')} | {col('dropped_on_twin')} | {col('adaptation_failure')} | "
                     f"{col('dropped_on_paraphrase')} | {fmt(mg)} {ci(cg)} |")
        # trend over items and the discriminant contrast
        def trend(key):
            pairs = [(it[label_key], it[key]) for it in items.values()
                     if it[label_key] in (1, 2, 3) and it.get(key) is not None]
            return spearman_perm(pairs)
        rho_t, p_t = trend("dropped_on_twin")
        rho_c, p_c = trend("dropped_on_paraphrase")
        hi = [i["dropped_on_twin"] - i["dropped_on_paraphrase"] for i in lv.get(3, [])
              if i.get("dropped_on_twin") is not None and i.get("dropped_on_paraphrase") is not None]
        lo = [i["dropped_on_twin"] - i["dropped_on_paraphrase"] for i in lv.get(1, [])
              if i.get("dropped_on_twin") is not None and i.get("dropped_on_paraphrase") is not None]
        diff = None
        if hi and lo:
            rng = random.Random(1)
            obs = mean(hi) - mean(lo)
            draws = sorted(mean([hi[rng.randrange(len(hi))] for _ in hi]) - mean([lo[rng.randrange(len(lo))] for _ in lo])
                           for _ in range(BOOT))
            diff = (obs, (draws[int(0.025 * BOOT)], draws[int(0.975 * BOOT)]))
        L += ["",
              f"Trend over items: Spearman rho {fmt(rho_t)} on the twin (permutation p {pfmt(p_t)}) against "
              f"{fmt(rho_c)} on the paraphrase control (p {pfmt(p_c)}).",
              "" if diff is None else
              f"Evidence effect at materiality 3 minus materiality 1: {fmt(diff[0])} {ci(diff[1])}.", ""]
        return L

    L = ["# Criterion validity: materiality against measured behaviour", "",
         "Both other anchors ask whether our labels agree with something physicians wrote. This one asks whether the label predicts "
         "what it claims to predict. A twin labelled material is one whose original commitment the evidence no longer supports, so "
         "assistants should stop committing on it more often than on a twin labelled immaterial. The replies that test this are already "
         "in the release: five assistants on the 80 `missing_evidence` twins of the reference pilot, each reply classified, each item also "
         "answered in a paraphrase-only version that changes wording and no evidence.", "",
         "**Why the paraphrase column decides it.** A label that predicts the drop on both sides is tracking how much the message was "
         "disturbed. A label that predicts the drop on the perturbed side only is tracking the evidence. The last column is that "
         "difference, per item, and it is the number this page is for.", "",
         "Rates are computed per item across the five assistants before being averaged, so one item contributes one observation. "
         "Intervals are 95 percent bootstrap over items. Empty replies are missing data and enter no denominator.", ""]
    L += ["The fourth column is the release's adaptation-failure outcome under a plainer name, because on an immaterial twin staying "
          "definitive is the correct behaviour: that column is a quality measure only where the edit is material, and it is shown across all "
          "three levels so the contrast is visible rather than hidden.", ""]
    L += table("blind", "Materiality from the two rubric-blind reviewers, where they agree")
    L += table("majority", "Materiality as the three-rater median, for comparison")

    # per-model, so that one assistant cannot carry the result
    L += ["### Per assistant", "",
          "The same contrast computed inside each assistant's own replies, to show the result is not one model's behaviour.", "",
          "| Assistant | Items | Dropped on twin, materiality 3 | materiality 1 | Difference |", "|---|---|---|---|---|"]
    for model in sorted(per_model):
        byl = defaultdict(list)
        for sid, v in per_model[model].get("dropped_on_twin", []):
            lab = items.get(sid, {}).get("blind")
            if lab in (1, 2, 3):
                byl[lab].append(v)
        if not byl.get(3) or not byl.get(1):
            L.append(f"| `{model.split('/')[-1]}` | {sum(len(v) for v in byl.values())} | too few at one end | | |")
            continue
        L.append(f"| `{model.split('/')[-1]}` | {sum(len(v) for v in byl.values())} | {fmt(mean(byl[3]))} (n={len(byl[3])}) | "
                 f"{fmt(mean(byl[1]))} (n={len(byl[1])}) | {fmt(mean(byl[3]) - mean(byl[1]))} |")

    # the rubric side: does materiality predict how much of the physician rubric stops applying
    app = [(it["blind"], it["inapplicable_share"]) for it in items.values()
           if it["blind"] in (1, 2, 3) and it.get("inapplicable_share") is not None]
    rho_a, p_a = spearman_perm(app)
    L += ["", "### The rubric side", "",
          f"On the {len(app)} items whose replies were also rubric-graded, the share of the physicians' criteria that the applicability "
          f"judge ruled no longer judgeable tracks materiality at Spearman rho {fmt(rho_a)} (permutation p {pfmt(p_a)}). "
          "Same labels, a different measured consequence.", ""]

    L += ["## Reading", "",
          "The label earns its name when the twin column rises with materiality while the paraphrase column stays flat, because that is "
          "the difference between a label that tracks evidence and a label that tracks editing. Read the last column of each table "
          "first, then the per-assistant table to check that no single model carries it.", "",
          "Limits worth stating. Eighty items and five assistants from one pilot, so the intervals are wide and the materiality-1 cell is "
          "the smallest; the classification of each reply is a model's, the same judge family throughout; and this is the "
          "`missing_evidence` family only, because that is the family the pilot covered. Running the other families is the obvious "
          "extension and needs model calls rather than new data. A label that predicts behaviour is still a label a model wrote: the "
          "release stays `tier: silver`, and `gold` is the tier a clinician-confirmed row carries.", ""]
    Path(a.out).write_text("\n".join(L) + "\n")
    print(f"{len(items)} items, {len(recs)} records -> {a.out}")


if __name__ == "__main__":
    main()
