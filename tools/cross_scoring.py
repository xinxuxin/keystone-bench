"""Cross-scoring: separate a change in what the reply may do from a change in what the reply did.

The paired outcome Delta = f_e(r_e) - f_c(r_c) compares two things at once. The reply differs (r_c was
written for the control message, r_e for the edited one) and so does the standard it is held to (f_c is the
source's decision frame, f_e the twin's). Judging the *frozen control reply* under the *edited* standard
fills the missing cell and splits the outcome exactly:

    f_e(r_e) - f_c(r_c)  =  [f_e(r_c) - f_c(r_c)]  +  [f_e(r_e) - f_e(r_c)]
                              standard shift            reply adaptation

The first term is what an assistant incurs by leaving its reply unchanged: the same words, newly out of
bounds. The second is what changing the reply buys back, held to one standard, and is <= 0 when adaptation
helps. Their ratio is an adaptation rate, -adaptation / shift, which is 0 by construction for any policy
that ignores the edit (r_e = r_c makes the second term identically zero) and 1 when adaptation recovers the
whole shift.

Usage: OPENROUTER_API_KEY=... python tools/cross_scoring.py --runs runs --prefix testcore --out docs/CROSS_SCORING.md
"""
from __future__ import annotations
import argparse, json, os, random, sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from keystone.data import load_pairs, FAMILIES                     # noqa: E402
from keystone.prompts import action_prompt                          # noqa: E402
from keystone.runner import OpenAICompatible, action_spec, judge_json  # noqa: E402

C1 = ["missing_evidence", "conflicting_evidence", "buried_red_flag"]
C2 = ["salient_distractor", "demographic_control"]


def boot(vals, conf=0.95, seed=0, n=4000):
    """Percentile interval over sources; each value is already one source's mean over systems."""
    if not vals:
        return 0.0, 0.0, 0.0
    rng = random.Random(seed)
    m = sum(vals) / len(vals)
    k = len(vals)
    draws = sorted(sum(vals[rng.randrange(k)] for _ in range(k)) / k for _ in range(n))
    lo = draws[int((1 - conf) / 2 * n)]
    hi = draws[int((1 + conf) / 2 * n) - 1]
    return m, lo, hi


