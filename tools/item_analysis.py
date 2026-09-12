"""Item-level properties of the benchmark: discrimination, ceiling and floor effects, and the size a run needs.

A benchmark is only as good as its items. Three things a reader should be able to check before believing an effect:

  1. **Discrimination.** An item every model gets right, or every model gets wrong, carries no information about
     models. Reported per family as the share of items whose outcome is constant across the evaluated models, and as
     the item-total correlation (point-biserial against the model's mean score on the rest of the family).
  2. **Ceiling.** An item whose *unedited* version already draws a forbidden action cannot show an effect of editing;
     the paired effect is reported both over all items and over the items where the original was handled correctly.
  3. **Size.** Given the observed per-family effect and the between-item variance, the number of items needed for 80
     percent power at the family's own effect and at a reference effect of 0.10.

Usage: python tools/item_analysis.py [--runs runs] [--out docs/ITEM_ANALYSIS.md] [--layer quick]
"""
from __future__ import annotations
import argparse, glob, json, math, os, random, statistics, sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from keystone.metrics import PRIMARY_OUTCOME  # noqa: E402

FAMILIES = ["missing_evidence", "conflicting_evidence", "buried_red_flag", "demographic_shift",
            "alternative_evidence", "missing_evidence_early", "salient_distractor", "demographic_control"]
BOOT = int(os.environ.get("KEYSTONE_BOOT", "2000"))


def outcome(rec: dict, cond: str, key: str = "forbidden"):
    a = (rec.get("action") or {}).get(cond) or {}
    if key == "forbidden":
        return None if not a else bool(a.get("forbidden"))
    if key == "decisive_hit":
        return None if not a else (bool(a.get("asks_decisive_question")) or bool(a.get("conditional")))
    if key == "escalates":
        return None if not a else bool(a.get("escalates"))
    if key == "acceptable":
        return None if not a else bool(a.get("acceptable"))
    return None


def load(runs: str, layer: str) -> dict:
    """{(family, item): {model: {cond: {key: value}}}}"""
    out = defaultdict(dict)
    for d in sorted(glob.glob(os.path.join(runs, f"{layer}__*"))):
        model = Path(d).name.split("__", 1)[1]
        if "__judge-" in model or model.startswith(("n1_", "floor_")):
            continue
        for f in sorted(glob.glob(os.path.join(d, "*", "records.jsonl"))):
            for line in open(f):
                if not line.strip():
                    continue
                r = json.loads(line)
                out[(r["family"], r["id"])][model] = {
                    c: {k: outcome(r, c, k) for k in ("forbidden", "decisive_hit", "escalates", "acceptable")}
                    for c in ("original", "perturbed", "paraphrase")}
    return out


def boot_ci(vals: list[float], seed: int = 0) -> tuple[float, float, float]:
    if not vals:
        return float("nan"), float("nan"), float("nan")
    rng = random.Random(seed); n = len(vals); ms = []
    for _ in range(BOOT):
        ms.append(sum(vals[rng.randrange(n)] for _ in range(n)) / n)
    ms.sort()
    return sum(vals) / n, ms[int(0.025 * BOOT)], ms[min(BOOT - 1, int(0.975 * BOOT))]


