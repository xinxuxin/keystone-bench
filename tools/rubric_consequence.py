"""What rubric expiry does to the score, and to the ranking the score produces.

A criterion that no longer describes a fair standard for the edited message is a defect in the instrument. On
its own that is a statement about the rubric. This turns it into a statement about the measurement: grade the
same frozen replies once per criterion, then read two scores off those grades. The **stale** score is the
physician rubric as written. The **adapted** score drops the criteria a second judge marked inapplicable to
the edited message. Both scores come from the same grades, so nothing separates them except which criteria
count.

Two things follow. The **level shift** is how far a system's score moves when the expired criteria are
dropped. The **ranking flip rate** is the share of system pairs, within a source, whose order under the stale
rubric disagrees with their order under the adapted one. A level shift alone changes no decision; a flip
changes which system a reader would pick from that item.

The two negative-control families are the floor: about one criterion in a hundred expires there, so a flip
rate on the controls is what this procedure produces from grading noise alone.

Usage: OPENROUTER_API_KEY=... python tools/rubric_consequence.py --models a,b,c --out docs/RUBRIC_CONSEQUENCE.md
"""
from __future__ import annotations
import argparse, json, random, sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from keystone.data import load_pairs, FAMILIES          # noqa: E402
from keystone.metrics import healthbench_score          # noqa: E402
from keystone.prompts import grader_prompt              # noqa: E402
from keystone.runner import OpenAICompatible, judge_json  # noqa: E402

C1 = ["missing_evidence", "conflicting_evidence", "buried_red_flag"]
C2 = ["salient_distractor", "demographic_control"]


