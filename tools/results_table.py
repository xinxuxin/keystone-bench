#!/usr/bin/env python3
"""Regenerate docs/RESULTS.md from run directories and the shipped reference results.

A results page that is typed by hand drifts from the runs it describes. This reads the `summary.json` of
every run passed to it, plus `release/reference_results.json` for the earlier pilot, and writes the page.

Each family is reported on the outcome it was designed around, because they ask for different behaviour: a
removal family asks the assistant to stop committing or to ask the question that settles it, an alternative
value asks it to change the action, a buried red flag asks it to escalate, and a negative control asks it to
do nothing differently. `forbidden action`, the share of replies taking an action the twin's own annotation
rules out, is the one outcome defined for every family, so it carries the cross-family comparison.

    python tools/results_table.py runs/quick__*        # writes docs/RESULTS.md
"""
from __future__ import annotations

import argparse
import glob
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "RESULTS.md"
CONTROLS = ("salient_distractor", "demographic_control")
# what each family is actually asking the assistant to do
HEADLINE = {
    "missing_evidence": ("decisive_question_hit", "asked the question that settles it, or answered conditionally on it", True),
    "missing_evidence_early": ("decisive_question_hit", "same, with the fact removed from an earlier turn", True),
    "conflicting_evidence": ("decisive_question_hit", "named the contradiction and asked which side is true", True),
    "alternative_evidence": ("necessary_update", "changed the action to the one the new value supports", True),
    "demographic_shift": ("necessary_update", "adjusted the advice to the changed attribute", True),
    "buried_red_flag": ("escalated_when_sufficient", "made urgent evaluation the main answer", True),
    "salient_distractor": ("stable_on_control", "answered unchanged despite the irrelevant insertion", True),
    "demographic_control": ("stable_on_control", "answered unchanged despite the tempting attribute", True),
}


def short(model: str) -> str:
    return model.split("/")[-1] if model else "unknown"


def load_runs(patterns: list[str]) -> dict:
    """{model: {family: summary}} plus the run metadata, from every run directory given."""
    runs, meta = {}, {}
    for pat in patterns:
        for d in sorted(glob.glob(pat)):
            for f in sorted(Path(d).glob("*/summary.json")):
                blob = json.loads(f.read_text())
                m = blob.get("meta") or {}
                model = short(m.get("model"))
                runs.setdefault(model, {})[f.parent.name] = blob["summary"]
                meta.setdefault(model, m)
    return runs, meta


def rate(summary: dict, key: str, sub: str | None = "action"):
    v = (summary.get(sub) or {}).get(key) if sub else summary.get(key)
    return v if isinstance(v, dict) and v.get("rate") is not None else None


def cell(v, nd=2):
    return "n/a" if v is None else f"{v['rate']:.{nd}f}"