def n_for_power(effect: float, sd: float, power: float = 0.80, alpha: float = 0.05) -> int | None:
    """Paired one-sample size for a mean difference of `effect` with between-item sd `sd` (normal approximation)."""
    if not effect or sd <= 0 or math.isnan(effect) or math.isnan(sd):
        return None
    z_a, z_b = 1.959963985, 0.8416212336 if power == 0.80 else 1.2815515655
    return max(2, math.ceil(((z_a + z_b) * sd / abs(effect)) ** 2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="runs"); ap.add_argument("--layer", default="quick"); ap.add_argument("--out")
    a = ap.parse_args()
    data = load(a.runs, a.layer)
    models = sorted({m for v in data.values() for m in v})
    L = ["# Item analysis", "",
         f"Layer `{a.layer}`, {len({k[1] for k in data})} items over {len(FAMILIES)} families, evaluated on "
         f"{len(models)} models ({', '.join(models)}). Every number here is a property of the items, not of a model.", ""]

    # 1. discrimination
    L += ["## Discrimination", "",
          "An item whose primary outcome is the same for every evaluated model separates nothing. `constant` is the "
          "share of such items; `item-total r` is the point-biserial correlation between the item's outcome and the "
          "model's mean outcome on the rest of the family, averaged over models (higher is better, negative means the "
          "item runs against the family).", "",
          "| family | items | primary outcome | constant | mean item-total r |", "|---|---|---|---|---|"]
    disc_rows = {}
    for fam in FAMILIES:
        key = {"decisive_question_hit": "decisive_hit", "escalated_when_sufficient": "escalates",
               "necessary_update": "acceptable", "stable_on_control": "acceptable"}[PRIMARY_OUTCOME[fam][0]]
        items = {k[1]: v for k, v in data.items() if k[0] == fam}
        vals = {i: {m: (v.get(m, {}).get("perturbed") or {}).get(key) for m in models} for i, v in items.items()}
        vals = {i: {m: x for m, x in d.items() if x is not None} for i, d in vals.items()}
        vals = {i: d for i, d in vals.items() if len(d) >= 2}
        if not vals:
            continue
        const = sum(1 for d in vals.values() if len(set(d.values())) == 1) / len(vals)
        rs = []
        for m in models:
            xs = [(i, d[m]) for i, d in vals.items() if m in d]
            if len(xs) < 4:
                continue
            tot = []
            for i, _ in xs:
                rest = [float(v) for mm, v in vals[i].items() if mm != m]
                tot.append(statistics.fmean(rest) if rest else 0.0)
            xv = [float(x) for _, x in xs]
            if len(set(xv)) > 1 and len(set(tot)) > 1:
                rs.append(statistics.correlation(xv, tot))
        disc_rows[fam] = (len(vals), const, statistics.fmean(rs) if rs else float("nan"))
        r_cell = f"{statistics.fmean(rs):.2f}" if rs else "n/a"
        L.append(f"| {fam} | {len(vals)} | {PRIMARY_OUTCOME[fam][1]} | {const:.2f} | {r_cell} |")
    L.append("")

    # 2. ceiling: items whose original already draws a forbidden action
    L += ["## Ceiling", "",
          "An item whose unedited version already draws a forbidden action has no room to show an effect of editing. "
          "`original forbidden` is the share of (item, model) cells in that state; the effect is then reported over "
          "all items and over the subset where the original was handled correctly.", "",
          "| family | items | original forbidden | effect, all items | effect, original correct |", "|---|---|---|---|---|"]
    power_in = {}
    for fam in FAMILIES:
        items = {k[1]: v for k, v in data.items() if k[0] == fam}
        cells = [(i, m, v[m]) for i, v in items.items() for m in v]
        og = [c for c in cells if (c[2].get("original") or {}).get("forbidden") is not None]
        share = sum(1 for c in og if c[2]["original"]["forbidden"]) / len(og) if og else float("nan")
        def eff(only_clean: bool):
            per = defaultdict(list)
            for i, m, v in cells:
                p, q, o = v.get("perturbed") or {}, v.get("paraphrase") or {}, v.get("original") or {}
                if p.get("forbidden") is None or q.get("forbidden") is None:
                    continue
                if only_clean and o.get("forbidden") is not False:
                    continue
                per[i].append(float(p["forbidden"]) - float(q["forbidden"]))
            vals = [statistics.fmean(v) for v in per.values() if v]
            return vals
        all_v, clean_v = eff(False), eff(True)
        if not all_v:
            continue
        m1, lo1, hi1 = boot_ci(all_v); m2, lo2, hi2 = boot_ci(clean_v, seed=1)
        power_in[fam] = (m1, statistics.pstdev(all_v) if len(all_v) > 1 else float("nan"), len(all_v))
        c2 = f"{m2:+.3f} [{lo2:+.3f}, {hi2:+.3f}] (n={len(clean_v)})" if clean_v else "n/a"
        L.append(f"| {fam} | {len(all_v)} | {share:.2f} | {m1:+.3f} [{lo1:+.3f}, {hi1:+.3f}] | {c2} |")
    L.append("")

    # 3. size
    L += ["## Items a run needs", "",
          "Paired items for 80 percent power at two-sided 0.05, from the observed between-item standard deviation of "
          "the paired difference. The second column is the family's own effect; the third is a reference effect of "
          "0.10, the smallest difference this benchmark is meant to resolve.", "",
          "| family | items now | observed effect | sd | n for own effect | n for 0.10 |", "|---|---|---|---|---|---|"]
    for fam, (e, sd, n) in power_in.items():
        L.append(f"| {fam} | {n} | {e:+.3f} | {sd:.3f} | {n_for_power(e, sd) or 'n/a'} | {n_for_power(0.10, sd) or 'n/a'} |")
    L += ["", "The core layer has between 86 and 1,232 items per family, so the families whose row above asks for more "
              "items than the quick layer holds are answerable at full scale; the number is what sets the size of a "
              "confirmatory run rather than a reason to read the quick layer differently.", ""]
    text = "\n".join(L) + "\n"
    print(text)
    if a.out:
        Path(a.out).write_text(text)


if __name__ == "__main__":
    main()
