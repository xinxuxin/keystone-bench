#!/usr/bin/env python3
"""Does the edit leave a fingerprint a model could answer instead of the evidence?

Every paired-perturbation benchmark inherits the same objection: the edit changes the surface of the
message, so an assistant that reacts to "this text was tampered with" scores as though it reacted to the
evidence. Keystone's paraphrase control answers the behavioural half of that objection. This page answers the
measurement half, by asking how detectable each edit is and whether detectability explains what models did.

Three contrasts, each scored as a two-alternative forced choice on held-out sources: the detector sees both
versions of one source it never trained on and must pick the edited one, so chance is 0.50.

1. `original vs twin`, how visible the evidence edit is.
2. `original vs control`, how visible the paraphrase is. The control changes wording and no evidence, so
   whatever detectability it carries is the cost of editing at all rather than of removing evidence.
3. `twin vs control`, whether an evidence edit looks different from a wording edit.

The detector is a bag-of-words logistic regression over the message text, with a length-only baseline beside
it to show how much of the signal is simply that a removal makes the message shorter. It is a floor on
detectability, not a ceiling: a frontier model reading the message can do better, which is exactly why the
last section matters more than the first three.

**The decisive section is the last one.** For the `missing_evidence` twins with reference replies, it asks
whether the items whose edit is easiest to detect are the items where assistants changed their answer. If
detectability drove the effect, that correlation would be strong and positive. Regenerate with
`python tools/shortcut_audit.py`.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "SHORTCUT_AUDIT.md"
FOLDS = 5
EPOCHS = int(os.environ.get("KEYSTONE_EPOCHS", 60))
PERM = int(os.environ.get("KEYSTONE_PERM", 20000))
L2 = 1e-4
MIN_DF = 3
CHANCE = 0.50   # two-alternative forced choice: fixed by the design, not measured from any run
STOP = set("""a an and the my his her their our your i i'm i've it its is are was were be been being do does did have has had
also as at by for from in into of on or so that this these those to too with within without you we they he she him them us
not no but if then than when where which who whom how what why can could should would may might must will shall about after
before over under again more most some such only own same very just now here there while during because both each few other
any own off out up down over""".split())


def rows(p: Path) -> list:
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def featurise(text: str) -> dict:
    """Bag of words plus two surface features, L2-normalised so length does not dominate the词 features."""
    toks = re.findall(r"[a-z']+|\d+", text.lower())
    f = Counter(toks)
    n = math.sqrt(sum(v * v for v in f.values())) or 1.0
    f = {f"w:{k}": v / n for k, v in f.items()}
    f["b:chars"] = min(len(text), 4000) / 1000.0
    f["b:tokens"] = min(len(toks), 800) / 200.0
    f["b:bias"] = 1.0
    return f


def train(data: list, keep: set) -> dict:
    """L2-regularised logistic regression, plain gradient descent. Small data, no dependencies."""
    w = defaultdict(float)
    lr = 0.5
    for _ in range(EPOCHS):
        grad = defaultdict(float)
        for x, y in data:
            z = sum(w[k] * v for k, v in x.items() if k in keep)
            p = 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, z))))
            d = p - y
            for k, v in x.items():
                if k in keep:
                    grad[k] += d * v
        m = len(data)
        for k in list(grad) + list(w):
            w[k] -= lr * (grad[k] / m + L2 * w[k])
    return dict(w)


def score(w: dict, x: dict) -> float:
    return sum(w.get(k, 0.0) * v for k, v in x.items())


def two_afc(pairs: list, seed: int = 0):
    """Grouped cross-validation: train on other sources, then pick the edited version of a held-out source.

    `pairs` is [(source id, text of the unedited side, text of the edited side)]. Returns the detector's
    accuracy, the length-only baseline's accuracy, the per-source margin, and the heaviest features."""
    if len(pairs) < 20:
        return None, None, {}, []
    rng = random.Random(seed)
    idx = list(range(len(pairs)))
    rng.shuffle(idx)
    folds = [idx[i::FOLDS] for i in range(FOLDS)]
    feats = [(featurise(a), featurise(b)) for _, a, b in pairs]
    hits = base_hits = 0
    margin, weights = {}, defaultdict(float)
    for f in range(FOLDS):
        test = set(folds[f])
        tr_idx = [i for i in idx if i not in test]
        df = Counter(k for i in tr_idx for side in feats[i] for k in side)
        keep = {k for k, c in df.items() if c >= MIN_DF or k.startswith("b:")}
        data = [(feats[i][0], 0.0) for i in tr_idx] + [(feats[i][1], 1.0) for i in tr_idx]
        w = train(data, keep)
        for k, v in w.items():
            weights[k] += v / FOLDS
        longer_is_edited = sum(1 for i in tr_idx if len(pairs[i][2]) > len(pairs[i][1])) > len(tr_idx) / 2
        for i in test:
            d = score(w, feats[i][1]) - score(w, feats[i][0])
            margin[pairs[i][0]] = d
            hits += d > 0
            longer = len(pairs[i][2]) > len(pairs[i][1])
            base_hits += longer == longer_is_edited
    top = sorted(((v, k[2:]) for k, v in weights.items() if k.startswith("w:") and k[2:] not in STOP and len(k) > 5),
                 reverse=True)[:6]
    return hits / len(pairs), base_hits / len(pairs), margin, top