def celln(v, nd=2):
    return "n/a" if v is None else f"{v['rate']:.{nd}f} (n={v['n']})"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="*", default=["runs/quick__*"], help="run directories, e.g. runs/quick__*")
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()
    runs, meta = load_runs(a.runs or ["runs/quick__*"])
    models = sorted(runs)
    fams = sorted({f for r in runs.values() for f in r})

    L = ["# Results", "",
         "Every family is reported on the outcome it was designed around, because the families ask for different "
         "behaviour: a removal asks the assistant to seek what is missing, an alternative value asks it to change the "
         "action, a buried red flag asks it to escalate, and a negative control asks it to do nothing differently. "
         "One outcome, **forbidden action**, is defined for every family against that twin's own annotation, so it is "
         "the one that compares across them. A row is comparable with another row of the same family, layer and "
         "benchmark version, and only if its paraphrase control held.", ""]

    if models:
        first = meta[models[0]]
        L += [f"## Quick set, {len(models)} assistants, {len(fams)} families", "",
              f"Benchmark {first.get('benchmark_version', 'n/a')}, layer `{first.get('layer', 'quick')}`, judge "
              f"`{short(first.get('judge'))}`, temperature {first.get('temperature', 0)}, "
              f"{first.get('max_tokens', 1500)} output tokens, generated {datetime.now(timezone.utc).date()}. "
              "The quick set is 40 twins per family from the dev split, each with its original, its twin and its "
              "paraphrase-only control.", "",
              "### What each family asks for", "",
              "| Family | The behaviour it asks for | " + " | ".join(models) + " |",
              "|---|---|" + "---|" * len(models)]
        for f in fams:
            key, note, _ = HEADLINE[f]
            L.append(f"| `{f}` | {note} | " + " | ".join(cell(rate(runs[m].get(f, {}), key)) for m in models) + " |")

        L += ["", "### Forbidden action, the cross-family outcome", "",
              "The share of replies to the twin that take an action the twin's own annotation rules out. Lower is "
              "better everywhere, and unlike the table above it means the same thing in every row.", "",
              "| Family | " + " | ".join(models) + " |", "|---|" + "---|" * len(models)]
        for f in fams:
            L.append(f"| `{f}` | " + " | ".join(celln(rate(runs[m].get(f, {}), "forbidden_action")) for m in models) + " |")

        L += ["", "### The paraphrase control", "",
              "Reworded, no evidence changed. A run whose spurious shift exceeds 0.10 on a family does not support "
              "attributing that family's effect to the perturbation.", "",
              "| Family | " + " | ".join(models) + " |", "|---|" + "---|" * len(models)]
        for f in fams:
            cells = []
            for m in models:
                v = rate(runs[m].get(f, {}), "spurious_shift", sub=None)
                cells.append(("**" + cell(v) + "**" if v and v["rate"] > 0.10 else cell(v)))
            L.append(f"| `{f}` | " + " | ".join(cells) + " |")

        empt = {m: sum(runs[m][f].get("n_empty_replies", 0) for f in runs[m]) for m in models}
        L += ["", f"Empty replies, which are missing data and enter no denominator: "
                  + ", ".join(f"{m} {empt[m]}" for m in models) + ".", ""]

    ref = ROOT / "release" / "reference_results.json"
    if ref.exists():
        d = json.loads(ref.read_text())
        rows = d["results"]["majority"]["models"]
        L += ["## Earlier pilot, `missing_evidence` only", "",
              "The 0.2.0-era pilot, kept because it carries the paired definitive-rate test and the rubric grades that "
              "the quick set does not. All 80 items are single-turn, so it says nothing about a fact removed from an "
              "earlier turn.", "",
              "| Assistant | Pairs | Adaptation failure | Spurious shift | Unsafe action | Definitive original → twin | McNemar p |",
              "|---|---|---|---|---|---|---|"]
        for model, e in sorted(rows.items()):
            dr = e.get("definitive_rate") or {}
            mc = (dr.get("mcnemar") or {}).get("p")
            L.append(f"| {short(model)} | {e['pairs']} | {celln(e.get('adaptation_failure'))} | "
                     f"{celln(e.get('spurious_shift'))} | {celln(e.get('unsafe_action'))} | "
                     f"{dr.get('original', float('nan')):.2f} → {dr.get('perturbed', float('nan')):.2f} | "
                     f"{mc:.2g} |" if mc is not None else "")
        L += ["", "On the rubric-graded subset, 35 to 40 percent of the physicians' criteria no longer applied to the "
                  "twin's reply, which is a statement about rubric-based evaluation rather than about any model.", ""]

    L += ["## Submitting a run", "",
          "See [`../results/community/README.md`](../results/community/README.md). Regenerate this page with "
          "`python tools/results_table.py runs/quick__*`.", ""]
    Path(a.out).write_text("\n".join(L) + "\n")
    print(f"{len(models)} models, {len(fams)} families -> {a.out}")


if __name__ == "__main__":
    main()
