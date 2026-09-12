#!/usr/bin/env python3
"""Criterion validity: does the materiality label predict what models actually do?

The other two anchors compare our labels with physician-written artefacts. This one asks the harder question,
the one a rater-agreement study cannot answer: a twin labelled material is supposed to be a twin whose original
commitment the evidence no longer supports, so **assistants should behave differently on it than on a twin
labelled immaterial**. That prediction is about behaviour, and behaviour is measured.

The design has a built-in discriminant control. Every item also carries a paraphrase-only twin, which changes
the wording and no evidence. Materiality must predict the change on the **perturbed** side and must *not*
predict it on the **paraphrase** side: a label that predicts both is measuring how much the text was disturbed
rather than whether the evidence still supports the answer. Each table's last column is that difference,
computed per item, so no model contributes more than one observation to it.

Two outcomes, because the families ask for different behaviour. **Dropped commitment** is the removal
families' prediction and means little where the correct response is to change the action rather than withhold
it. **Forbidden action** is the 0.5.0 outcome and is defined for every family against that twin's own
annotation, so it is the one to read outside `missing_evidence`.

Materiality comes from the two rubric-blind reviewers where they agree, the release's own two-rater rule, with
the three-rater median beside it. Rates are aggregated per item before being averaged.

    python tools/behaviour_anchor.py                                  # the shipped reference pilot
    python tools/behaviour_anchor.py --family all --records release/reference_records.jsonl runs/quick__*
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


def load_records(paths: list[str]) -> list:
    """Records from several runs. A run's records carry no model name, so take it from its summary.json."""
    out = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            p = p / "records.jsonl"
        if not p.exists():
            continue
        model = None
        summary = p.parent / "summary.json"
        if summary.exists():
            meta = json.loads(summary.read_text()).get("meta") or {}
            model = meta.get("model")
        for r in rows(p):
            r["model"] = r.get("model") or model or p.parent.name
            out.append(r)
    return out


def blind(t: dict):
    a, b = t.get("reviewer_materiality"), t.get("codex_materiality")
    if a in (1, 2, 3) and b in (1, 2, 3):
        return a if a == b else None
    return a if a in (1, 2, 3) else (b if b in (1, 2, 3) else None)


def stance(rec: dict, cond: str):
    return (rec.get("behavior", {}).get(cond) or {}).get("stance")


def forbidden(rec: dict, cond: str):
    """True when the judge named a forbidden action for this condition, None when it did not judge it."""
    a = (rec.get("action") or {}).get(cond)
    if not a:
        return None
    return bool(a.get("forbidden"))


def mean(v: list):
    return sum(v) / len(v) if v else None


def boot_ci(vals: list, seed: int = 0):
    if not vals:
        return None, (None, None)
    rng = random.Random(seed)
    draws = sorted(mean([vals[rng.randrange(len(vals))] for _ in range(len(vals))]) for _ in range(BOOT))
    return mean(vals), (draws[int(0.025 * BOOT)], draws[int(0.975 * BOOT)])


def boot_diff(hi: list, lo: list, seed: int = 1):
    if not hi or not lo:
        return None, (None, None)
    rng = random.Random(seed)
    draws = sorted(mean([hi[rng.randrange(len(hi))] for _ in hi]) - mean([lo[rng.randrange(len(lo))] for _ in lo])
                   for _ in range(BOOT))
    return mean(hi) - mean(lo), (draws[int(0.025 * BOOT)], draws[int(0.975 * BOOT)])


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
        mx, my = mean(rx), mean(ry)
        num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
        den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
        return num / den if den else 0.0
    xs, ys = [p[0] for p in pairs], [p[1] for p in pairs]
    obs = rho(xs, ys)
    rng = random.Random(seed)
    hits = 0
    for _ in range(PERM):
        sh = ys[:]
        rng.shuffle(sh)
        hits += abs(rho(xs, sh)) >= abs(obs)
    return obs, (hits + 1) / (PERM + 1)


def fmt(x, nd=3):
    return "n/a" if x is None else f"{x:.{nd}f}"


def ci(t):
    return "" if t is None or t[0] is None else f"[{fmt(t[0])}, {fmt(t[1])}]"


def pfmt(p):
    return "n/a" if p is None else (f"<{1 / (PERM + 1):.1g}" if p <= 1 / (PERM + 1) else f"{p:.2g}")


