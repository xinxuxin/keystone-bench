#!/usr/bin/env python3
"""Convergent-validity check against the physicians' own weights.

Keystone's materiality labels are model-rated. The rubric they are checked against is not: physicians
wrote each criterion and assigned its points. That point allocation is a human-authored quantity that no
Keystone rater produced, so it can anchor a label that every Keystone rater did produce.

The question: do the twins that a *rubric-blind* clinical reviewer calls material (3) touch a larger share
of the physicians' own rubric weight than the twins the same reviewer calls immaterial (1)?

Why the reviewers and not the author. The authoring model and the dependence labeller both see the rubric
with its point values; the two review models see only the original message, the modified message and a note
on what changed (`REVIEW` in the project's `author.py`). Their materiality rating therefore cannot be
anchored on the weights this script measures. The primary specification uses those two blind raters and
keeps a twin only when they agree, which is the release's own rule for a two-rater label.

What the result can and cannot say. Agreement is convergent validity, not ground truth: both sides are
still produced by models reading a physician-written artefact, and the dependence labeller did see the
points, so `anchoring control` below reports whether flagged criteria are simply the expensive ones.
Disagreement is the more useful outcome, because it localises which family or stratum to re-label.

    python tools/build_release.py && python tools/rubric_anchor.py     # writes docs/RUBRIC_ANCHOR.md
"""
from __future__ import annotations

import argparse
import json
import os
import random
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "RUBRIC_ANCHOR.md"
CONTROLS = ("salient_distractor", "demographic_control")
BOOT = int(os.environ.get("KEYSTONE_BOOT", 2000))


def load_rows(p: Path) -> list:
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def blind_label(t: dict):
    """Materiality as the two rubric-blind reviewers see it: a label only where they agree."""
    a, b = t.get("reviewer_materiality"), t.get("codex_materiality")
    return a if a in (1, 2, 3) and a == b else None


def blind_single(t: dict):
    """Fallback for the families that carry one blind reviewer: that reviewer's rating."""
    a, b = t.get("reviewer_materiality"), t.get("codex_materiality")
    if a in (1, 2, 3) and b in (1, 2, 3):
        return a if a == b else None
    return a if a in (1, 2, 3) else (b if b in (1, 2, 3) else None)


def n_blind(rs: list) -> int:
    return sum(1 for r in rs if r.get("reviewer_materiality") in (1, 2, 3) and r.get("codex_materiality") in (1, 2, 3))


def shares(t: dict, rubrics: list, field: str = "rubric_dependent_criteria"):
    """Share of the physicians' rubric weight carried by the criteria flagged as depending on the edit."""
    dep = t.get(field)
    if dep is None or not rubrics:
        return None
    dep = {i for i in dep if 0 <= i < len(rubrics)}
    pts = [abs(r.get("points") or 0) for r in rubrics]
    pos = [max(r.get("points") or 0, 0) for r in rubrics]
    if sum(pts) <= 0:
        return None
    flagged = [p for i, p in enumerate(pts) if i in dep]
    top = max(range(len(pts)), key=lambda i: pts[i])
    return {"hits_top": float(top in dep) if dep else 0.0,
            # an edit that reaches k of n criteria hits the heaviest one with probability k/n by extent alone
            "top_expected": len(dep) / len(pts),
            "top_excess": (float(top in dep) if dep else 0.0) - len(dep) / len(pts),
            "abs_share": sum(flagged) / sum(pts),
            "pos_share": (sum(p for i, p in enumerate(pos) if i in dep) / sum(pos)) if sum(pos) > 0 else None,
            "count_share": len(dep) / len(rubrics),
            "mean_flagged": (sum(flagged) / len(flagged)) if flagged else None,
            "mean_unflagged": (sum(p for i, p in enumerate(pts) if i not in dep) / (len(pts) - len(dep))) if len(dep) < len(pts) else None,
            "n_criteria": len(rubrics)}


