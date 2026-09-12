"""Judge panel: agreement between judge vendors and the headline effects under each judge.

Reads the reference runs (judge GPT-4.1) and the panel re-judgings of the same replies
(runs/quick__<model>__judge-<judge>/<family>/records.jsonl), aligns them item by item, and reports

  1. pairwise agreement and Cohen's kappa per outcome (forbidden, acceptable, decisive-question hit,
     escalates, behaviour stance), pooled over conditions and on the edited condition alone;
  2. the twin-minus-paraphrase forbidden-action risk difference per family under each judge
     (item bootstrap, models averaged within item);
  3. the same effect with the model's own vendor excluded from the judging.

Usage: python tools/judge_panel.py --out docs/JUDGE_PANEL.md
"""
from __future__ import annotations
import argparse, glob, json, os, random, statistics, sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

MODELS = ["claude-sonnet-5", "deepseek-v4-pro", "gemini-3.8-flash", "gpt-5.6-terra", "llama-4-maverick"]
VENDOR = {"claude-sonnet-5": "anthropic", "deepseek-v4-pro": "deepseek", "gemini-3.8-flash": "google",
          "gpt-5.6-terra": "openai", "llama-4-maverick": "meta",
          "gpt-4.1": "openai"}
CONDS = ("original", "perturbed", "paraphrase")
FAMILIES = ["missing_evidence", "conflicting_evidence", "buried_red_flag", "demographic_shift",
            "alternative_evidence", "missing_evidence_early", "salient_distractor", "demographic_control"]
BOOT = int(os.environ.get("KEYSTONE_BOOT", "2000"))


def load(pattern: str) -> dict:
    """{(family, id): record} over every family directory matching pattern/*/records.jsonl."""
    out = {}
    for f in sorted(glob.glob(os.path.join(pattern, "*", "records.jsonl"))):
        for line in open(f):
            if line.strip():
                r = json.loads(line); out[(r["family"], r["id"])] = r
    return out


def outcomes(r: dict, cond: str) -> dict:
    a = (r.get("action") or {}).get(cond) or {}
    b = (r.get("behavior") or {}).get(cond) or {}
    if not a and not b:
        return {}
    return {
        "forbidden": bool(a.get("forbidden")) if a else None,
        "acceptable": bool(a.get("acceptable")) if a else None,
        "decisive_hit": (bool(a.get("asks_decisive_question")) or bool(a.get("conditional"))) if a else None,
        "escalates": bool(a.get("escalates")) if a else None,
        "stance": b.get("stance") if b else None,
    }


def kappa(pairs: list[tuple]) -> float | None:
    """Cohen's kappa for a list of (label_a, label_b)."""
    pairs = [(x, y) for x, y in pairs if x is not None and y is not None]
    n = len(pairs)
    if n == 0:
        return None
    po = sum(1 for x, y in pairs if x == y) / n
    ca, cb = Counter(x for x, _ in pairs), Counter(y for _, y in pairs)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return None if pe == 1 else (po - pe) / (1 - pe)


def fleiss(rows: list[list]) -> float | None:
    """Fleiss' kappa; rows = per item list of labels from every rater (same count per item)."""
    rows = [r for r in rows if r and all(x is not None for x in r)]
    if not rows:
        return None
    m = len(rows[0]); rows = [r for r in rows if len(r) == m]
    cats = sorted({x for r in rows for x in r}, key=str)
    N = len(rows)
    pj = {c: sum(r.count(c) for r in rows) / (N * m) for c in cats}
    Pi = [(sum(r.count(c) ** 2 for c in cats) - m) / (m * (m - 1)) for r in rows] if m > 1 else []
    if not Pi:
        return None
    Pbar, Pe = sum(Pi) / N, sum(v * v for v in pj.values())
    return None if Pe == 1 else (Pbar - Pe) / (1 - Pe)