def collect(twins: dict, recs: list) -> tuple[dict, dict]:
    """One observation per (item, model), collapsed to items. Returns items and the per-model view."""
    per_item, per_model = defaultdict(lambda: defaultdict(list)), defaultdict(lambda: defaultdict(list))
    for r in recs:
        t = twins.get(r.get("source_id"))
        if t is None:
            continue
        o, p, q = stance(r, "original"), stance(r, "perturbed"), stance(r, "paraphrase")
        if o is None:                                   # empty reply: missing data, never a stance
            continue
        committed = o == "definitive"
        names = bool((r.get("behavior", {}).get("perturbed") or {}).get("names_missing_element"))
        cells = {"committed_original": float(committed)}
        if committed and p is not None:
            cells["dropped_on_twin"] = float(p != "definitive")
            cells["held_without_naming"] = float(p == "definitive" and not names)
        if committed and q is not None:
            cells["dropped_on_paraphrase"] = float(q != "definitive")
        for cond, key in (("perturbed", "forbidden_on_twin"), ("paraphrase", "forbidden_on_paraphrase")):
            f = forbidden(r, cond)
            if f is not None:
                cells[key] = float(f)
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
    return items, per_model


def contrast_table(items: dict, label_key: str, twin_key: str, control_key: str, title: str, note: str) -> list:
    lv = defaultdict(list)
    for it in items.values():
        if it[label_key] in (1, 2, 3):
            lv[it[label_key]].append(it)
    # The `all` row is every item with both sides judged, whatever its materiality label. Restricting it to
    # labelled items silently selected a subset (19 of 40 missing_evidence items) and overstated the effect.
    paired = [i for i in items.values() if i.get(twin_key) is not None and i.get(control_key) is not None]
    if len(paired) < 5:
        return [f"#### {title}", "", "Too few paired items.", ""]
    L = [f"#### {title}", "", note, "",
         "| Materiality | Items | On the twin | On the paraphrase (control) | Evidence effect |", "|---|---|---|---|---|"]
    gaps = {}
    # Every item first. On a run over the quick or strict set the materiality rows below are empty by
    # construction, because those layers admit one materiality, and this row is then the whole result: the
    # edit moved the behaviour and the reword of the same message did not.
    ga = [i[twin_key] - i[control_key] for i in paired]
    def col_of(its, key, seed=0):
        v = [i[key] for i in its if i.get(key) is not None]
        m, c = boot_ci(v, seed=seed)
        return f"{fmt(m)} {ci(c)}" if m is not None else "n/a"
    mga, cga = boot_ci(ga, seed=99)
    L.append(f"| all | {len(paired)} | {col_of(paired, twin_key, 1)} | {col_of(paired, control_key, 2)} | {fmt(mga)} {ci(cga)} |")
    for k in (3, 2, 1):
        # n is the number of items that carry both cells, not every item with the label
        its = [i for i in lv.get(k, []) if i.get(twin_key) is not None and i.get(control_key) is not None]
        if not its:
            L.append(f"| {k} | 0 | | | |")
            continue
        def col(key):
            v = [i[key] for i in its if i.get(key) is not None]
            m, c = boot_ci(v, seed=k)
            return f"{fmt(m)} {ci(c)}" if m is not None else "n/a"
        gap = [i[twin_key] - i[control_key] for i in its
               if i.get(twin_key) is not None and i.get(control_key) is not None]
        gaps[k] = gap
        mg, cg = boot_ci(gap, seed=k + 10)
        L.append(f"| {k} | {len(its)} | {col(twin_key)} | {col(control_key)} | {fmt(mg)} {ci(cg)} |")
    if len([k for k in (1, 2, 3) if len(lv.get(k, [])) >= 5]) < 2:
        L += ["", "This layer admits a single materiality, so the rows below `all` are empty and no trend is defined. "
                  "The `all` row is the comparison the design rests on: the same item, edited two ways.", ""]
        return L
    def trend(key):
        return spearman_perm([(it[label_key], it[key]) for it in items.values()
                              if it[label_key] in (1, 2, 3) and it.get(key) is not None])
    rt, pt = trend(twin_key)
    rc, pc = trend(control_key)
    d, cd = boot_diff(gaps.get(3, []), gaps.get(1, []))
    L += ["", f"Trend over items: rho {fmt(rt)} on the twin (p {pfmt(pt)}) against {fmt(rc)} on the control (p {pfmt(pc)}). "
              + (f"Evidence effect at materiality 3 minus 1: {fmt(d)} {ci(cd)}." if d is not None else ""), ""]
    return L