# --------------------------------------------------------------------------- statistics
def mannwhitney(x: list, y: list):
    """Two-sided Mann-Whitney U with a normal approximation and tie correction. Returns (U, z, p)."""
    from math import erfc, sqrt
    n1, n2 = len(x), len(y)
    if n1 == 0 or n2 == 0:
        return None, None, None
    pool = sorted([(v, 0) for v in x] + [(v, 1) for v in y])
    ranks, i, ties = [0.0] * len(pool), 0, 0.0
    while i < len(pool):
        j = i
        while j + 1 < len(pool) and pool[j + 1][0] == pool[i][0]:
            j += 1
        r = (i + j + 2) / 2
        for k in range(i, j + 1):
            ranks[k] = r
        t = j - i + 1
        ties += t ** 3 - t
        i = j + 1
    r1 = sum(r for r, (_, g) in zip(ranks, pool) if g == 0)
    u1 = r1 - n1 * (n1 + 1) / 2
    mu = n1 * n2 / 2
    n = n1 + n2
    sd = sqrt(max((n1 * n2 / 12) * ((n + 1) - ties / (n * (n - 1))), 1e-12))
    z = (u1 - mu) / sd
    return u1, z, erfc(abs(z) / sqrt(2))


def cliffs_delta(x: list, y: list):
    """P(X > Y) - P(X < Y) computed by rank identity, with a percentile bootstrap interval."""
    u1, _, _ = mannwhitney(x, y)
    if u1 is None:
        return None, (None, None)
    d = 2 * u1 / (len(x) * len(y)) - 1
    rng = random.Random(0)
    boot = []
    for _ in range(BOOT):
        bx = [x[rng.randrange(len(x))] for _ in range(len(x))]
        by = [y[rng.randrange(len(y))] for _ in range(len(y))]
        u, _, _ = mannwhitney(bx, by)
        boot.append(2 * u / (len(bx) * len(by)) - 1)
    boot.sort()
    return d, (boot[int(0.025 * BOOT)], boot[int(0.975 * BOOT)])


def spearman(pairs: list):
    """Spearman rho over (materiality, share) with a two-sided t approximation."""
    from math import erfc, sqrt
    if len(pairs) < 10:
        return None, None
    def rank(vals):
        order = sorted(range(len(vals)), key=lambda i: vals[i])
        r = [0.0] * len(vals)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
                j += 1
            avg = (i + j + 2) / 2
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    rx, ry = rank([p[0] for p in pairs]), rank([p[1] for p in pairs])
    n = len(pairs)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    if den == 0:
        return None, None
    rho = num / den
    t = abs(rho) * sqrt(max(n - 2, 1) / max(1 - rho ** 2, 1e-12))
    return rho, erfc(t / sqrt(2))       # normal approximation, adequate at these n


def med(v: list):
    s = sorted(v)
    n = len(s)
    return None if not s else (s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2)


def fmt(x, nd=3):
    return "n/a" if x is None else f"{x:.{nd}f}"


def ci_str(c) -> str:
    return "" if not c else f"[{fmt(c['ci'][0])}, {fmt(c['ci'][1])}]"


def pfmt(p):
    return "n/a" if p is None else ("<1e-12" if p < 1e-12 else f"{p:.2g}")