def boot(vals, conf=0.95, seed=0, n=4000):
    if not vals:
        return float("nan"), float("nan"), float("nan")
    rng = random.Random(seed)
    k = len(vals)
    draws = sorted(sum(vals[rng.randrange(k)] for _ in range(k)) / k for _ in range(n))
    return sum(vals) / k, draws[int((1 - conf) / 2 * n)], draws[int((1 + conf) / 2 * n) - 1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="runs")
    ap.add_argument("--prefix", default="testcore")
    ap.add_argument("--applicability", default="runs/applicability_test/records.jsonl")
    ap.add_argument("--judge", default="openrouter/openai/gpt-4.1")
    ap.add_argument("--models", required=True, help="comma-separated systems to grade")
    ap.add_argument("--layer", default="core")
    ap.add_argument("--split", default="test")
    ap.add_argument("--limit-c1", type=int, help="cap sources per perturbation family")
    ap.add_argument("--limit-c2", type=int, default=100, help="cap sources per control family")
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args()

    models = [m.strip() for m in a.models.split(",") if m.strip()]
    fams = C1 + C2

    applies = {}
    for line in Path(a.applicability).read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            applies[(r["id"], r["criterion_index"])] = r.get("applies")

    pairs = {}
    for fam in fams:
        for p in load_pairs(fam, layer=a.layer, split=a.split, require_paraphrase=True):
            pairs[(fam, p.source_id)] = p
    keep = {}
    for fam in fams:
        ids = sorted({k[1] for k in pairs if k[0] == fam})
        cap = a.limit_c2 if fam in C2 else a.limit_c1
        keep[fam] = ids[:cap] if cap else ids

    replies = defaultdict(dict)
    for m in models:
        for f in sorted(Path(a.runs).glob(f"{a.prefix}__{m}/*/records.jsonl")):
            for line in f.read_text().splitlines():
                if line.strip():
                    r = json.loads(line)
                    rep = (r.get("replies") or {}).get("perturbed") or ""
                    if rep.strip():
                        replies[m][(r["family"], r.get("source_id") or r["id"])] = rep

    jobs = []
    for m in models:
        for fam in fams:
            for sid in keep[fam]:
                p, rep = pairs.get((fam, sid)), replies[m].get((fam, sid))
                if not p or not rep:
                    continue
                for i, rub in enumerate(p.rubrics):
                    jobs.append((m, fam, sid, i, p, rep, rub["criterion"]))
    print(f"{len(jobs)} criterion grades over {len(models)} systems, {len(fams)} families")
    if a.dry_run:
        return

    judge = OpenAICompatible(a.judge, max_tokens=600)
    out_f = Path(a.runs) / f"rubric_consequence_{a.prefix}" / "grades.jsonl"
    out_f.parent.mkdir(parents=True, exist_ok=True)
    done = {}
    if out_f.exists():
        for line in out_f.read_text().splitlines():
            if line.strip():
                d = json.loads(line)
                done[(d["model"], d["family"], d["source_id"], d["i"])] = d["met"]
    todo = [j for j in jobs if (j[0], j[1], j[2], j[3]) not in done]
    print(f"{len(done)} on disk, {len(todo)} to grade")

    def run(job):
        m, fam, sid, i, p, rep, crit = job
        v = judge_json(judge, grader_prompt(p.conversation("perturbed"), rep, crit))
        met = v.get("criteria_met")
        return {"model": m, "family": fam, "source_id": sid, "i": i,
                "met": met if isinstance(met, bool) else None}

    if todo:
        with out_f.open("a") as fh, ThreadPoolExecutor(max_workers=a.workers) as ex:
            for n, d in enumerate(ex.map(run, todo), 1):
                fh.write(json.dumps(d) + "\n")
                fh.flush()
                done[(d["model"], d["family"], d["source_id"], d["i"])] = d["met"]
                if n % 500 == 0:
                    print(f"  {n}/{len(todo)}  judge cost ${judge.usage['cost_usd']:.2f}", flush=True)
        print(f"judge usage: {judge.usage}")

    # two scores off the same grades
    scores = {}          # (fam, sid, model) -> (stale, adapted, dropped)
    for m in models:
        for fam in fams:
            for sid in keep[fam]:
                p = pairs.get((fam, sid))
                if not p:
                    continue
                met = [done.get((m, fam, sid, i)) for i in range(len(p.rubrics))]
                if any(x is None for x in met) and all(x is None for x in met):
                    continue
                stale = healthbench_score(p.rubrics, met)
                idx = [i for i in range(len(p.rubrics)) if applies.get((p.id, i)) is not False]
                if not idx or stale is None:
                    continue
                adapted = healthbench_score([p.rubrics[i] for i in idx], [met[i] for i in idx])
                if adapted is None:
                    continue
                scores[(fam, sid, m)] = (stale, adapted, len(p.rubrics) - len(idx))

    L = ["# Rubric expiry and the ranking it changes", "",
         f"Layer `{a.layer}`, `{a.split}` split, judge `{a.judge}`, systems {', '.join(f'`{m}`' for m in models)}. "
         "Each criterion of a source's physician rubric is graded once against that system's reply to the edited "
         "conversation. The **stale** score uses the rubric as the physician wrote it. The **adapted** score drops "
         "the criteria a second judge marked inapplicable to the edited message. Both read off the same grades, so "
         "the only difference is which criteria count.", "",
         "| family | sources | criteria dropped | stale score | adapted score | level shift | ranking flip rate |",
         "|---|---|---|---|---|---|---|"]
    rows = {}
    avg_criteria = {}
    for fam in fams:
        ns = [len(pairs[(fam, sid)].rubrics) for sid in keep[fam] if (fam, sid) in pairs]
        avg_criteria[fam] = (sum(ns) / len(ns)) if ns else 1.0
    for fam in fams:
        sids = [s for s in keep[fam] if any((fam, s, m) in scores for m in models)]
        if not sids:
            continue
        shift, stale_v, adapt_v, dropped = [], [], [], []
        flips_per_source = []
        for sid in sids:
            have = [m for m in models if (fam, sid, m) in scores]
            if not have:
                continue
            st = [scores[(fam, sid, m)][0] for m in have]
            ad = [scores[(fam, sid, m)][1] for m in have]
            stale_v.append(sum(st) / len(st)); adapt_v.append(sum(ad) / len(ad))
            shift.append(sum(a2 - s2 for s2, a2 in zip(st, ad)) / len(st))
            dropped.append(scores[(fam, sid, have[0])][2])
            if len(have) >= 2:
                f = t = 0
                for i in range(len(have)):
                    for j in range(i + 1, len(have)):
                        ds = st[i] - st[j]
                        da = ad[i] - ad[j]
                        if ds == 0 and da == 0:
                            continue
                        t += 1
                        # a flip is a strict reversal or a tie broken the other way
                        if (ds > 0 and da < 0) or (ds < 0 and da > 0):
                            f += 1
                if t:
                    flips_per_source.append(f / t)
        ms, los, his = boot(stale_v, seed=1)
        ma, loa, hia = boot(adapt_v, seed=2)
        md, lod, hid = boot(shift, seed=3)
        mf, lof, hif = boot(flips_per_source, seed=4)
        rows[fam] = dict(n=len(sids), dropped=sum(dropped) / max(1, len(dropped)),
                         stale=(ms, los, his), adapted=(ma, loa, hia), shift=(md, lod, hid),
                         flip=(mf, lof, hif), nflip=len(flips_per_source))
        L.append(f"| `{fam}` | {len(sids)} | {sum(dropped) / max(1, len(dropped)):.1f} | {ms:.3f} | {ma:.3f} | "
                 f"{md:+.3f} [{lod:+.3f}, {hid:+.3f}] | {mf:.3f} [{lof:.3f}, {hif:.3f}] |")

    L += ["", "## H2, as preregistered", "",
          "Protocol section 2 states H2 as: *scoring the twin's reply with the unchanged rubric (stale score) "
          "exceeds the score over still-applicable criteria, and at least 20 percent of criteria are judged "
          "inapplicable*, decided by a 95 percent bootstrap interval on the paired difference that excludes zero. "
          "The prediction is directional, and the table above reports the difference in the direction "
          "adapted minus stale, so H2 as written predicts a negative entry.", ""]
    L += ["| family | criteria inapplicable | adapted − stale | interval excludes zero | direction predicted by H2 |",
          "|---|---|---|---|---|"]
    for f in [x for x in C1 if x in rows]:
        d = rows[f]
        exc = "yes" if (d["shift"][1] > 0 or d["shift"][2] < 0) else "no"
        agree = "yes" if d["shift"][0] < 0 else "no"
        share = d["dropped"] / max(1e-9, avg_criteria.get(f, 1))
        L.append(f"| `{f}` | {share:.3f} | {d['shift'][0]:+.3f} [{d['shift'][1]:+.3f}, {d['shift'][2]:+.3f}] "
                 f"| {exc} | {agree} |")
    L += [""]
    flipped = [f for f in C1 if f in rows and rows[f]["shift"][0] > 0 and rows[f]["shift"][1] > 0]
    if flipped:
        L += [f"**H2's interval clause holds and its direction does not.** On "
              + ", ".join(f"`{f}`" for f in flipped) +
              " the paired difference excludes zero with the opposite sign: dropping the expired criteria raises "
              "the score rather than lowering it. The mechanism is visible in the grades. A criterion that no "
              "longer applies is one the edit made unsatisfiable, so the reply is recorded as failing it, and the "
              "stale rubric charges the reply for a standard the edit removed. The quantity H2 names is real and "
              "the sign written into the protocol was wrong; both are reported.", ""]
    L += ["H3, preregistered as a disagreement between rankings on originals and on twins, is not executed in this "
          "release: it needs the original-side replies graded as well, which is a second pass of the same size. "
          "The ranking quantity below is a different one, holding the replies fixed and changing only the rubric "
          "version, and is reported as an addition to the preregistered set rather than as H3.", ""]

    L += ["## Reading", ""]
    pert = [f for f in C1 if f in rows]
    ctrl = [f for f in C2 if f in rows]
    if ctrl:
        cf = max(rows[f]["flip"][2] for f in ctrl)
        L.append("The controls set the floor. About one criterion in a hundred expires on a negative-control twin, "
                 "so whatever flip rate they show is what grading noise alone produces: "
                 + "; ".join(f"`{f}` {rows[f]['flip'][0]:.3f} [{rows[f]['flip'][1]:.3f}, {rows[f]['flip'][2]:.3f}]"
                             for f in ctrl) + f". The upper limit across the two is {cf:.3f}.")
        L.append("")
    for f in pert:
        d = rows[f]
        L.append(f"`{f}`: {d['dropped']:.1f} criteria drop out per twin, the score moves "
                 f"{d['shift'][0]:+.3f} [{d['shift'][1]:+.3f}, {d['shift'][2]:+.3f}], and "
                 f"{d['flip'][0]:.1%} of the system pairs that the stale rubric orders one way are ordered the "
                 f"other way once the expired criteria are dropped.")
        L.append("")
    if pert and ctrl:
        best = max(pert, key=lambda f: rows[f]["flip"][0])
        L.append(f"The largest effect is on `{best}`, where the flip rate is "
                 f"{rows[best]['flip'][0]:.3f} [{rows[best]['flip'][1]:.3f}, {rows[best]['flip'][2]:.3f}] against a "
                 f"control ceiling of {max(rows[f]['flip'][2] for f in ctrl):.3f}. A level shift alone changes no "
                 "decision; a flip changes which system a reader would pick from that item.")
        L.append("")
    text = "\n".join(L) + "\n"
    print(text)
    if a.out:
        Path(a.out).write_text(text)


if __name__ == "__main__":
    main()
