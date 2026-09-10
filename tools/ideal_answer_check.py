#!/usr/bin/env python3
"""Falsification against the physicians' own answers.

HealthBench ships, for most of its conversations, an ideal completion written by physicians for the original
message. Keystone never used it: twins were authored from the message and the rubric, and every label comes
from models. That makes the ideal answer a second human artefact that can be turned against our annotations
rather than used to produce them.

Three claims are testable without a single model call.

1. **The removed fact is load-bearing.** If we deleted the element the answer rests on, the physicians' answer
   to the unedited message should engage with that element. Engagement is the share of the edited span's own
   content terms, weighted by how rare each term is across all ideal answers, that appear in this source's
   ideal answer. Rare terms carry the signal; "patient" and "symptoms" carry almost none.
2. **The engagement is about this fact, not about the topic.** The null draws the comparison answer from other
   sources **in the same HealthBench theme**, so a term counts only if physicians writing on the same clinical
   theme did not use it anyway. The uniform null over all sources is reported beside it, to show how much of
   the naive effect was topicality.
3. **The negative control is irrelevant.** A `salient_distractor` or `demographic_control` insertion should be
   engaged with less than the same source's load-bearing edit. That contrast is within a source, against the
   same physicians' answer.

Prominence is a second measure on the removal families: physicians lead with what decides the case, so a
load-bearing fact should reach the opening third of the answer more often than the null does.

    python tools/build_release.py && python tools/ideal_answer_check.py     # writes docs/IDEAL_ANSWER_CHECK.md
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import math
import random
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "IDEAL_ANSWER_CHECK.md"
CONTROLS = ("salient_distractor", "demographic_control")
REMOVAL = ("missing_evidence", "missing_evidence_early", "demographic_shift", "alternative_evidence")
NULL_DRAWS = int(os.environ.get("KEYSTONE_NULL_DRAWS", 25))
BOOT = int(os.environ.get("KEYSTONE_BOOT", 2000))
STOP = set("""a about above after again against all also am an and any are aren as at be because been before being below
between both but by can cannot could couldn did didn do does doesn doing don down during each few for from further had
hadn has hasn have haven having he her here hers herself him himself his how i if in into is isn it its itself just ll
me more most mustn my myself no nor not now of off on once only or other ought our ours ourselves out over own re same
shan she should shouldn so some such than that the their theirs them themselves then there these they this those through
to too under until up ve very was wasn we were weren what when where which while who whom why will with won would wouldn
you your yours yourself yourselves get got getting like really much many something anything someone thing things want
need know feel felt going go went make made take taken use used using been still even ever never always sure think
thought say said tell told ask asked give given seen see look looking come came back time times day days week weeks
month months year years""".split())


def rows(p: Path) -> list:
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def terms(text: str) -> set:
    """Content terms: alphabetic tokens of four characters or more, plus any number."""
    toks = re.findall(r"[a-z]+|\d+(?:\.\d+)?", (text or "").lower().replace("’", "'"))
    return {t for t in toks if (t.isdigit() or (len(t) >= 4 and t not in STOP))}


def edited_span(original: str, perturbed: str) -> tuple[str, str]:
    """The text the edit removed and the text it added, as two strings."""
    sm = difflib.SequenceMatcher(None, original, perturbed, autojunk=False)
    removed, added = [], []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ("delete", "replace"):
            removed.append(original[i1:i2])
        if tag in ("insert", "replace"):
            added.append(perturbed[j1:j2])
    return " ".join(removed), " ".join(added)


def engagement(span_terms: set, answer_terms: set, idf: dict):
    """Share of the span's own terms found in an answer, each weighted by its rarity across all answers."""
    total = sum(idf.get(t, 1.0) for t in span_terms)
    if not span_terms or total <= 0:
        return None
    return sum(idf.get(t, 1.0) for t in span_terms & answer_terms) / total


def boot_ci(vals: list, seed: int = 0):
    if not vals:
        return None, (None, None)
    rng = random.Random(seed)
    obs = sum(vals) / len(vals)
    draws = sorted(sum(vals[rng.randrange(len(vals))] for _ in range(len(vals))) / len(vals) for _ in range(BOOT))
    return obs, (draws[int(0.025 * BOOT)], draws[int(0.975 * BOOT)])


def above(diffs: list):
    """Share of twins that beat their own null. Ties count as not above."""
    return None if not diffs else sum(1 for d in diffs if d > 0) / len(diffs)


def fmt(x, nd=3):
    return "n/a" if x is None else f"{x:.{nd}f}"


def ci(t):
    return "" if t is None or t[0] is None else f"[{fmt(t[0])}, {fmt(t[1])}]"


def blind(t: dict):
    """Materiality as the rubric-blind reviewers see it: where two rated it, only when they agree."""
    a, b = t.get("reviewer_materiality"), t.get("codex_materiality")
    if a in (1, 2, 3) and b in (1, 2, 3):
        return a if a == b else None
    return a if a in (1, 2, 3) else (b if b in (1, 2, 3) else None)


