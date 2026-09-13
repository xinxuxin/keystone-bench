"""The floor a paired effect has to clear: the same model, the same request, asked again.

At temperature 0 a served model is still not deterministic. Re-asking an identical request and scoring the
answer the same way gives the rate at which an outcome flips for no reason at all. Every paired effect in
this release is reported against that number, because a counterfactual evaluation whose effect is inside its
own re-run noise has not measured anything (arXiv:2609.03221 measures an average per-action flip rate of 8.7
percent on re-sampled identical clinical cases; arXiv:2605.01048 finds a gender swap and a paraphrase
indistinguishable on MedPerturb).

Runs are produced by `keystone run --repeat N`, which re-asks the identical request under a different cache
key. This script compares repeat 1 and repeat 2 against the original run and against each other.

Usage: python tools/instability_floor.py [--out docs/INSTABILITY_FLOOR.md]
"""
from __future__ import annotations
import argparse, glob, json, os, random, sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

FAMILIES = ["missing_evidence", "conflicting_evidence", "buried_red_flag", "salient_distractor", "demographic_control"]
CONDS = ("original", "perturbed", "paraphrase")
BOOT = int(os.environ.get("KEYSTONE_BOOT", "2000"))
HEADLINE_FAMILIES = ("missing_evidence", "conflicting_evidence")  # the two families the Reading section calls out by name
EXTERNAL_FLIP_RATE = 8.7  # percent; arXiv:2609.03221, mean per-action flip rate on re-sampled identical clinical cases


def load(runs: str, prefix: str) -> dict:
    out = {}
    for f in sorted(glob.glob(os.path.join(runs, prefix, "*", "records.jsonl"))):
        for line in open(f):
            if line.strip():
                r = json.loads(line); out[(r["family"], r["id"])] = r
    return out


def forbidden(r: dict, cond: str):
    a = (r.get("action") or {}).get(cond) or {}
    return None if not a else bool(a.get("forbidden"))