def boot_ci(values: list[float], seed: int = 0) -> tuple[float, float, float]:
    """mean and percentile 95 percent interval over item resamples."""
    if not values:
        return float("nan"), float("nan"), float("nan")
    rng = random.Random(seed); n = len(values); ms = []
    for _ in range(BOOT):
        s = [values[rng.randrange(n)] for _ in range(n)]; ms.append(sum(s) / n)
    ms.sort()
    return sum(values) / n, ms[int(0.025 * BOOT)], ms[min(BOOT - 1, int(0.975 * BOOT))]


def effect_table(judged: dict, label: str) -> list[str]:
    """judged: {(model, family, id): {cond: outcomes}}. Twin-minus-paraphrase forbidden risk difference per family."""
    per_item = defaultdict(list)  # (family, id) -> per-model differences
    for (model, fam, iid), conds in judged.items():
        p, q = conds.get("perturbed") or {}, conds.get("paraphrase") or {}
        if p.get("forbidden") is None or q.get("forbidden") is None:
            continue
        per_item[(fam, iid)].append(float(p["forbidden"]) - float(q["forbidden"]))
    lines = []
    for fam in FAMILIES:
        vals = [sum(v) / len(v) for (f, _), v in per_item.items() if f == fam]
        if not vals:
            continue
        m, lo, hi = boot_ci(vals)
        lines.append(f"| {fam} | {label} | {len(vals)} | {m:+.3f} [{lo:+.3f}, {hi:+.3f}] |")
    return lines


