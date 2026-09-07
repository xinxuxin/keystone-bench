"""Mechanical quality checks on the built release. No model calls, no keys.

Every flag here is decidable from the text alone, which is the point: the layer definitions lean on
model ratings, so the defect screen underneath them must not.

    C1  multi-turn integrity   only the last user message may differ from the source
    C2  non-empty and changed  the perturbed text exists and differs from the original
    C3  edit size              minimal edits; removal should shorten, insertion should lengthen
    C4  family direction       a negative control must be rated materiality 1
    C5  paraphrase fidelity    same numbers and same negation count as the original
    C6  leakage                no meta-language ("the removed", "as an AI", "rubric", ...)
    C7  cross-family duplicate two families of one source wrote nearly the same text
    C8  paraphrase == perturbed

Writes `dist/quality_report.md` and `dist/quality_flags.jsonl`. Run `tools/build_release.py` first.
Usage: python tools/quality_checks.py
"""
from __future__ import annotations
import json, re, difflib
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

META = re.compile(r"\b(as an AI|note that|the removed|perturbed|rubric|benchmark|hypothetical scenario)\b", re.I)
NUM = re.compile(r"\d+(?:\.\d+)?")
# Negation counting must see contractions, or "no dryness" -> "don't have dryness" reads as drift
NEG = re.compile(r"(\b(?:no|not|never|none|without|denies|negative|nor|lack(?:s|ing)?|absent|free of)\b|n't\b)", re.I)


def norm(s: str) -> str:
    """Normalise curly quotes and dashes: sources use curly, rewrites use straight, and without
    this the negation counts are all false positives."""
    return (s or "").replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"').replace("\u2014", "--").replace("\u2013", "-")


def ratio(a: str, b: str) -> float:
    return 1 - difflib.SequenceMatcher(None, a, b).ratio()


def main():
    src = {r["prompt_id"]: r for r in (json.loads(l) for l in (ROOT / ".cache/healthbench_oss.jsonl").read_text().splitlines() if l.strip())}
    twins = [json.loads(l) for l in (ROOT / "dist/keystone_twins.jsonl").read_text().splitlines() if l.strip()]
    flags, stats = [], defaultdict(list)
    by_src = defaultdict(list)
    for t in twins:
        by_src[t["prompt_id"]].append(t)
    near_dup = set()  # two families of one source produced nearly identical twins
    for pid, ts in by_src.items():
        # alternative_evidence is by design a near-duplicate of the missing-evidence twin (one slot differs); skip it here
        ts = [t for t in ts if t["family"] != "alternative_evidence"]
        for i in range(len(ts)):
            for j in range(i + 1, len(ts)):
                a, b = norm(ts[i]["perturbed_prompt"]).strip(), norm(ts[j]["perturbed_prompt"]).strip()
                if a and b and ratio(a, b) < 0.02:
                    near_dup.add((pid, ts[i]["family"])); near_dup.add((pid, ts[j]["family"]))
    for t in twins:
        f = []
        s = src.get(t["prompt_id"])
        if s:
            last = s["prompt"][-1]["content"]
            if t["original_prompt"].strip() != last.strip():
                f.append("C1_original_not_last_user_turn")
        op, pp = norm(t["original_prompt"]).strip(), norm(t["perturbed_prompt"]).strip()
        if not pp:
            f.append("C2_empty")
        elif pp == op:
            f.append("C2_identical")
        d = ratio(op, pp) if op and pp else 1.0
        stats[t["family"]].append((d, len(pp) - len(op)))
        # One added sentence blows past a relative threshold on a short source, so gate on
        # absolute characters changed as well as relative distance.
        changed = abs(len(pp) - len(op)) + sum(1 for x in difflib.ndiff(op, pp) if x[0] == "-")
        if d > 0.60 and changed > 220:
            f.append("C3_edit_too_large")
        # missing_evidence may neutralise (replace a specific term with a vaguer one), so only
        # flag it when the text grew appreciably.
        if t["family"] == "missing_evidence" and len(pp) - len(op) > 40:
            f.append("C3_missing_grew_a_lot")
        if t["family"] in ("conflicting_evidence", "salient_distractor") and len(pp) < len(op):
            f.append("C3_added_but_shorter")
        if t["family"] == "salient_distractor" and (t.get("materiality") or 0) != 1:
            f.append("C4_distractor_not_materiality1")
        if META.search(pp):
            f.append("C6_meta_language")
        if (t["prompt_id"], t["family"]) in near_dup:
            f.append("C7_near_duplicate_across_families")
        para_raw = norm(t.get("paraphrase_prompt")).strip()
        if para_raw and para_raw == pp:
            f.append("C8_paraphrase_equals_perturbed")
        para = norm(t.get("paraphrase_prompt")).strip()
        if para:
            if Counter(NUM.findall(para)) != Counter(NUM.findall(op)):
                f.append("C5_paraphrase_numbers_changed")
            if len(NEG.findall(para)) != len(NEG.findall(op)):
                f.append("C5R_paraphrase_negation_count_differs")  # R = review, not a defect: English negates many ways
        if f:
            flags.append({"prompt_id": t["prompt_id"], "family": t["family"], "flags": f})
    (ROOT / "dist/quality_flags.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in flags))
    cnt = Counter(x for r in flags for x in r["flags"])
    defects = [r for r in flags if any(not x.startswith("C5R") for x in r["flags"])]
    lines = ["# Mechanical quality checks", "",
             f"{len(twins)} twins. **{len(defects)} carry a defect ({len(defects)/len(twins):.1%})**; "
             f"flags suffixed `R` are screens for review, not defects. Definitions in "
             f"`tools/quality_checks.py`.", "",
             "| flag | twins | meaning |", "|---|---|---|"]
    desc = {"C1_original_not_last_user_turn": "recorded original differs from the source's last user message",
            "C3_missing_grew_a_lot": "removal family grew by more than 40 characters (neutralising is fine, growing is not)",
            "C2_empty": "perturbed text is empty", "C2_identical": "perturbed text equals the original",
            "C3_edit_too_large": "relative edit distance > 0.60 and > 220 characters changed (edits should be minimal)",
            "C3_added_but_shorter": "insertion family, yet the text got shorter",
            "C4_distractor_not_materiality1": "negative control not rated materiality 1",
            "C5_paraphrase_numbers_changed": "paraphrase changed a number (defect)",
            "C5R_paraphrase_negation_count_differs": "paraphrase has a different negation count (**screen, not a defect**: English negates many ways; sent to a model for review)",
            "C6_meta_language": "perturbed text contains meta-language, leaking the construction",
            "C7_near_duplicate_across_families": "two families of one source wrote nearly the same twin (relative distance < 0.02)",
            "C8_paraphrase_equals_perturbed": "paraphrase control equals the perturbed version"}
    for k, v in cnt.most_common():
        lines.append(f"| `{k}` | {v} | {desc.get(k, '')} |")
    lines += ["", "## Edit size by family", "",
              "| family | median relative edit distance | median length change (chars) |", "|---|---|---|"]
    import statistics
    for fam in sorted(stats):
        ds = [x[0] for x in stats[fam]]; ls = [x[1] for x in stats[fam]]
        lines.append(f"| {fam} | {statistics.median(ds):.3f} | {statistics.median(ls):+.0f} |")
    (ROOT / "dist/quality_report.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