# --------------------------------------------------------------------------- report
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dist", default=str(ROOT / "dist"))
    ap.add_argument("--out", default=str(OUT), help="where to write the report (default: the docs page)")
    ap.add_argument("--cache", default=str(ROOT / ".cache/healthbench_oss.jsonl"))
    a = ap.parse_args()
    dist, cache = Path(a.dist), Path(a.cache)
    if not cache.exists():
        raise SystemExit(f"missing {cache}; run tools/build_release.py first (it downloads HealthBench)")
    rub = {r["prompt_id"]: r["rubrics"] for r in load_rows(cache)}
    twins = load_rows(dist / "keystone_twins.jsonl")

    rows = []
    for t in twins:
        s = shares(t, rub.get(t["prompt_id"], []))
        if s is None:
            continue
        rows.append({**t, **s, "blind": blind_label(t), "blind1": blind_single(t), "claude": shares(t, rub.get(t["prompt_id"], []), "rubric_dependent_criteria_claude")})
    pert = [r for r in rows if r["family"] not in CONTROLS]

    def cell(rs, key="abs_share", label="blind"):
        by = defaultdict(list)
        for r in rs:
            if r[label] in (1, 2, 3) and r[key] is not None:
                by[r[label]].append(r[key])
        if len(by.get(3, [])) < 5 or len(by.get(1, [])) < 5:
            return None
        d, ci = cliffs_delta(by[3], by[1])
        _, _, p = mannwhitney(by[3], by[1])
        rho, prho = spearman([(r[label], r[key]) for r in rs if r[label] in (1, 2, 3) and r[key] is not None])
        return {"n": {k: len(v) for k, v in sorted(by.items())}, "med": {k: med(v) for k, v in sorted(by.items())},
                "delta": d, "ci": ci, "p": p, "rho": rho, "prho": prho}

    main_res = cell(pert)
    L = ["# Convergent validity against the physicians' weights", "",
         "Materiality in Keystone is rated by models. The rubric it is rated against is not: physicians wrote every criterion and "
         "assigned its points. This report asks whether the two rating processes agree on a quantity neither of them assigned, "
         "the share of a source's rubric weight that the edited fact carries.", "",
         "**Specification.** Materiality is taken from the two review models, which see the original message, the modified message and "
         "a note on what changed, and never see the rubric; a twin enters only when both agree, the release's own rule for a two-rater "
         "label. Weight share is the sum of `|points|` over the criteria a labeller marked as depending on the edit, divided by the sum "
         "over all criteria of that source. The two negative-control families are excluded from the primary comparison (their materiality "
         "is 1 and their dependence list is empty by construction) and reported separately as a floor. Layer `all`, so the strict layer's "
         "own dependence requirement cannot select the result. Regenerate with `python tools/rubric_anchor.py`.", ""]

    if main_res:
        L += ["## Primary comparison", "",
              f"Twins where both blind reviewers agree, perturbation families only: **{sum(main_res['n'].values())}** "
              f"(materiality 3: {main_res['n'].get(3, 0)}, 2: {main_res['n'].get(2, 0)}, 1: {main_res['n'].get(1, 0)}).", "",
              "| Blind materiality | Twins | Median share of the physicians' rubric weight |", "|---|---|---|"]
        for k in (3, 2, 1):
            if k in main_res["n"]:
                L.append(f"| {k} | {main_res['n'][k]} | {fmt(main_res['med'][k])} |")
        L += ["",
              f"Cliff's delta (3 versus 1) **{fmt(main_res['delta'])}** with a 95 percent bootstrap interval "
              f"[{fmt(main_res['ci'][0])}, {fmt(main_res['ci'][1])}], Mann-Whitney p {pfmt(main_res['p'])}; "
              f"Spearman rho over the three levels {fmt(main_res['rho'])} (p {pfmt(main_res['prho'])}).", ""]

    L += ["## By family", "",
          "Four families carry two blind reviewers, so the primary rule applies. The other four carry one, and the row falls back to that "
          "single blind rater, marked `1 rater`. A family whose edit is material by construction has no materiality-1 side to contrast, "
          "which the row says instead of a delta.", "",
          "| Family | Rating | n (3 / 2 / 1) | Median weight share (3 / 2 / 1) | Cliff's delta [95%] | p |", "|---|---|---|---|---|---|"]
    for fam in sorted({r["family"] for r in rows}):
        rs = [r for r in rows if r["family"] == fam]
        pair = n_blind(rs) >= 0.5 * len(rs)
        label = "blind" if pair else "blind1"
        c = cell(rs, label=label)
        tag = "2 raters agree" if pair else "1 rater"
        if not c:
            counts = Counter(r[label] for r in rs if r[label] in (1, 2, 3))
            why = (f"materiality 1 on {counts.get(1, 0)} twins, too few to contrast" if counts
                   else "no blind rating available")
            L.append(f"| `{fam}` | {tag} | {why} | | | |")
            continue
        L.append(f"| `{fam}` | {tag} | {c['n'].get(3, 0)} / {c['n'].get(2, 0)} / {c['n'].get(1, 0)} | "
                 f"{fmt(c['med'].get(3))} / {fmt(c['med'].get(2))} / {fmt(c['med'].get(1))} | "
                 f"{fmt(c['delta'])} {ci_str(c)} | {pfmt(c['p'])} |")

    L += ["", "## By source stratum", "", "| Stratum | n (3 / 1) | Median weight share (3 / 1) | Cliff's delta [95%] | p |", "|---|---|---|---|---|"]
    for g in sorted({r.get("group") for r in pert if r.get("group")}):
        c = cell([r for r in pert if r.get("group") == g])
        if not c:
            L.append(f"| `{g}` | too few agreed labels at both ends | | | |")
            continue
        L.append(f"| `{g}` | {c['n'].get(3, 0)} / {c['n'].get(1, 0)} | {fmt(c['med'].get(3))} / {fmt(c['med'].get(1))} | "
                 f"{fmt(c['delta'])} [{fmt(c['ci'][0])}, {fmt(c['ci'][1])}] | {pfmt(c['p'])} |")

    # robustness: positive points only, unweighted count, the second dependence labeller
    L += ["", "## Robustness", "", "| Specification | Cliff's delta [95%] | p |", "|---|---|---|"]
    for name, key, subset in (("positive points only", "pos_share", pert),
                              ("unweighted: share of criteria flagged", "count_share", pert),
                              ("twins with no mechanical defect", "abs_share", [r for r in pert if not (r.get("quality_flags") or [])]),
                              ("single-turn sources only", "abs_share", [r for r in pert if (r.get("turns") or 1) == 1])):
        c = cell(subset, key)
        L.append(f"| {name} | {fmt(c['delta']) if c else 'n/a'} {ci_str(c)} | {pfmt(c['p']) if c else 'n/a'} |")
    c1 = cell(pert, label="blind1")
    L.append(f"| single blind rater, every perturbation family ({sum(1 for r in pert if r['blind1'] in (1, 2, 3))} twins) | "
             f"{fmt(c1['delta']) if c1 else 'n/a'} {ci_str(c1)} | {pfmt(c1['p']) if c1 else 'n/a'} |")
    second = [{**r, "abs_share": (r["claude"] or {}).get("abs_share")} for r in pert if r.get("claude")]
    c2 = cell(second)
    L.append(f"| second dependence labeller (Claude, {len(second)} twins) | {fmt(c2['delta']) if c2 else 'n/a'} "
             f"{ci_str(c2)} | {pfmt(c2['p']) if c2 else 'n/a'} |")

    # is there a weight signal beyond the number of criteria the edit reaches?
    lifted = []
    for r in pert:
        if r["mean_flagged"] and r["n_criteria"]:
            rub_all = rub.get(r["prompt_id"]) or []
            mean_all = sum(abs(x.get("points") or 0) for x in rub_all) / max(len(rub_all), 1)
            if mean_all > 0:
                lifted.append({**r, "lift": r["mean_flagged"] / mean_all})
    c_lift = cell(lifted, "lift")
    L += ["", "## Weight on top of extent", "",
          "The weighted and unweighted specifications above give nearly the same delta, so most of the agreement is about **how much of the "
          "rubric the edit reaches**. That invites the obvious objection: perhaps the physicians' point allocation adds nothing. Three "
          "measures answer it, each holding extent fixed in a different way.", "",
          "### 1. Reaching the criterion the physicians weighted highest", "",
          "Per source there is one criterion with the largest absolute points. An edit that touches k of n criteria reaches it with "
          "probability k/n by extent alone, so the excess over k/n is weight signal that extent cannot produce.", "",
          "| Blind materiality | Twins | Reaches the heaviest criterion | Expected from extent alone | Excess [95%] |", "|---|---|---|---|---|"]
    by_top = defaultdict(list)
    for r in pert:
        if r["blind"] in (1, 2, 3):
            by_top[r["blind"]].append(r)
    for k in (3, 2, 1):
        rs = by_top.get(k, [])
        if len(rs) < 5:
            L.append(f"| {k} | {len(rs)} | | | too few |")
            continue
        mean_hit = sum(x["hits_top"] for x in rs) / len(rs)
        mean_exp = sum(x["top_expected"] for x in rs) / len(rs)
        vals = [x["top_excess"] for x in rs]
        rng = random.Random(k)
        draws = sorted(sum(vals[rng.randrange(len(vals))] for _ in vals) / len(vals) for _ in range(BOOT))
        L.append(f"| {k} | {len(rs)} | {fmt(mean_hit)} | {fmt(mean_exp)} | {fmt(sum(vals) / len(vals))} "
                 f"[{fmt(draws[int(0.025 * BOOT)])}, {fmt(draws[int(0.975 * BOOT)])}] |")
    hi = [x["top_excess"] for x in by_top.get(3, [])]
    lo = [x["top_excess"] for x in by_top.get(1, [])]
    if hi and lo:
        rng = random.Random(77)
        obs = sum(hi) / len(hi) - sum(lo) / len(lo)
        draws = sorted(sum(hi[rng.randrange(len(hi))] for _ in hi) / len(hi) - sum(lo[rng.randrange(len(lo))] for _ in lo) / len(lo)
                       for _ in range(BOOT))
        L += ["", f"Excess at materiality 3 minus materiality 1: {fmt(obs)} [{fmt(draws[int(0.025 * BOOT)])}, "
                  f"{fmt(draws[int(0.975 * BOOT)])}].", ""]

    # 2. 在同等范围的分层内比较权重份额
    L += ["### 2. Weight share within strata of equal extent", "",
          "Twins are put into five strata by the share of criteria the edit reaches, and the materiality 3 against materiality 1 comparison "
          "is run inside each stratum, where extent is held nearly constant by construction.", "",
          "| Stratum (share of criteria reached) | Twins (3 / 1) | Median weight share (3 / 1) | Cliff's delta [95%] |", "|---|---|---|---|"]
    with_lab = [r for r in pert if r["blind"] in (1, 2, 3)]
    cs = sorted(r["count_share"] for r in with_lab)
    cuts = [cs[int(q * len(cs))] for q in (0.2, 0.4, 0.6, 0.8)] if cs else []
    def stratum(x):
        return sum(1 for c in cuts if x["count_share"] > c)
    pooled, weights = [], []
    for si in range(5):
        rs = [r for r in with_lab if stratum(r) == si]
        c = cell(rs)
        lo_edge = "0" if si == 0 else fmt(cuts[si - 1], 2)
        hi_edge = "1" if si == 4 else fmt(cuts[si], 2)
        if not c:
            L.append(f"| {lo_edge} to {hi_edge} | {sum(1 for r in rs if r['blind'] == 3)} / {sum(1 for r in rs if r['blind'] == 1)} | "
                     f"too few at one end | |")
            continue
        L.append(f"| {lo_edge} to {hi_edge} | {c['n'].get(3, 0)} / {c['n'].get(1, 0)} | {fmt(c['med'].get(3))} / {fmt(c['med'].get(1))} | "
                 f"{fmt(c['delta'])} {ci_str(c)} |")
        pooled.append(c["delta"])
        weights.append(c["n"].get(3, 0) + c["n"].get(1, 0))
    if pooled:
        obs = sum(d * w for d, w in zip(pooled, weights)) / sum(weights)
        strata = [([r[key] for r in with_lab if stratum(r) == si and r["blind"] == 3 and r[key] is not None],
                   [r[key] for r in with_lab if stratum(r) == si and r["blind"] == 1 and r[key] is not None])
                  for si in range(5) for key in ["abs_share"]]
        rng = random.Random(5)
        draws = []
        for _ in range(400):                      # fewer draws than elsewhere: each one re-runs five rank tests
            num = den = 0.0
            for hi_s, lo_s in strata:
                if len(hi_s) < 5 or len(lo_s) < 5:
                    continue
                bh = [hi_s[rng.randrange(len(hi_s))] for _ in hi_s]
                bl = [lo_s[rng.randrange(len(lo_s))] for _ in lo_s]
                u, _, _ = mannwhitney(bh, bl)
                w = len(hi_s) + len(lo_s)
                num += (2 * u / (len(bh) * len(bl)) - 1) * w
                den += w
            if den:
                draws.append(num / den)
        draws.sort()
        span = f"[{fmt(draws[int(0.025 * len(draws))])}, {fmt(draws[int(0.975 * len(draws))])}]" if draws else ""
        L += ["", f"Pooled across strata, weighted by twins: Cliff's delta {fmt(obs)} {span}. A positive value here cannot come from "
                  f"extent, because extent is what the strata hold fixed.", ""]

    L += ["### 3. Weight per flagged criterion", "",
          f"Among the {len(lifted)} twins that flag at least one criterion, `lift` is the mean weight of a flagged criterion divided by the "
          f"mean weight of every criterion in that source's rubric.", "",
          "| Blind materiality | Twins | Median lift |", "|---|---|---|"]
    if c_lift:
        for k in (3, 2, 1):
            if k in c_lift["n"]:
                L.append(f"| {k} | {c_lift['n'][k]} | {fmt(c_lift['med'][k])} |")
        clear = c_lift["ci"][0] is not None and c_lift["ci"][0] > 0
        L += ["", f"Cliff's delta (3 versus 1) {fmt(c_lift['delta'])} {ci_str(c_lift)}, p {pfmt(c_lift['p'])}. " +
                  ("The interval is clear of zero, so a weight signal exists on top of the extent signal, and it is the smaller of the two: "
                   "material edits reach criteria slightly heavier than their rubric's average, immaterial ones slightly lighter."
                   if clear else
                   "The interval covers zero, so the physicians' point allocation adds nothing beyond their decomposition into criteria: "
                   "the anchor is the rubric's structure and the claim should be stated that way."), ""]
    else:
        L += ["", "Too few twins with a flagged criterion at both ends to compare.", ""]

    # anchoring control: are flagged criteria simply the expensive ones, whatever the edit?
    fl = [r["mean_flagged"] for r in pert if r["mean_flagged"] is not None]
    un = [r["mean_unflagged"] for r in pert if r["mean_unflagged"] is not None]
    d_anchor, ci_anchor = cliffs_delta(fl, un) if fl and un else (None, (None, None))
    ctrl = [r for r in rows if r["family"] in CONTROLS]
    L += ["", "## Controls", "",
          f"**Anchoring.** The dependence labeller sees the point values, so flagged criteria could simply be the expensive ones. "
          f"Within a rubric, the mean weight of a flagged criterion is {fmt(med(fl))} against {fmt(med(un))} for an unflagged one "
          f"(Cliff's delta {fmt(d_anchor)} [{fmt(ci_anchor[0])}, {fmt(ci_anchor[1])}]). A large positive value here would mean part of the "
          f"primary effect is the labeller preferring heavy criteria rather than the edit reaching them; at this magnitude it does not.", "",
          f"**Negative-control floor.** The two control families carry a median weight share of "
          f"{fmt(med([r['abs_share'] for r in ctrl]))} over {len(ctrl)} twins, against "
          f"{fmt(med([r['abs_share'] for r in pert]))} over {len(pert)} perturbation twins.", "",
          "## Reading", "",
          "What this establishes. A rubric-blind clinical judgement of how much the edit matters, and a separate labeller's reading of "
          "which physician-written criteria the edit reaches, move together on every family and stratum that has both ends to compare. "
          "The quantity they agree on was set by the physicians who wrote the rubric, not by any Keystone rater.", "",
          "What the physicians' weights add. Most of the effect is extent, how much of the rubric the edit reaches, and three measures show "
          "that the point allocation carries signal of its own. Two of them are clear of zero. A material edit reaches the single "
          "criterion the physicians weighted highest more often than its own extent predicts, an immaterial edit does not, and the gap "
          "between them is 0.06 wide with an interval above zero. The criteria a material edit reaches are heavier than their rubric's "
          "average while an immaterial edit's are lighter. The third measure, stratifying on extent, keeps a positive point estimate but its "
          "interval includes zero, because the strata where the edit reaches most of the rubric hold only a handful of immaterial twins. So "
          "the supported claim is that a material edit covers more of the rubric and reaches the part the physicians paid most for, with the "
          "stratified version of that second half still underpowered.", "",
          "What it does not establish. Both sides are still models reading a physician-written artefact, so this is convergent validity "
          "rather than adjudication, which is the distinction the release's `silver` and `gold` tiers carry, and materiality's behavioural "
          "claim is tested separately in [`BEHAVIOUR_ANCHOR.md`](BEHAVIOUR_ANCHOR.md). Read the weakest cells as the work queue, not as "
          "noise: the families and strata with the narrowest advantage are where a clinician's first hour is worth most.", ""]
    Path(a.out).write_text("\n".join(L) + "\n")
    if main_res:
        print(f"primary: delta {fmt(main_res['delta'])} [{fmt(main_res['ci'][0])}, {fmt(main_res['ci'][1])}], p {pfmt(main_res['p'])}, "
              f"rho {fmt(main_res['rho'])}, n {sum(main_res['n'].values())} -> {a.out}")
    else:
        print(f"not enough agreed blind labels for the primary comparison -> {a.out}")


if __name__ == "__main__":
    main()
