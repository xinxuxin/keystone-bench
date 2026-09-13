"""How much of the physicians' rubric still applies after the edit, on the held-out split.

The criteria were written for the original message. Once a decisive fact is removed, contradicted or changed,
some of them no longer describe a fair standard, and a grader that keeps applying them is scoring a reply
against a target that has moved. This is a property of the pair, not of any reply, so each criterion is judged
once per twin and the number does not depend on which system is being evaluated.

Reported per family and per materiality, with the source as the unit of resampling.

Usage: python tools/applicability.py --judge openrouter/openai/gpt-4.1 [--split test] [--layer core]
                                     [--families all] [--workers 12] [--out docs/APPLICABILITY.md]
"""
from __future__ import annotations
import argparse, json, os, random, sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from keystone.data import load_pairs  # noqa: E402
from keystone.prompts import applicability_prompt  # noqa: E402
from keystone.runner import OpenAICompatible, _judge_json  # noqa: E402

FAMILIES = ["missing_evidence", "conflicting_evidence", "buried_red_flag", "demographic_shift",
            "alternative_evidence", "missing_evidence_early", "salient_distractor", "demographic_control"]
BOOT = int(os.environ.get("KEYSTONE_BOOT", "4000"))


def boot_ci(vals, seed=0):
    if not vals:
        return float("nan"), float("nan"), float("nan")
    rng = random.Random(seed); n = len(vals)
    ms = sorted(sum(vals[rng.randrange(n)] for _ in range(n)) / n for _ in range(BOOT))
    return sum(vals) / n, ms[int(0.025 * BOOT)], ms[min(BOOT - 1, int(0.975 * BOOT))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge", default="openrouter/openai/gpt-4.1")
    ap.add_argument("--split", default="test"); ap.add_argument("--layer", default="core")
    ap.add_argument("--families", default="all"); ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--limit", type=int); ap.add_argument("--out")
    ap.add_argument("--records", default="runs/applicability_test/records.jsonl")
    a = ap.parse_args()
    judge = OpenAICompatible(a.judge, max_tokens=600)
    fams = FAMILIES if a.families == "all" else a.families.split(",")

    rec_path = Path(a.records); rec_path.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if rec_path.exists():
        for line in rec_path.read_text().splitlines():
            if line.strip():
                r = json.loads(line); done.add((r["id"], r["criterion_index"]))
    jobs = []
    meta = {}
    for fam in fams:
        for p in load_pairs(fam, a.layer, split=a.split, limit=a.limit):
            meta[p.id] = (fam, p.materiality_majority, p.turns)
            ctx = p.perturbed[:-1] if len(p.perturbed) > 1 else None
            for i, c in enumerate(p.rubrics or []):
                text = c.get("criterion") or c.get("text")
                if not text or (p.id, i) in done:
                    continue
                jobs.append((p.id, i, applicability_prompt(p.original_edited_message, p.perturbed_message, text, ctx),
                             c.get("points")))
    print(f"{len(jobs)} criteria to judge ({len(done)} already done), {len(meta)} twins, judge {a.judge}", flush=True)

    lock_out = rec_path.open("a")
    n_done = [0]

    def work(job):
        pid, i, prompt, pts = job
        v = _judge_json(judge, prompt)
        row = {"id": pid, "family": meta[pid][0], "criterion_index": i, "points": pts,
               "applies": v.get("applicable"), "why": (v.get("reason") or "")[:300]}
        lock_out.write(json.dumps(row, ensure_ascii=False) + "\n"); lock_out.flush()
        n_done[0] += 1
        if n_done[0] % 250 == 0:
            print(f"  {n_done[0]}/{len(jobs)}  usage {judge.usage['calls']} calls ${judge.usage['cost_usd']:.2f}", flush=True)
    if jobs:
        with ThreadPoolExecutor(max_workers=a.workers) as ex:
            list(ex.map(work, jobs))
    lock_out.close()
    print(f"judge usage: {judge.usage}", flush=True)

    rows = [json.loads(l) for l in rec_path.read_text().splitlines() if l.strip()]
    by_twin = defaultdict(list)
    for r in rows:
        if r.get("applies") is not None:
            by_twin[(r["family"], r["id"])].append(0.0 if r["applies"] else 1.0)
    L = ["# Rubric applicability after the edit, held-out split", "",
         f"Layer `{a.layer}`, split `{a.split}`, judge `{a.judge}`. Each criterion of a source's physician rubric is "
         "judged once against that source's twin: does it still describe a fair standard for the edited message. "
         "The verdict depends on the pair, not on any reply, so it does not vary by evaluated system.", "",
         "The share is per twin, then averaged over twins with the source as the unit of resampling.", "",
         "| family | twins | criteria | share of criteria no longer applicable |", "|---|---|---|---|"]
    allv = []
    for fam in FAMILIES:
        vals = [sum(v) / len(v) for (f, _), v in by_twin.items() if f == fam and v]
        n_c = sum(len(v) for (f, _), v in by_twin.items() if f == fam)
        if not vals:
            continue
        m, lo, hi = boot_ci(vals, seed=abs(hash(fam)) % 999)
        allv += vals
        L.append(f"| `{fam}` | {len(vals)} | {n_c} | {m:.3f} [{lo:.3f}, {hi:.3f}] |")
    if allv:
        m, lo, hi = boot_ci(allv, seed=7)
        L.append(f"| **all** | {len(allv)} | {sum(len(v) for v in by_twin.values())} | **{m:.3f}** [{lo:.3f}, {hi:.3f}] |")
    # by materiality, perturbation families only
    L += ["", "## By materiality, perturbation families", "",
          "| median materiality | twins | share no longer applicable |", "|---|---|---|"]
    pert = {"missing_evidence", "conflicting_evidence", "buried_red_flag", "demographic_shift",
            "alternative_evidence", "missing_evidence_early"}
    bym = defaultdict(list)
    for (f, pid), v in by_twin.items():
        if f in pert and v and pid in meta:
            bym[meta[pid][1]].append(sum(v) / len(v))
    for k in sorted(x for x in bym if x is not None):
        m, lo, hi = boot_ci(bym[k], seed=k or 0)
        L.append(f"| {k} | {len(bym[k])} | {m:.3f} [{lo:.3f}, {hi:.3f}] |")
    L.append("")
    text = "\n".join(L) + "\n"
    print(text)
    if a.out:
        Path(a.out).write_text(text)


if __name__ == "__main__":
    main()