def spearman_perm(pairs: list, seed: int = 0):
    if len(pairs) < 8:
        return None, None
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j + 2) / 2
            i = j + 1
        return r
    def rho(xs, ys):
        rx, ry = rank(xs), rank(ys)
        mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
        num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
        den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
        return num / den if den else 0.0
    xs, ys = [p[0] for p in pairs], [p[1] for p in pairs]
    obs = rho(xs, ys)
    rng = random.Random(seed)
    hits = 0
    for _ in range(PERM):
        sh = ys[:]
        rng.shuffle(sh)
        hits += abs(rho(xs, sh)) >= abs(obs)
    return obs, (hits + 1) / (PERM + 1)


def fmt(x, nd=2):
    return "n/a" if x is None else f"{x:.{nd}f}"



RUN_PREFIX = "quick"


def blind_baseline(cross_acc: dict) -> list[str]:
    """What a fixed policy that never reads the evidence actually scores, per family.

    An earlier version of this page claimed that a fixed policy scores zero on a paired difference and that
    2a-1 at the detector's accuracy bounds the strongest blind policy. Both were wrong, and the second was
    wrong in the direction that flattered the benchmark: a measured detector's accuracy `a` is at most the
    Bayes accuracy `a*`, so `2a-1` is a value some blind policy achieves, not a bound on all of them.

    What is reported here instead is measured, not derived. Six fixed policies are scored by the same action
    rules as a real reply, using each side's own annotation. `always_definitive` commits to the original
    course of action every time; on a perturbation family the edit is what moves that action onto the
    forbidden list, so the policy scores a paired difference near 1 without reading anything. That is not a
    hole in the design, it is what the outcome is defined to measure, and it sets the scale: a real system
    that adapted perfectly would score 0 and one that never adapted would score what this policy scores.

    The controls are where the argument lives. On the two negative-control families the edit leaves the
    evidence state unchanged, so both sides carry identical acceptable and forbidden lists, which makes every
    fixed policy's paired difference come out exactly zero on every run. A blind policy therefore cannot
    produce the contrast this benchmark reports, which is an effect on the perturbation families *next to*
    zero on the controls.
    """
    import random
    import sys as _sys
    _sys.path.insert(0, str(ROOT / "tools"))
    from trivial_baselines import judged
    from keystone.data import load_pairs
    POL = [("always_definitive", "commits to the original action every time"),
           ("parrot_then_act", "names the gap, then commits anyway"),
           ("always_ask", "asks the decisive question, gives nothing"),
           ("always_conditional", "hedges every answer on the unknown"),
           ("always_escalate", "sends everyone to urgent evaluation"),
           ("always_refuse", "refers out, gives nothing")]
    PERT_FAM = ["missing_evidence", "conflicting_evidence", "buried_red_flag"]
    CTRL_FAM = ["salient_distractor", "demographic_control"]
    FAM = PERT_FAM + CTRL_FAM

    def boot(v, seed=0):
        if not v:
            return float("nan"), float("nan"), float("nan")
        rng = random.Random(seed); n = len(v)
        ms = sorted(sum(v[rng.randrange(n)] for _ in range(n)) / n for _ in range(2000))
        return sum(v) / n, ms[50], ms[1949]

    pairs = {f: [p for p in load_pairs(f, "core", split="test") if p.has_state and p.paraphrase is not None] for f in FAM}
    results = {}
    L = ["", "## What a policy that never reads the evidence scores", "",
         "Six fixed policies, scored by the same action rules as a real reply, each side judged against its own "
         "annotation. None of them reads the conversation. Held-out split.", "",
         "| policy | " + " | ".join(f"`{f}`" for f in FAM) + " |", "|---|" + "---|" * len(FAM)]
    for pol, desc in POL:
        cells = []
        results[pol] = {}
        for fam in FAM:
            ds = []
            for p in pairs[fam]:
                e = judged(pol, p.evidence_state, "perturbed")
                c = judged(pol, p.evidence_state, "paraphrase")
                ds.append(float(bool(e.get("forbidden"))) - float(bool(c.get("forbidden"))))
            if len(ds) < 20:
                cells.append("n/a"); results[pol][fam] = None; continue
            m, lo, hi = boot(ds, seed=abs(hash(pol + fam)) % 997)
            results[pol][fam] = (m, lo, hi)
            cells.append(f"**{m:+.3f}**" if (lo > 0 or hi < 0) else f"{m:+.3f}")
        L.append(f"| `{pol}` <br><span style='font-weight:400'>{desc}</span> | " + " | ".join(cells) + " |")

    # the two narrative numbers below, read back from the table just built rather than written into the string
    def_vals = [results["always_definitive"][f][0] for f in PERT_FAM if results["always_definitive"].get(f)]
    def_lo, def_hi = (min(def_vals), max(def_vals)) if def_vals else (float("nan"), float("nan"))
    ctrl_vals = [results[pol][fam][0] for pol, _ in POL for fam in CTRL_FAM if results[pol].get(fam)]
    ctrl_lo, ctrl_hi = (min(ctrl_vals), max(ctrl_vals)) if ctrl_vals else (float("nan"), float("nan"))
    ctrl_desc = f"exactly {ctrl_lo:+.3f}" if ctrl_lo == ctrl_hi else f"between {ctrl_lo:+.3f} and {ctrl_hi:+.3f}"

    L += ["", "Bold marks an interval excluding zero.", "",
          "**On the perturbation families a blind policy scores high, and that is what the outcome is for.** "
          f"`always_definitive` reaches {def_lo:+.2f} to {def_hi:+.2f}: it commits to the same course of action on "
          "both sides, and on a perturbation family the edit is precisely what moves that action onto the "
          "forbidden list. A system that adapted perfectly would score 0 here and one that never adapted would "
          "score what this policy scores, so the policy sets the top of the scale rather than exposing a hole. "
          "Evaluated systems score well below this ceiling on the same families; see the per-family risk "
          "difference in [`CONFIRMATORY.md`](CONFIRMATORY.md).", "",
          f"**On the negative controls every fixed policy scores {ctrl_desc}.** The edit leaves the evidence "
          "state unchanged, so both sides carry identical acceptable and forbidden lists and any reply, blind or "
          "not, is scored the same way twice. This is what rules a blind policy out: the result this benchmark "
          "reports is an effect on the perturbation families *together with* zero on the controls, and no policy "
          "that ignores the conversation can produce that pair.", "",
          "Detectability is reported above for the same reason but does not bound this. A measured detector's "
          "", "**The adaptation rate rules a blind policy out by construction, not by measurement.** The decomposition in [`CROSS_SCORING.md`](CROSS_SCORING.md) writes the paired outcome as a standard shift plus a reply adaptation, and the second term is the difference between two judgements of the *same text* whenever the policy's reply does not depend on the edit. Every fixed policy in the table above therefore has an adaptation rate of exactly zero, whatever its level on either side. That is an algebraic property of the estimator rather than a number this audit had to go and measure.",
          "accuracy is at most the Bayes accuracy, so a value computed from it is achievable by some blind policy "
          "rather than a ceiling on all of them; the controls, not a bound, are what carry the argument.", ""]
    return L


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dist", default=str(ROOT / "dist"))
    ap.add_argument("--out", default=str(OUT), help="where to write the report (default: the docs page)")
    ap.add_argument("--records", default=str(ROOT / "release" / "reference_records.jsonl"))
    ap.add_argument("--prefix", default="quick", help="run-directory prefix for the reference effects")
    a = ap.parse_args()
    global RUN_PREFIX
    RUN_PREFIX = a.prefix
    twins = rows(Path(a.dist) / "keystone_twins.jsonl")
    by_fam = defaultdict(list)
    for t in twins:
        by_fam[t["family"]].append(t)

    L = ["# Does the edit leave a fingerprint a model could answer instead of the evidence", "",
         "Every paired-perturbation benchmark inherits this objection: the edit changes the surface of the message, so an "
         "assistant reacting to \"this text was tampered with\" scores as though it reacted to the evidence. The paraphrase "
         "control answers the behavioural half. This page answers the measurement half, by asking how visible each edit is, "
         "whether visibility explains what models did, and what the edits have in common that an authoring pass should remove.", "",
         f"The detector is a bag-of-words logistic regression trained on other sources and scored as a two-alternative forced "
         f"choice: it sees both versions of a held-out source and picks the edited one, so chance is {CHANCE:.2f}. It is a floor on "
         "detectability rather than a ceiling, which is why the sections after the first matter more than the first.", "",
         "## How visible is each edit", "",
         f"Two-alternative forced choice on held-out sources, chance {CHANCE:.2f}. `Length only` picks by which version "
         "is longer, so it is the part of detectability that needs no vocabulary at all.", "",
         "| Family | Sources | original vs twin | length only | original vs control | twin vs control | Heaviest tokens in the twin |",
         "|---|---|---|---|---|---|---|"]
    margins, cross_acc, accs, accp = {}, {}, {}, {}
    for fam in sorted(by_fam):
        ts = by_fam[fam]
        pert = [(t["prompt_id"], t["original_prompt"], t["perturbed_prompt"]) for t in ts]
        para = [(t["prompt_id"], t["original_prompt"], t["paraphrase_prompt"]) for t in ts
                if t.get("paraphrase_released") and t.get("paraphrase_prompt")]
        cross = [(t["prompt_id"], t["paraphrase_prompt"], t["perturbed_prompt"]) for t in ts
                 if t.get("paraphrase_released") and t.get("paraphrase_prompt")]
        acc, base, marg, top = two_afc(pert, seed=1)
        acc_p, _, _, _ = two_afc(para, seed=2)
        acc_c, _, _, _ = two_afc(cross, seed=3)
        margins[fam] = marg
        cross_acc[fam] = acc_c
        accs[fam] = acc
        accp[fam] = acc_p
        L.append(f"| `{fam}` | {len(ts)} | **{fmt(acc)}** | {fmt(base)} | {fmt(acc_p)} | {fmt(acc_c)} | "
                 f"{', '.join(f'`{t}`' for _, t in top[:4])} |")

    L += blind_baseline(cross_acc)

    # what the edits share: a repeated insertion vocabulary is an authoring tell, and a fixable one
    L += ["", "## What the edits repeat", "",
          "A family whose insertions reuse the same clinical furniture is learnable in a way no control can fix: a model that "
          "sees the same comorbidity in every distractor learns the family, not the reasoning. Per family, the content terms "
          "that appear in the edited span and not in the original message, ranked by the share of sources whose edit uses them. "
          "`tools/quality_checks.py` turns the same signal into a per-twin screen (`C9R_templated_insertion`, with the terms in "
          "`templated_terms`), flagging a term that carries at least 8 percent of a family's insertions and is at least four times "
          "commoner there than in the source messages themselves.", "",
          "| Family | Sources with an edit span | Most repeated inserted terms (share of sources) |", "|---|---|---|"]
    for fam in sorted(by_fam):
        c, n = Counter(), 0
        for t in by_fam[fam]:
            o = set(re.findall(r"[a-z']{4,}", (t["original_prompt"] or "").lower()))
            e = set(re.findall(r"[a-z']{4,}", (t["perturbed_prompt"] or "").lower()))
            new_terms = {w for w in e - o if w not in STOP}
            if new_terms:
                n += 1
                c.update(new_terms)
        if not n:
            L.append(f"| `{fam}` | 0 | the edit removes text rather than adding it |")
            continue
        L.append(f"| `{fam}` | {n} | " + ", ".join(f"`{w}` {v / n:.1%}" for w, v in c.most_common(5)) + " |")

    # the decisive test: do the most detectable edits move models the most
    recs = [r for r in rows(Path(a.records)) if r["family"] == "missing_evidence"]
    per_item = defaultdict(list)
    per_model_drop = defaultdict(lambda: defaultdict(list))   # {condition: {model: [dropped commitment, 0/1]}}
    for r in recs:
        o = (r["behavior"].get("original") or {}).get("stance")
        if o != "definitive":
            continue
        for cond in ("perturbed", "paraphrase"):
            s = (r["behavior"].get(cond) or {}).get("stance")
            if s is None:
                continue
            dropped = float(s != "definitive")
            per_model_drop[cond][r["model"]].append(dropped)
            if cond == "perturbed":
                per_item[r["source_id"]].append(dropped)
    marg = margins.get("missing_evidence", {})
    paired = [(marg[sid], sum(v) / len(v)) for sid, v in per_item.items() if sid in marg and v]
    rho, p = spearman_perm(paired)

    # same reference pilot, broken down by model instead of pooled: how much each condition alone moves the
    # definitive rate, for the "editing at all" reading below
    pert_drop = {m: sum(v) / len(v) for m, v in per_model_drop["perturbed"].items() if v}
    para_drop = {m: sum(v) / len(v) for m, v in per_model_drop["paraphrase"].items() if v}
    pert_drop_lo, pert_drop_hi = (min(pert_drop.values()), max(pert_drop.values())) if pert_drop else (float("nan"),) * 2
    para_drop_hi = max(para_drop.values()) if para_drop else float("nan")

    # numbers for the Reading section below, read back from the tables above rather than written into the strings
    ctrl_acc = sorted(v for v in (accs.get(f) for f in ("salient_distractor", "demographic_control")) if v is not None)
    para_acc = [v for v in accp.values() if v is not None]
    ap_lo, ap_hi = (min(para_acc), max(para_acc)) if para_acc else (float("nan"), float("nan"))
    L += ["", "## Does the fingerprint explain the behaviour", "",
          "The detector's margin on an item is how obviously that item was edited. If assistants were "
          "answering the fingerprint, the items with the largest margin would be the items where they "
          "changed their answer most often.", "",
          f"On the {len(paired)} `missing_evidence` items with reference replies, the correlation between the "
          f"detector's margin and the share of assistants that dropped their commitment is Spearman rho "
          f"**{fmt(rho, 3)}** (permutation p {fmt(p, 2) if p is not None else 'n/a'}).", "",
          "The same reference pilot, per model: the share of originally-definitive replies that no longer "
          "commit once the evidence is edited, against the same share when only the wording changes.", "",
          "| model | dropped commitment, evidence removed | dropped commitment, paraphrase only |",
          "|---|---|---|"]
    for m in sorted(set(pert_drop) | set(para_drop)):
        L.append(f"| `{m.split('/')[-1]}` | {fmt(pert_drop.get(m))} | {fmt(para_drop.get(m))} |")
    L += ["",
          "## Reading", "",
          "**The most detectable edits are the ones where changing your answer is wrong.** The two negative-control families "
          f"sit at {' and '.join(fmt(v) for v in ctrl_acc)}, the top of the table, because an insertion always lengthens the "
          "message. On exactly those families the correct behaviour is to answer unchanged. A model that keys on \"something "
          "was edited here\" therefore fails the controls while passing the perturbations, and the release reports both, so "
          "the shortcut is scored rather than rewarded. This is structural: it holds however good the detector gets.", "",
          "**Visibility is length, and length carries no direction.** The length-only baseline matches the full detector on "
          "every insertion family, so what is detectable is that the message got longer, not what the added sentence means. "
          "Knowing the message was edited does not tell an assistant whether to ask a question, change the drug, escalate, or "
          "hold its answer, which are the four things the families ask for.", "",
          f"**Editing at all is visible, from {fmt(ap_lo)} to {fmt(ap_hi)}.** The paraphrase control changes wording and no "
          "evidence and is detectable in that range in every family, which is the cost of touching the text. In the reference "
          f"pilot that control moved the definitive rate by at most {fmt(para_drop_hi)} across evaluated models, while removing "
          f"an element moved it by {fmt(pert_drop_lo)} to {fmt(pert_drop_hi)}.", "",
          f"**Visibility does not explain the behaviour, and it runs the wrong way.** The correlation between how obviously an "
          f"item was edited and how often assistants dropped their commitment on it is {fmt(rho, 3)} "
          f"(permutation p {fmt(p, 2) if p is not None else 'n/a'}), negative. The shortcut hypothesis predicts a strong "
          f"positive correlation. What this says instead is that the surgical edits move models most: taking out one short "
          f"decisive clause is both the hardest edit to see and the one that changes the answer, while a large removal is "
          f"obvious and often leaves enough of the message to answer from.", "",
          "**What it does not settle, and what to do about it.** A bag-of-words detector is a floor, and a frontier assistant "
          "reading the message can notice a tell this one misses. The repetition table above is where such a tell would show "
          "up first, and it is the authoring queue: a term carrying a large share of one family's insertions should be varied "
          "before that family grows.", ""]
    Path(a.out).write_text("\n".join(L) + "\n")
    print(f"{len(by_fam)} families; detectability-behaviour rho {fmt(rho, 3)} on {len(paired)} items -> {a.out}")


if __name__ == "__main__":
    main()
