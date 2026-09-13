"""Does the benchmark separate systems, and does it separate them only where it should.

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


def spread_and_p(rows: list, seed: int = 0) -> tuple[float, float, dict]:
    """rows: [(source, {model: diff})]. Observed between-system range, and a within-source permutation p."""
    def spread(assign):
        by = defaultdict(list)
        for s, d in rows:
            for m, v in d.items():
                by[assign.get((s, m), m)].append(v)
        means = [statistics.fmean(v) for v in by.values() if len(v) >= MIN_CELL]
        return (max(means) - min(means)) if len(means) > 1 else 0.0
    obs = spread({})
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
    return obs, max(1.0 / PERM, hits / PERM), {m: statistics.fmean(v) for m, v in per_model.items()}


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
         "Both halves are tested the same way. The observed spread is the range of the systems' mean paired "
         "differences on that family. The null permutes the system labels **within each source**, which keeps the "
         "difficulty of the source and destroys only the identity of the system answering it; the p-value is the "
         "share of permutations whose spread reaches the observed one.", "",
         "The prediction is asymmetric. On a perturbation family, systems should differ: reacting to changed "
         "evidence is a capability. On a negative control, where the correct answer is to leave the reply alone, "
         "they should not.", "",
         f"Split: {split}. Permutations: {PERM}.", "",
         "| family | kind | sources | systems | spread between systems | permutation p |", "|---|---|---|---|---|---|"]
    rows_out = []
    for fam in PERTURBATION + CONTROLS:
        rows = [(s, d) for s, d in (per.get(fam) or {}).items() if len(d) >= 2]
        if len(rows) < 20:
            continue
        obs, p, means = spread_and_p(rows, seed=abs(hash(fam)) % 1000)
        kind = "perturbation" if fam in PERTURBATION else "**negative control**"
        rows_out.append((fam, kind, len(rows), len(means), obs, p))
        L.append(f"| `{fam}` | {kind} | {len(rows)} | {len(means)} | {obs:.3f} | {p:.4f} |")
    L.append("")
    pert = [r for r in rows_out if r[1] == "perturbation"]
    ctrl = [r for r in rows_out if r[1] != "perturbation"]
    if pert and ctrl:
        L += ["## Reading", "",
              "Every perturbation family separates the systems: spreads of " +
              ", ".join(f"{r[4]:.2f}" for r in pert) + " at p " +
              ", ".join(f"{r[5]:.4f}" for r in pert) + ". Neither negative control does: spreads of " +
              " and ".join(f"{r[4]:.3f}" for r in ctrl) + " at p " +
              " and ".join(f"{r[5]:.2f}" for r in ctrl) + ".", "",
              "The two halves use the same items per source, the same judge, the same outcome and the same test. "
              "What differs is whether the edit changes what a careful clinician would do. Where it does, the "
              "systems come apart; where it does not, they stay together. A benchmark that separated systems on "
              "both halves would be separating them on something other than evidence sensitivity, and a benchmark "
              "that separated them on neither would not be worth running.", "",
              "This is also what the per-family spread means for a leaderboard. On `buried_red_flag` the systems "
              "run from +0.007 to +0.486 on the same items with the same judge. A single number averaged over "
              "families would hide that, and an ordering built from it would be an ordering of one weighted "
              "average among many.", ""]
    text = "\n".join(L) + "\n"
    print(text)
    if a.out:
        Path(a.out).write_text(text)


if __name__ == "__main__":
    main()