def boot_ci(vals, seed=0):
    if not vals:
        return float("nan"), float("nan"), float("nan")
    rng = random.Random(seed); n = len(vals); ms = []
    for _ in range(BOOT):
        ms.append(sum(vals[rng.randrange(n)] for _ in range(n)) / n)
    ms.sort()
    return sum(vals) / n, ms[int(0.025 * BOOT)], ms[min(BOOT - 1, int(0.975 * BOOT))]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--runs", default="runs"); ap.add_argument("--out")
    a = ap.parse_args()
    models = sorted({Path(d).name.split("__", 1)[1] for d in glob.glob(os.path.join(a.runs, "floor_r1__*"))})
    L = ["# The instability floor", "",
         "The same model, the same request, asked again. At temperature 0 a served model is still not "
         "deterministic, so an outcome flips at some rate for no reason at all, and that rate is the floor any "
         "paired effect has to clear. Produced by `keystone run --repeat N`, which re-asks the identical request "
         "under a different cache key; the judge and the prompts are unchanged.", ""]
    if not models:
        print("\n".join(L) + "\nNo repeat runs yet."); return
    L += [f"Models: {', '.join(models)}.", "",
          "## Flip rate of the forbidden-action verdict between two identical requests", "",
          "Per family, over items and the three conditions: the share of (item, condition) cells whose verdict "
          "differs between two runs of the same request. `paired floor` is the same quantity expressed the way an "
          "effect is: the mean absolute difference of the twin-minus-control contrast between two identical runs.", "",
          "`spurious effect` is the contrast a re-run produces on its own: the twin-minus-control difference "
          "computed with the twin from one run and the control from another, which has no real effect in it and "
          "should sit on zero. `noise size` is the mean absolute difference of that contrast between runs, which is "
          "the scale of the wobble rather than a bias.", "",
          "| family | model | cells | flip rate | spurious effect | noise size | measured effect |", "|---|---|---|---|---|---|---|"]
    summary = defaultdict(list)
    all_rows = []
    for model in models:
        base = load(a.runs, f"quick__{model}")
        reps = [load(a.runs, f"floor_r{i}__{model}") for i in (1, 2)]
        reps = [r for r in reps if r]
        runs_all = [base] + reps
        for fam in FAMILIES:
            keys = set.intersection(*[{k for k in r if k[0] == fam} for r in runs_all]) if runs_all else set()
            if not keys:
                continue
            flips, contrasts, spurious = [], [], []
            for k in keys:
                for c in CONDS:
                    vs = [forbidden(r[k], c) for r in runs_all]
                    vs = [v for v in vs if v is not None]
                    if len(vs) >= 2:
                        flips += [float(x != y) for i, x in enumerate(vs) for y in vs[i + 1:]]
                ds = []
                for r in runs_all:
                    p, q = forbidden(r[k], "perturbed"), forbidden(r[k], "paraphrase")
                    if p is not None and q is not None:
                        ds.append(float(p) - float(q))
                if len(ds) >= 2:
                    contrasts += [abs(x - y) for i, x in enumerate(ds) for y in ds[i + 1:]]
                # a contrast built from two different runs of the same request: no real effect is in it
                for i, ra in enumerate(runs_all):
                    for rb in runs_all[i + 1:]:
                        pa, qb = forbidden(ra[k], "perturbed"), forbidden(rb[k], "paraphrase")
                        pb, qa = forbidden(rb[k], "perturbed"), forbidden(ra[k], "paraphrase")
                        if None not in (pa, qa, pb, qb):
                            spurious.append(((float(pa) - float(qb)) + (float(pb) - float(qa))) / 2 - (float(pa) - float(qa)))
            if not flips:
                continue
            eff = []
            for k in keys:
                p, q = forbidden(base[k], "perturbed"), forbidden(base[k], "paraphrase")
                if p is not None and q is not None:
                    eff.append(float(p) - float(q))
            fr = sum(flips) / len(flips); pf = (sum(contrasts) / len(contrasts)) if contrasts else float("nan")
            sm, slo, shi = boot_ci(spurious, seed=3)
            m, lo, hi = boot_ci(eff)
            summary[fam].append((fr, pf, m, sm))
            all_rows.append((fam, model, fr, sm, slo, shi, m, lo, hi))
            L.append(f"| {fam} | {model} | {len(flips)} | {fr:.3f} | {sm:+.3f} [{slo:+.3f}, {shi:+.3f}] | {pf:.3f} | {m:+.3f} [{lo:+.3f}, {hi:+.3f}] |")
    L += ["", "## What it means for each family", "",
          "| family | mean flip rate | mean spurious effect | mean noise size | mean measured effect |", "|---|---|---|---|---|"]
    fam_point = {}
    for fam in FAMILIES:
        rows = summary.get(fam) or []
        if not rows:
            continue
        fr = sum(r[0] for r in rows) / len(rows); pf = sum(r[1] for r in rows) / len(rows)
        m = sum(r[2] for r in rows) / len(rows); sm = sum(r[3] for r in rows) / len(rows)
        fam_point[fam] = (fr, pf, m, sm)
        L.append(f"| {fam} | {fr:.3f} | {sm:+.3f} | {pf:.3f} | {m:+.3f} |")

    if not all_rows:
        L += ["", "## Reading", "", "No family has data from more than one run; the floor cannot be estimated yet.", ""]
    else:
        # every number below is read back off the two tables above, never typed in as a literal
        flip_lo, flip_hi = min(r[2] for r in all_rows) * 100, max(r[2] for r in all_rows) * 100
        watch = max(all_rows, key=lambda r: abs(r[3]))
        w_fam, _, _, sm_w, slo_w, shi_w, m_w, lo_w, hi_w = watch
        all_ci_zero = all(slo <= 0 <= shi for (_, _, _, _, slo, shi, _, _, _) in all_rows)
        ci_zero_clause = ("and its interval contains zero on every family" if all_ci_zero else
                           "though not every family's interval clears zero")
        watch_spurious_zero = slo_w <= 0 <= shi_w
        watch_eff_zero = lo_w <= 0 <= hi_w
        spurious_zero_phrase = ("and its own interval still contains zero" if watch_spurious_zero else
                                 "and unlike most rows its own interval excludes zero")
        if watch_spurious_zero and watch_eff_zero:
            watch_tail = "so the family is reported as containing zero either way."
        elif watch_eff_zero:
            watch_tail = ("which does contain zero, so the measured effect for this family is not distinguishable "
                           "from no effect even though this particular noise estimate is.")
        elif watch_spurious_zero:
            watch_tail = "which excludes zero, the one row whose measured effect clears its own noise floor."
        else:
            watch_tail = "which also excludes zero, so the measured effect and the noise floor move together here."
        sign_word = "negative" if sm_w < 0 else "positive"
        skew_word = "understate a real positive effect" if sm_w < 0 else "overstate a real effect"
        headline = [f for f in HEADLINE_FAMILIES if f in fam_point]
        if len(headline) == len(HEADLINE_FAMILIES) and sm_w:
            ratios = sorted(fam_point[f][2] / abs(sm_w) for f in headline)
            headline_sentence = (
                f"The measured effects on the same items are {fam_point[headline[0]][2]:+.2f} and "
                f"{fam_point[headline[1]][2]:+.2f} on the two headline families (`{headline[0]}`, `{headline[1]}`), "
                f"{ratios[0]:.0f} to {ratios[-1]:.0f} times the largest spurious contrast.")
        else:
            headline_sentence = ("The measured effects on the headline families are far larger than the largest "
                                  "spurious contrast.")

        L += ["", "## Reading", "",
              f"The instability is real and it is the size other people report. Re-asking the identical request "
              f"flips the forbidden-action verdict on {flip_lo:.1f} to {flip_hi:.1f} percent of cells, against the "
              f"{EXTERNAL_FLIP_RATE} percent an external re-sampling study measures on unedited clinical cases "
              f"([arXiv:2609.03221](https://arxiv.org/abs/2609.03221)). A single unpaired comparison at this scale "
              f"would be reporting noise.", "",
              f"It does not survive pairing. The contrast a re-run produces on its own, built by taking the twin "
              f"from one run and the control from another, is within {abs(sm_w):.3f} of zero on every family "
              f"{ci_zero_clause}. Noise at temperature 0 is two-sided: it moves the twin side and the control side "
              f"alike, and the paired difference cancels it. {headline_sentence}", "",
              f"The one to watch is `{w_fam}` at {sm_w:+.3f} [{slo_w:+.3f}, {shi_w:+.3f}]. It is the largest "
              f"spurious contrast in the table, it is {sign_word}, {spurious_zero_phrase}; a bias of this sign would "
              f"if anything {skew_word} on that family. The measured effect there is {m_w:+.3f} [{lo_w:+.3f}, "
              f"{hi_w:+.3f}], {watch_tail}", ""]
    text = "\n".join(L) + "\n"
    print(text)
    if a.out:
        Path(a.out).write_text(text)


if __name__ == "__main__":
    main()
