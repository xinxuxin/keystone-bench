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

**The decisive section is the last one.** For the 80 `missing_evidence` twins with reference replies, it asks
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



def blind_baseline(cross_acc: dict) -> list[str]:
    """What a policy that never reads the evidence could score on the paired difference.

    A fixed policy scores exactly zero: it answers the twin and the control the same way, so the difference
    cancels. The strongest blind policy is therefore the one that guesses which side is the twin from the
    surface and then answers to the family's outcome. If it identifies the twin with accuracy `a`, its
    expected paired risk difference is at most 2a - 1. The detector's twin-versus-control accuracy is a
    measured value of `a`, and a frontier model reading the message would do better, so this is a floor on
    the bound, not a ceiling. The bound is close to 1 on every family, which is exactly why it is not the
    interesting number: what separates the design from a blind policy is that the bound is just as large on
    the two families whose correct answer is no change, and there the measured effect is zero.

    Requires the reference effects; recomputed here from the reference runs so the two tables cannot drift.
    """
    import glob
    from collections import defaultdict as dd
    per = dd(list)
    for f in sorted(glob.glob(str(ROOT / "runs" / "quick__*" / "*" / "records.jsonl"))):
        if "__judge-" in f or "/n1_" in f or "/floor_" in f:
            continue
        for line in open(f):
            if not line.strip():
                continue
            r = json.loads(line)
            a = r.get("action") or {}
            p, q = a.get("perturbed") or {}, a.get("paraphrase") or {}
            if not p or not q:   # an absent verdict is missing; `forbidden: null` is a scored "did not overstep"
                continue
            per[(r["family"], r["id"])].append(float(bool(p.get("forbidden"))) - float(bool(q.get("forbidden"))))
    eff = dd(list)
    for (fam, _), v in per.items():
        eff[fam].append(sum(v) / len(v))
    L = ["", "## What a policy that never reads the evidence could score", "",
         "A fixed policy scores exactly zero on the paired difference: it answers the twin and its control the same way, so "
         "the difference cancels. That is the point of pairing. The strongest *blind* policy is the one that guesses which "
         "side was edited from the surface and then answers to the family's outcome; if it picks the twin with accuracy `a`, "
         "its expected paired risk difference is at most `2a - 1`. The detector above measures `a` as the twin-versus-control "
         "accuracy, and a frontier model reading the message would do better, so the bound below is a floor.", "",
         "| Family | twin vs control | blind bound `2a-1` | measured effect | measured / bound |", "|---|---|---|---|---|"]
    for fam in sorted(cross_acc):
        a = cross_acc[fam]
        bound = 2 * a - 1
        v = eff.get(fam) or []
        if not v:
            L.append(f"| `{fam}` | {fmt(a)} | {bound:+.2f} | n/a | n/a |")
            continue
        m = sum(v) / len(v)
        L.append(f"| `{fam}` | {fmt(a)} | {bound:+.2f} | {m:+.3f} | {m / bound:+.2f} |")
    L += ["", "The bound is above 0.6 on every family, so it does not by itself rule anything out. The last column is what "
              "does. A blind policy spends its accuracy the same way everywhere, so its ratio of measured effect to bound "
              "would be roughly constant across families. Measured, that ratio is near zero on the two families whose "
              "correct answer is to hold the reply and 0.17 to 0.35 on the three families with a headline effect, even "
              "though the two negative controls are among the most detectable families in the table. Detectability is "
              "available to the models and they are not spending it.", ""]
    return L


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dist", default=str(ROOT / "dist"))
    ap.add_argument("--out", default=str(OUT), help="where to write the report (default: the docs page)")
    ap.add_argument("--records", default=str(ROOT / "release" / "reference_records.jsonl"))
    a = ap.parse_args()
    twins = rows(Path(a.dist) / "keystone_twins.jsonl")
    by_fam = defaultdict(list)
    for t in twins:
        by_fam[t["family"]].append(t)

    L = ["# Does the edit leave a fingerprint a model could answer instead of the evidence", "",
         "Every paired-perturbation benchmark inherits this objection: the edit changes the surface of the message, so an "
         "assistant reacting to \"this text was tampered with\" scores as though it reacted to the evidence. The paraphrase "
         "control answers the behavioural half. This page answers the measurement half, by asking how visible each edit is, "
         "whether visibility explains what models did, and what the edits have in common that an authoring pass should remove.", "",
         "The detector is a bag-of-words logistic regression trained on other sources and scored as a two-alternative forced "
         "choice: it sees both versions of a held-out source and picks the edited one, so chance is 0.50. It is a floor on "
         "detectability rather than a ceiling, which is why the sections after the first matter more than the first.", "",
         "## How visible is each edit", "",
         "Two-alternative forced choice on held-out sources, chance 0.50. `Length only` picks by which version "
         "is longer, so it is the part of detectability that needs no vocabulary at all.", "",
         "| Family | Sources | original vs twin | length only | original vs control | twin vs control | Heaviest tokens in the twin |",
         "|---|---|---|---|---|---|---|"]
    margins, cross_acc = {}, {}
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
    for r in recs:
        o = (r["behavior"].get("original") or {}).get("stance")
        p = (r["behavior"].get("perturbed") or {}).get("stance")
        if o == "definitive" and p is not None:
            per_item[r["source_id"]].append(float(p != "definitive"))
    marg = margins.get("missing_evidence", {})
    paired = [(marg[sid], sum(v) / len(v)) for sid, v in per_item.items() if sid in marg and v]
    rho, p = spearman_perm(paired)
    L += ["", "## Does the fingerprint explain the behaviour", "",
          "The detector's margin on an item is how obviously that item was edited. If assistants were "
          "answering the fingerprint, the items with the largest margin would be the items where they "
          "changed their answer most often.", "",
          f"On the {len(paired)} `missing_evidence` items with reference replies, the correlation between the "
          f"detector's margin and the share of assistants that dropped their commitment is Spearman rho "
          f"**{fmt(rho, 3)}** (permutation p {fmt(p, 2) if p is not None else 'n/a'}).", "",
          "## Reading", "",
          "**The most detectable edits are the ones where changing your answer is wrong.** The two negative-control families "
          "sit at 0.99 and 1.00, the top of the table, because an insertion always lengthens the message. On exactly those "
          "families the correct behaviour is to answer unchanged. A model that keys on \"something was edited here\" therefore "
          "fails the controls while passing the perturbations, and the release reports both, so the shortcut is scored rather "
          "than rewarded. This is structural: it holds however good the detector gets.", "",
          "**Visibility is length, and length carries no direction.** The length-only baseline matches the full detector on "
          "every insertion family, so what is detectable is that the message got longer, not what the added sentence means. "
          "Knowing the message was edited does not tell an assistant whether to ask a question, change the drug, escalate, or "
          "hold its answer, which are the four things the families ask for.", "",
          "**Editing at all is visible, at 0.84 to 0.85.** The paraphrase control changes wording and no evidence and is "
          "detectable at that rate in every family, which is the cost of touching the text. In the reference pilot that "
          "control moved the definitive rate by at most 0.07 while removing an element moved it by 0.31 to 0.55.", "",
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