def primary_rates(judged: dict, label: str) -> dict:
    """Edited-condition rates of the family primary outcomes under one judge."""
    from keystone.metrics import PRIMARY_OUTCOME
    key_map = {"decisive_question_hit": "decisive_hit", "escalated_when_sufficient": "escalates",
               "necessary_update": None, "stable_on_control": None}
    out = {}
    for fam in FAMILIES:
        k = key_map.get(PRIMARY_OUTCOME[fam][0])
        if k is None:
            continue
        xs = [c["perturbed"][k] for (m, f, i), c in judged.items() if f == fam and c.get("perturbed") and c["perturbed"].get(k) is not None]
        if xs:
            out[fam] = (sum(xs) / len(xs), len(xs))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="runs")
    ap.add_argument("--judges", nargs="*", default=["claude-sonnet-5", "gemini-3.8-flash"])
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    # judged[judge][(model, family, id)] = {cond: outcomes}
    judged: dict[str, dict] = {"gpt-4.1": {}}
    for model in MODELS:
        base = load(os.path.join(a.runs, f"quick__{model}"))
        for (fam, iid), r in base.items():
            judged["gpt-4.1"][(model, fam, iid)] = {c: outcomes(r, c) for c in CONDS}
        for j in a.judges:
            recs = load(os.path.join(a.runs, f"quick__{model}__judge-{j}"))
            if not recs:
                continue
            judged.setdefault(j, {})
            for (fam, iid), r in recs.items():
                judged[j][(model, fam, iid)] = {c: outcomes(r, c) for c in CONDS}
    judges = [j for j in judged if judged[j]]
    L = [f"# Judge panel", "",
         f"Judges: {', '.join(judges)}. Items are the quick-set replies of {len(MODELS)} models, re-judged with the same "
         f"frozen prompts; the model outputs are identical across judges (cached), only the judge changes.", ""]
    cover = {j: len(judged[j]) for j in judges}
    L += ["| judge | (model, item) pairs judged |", "|---|---|"] + [f"| {j} | {n} |" for j, n in cover.items()] + [""]

    # 1. pairwise agreement
    L += ["## Agreement between judges", "",
          "Percent agreement and Cohen's kappa over every (model, item, condition) both judges scored; the second pair of columns restricts to the edited condition.", "",
          "| outcome | judges | n all | agree all | kappa all | n edited | agree edited | kappa edited |", "|---|---|---|---|---|---|---|---|"]
    for key in ("forbidden", "acceptable", "decisive_hit", "escalates", "stance"):
        for ja, jb in combinations(judges, 2):
            common = set(judged[ja]) & set(judged[jb])
            allp, edp = [], []
            for k in common:
                for c in CONDS:
                    x, y = (judged[ja][k].get(c) or {}).get(key), (judged[jb][k].get(c) or {}).get(key)
                    if x is None or y is None:
                        continue
                    allp.append((x, y))
                    if c == "perturbed":
                        edp.append((x, y))
            if not allp:
                continue
            ag = sum(1 for x, y in allp if x == y) / len(allp); ka = kappa(allp)
            ae = sum(1 for x, y in edp if x == y) / len(edp) if edp else float("nan"); ke = kappa(edp)
            L.append(f"| {key} | {ja} vs {jb} | {len(allp)} | {ag:.3f} | {ka if ka is None else round(ka, 3)} | {len(edp)} | {ae:.3f} | {ke if ke is None else round(ke, 3)} |")
    if len(judges) >= 3:
        L += ["", "Fleiss' kappa over items scored by all judges:", "", "| outcome | n | Fleiss kappa |", "|---|---|---|"]
        common = set.intersection(*(set(judged[j]) for j in judges))
        for key in ("forbidden", "acceptable", "decisive_hit", "stance"):
            rows = [[(judged[j][k].get(c) or {}).get(key) for j in judges] for k in common for c in CONDS]
            rows = [r for r in rows if all(x is not None for x in r)]
            fk = fleiss(rows)
            L.append(f"| {key} | {len(rows)} | {fk if fk is None else round(fk, 3)} |")
    L.append("")

    # 2. effects per judge
    L += ["## Twin-minus-paraphrase forbidden action under each judge", "",
          "Per family: mean over items of the mean over models of (edited forbidden minus paraphrase forbidden), item bootstrap 95 percent interval. "
          "A judge that only shifts the level would move every family; a judge that changes the finding would move the intervals across zero.", "",
          "| family | judge | items | risk difference |", "|---|---|---|---|"]
    for j in judges:
        L += effect_table(judged[j], j)
    L.append("")

    # 3. own-vendor exclusion
    L += ["## Own-vendor exclusion", "",
          "For every model, the judging is averaged over the panel judges whose vendor differs from the model's vendor "
          "(majority when three remain, mean when two); models without a same-vendor judge use the full panel.", "",
          "| family | judging | items | risk difference |", "|---|---|---|---|"]
    excl: dict = {}
    for k in set.union(*(set(judged[j]) for j in judges)):
        model = k[0]
        use = [j for j in judges if VENDOR.get(j) != VENDOR.get(model) and k in judged[j]]
        if not use:
            continue
        conds = {}
        for c in CONDS:
            fs = [judged[j][k][c].get("forbidden") for j in use if judged[j][k].get(c)]
            fs = [f for f in fs if f is not None]
            if fs:
                conds[c] = {"forbidden": (sum(fs) / len(fs)) if len(fs) != 3 else (sum(fs) >= 2)}
        excl[k] = conds
    L += effect_table(excl, "panel minus own vendor")
    L.append("")

    # 4. primary outcomes per judge
    L += ["## Family primary outcomes on the edited condition, per judge", "", "| family | " + " | ".join(judges) + " |", "|---|" + "---|" * len(judges)]
    pr = {j: primary_rates(judged[j], j) for j in judges}
    for fam in FAMILIES:
        cells = [f"{pr[j][fam][0]:.2f} (n={pr[j][fam][1]})" if fam in pr[j] else "n/a" for j in judges]
        if any(c != "n/a" for c in cells):
            L.append(f"| {fam} | " + " | ".join(cells) + " |")
    text = "\n".join(L) + "\n"
    print(text)
    if a.out:
        Path(a.out).write_text(text)


if __name__ == "__main__":
    main()