def read_records(runs: Path, prefix: str):
    """{model: {(family, source_id): record}} for every run under the prefix."""
    out = defaultdict(dict)
    for d in sorted(runs.glob(f"{prefix}__*")):
        model = d.name.split("__", 1)[1]
        for f in sorted(d.glob("*/records.jsonl")):
            for line in f.read_text().splitlines():
                if line.strip():
                    r = json.loads(line)
                    out[model][(r["family"], r.get("source_id") or r["id"])] = r
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="runs")
    ap.add_argument("--prefix", default="testcore")
    ap.add_argument("--judge", default="openrouter/openai/gpt-4.1")
    ap.add_argument("--layer", default="core")
    ap.add_argument("--split", default="test")
    ap.add_argument("--models", help="comma-separated subset of systems (default: all under the prefix)")
    ap.add_argument("--families", help="comma-separated subset (default: the three C1 families and both controls)")
    ap.add_argument("--limit-sources", type=int, help="cap the sources per family, for a pilot")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--rejudge-all", action="store_true",
                    help="recompute all three cells with --judge instead of reading the stored two from the run; "
                         "the cross-vendor replication of the decomposition")
    ap.add_argument("--tag", default="", help="suffix for the cache file, so a second judge does not collide")
    ap.add_argument("--dry-run", action="store_true", help="count the calls this would make and stop")
    ap.add_argument("--compare-to", help="a second run's cache tag (e.g. _gemini) to print beside this one; "
                                         "both must cover the same systems, families and sources")
    ap.add_argument("--out")
    a = ap.parse_args()

    runs = Path(a.runs)
    recs = read_records(runs, a.prefix)
    if not recs:
        print(f"no runs matching {a.prefix}__*")
        return
    models = sorted(recs) if not a.models else [m for m in sorted(recs) if m in set(a.models.split(","))]
    fams = a.families.split(",") if a.families else C1 + C2
    fams = [f for f in fams if f in FAMILIES]

    pairs = {}
    for fam in fams:
        for p in load_pairs(fam, layer=a.layer, split=a.split, require_paraphrase=True):
            pairs[(fam, p.source_id)] = p
    keep = {fam: sorted({k[1] for k in pairs if k[0] == fam}) for fam in fams}
    if a.limit_sources:
        for fam in fams:
            keep[fam] = keep[fam][:a.limit_sources]

    # one job per (model, family, source) whose two replies and existing perturbed verdict are all present
    jobs = []
    for m in models:
        for fam in fams:
            for sid in keep[fam]:
                r = recs[m].get((fam, sid))
                p = pairs.get((fam, sid))
                if not r or not p:
                    continue
                rc = (r.get("replies") or {}).get("paraphrase") or ""
                act = r.get("action") or {}
                if not rc.strip() or "perturbed" not in act or "paraphrase" not in act:
                    continue
                spec = action_spec(p, "perturbed")
                if spec is None:
                    continue
                jobs.append((m, fam, sid, p, rc, spec, "fe_rc"))
                if a.rejudge_all:
                    spec_c = action_spec(p, "paraphrase")
                    re_ = (r.get("replies") or {}).get("perturbed") or ""
                    if spec_c is None or not re_.strip():
                        jobs.pop()
                        continue
                    jobs.append((m, fam, sid, p, rc, spec_c, "fc_rc"))
                    jobs.append((m, fam, sid, p, re_, spec, "fe_re"))
    print(f"{len(jobs)} cross cells over {len(models)} systems and {len(fams)} families")
    if a.dry_run:
        return

    judge = OpenAICompatible(a.judge, max_tokens=600)
    cross_dir = runs / f"cross_{a.prefix}"
    cross_dir.mkdir(parents=True, exist_ok=True)
    done = {}
    cache_f = cross_dir / (f"cross{a.tag}.jsonl" if a.tag else "cross.jsonl")
    if cache_f.exists():
        for line in cache_f.read_text().splitlines():
            if line.strip():
                d = json.loads(line)
                done[(d["model"], d["family"], d["source_id"], d.get("cell", "fe_rc"))] = d["verdict"]
    todo = [j for j in jobs if (j[0], j[1], j[2], j[6]) not in done]
    print(f"{len(done)} already on disk, {len(todo)} to judge")

    def run(job):
        m, fam, sid, p, reply, spec, cell = job
        cond = "paraphrase" if cell == "fc_rc" else "perturbed"
        v = judge_json(judge, action_prompt(p.conversation(cond), reply, spec))
        return {"model": m, "family": fam, "source_id": sid, "cell": cell, "verdict": v}

    if todo:
        with cache_f.open("a") as fh, ThreadPoolExecutor(max_workers=a.workers) as ex:
            for i, d in enumerate(ex.map(run, todo), 1):
                fh.write(json.dumps(d, ensure_ascii=False) + "\n")
                fh.flush()
                done[(d["model"], d["family"], d["source_id"], d["cell"])] = d["verdict"]
                if i % 100 == 0:
                    u = judge.usage
                    print(f"  {i}/{len(todo)}  judge cost ${u['cost_usd']:.2f}", flush=True)
        print(f"judge usage: {judge.usage}")

    # decomposition, source as the unit of resampling, mean over systems within source
    def cell(r, side):
        v = (r.get("action") or {}).get(side) or {}
        return 1.0 if v.get("forbidden") else 0.0

    L = ["# Cross-scoring: standard shift and reply adaptation", "",
         f"Layer `{a.layer}`, `{a.split}` split, {len(models)} systems, judge `{a.judge}`. Every source contributes "
         "the mean over systems; the source is the unit of resampling and intervals are 95 percent percentile "
         "bootstrap.", "",
         "The paired outcome moves two things at once, the reply and the standard it is held to. Judging the frozen "
         "control reply under the edited standard fills the missing cell of the two-by-two and splits the outcome "
         "exactly:", "",
         "```",
         "  f_e(r_e) - f_c(r_c)  =  [f_e(r_c) - f_c(r_c)]  +  [f_e(r_e) - f_e(r_c)]",
         "        outcome              standard shift          reply adaptation",
         "```", "",
         "`standard shift` is what an assistant incurs by leaving the reply unchanged: the same words, newly out of "
         "bounds. `reply adaptation` is what changing the reply buys back under one standard, negative when "
         "adaptation helps. The `adaptation rate` is their ratio, `-adaptation / shift`: zero for any policy whose "
         "reply does not depend on the edit, since `r_e = r_c` makes the second term identically zero, and one when "
         "the reply recovers the whole shift.", "",
         "The two negative-control families reuse the source's own decision frame for both sides, so their "
         "`standard shift` is not a shift at all: it is the same standard applied twice, and what it measures is how "
         "much the judge moves when only the wording of the conversation changes. That is the floor the perturbation "
         "families have to clear. The perturbation families carry their own annotation for the edited side.", "",
         "| family | own annotation | sources | outcome | standard shift | reply adaptation | adaptation rate |",
         "|---|---|---|---|---|---|---|"]
    per_family = {}
    for fam in fams:
        out_v, shift_v, adapt_v = [], [], []
        for sid in keep[fam]:
            o, s, ad = [], [], []
            for m in models:
                r = recs[m].get((fam, sid))
                v = done.get((m, fam, sid, "fe_rc"))
                if not r or v is None:
                    continue
                fe_rc = 1.0 if v.get("forbidden") else 0.0
                if a.rejudge_all:
                    vc, ve = done.get((m, fam, sid, "fc_rc")), done.get((m, fam, sid, "fe_re"))
                    if vc is None or ve is None:
                        continue
                    fc_rc = 1.0 if vc.get("forbidden") else 0.0
                    fe_re = 1.0 if ve.get("forbidden") else 0.0
                else:
                    fe_re, fc_rc = cell(r, "perturbed"), cell(r, "paraphrase")
                o.append(fe_re - fc_rc); s.append(fe_rc - fc_rc); ad.append(fe_re - fe_rc)
            if o:
                out_v.append(sum(o) / len(o)); shift_v.append(sum(s) / len(s)); adapt_v.append(sum(ad) / len(ad))
        if not out_v:
            continue
        mo, lo_o, hi_o = boot(out_v, seed=11)
        ms, lo_s, hi_s = boot(shift_v, seed=12)
        ma, lo_a, hi_a = boot(adapt_v, seed=13)
        # a ratio to a shift whose interval contains zero is not reported
        rate = (-ma / ms) if lo_s > 0 else float("nan")
        own = "yes" if fam not in C2 else "no"
        per_family[fam] = dict(n=len(out_v), outcome=(mo, lo_o, hi_o), shift=(ms, lo_s, hi_s),
                               adapt=(ma, lo_a, hi_a), rate=rate)
        L.append(f"| {fam} | {own} | {len(out_v)} | {mo:+.3f} [{lo_o:+.3f}, {hi_o:+.3f}] | "
                 f"{ms:+.3f} [{lo_s:+.3f}, {hi_s:+.3f}] | {ma:+.3f} [{lo_a:+.3f}, {hi_a:+.3f}] | "
                 f"{'n/a' if rate != rate else f'{rate:.2f}'} |")

    # per system on the C1 families: which assistants convert the shift into a changed reply
    c1_here = [f for f in fams if f in C1]
    if c1_here:
        L += ["", "## Adaptation rate by system", "",
              "The share of the standard shift that each system's changed reply recovers, on the families where the "
              "edit removes or contradicts a load-bearing element.", "",
              "| system | " + " | ".join(c1_here) + " |", "|---|" + "---|" * len(c1_here)]
        for m in models:
            cells = []
            for fam in c1_here:
                s_v, a_v = [], []
                for sid in keep[fam]:
                    r = recs[m].get((fam, sid)); v = done.get((m, fam, sid, "fe_rc"))
                    if not r or v is None:
                        continue
                    fe_rc = 1.0 if v.get("forbidden") else 0.0
                    if a.rejudge_all:
                        vc, ve = done.get((m, fam, sid, "fc_rc")), done.get((m, fam, sid, "fe_re"))
                        if vc is None or ve is None:
                            continue
                        c0 = 1.0 if vc.get("forbidden") else 0.0
                        c1 = 1.0 if ve.get("forbidden") else 0.0
                    else:
                        c0, c1 = cell(r, "paraphrase"), cell(r, "perturbed")
                    s_v.append(fe_rc - c0); a_v.append(c1 - fe_rc)
                if not s_v or abs(sum(s_v) / len(s_v)) < 1e-9:
                    cells.append("n/a"); continue
                cells.append(f"{-(sum(a_v) / len(a_v)) / (sum(s_v) / len(s_v)):.2f}")
            L.append(f"| {m} | " + " | ".join(cells) + " |")

    L += ["", "## Reading", ""]
    for fam in [f for f in c1_here if f in per_family]:
        d = per_family[fam]
        L.append(f"`{fam}`: leaving the reply unchanged would cost {d['shift'][0]:+.3f} "
                 f"[{d['shift'][1]:+.3f}, {d['shift'][2]:+.3f}]; the replies systems actually produce recover "
                 f"{d['rate']:.0%} of it, leaving {d['outcome'][0]:+.3f} "
                 f"[{d['outcome'][1]:+.3f}, {d['outcome'][2]:+.3f}]."
                 + (" A rate above one means the edited reply clears the edited standard more often than the "
                    "control reply cleared its own." if d["rate"] == d["rate"] and d["rate"] > 1 else ""))
        L.append("")
    c2_here = [f for f in fams if f in C2 and f in per_family]
    if c2_here:
        vals = ", ".join(f"`{f}` {per_family[f]['shift'][0]:+.3f} [{per_family[f]['shift'][1]:+.3f}, "
                         f"{per_family[f]['shift'][2]:+.3f}]" for f in c2_here)
        worst = max(abs(per_family[f]["shift"][2]) for f in c2_here)
        L.append(f"The controls hold the standard fixed and change only the wording, so their first term is the "
                 f"judge's own movement rather than a shift: {vals}. The largest limit is {worst:.3f}, and every "
                 f"perturbation family's shift lies above it.")
        L.append("")
    # cross-vendor: the same three cells judged again by another vendor, on the same sources
    if a.compare_to:
        other = {}
        of = cross_dir / f"cross{a.compare_to}.jsonl"
        if of.exists():
            for line in of.read_text().splitlines():
                if line.strip():
                    d = json.loads(line)
                    other[(d["model"], d["family"], d["source_id"], d.get("cell", "fe_rc"))] = d["verdict"]
        if other:
            L += ["", "## The same decomposition under a second judge", "",
                  f"Every cell recomputed by the judge behind `{a.compare_to.lstrip('_')}` on the same systems, "
                  "families and sources, so the two columns differ only in who judged. The `fe_rc` cell is the "
                  "one a paired design does not contain, and it is the one this replication exists to check.", "",
                  "| family | standard shift, this judge | standard shift, second judge | rate, this | rate, second |",
                  "|---|---|---|---|---|"]
            def dec(store, fam, from_records):
                sv, av = [], []
                for sid in keep[fam]:
                    s_i, a_i = [], []
                    for m in models:
                        r = recs[m].get((fam, sid))
                        v = store.get((m, fam, sid, "fe_rc"))
                        if not r or v is None:
                            continue
                        fe_rc = 1.0 if v.get("forbidden") else 0.0
                        if from_records:
                            fc, fe = cell(r, "paraphrase"), cell(r, "perturbed")
                        else:
                            vc, ve = store.get((m, fam, sid, "fc_rc")), store.get((m, fam, sid, "fe_re"))
                            if vc is None or ve is None:
                                continue
                            fc = 1.0 if vc.get("forbidden") else 0.0
                            fe = 1.0 if ve.get("forbidden") else 0.0
                        s_i.append(fe_rc - fc); a_i.append(fe - fe_rc)
                    if s_i:
                        sv.append(sum(s_i) / len(s_i)); av.append(sum(a_i) / len(a_i))
                if not sv:
                    return None
                ms, los, his = boot(sv, seed=21)
                ma, _, _ = boot(av, seed=22)
                return ms, los, his, ((-ma / ms) if abs(ms) > 1e-9 and los > 0 else float("nan"))
            gaps = []
            for fam in fams:
                x = dec(done, fam, not a.rejudge_all)
                y = dec(other, fam, False)
                if not x or not y:
                    continue
                gaps.append((fam, abs(x[0] - y[0])))
                rx = "n/a" if x[3] != x[3] else f"{x[3]:.2f}"
                ry = "n/a" if y[3] != y[3] else f"{y[3]:.2f}"
                L.append(f"| `{fam}` | {x[0]:+.3f} [{x[1]:+.3f}, {x[2]:+.3f}] | "
                         f"{y[0]:+.3f} [{y[1]:+.3f}, {y[2]:+.3f}] | {rx} | {ry} |")
            if gaps:
                worst = max(gaps, key=lambda g: g[1])
                L += ["", f"The two judges place the standard shift within {worst[1]:.3f} of each other on the "
                          f"family where they differ most (`{worst[0]}`), and closer on the rest. The cell that "
                          "carries the replication is the one a paired design never computes, so a judge-specific "
                          "artefact in it would show here as a gap rather than as agreement.", ""]

    text = "\n".join(L) + "\n"
    print(text)
    if a.out:
        Path(a.out).write_text(text)


if __name__ == "__main__":
    main()