def analyse(fam: str, twins: dict, recs: list) -> list:
    items, per_model = collect(twins, recs)
    models = sorted({r["model"] for r in recs})
    L = [f"### `{fam}`", "",
         f"{len(items)} items, {len(models)} assistant{'s' if len(models) != 1 else ''}, {len(recs)} records.", ""]
    L += contrast_table(items, "blind", "dropped_on_twin", "dropped_on_paraphrase",
                        "Dropped commitment, by rubric-blind materiality",
                        "Share of assistants that stopped committing, among those that committed on the original. "
                        "This is the removal families' prediction; where the correct response is a *different* action "
                        "rather than none, read the next table instead.")
    if any(i.get("forbidden_on_twin") is not None for i in items.values()):
        L += contrast_table(items, "blind", "forbidden_on_twin", "forbidden_on_paraphrase",
                            "Forbidden action, by rubric-blind materiality",
                            "Share of assistants that took an action this twin's own annotation forbids. Defined for "
                            "every family, so this is the cross-family outcome.")
    hi = [(sid, v) for sid, v in per_model.items()]
    if len(models) > 1:
        L += ["#### Per assistant", "",
              "The twin-side rate inside each assistant's own replies, so the result is not one model's behaviour.", "",
              "| Assistant | Materiality 3 | Materiality 1 | Difference |", "|---|---|---|---|"]
        for model in models:
            byl = defaultdict(list)
            for sid, v in per_model[model].get("dropped_on_twin", []):
                lab = items.get(sid, {}).get("blind")
                if lab in (1, 2, 3):
                    byl[lab].append(v)
            if not byl.get(3) or not byl.get(1):
                L.append(f"| `{model.split('/')[-1]}` | too few at one end | | |")
                continue
            L.append(f"| `{model.split('/')[-1]}` | {fmt(mean(byl[3]))} (n={len(byl[3])}) | {fmt(mean(byl[1]))} (n={len(byl[1])}) | "
                     f"{fmt(mean(byl[3]) - mean(byl[1]))} |")
        L.append("")
    app = [(it["blind"], it["inapplicable_share"]) for it in items.values()
           if it["blind"] in (1, 2, 3) and it.get("inapplicable_share") is not None]
    if len(app) >= 10:
        r, p = spearman_perm(app)
        L += [f"On the {len(app)} items whose replies were also rubric-graded, the share of the physicians' criteria the "
              f"applicability judge ruled no longer judgeable tracks the same label at rho {fmt(r)} (p {pfmt(p)}).", ""]
    return L


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dist", default=str(ROOT / "dist"))
    ap.add_argument("--out", default=str(OUT), help="where to write the report (default: the docs page)")
    ap.add_argument("--records", nargs="+", default=[str(ROOT / "release" / "reference_records.jsonl")],
                    help="records.jsonl files or run directories; a run's model comes from its summary.json")
    ap.add_argument("--family", default="missing_evidence", help="one family, or 'all' for a section each")
    a = ap.parse_args()
    all_twins = rows(Path(a.dist) / "keystone_twins.jsonl")
    all_recs = load_records(a.records)
    fams = (sorted({r["family"] for r in all_recs if r.get("family") and r["family"] != "reference"})
            if a.family == "all" else [a.family])

    sections, done = [], []
    for fam in fams:
        twins = {t["prompt_id"]: t for t in all_twins if t["family"] == fam}
        recs = [r for r in all_recs if r.get("family") == fam]
        if len({r["source_id"] for r in recs}) < 10:
            continue
        done.append(fam)
        sections += analyse(fam, twins, recs)
    if not sections:
        raise SystemExit("no family has enough records to analyse")

    models = sorted({r["model"] for r in all_recs})
    L = ["# Criterion validity: materiality against measured behaviour", "",
         "The other two anchors ask whether our labels agree with something physicians wrote. This one asks whether the "
         "label predicts what it claims to predict: on a twin whose edit is material, assistants should behave "
         "differently, and on the paraphrase-only twin of the same item they should not. The second half is what makes "
         "this a test rather than a correlation, because a label that predicts both sides is tracking how much the text "
         "was disturbed rather than whether the evidence still supports the answer.", "",
         f"Sources: {', '.join(Path(p).name if Path(p).is_file() else Path(p).name for p in a.records)}. "
         f"Assistants: {', '.join(m.split('/')[-1] for m in models)}. Families with at least ten items: "
         f"{', '.join('`' + f + '`' for f in done)}.", "",
         "Rates are computed per item across assistants before being averaged, so one item is one observation. "
         "Intervals are 95 percent bootstrap over items; empty replies are missing data and enter no denominator.", ""]
    L += sections
    L += ["## Reading", "",
          "The label earns its name where the twin column rises with materiality while the paraphrase column stays flat. "
          "Read the evidence-effect column first, then the per-assistant table to check that no single model carries it.", "",
          "`Forbidden action` is the outcome to compare across families: dropping a commitment is the right response only "
          "where the evidence went missing, while taking an action the annotation forbids is wrong everywhere.", "",
          "Limits. Every classification here is a model's, from one judge family. A label that predicts behaviour is still "
          "a label a model wrote: the release stays `tier: silver`, and `gold` is the tier a clinician-confirmed row "
          "carries.", ""]
    Path(a.out).write_text("\n".join(L) + "\n")
    print(f"{len(done)} famil{'y' if len(done) == 1 else 'ies'} ({', '.join(done)}), {len(all_recs)} records, "
          f"{len(models)} model(s) -> {a.out}")


if __name__ == "__main__":
    main()
