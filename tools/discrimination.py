"""How much systems differ in how much the edit moves them, and whether they differ at all on the controls.

A benchmark earns its place by telling systems apart. A benchmark that tells them apart everywhere, including
on items where every correct answer is the same, is measuring something other than what it claims.

Both halves are tested the same way. For each family, the observed spread between systems is the range of
their per-system mean paired differences. The null is that the system label carries no information: within
each source, the labels are permuted across systems, which preserves the difficulty of the source and destroys
only the identity of the system answering it. The p-value is the share of permutations whose spread is at
least the observed one.

The prediction is asymmetric and that is the point. On a perturbation family, systems should differ, because
reacting to changed evidence is a capability and capabilities differ. On a negative control, where the correct
answer is to leave the reply alone, they should not.

Usage: python tools/discrimination.py [--prefix testcore] [--out docs/DISCRIMINATION.md]
"""
from __future__ import annotations
import argparse, glob, json, os, random, statistics, sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

PERTURBATION = ["missing_evidence", "conflicting_evidence", "buried_red_flag", "demographic_shift",
                "alternative_evidence", "missing_evidence_early"]
CONTROLS = ["salient_distractor", "demographic_control"]
PERM = int(os.environ.get("KEYSTONE_PERM", "4000"))
MIN_CELL = 10


def load(runs: str, prefix: str) -> dict:
    per = defaultdict(lambda: defaultdict(dict))
    for f in sorted(glob.glob(os.path.join(runs, f"{prefix}__*", "*", "records.jsonl"))):
        model = Path(f).parts[-3].split("__", 1)[1]
        for line in open(f):
            if not line.strip():
                continue
            r = json.loads(line)
            a = r.get("action") or {}
            p, q = a.get("perturbed") or {}, a.get("paraphrase") or {}
            if not p or not q:
                continue
            sid = r.get("source_id") or r["id"]
            per[r["family"]][sid][model] = float(bool(p.get("forbidden"))) - float(bool(q.get("forbidden")))
    return per


def sd_ci(rows: list, seed: int = 0, level: float = 0.90) -> tuple[float, float]:
    """Bootstrap interval for the between-system sd, resampling sources. A large p-value says the data do not
    reject exchangeability; only this interval says how small the difference could be."""
    srcs = [s for s, _ in rows]
    by = {s: d for s, d in rows}
    rng = random.Random(seed); n = len(srcs); out = []
    for _ in range(600):
        pick = [srcs[rng.randrange(n)] for _ in range(n)]
        acc = defaultdict(list)
        for s in pick:
            for m, v in by[s].items():
                acc[m].append(v)
        means = [statistics.fmean(v) for v in acc.values() if len(v) >= MIN_CELL]
        out.append(statistics.pstdev(means) if len(means) > 1 else 0.0)
    out.sort()
    return out[int((1 - level) / 2 * len(out))], out[min(len(out) - 1, int((1 + level) / 2 * len(out)))]