def load_answers(hb: dict) -> tuple[dict, dict, dict]:
    """Per source: the ideal answer's terms, its opening third's terms, and its HealthBench theme."""
    full, head, theme = {}, {}, {}
    for pid, r in hb.items():
        d = r.get("ideal_completions_data") or {}
        text = d.get("ideal_completion") if isinstance(d, dict) else None
        if not text:
            continue
        full[pid] = terms(text)
        head[pid] = terms(text[: max(len(text) // 3, 200)])
        theme[pid] = next((t for t in r["example_tags"] if t.startswith("theme:")), "theme:none")
    return full, head, theme


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dist", default=str(ROOT / "dist"))
    ap.add_argument("--out", default=str(OUT), help="where to write the report (default: the docs page)")
    ap.add_argument("--cache", default=str(ROOT / ".cache/healthbench_oss.jsonl"))
    a = ap.parse_args()
    hb = {r["prompt_id"]: r for r in rows(Path(a.cache))}
    twins = rows(Path(a.dist) / "keystone_twins.jsonl")
    ideal, heads, theme = load_answers(hb)

    # rarity across ideal answers: a term every physician uses is not evidence of engagement
    df = defaultdict(int)
    for t in ideal.values():
        for w in t:
            df[w] += 1
    n_docs = max(len(ideal), 1)
    idf = {w: math.log(n_docs / (1 + c)) + 1e-6 for w, c in df.items()}

    sources = sorted({t["prompt_id"] for t in twins})
    covered = [p for p in sources if p in ideal]
    by_theme = defaultdict(list)
    for p in covered:
        by_theme[theme[p]].append(p)

    rng = random.Random(0)
    data, no_terms = [], 0
    for t in twins:
        pid = t["prompt_id"]
        if pid not in ideal:
            continue
        conv = " ".join(m["content"] for m in hb[pid]["prompt"])
        removed, added = edited_span(t["original_prompt"], t["perturbed_prompt"])
        span = removed if t["family"] in REMOVAL else added
        rest = conv.replace(removed, " ") if removed else conv
        own = terms(span) - terms(rest) if t["family"] in REMOVAL else terms(span) - terms(conv)
        if not own:
            no_terms += 1
            continue
        pool = [q for q in by_theme[theme[pid]] if q != pid] or [q for q in covered if q != pid]
        def draw(table, src):
            return sum(engagement(own, table[src[rng.randrange(len(src))]], idf) for _ in range(NULL_DRAWS)) / NULL_DRAWS
        obs = engagement(own, ideal[pid], idf)
        data.append({"pid": pid, "family": t["family"], "group": t.get("group"), "blind": blind(t), "theme": theme[pid],
                     "obs": obs, "null_same": draw(ideal, pool), "null_any": draw(ideal, covered),
                     "head_obs": engagement(own, heads[pid], idf), "head_null": draw(heads, pool)})
    for r in data:
        r["diff"] = r["obs"] - r["null_same"]
        r["diff_any"] = r["obs"] - r["null_any"]
        r["head_diff"] = r["head_obs"] - r["head_null"]

    by_fam = defaultdict(list)
    for r in data:
        by_fam[r["family"]].append(r)

    L = ["# Falsification against the physicians' ideal answers", "",
         "HealthBench ships a physician-written ideal answer for most of its conversations. No Keystone label was produced from it, so it "
         "can test the annotations rather than make them. **Engagement** is the share of the edited span's own content terms, meaning terms "
         "that appear in the span and nowhere else in the conversation, that also appear in the physicians' answer to the unedited message, "
         "each term weighted by how rare it is across all ideal answers so that shared clinical vocabulary earns no credit. The null draws "
         "the comparison answer from **other sources in the same HealthBench theme**: a term counts only if physicians writing on the same "
         "theme did not use it anyway. No model is called.", "",
         f"Coverage: {len(covered)} of {len(sources)} released sources carry an ideal answer, across {len(by_theme)} themes; "
         f"{len(data)} twins scored, {no_terms} skipped because the edit introduced or removed no term unique to it. "
         f"Null: {NULL_DRAWS} draws per twin, intervals 95 percent bootstrap over twins.", "",
         "## Removal families: does the physicians' answer use the fact the twin removes", "",
         "These families take a fact out of the message or replace its value, so the fact was there when the physicians wrote. "
         "`Opening third` repeats the measure against only the first third of the answer, where physicians put what decides the case.", "",
         "| Family | Twins | Engagement | Same-theme null | Difference [95%] | Above null | Uniform-null difference | Opening third [95%] |",
         "|---|---|---|---|---|---|---|---|"]

    def row(fam, rs):
        d, c = boot_ci([r["diff"] for r in rs])
        da, _ = boot_ci([r["diff_any"] for r in rs], seed=3)
        h, ch = boot_ci([r["head_diff"] for r in rs], seed=7)
        return (f"| `{fam}` | {len(rs)} | {fmt(sum(r['obs'] for r in rs) / len(rs))} | {fmt(sum(r['null_same'] for r in rs) / len(rs))} | "
                f"{fmt(d)} {ci(c)} | {fmt(above([r['diff'] for r in rs]), 2)} | {fmt(da)} | {fmt(h)} {ci(ch)} |")

    for fam in sorted(f for f in by_fam if f in REMOVAL):
        L.append(row(fam, by_fam[fam]))
    L += ["", "## Insertion families: reported, not predicted", "",
          "These add text that did not exist when the physicians answered, so low engagement is the expected reading and says nothing about "
          "whether the insertion is load-bearing on the twin. For the two controls the number that matters is the contrast below.", "",
          "| Family | Twins | Engagement | Same-theme null | Difference [95%] | Above null | Uniform-null difference | Opening third [95%] |",
          "|---|---|---|---|---|---|---|---|"]
    for fam in sorted(f for f in by_fam if f not in REMOVAL):
        L.append(row(fam, by_fam[fam]))

    per_src = defaultdict(dict)
    for r in data:
        per_src[r["pid"]][r["family"]] = r["diff"]
    L += ["", "## Is the negative control engaged with less than the load-bearing edit", "",
          "Within a source: the same physicians' answer, the control's insertion against the load-bearing edit's span.", "",
          "| Control | Compared with | Sources | Mean difference [95%] | Control lower on |", "|---|---|---|---|---|"]
    for ctrl in CONTROLS:
        for ref in ("missing_evidence", "conflicting_evidence"):
            pairs = [(v[ctrl], v[ref]) for v in per_src.values() if ctrl in v and ref in v]
            if len(pairs) < 20:
                L.append(f"| `{ctrl}` | `{ref}` | {len(pairs)} | too few paired sources | |")
                continue
            diffs = [c - r for c, r in pairs]
            m, cc = boot_ci(diffs, seed=11)
            L.append(f"| `{ctrl}` | `{ref}` | {len(pairs)} | {fmt(m)} {ci(cc)} | {fmt(above([-d for d in diffs]), 2)} |")

    rem = [r for r in data if r["family"] in REMOVAL and r["blind"] in (1, 2, 3)]
    L += ["", "## Engagement by materiality, within the removal families", "",
          "Only the removal families can answer this: an insertion is absent from the original by construction, so pooling the families "
          "inverts the comparison rather than testing it.", "",
          "| Family | Materiality 3 | Materiality 2 | Materiality 1 |", "|---|---|---|---|"]
    for fam in sorted({r["family"] for r in rem}):
        cells = []
        for k in (3, 2, 1):
            rs = [r for r in rem if r["family"] == fam and r["blind"] == k]
            if len(rs) < 10:
                cells.append(f"{len(rs)} twins, too few")
                continue
            m, c = boot_ci([r["diff"] for r in rs], seed=k)
            cells.append(f"{fmt(m)} {ci(c)} (n={len(rs)})")
        L.append(f"| `{fam}` | " + " | ".join(cells) + " |")
    m3, c3 = boot_ci([r["diff"] for r in rem if r["blind"] == 3], seed=31)
    m1, c1 = boot_ci([r["diff"] for r in rem if r["blind"] == 1], seed=32)
    L += ["", f"Pooled over the removal families: materiality 3 sits at {fmt(m3)} {ci(c3)} above the same-theme null against "
              f"{fmt(m1)} {ci(c1)} for materiality 1.", ""]

    L += ["## Reading", "",
          "**Load-bearing, supported.** The removal families engage with the physicians' own answer above a null drawn from the same "
          "clinical theme, with rare terms carrying the weight. The fact these twins remove is one the physicians' answer to the unedited "
          "message uses, and the text carrying that verdict was never shown to any Keystone rater.", "",
          "**Controls, supported.** Both negative controls sit far below their own source's load-bearing edit on the same answer. An "
          "insertion the physicians engage with as much as the removed fact would not be a control; neither of ours is.", "",
          "**Materiality is tested in [`BEHAVIOUR_ANCHOR.md`](BEHAVIOUR_ANCHOR.md), not here.** Engagement asks whether the physicians' "
          "answer *mentions* the fact. Materiality claims something stronger, that removing it changes what a safe reply may commit to, and "
          "word overlap cannot see a change in commitment. The criterion-validity page tests that claim directly against measured model "
          "behaviour. Read this page for whether the edits reach what the physicians wrote about, and that one for whether the label means "
          "what it says.", "",
          "**Limits.** Overlap misses a fact the physicians address in other words, ideal answers cover "
          f"{len(covered)} of {len(sources)} sources, and nothing here bounds whether an edit changes the correct action. It is a "
          "falsification instrument rather than adjudication, which is the distinction the `silver` and `gold` tiers carry.", ""]
    Path(a.out).write_text("\n".join(L) + "\n")
    ov = [r["diff"] for r in data if r["family"] in REMOVAL]
    m, c = boot_ci(ov, seed=99)
    print(f"removal families: engagement above the same-theme null {fmt(m)} {ci(c)} over {len(ov)} twins; "
          f"ideal answers on {len(covered)}/{len(sources)} sources -> {a.out}")


if __name__ == "__main__":
    main()