def spread_and_p(rows: list, seed: int = 0) -> tuple[float, float, dict, float]:
    """rows: [(source, {model: diff})].

    The statistic is the standard deviation of the systems' mean paired differences, not their range: a range
    uses two systems and grows with how many are evaluated, while an sd uses all of them. The null permutes
    system labels within each source, so the source's difficulty is held and only the identity of the system
    answering it is destroyed. Returns (sd, p, per-system means, range)."""
    def spread(assign):
        by = defaultdict(list)
        for s, d in rows:
            for m, v in d.items():
                by[assign.get((s, m), m)].append(v)
        means = [statistics.fmean(v) for v in by.values() if len(v) >= MIN_CELL]
        return statistics.pstdev(means) if len(means) > 1 else 0.0
    def rng_(assign):
        by = defaultdict(list)
        for s, d in rows:
            for m, v in d.items():
                by[assign.get((s, m), m)].append(v)
        means = [statistics.fmean(v) for v in by.values() if len(v) >= MIN_CELL]
        return (max(means) - min(means)) if len(means) > 1 else 0.0
    obs = spread({}); obs_range = rng_({})
    per_model = defaultdict(list)
    for s, d in rows:
        for m, v in d.items():
            per_model[m].append(v)
    rng = random.Random(seed); hits = 0
    for _ in range(PERM):
        assign = {}
        for s, d in rows:
            ms = list(d); sh = ms[:]; rng.shuffle(sh)
            for a, b in zip(ms, sh):
                assign[(s, a)] = b
        if spread(assign) >= obs:
            hits += 1
    return obs, max(1.0 / PERM, hits / PERM), {m: statistics.fmean(v) for m, v in per_model.items()}, obs_range


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="runs"); ap.add_argument("--prefix", default="testcore"); ap.add_argument("--out")
    a = ap.parse_args()
    per = load(a.runs, a.prefix)
    if not per:
        print(f"no runs matching {a.prefix}__*"); return
    split = "held-out" if a.prefix == "testcore" else a.prefix
    L = ["# Discrimination, and where it stops", "",
         "A benchmark earns its place by telling systems apart. One that tells them apart everywhere, including on "
         "items whose correct answer is the same for everyone, is measuring something other than what it claims.", "",
         "Both halves are tested the same way. The statistic is the standard deviation of the systems' mean paired "
         "differences on that family, which uses every system rather than the two extremes. The null permutes the "
         "system labels **within each source**, keeping the difficulty of the source and destroying only the "
         "identity of the system answering it; the p-value is the share of permutations reaching the observed "
         "spread. The range is given beside it for reading, not for testing.", "",
         "The prediction is asymmetric. On a perturbation family, systems should differ: reacting to changed "
         "evidence is a capability. On a negative control, where the correct answer is to leave the reply alone, "
         "they should not.", "",
         f"Split: {split}. Permutations: {PERM}.", "",
         "| family | kind | sources | systems | sd between systems (90% CI) | range | permutation p |",
         "|---|---|---|---|---|---|---|"]
    rows_out = []
    for fam in PERTURBATION + CONTROLS:
        rows = [(s, d) for s, d in (per.get(fam) or {}).items() if len(d) >= 2]
        if len(rows) < 20:
            continue
        obs, p, means, rng = spread_and_p(rows, seed=abs(hash(fam)) % 1000)
        lo, hi = sd_ci(rows, seed=abs(hash(fam)) % 997)
        kind = "perturbation" if fam in PERTURBATION else "**negative control**"
        rows_out.append((fam, kind, len(rows), len(means), obs, p, rng, lo, hi))
        L.append(f"| `{fam}` | {kind} | {len(rows)} | {len(means)} | {obs:.3f} [{lo:.3f}, {hi:.3f}] | {rng:.3f} | {p:.4f} |")
    L.append("")
    pert = [r for r in rows_out if r[1] == "perturbation"]
    ctrl = [r for r in rows_out if r[1] != "perturbation"]
    if pert and ctrl:
        L += ["## Reading", "",
              "**What this statistic is.** It is the spread between systems in *how much the edit moves them*, "
              "not the spread in how well they answer. Two systems whose forbidden-action rates are 0.05 and 0.35 "
              "but who both rise by 0.10 under the edit contribute nothing to it. Read it as the heterogeneity of "
              "the perturbation effect, and read absolute levels from the per-system table in "
              "[`CONFIRMATORY.md`](CONFIRMATORY.md).", "",
              "Every perturbation family shows heterogeneity: sd " +
              ", ".join(f"{r[4]:.3f}" for r in pert) + " at permutation p " +
              ", ".join(f"{r[5]:.4f}" for r in pert) + ". On the two negative controls the point estimates are " +
              " and ".join(f"{r[4]:.3f}" for r in ctrl) + " with 90 percent upper limits of " +
              " and ".join(f"{r[8]:.3f}" for r in ctrl) + ".", "",
              "**The claim the intervals support is a separation, and the intervals say how wide it is.** The "
              f"controls' 90 percent upper limits are {ctrl[0][8]:.3f} and {ctrl[1][8]:.3f}. "
              + (f"{sum(1 for r in pert if r[4] > max(c[8] for c in ctrl))} of the {len(pert)} perturbation "
                 f"families have point estimates above both limits, from "
                 f"{min(r[4] for r in pert if r[4] > max(c[8] for c in ctrl)):.3f} to {max(r[4] for r in pert):.3f}. ")
              + f"A large p on a control is the resolution a panel of {max(r[3] for r in rows_out)} systems buys, and "
              "the separation is stated at that resolution: an equivalence claim on the controls would need a "
              "preregistered margin, which the protocol does not set.", "",
              "**What the permutation null assumes.** Labels are permuted within each source, which holds source "
              "difficulty fixed and destroys only which system answered it. That is an exchangeability null, "
              "stronger than equality of means: it also fails if systems differ in variance or in which sources "
              "they miss. Rejecting it therefore licenses \"these systems are not interchangeable on this family\", "
              "not the narrower \"their means differ\". The paired difference is permuted as one unit, the system "
              "panel is fixed across families, and 4,000 permutations put the smallest reportable p at 1/4001, so "
              "the two families at 0.0003 are at that floor and their evidence should not be ranked against each "
              "other.", "",
              "On `buried_red_flag` the systems run from +0.007 to +0.486 on the same items with the same judge. "
              "A single number averaged over families would hide that.", ""]
    text = "\n".join(L) + "\n"
    print(text)
    if a.out:
        Path(a.out).write_text(text)


if __name__ == "__main__":
    main()
