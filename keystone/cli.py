"""Command line: keystone build | run | show | report | panel | regress | compare-judges | validate | reference | pairs | estimate."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import textwrap
from collections import Counter
from pathlib import Path

from . import __version__
from .data import FAMILIES, LAYERS, SPLITS, find_dist, load_manifest, load_pairs, load_rows
from .metrics import cohen_kappa, pair_action_outcomes, pair_outcomes, panel_records, primary_hypothesis_supported, summarize
from .runner import OpenAICompatible, evaluate, report_markdown, write_run


def cmd_build(a):
    from .build import main as build_main
    argv = []
    for flag, value in (("--dist", a.out or a.dist), ("--cache", a.cache), ("--release", a.release)):
        if value:
            argv += [flag, str(value)]
    if a.check:
        argv.append("--check")
    raise SystemExit(build_main(argv))


def cmd_pairs(a):
    for fam in ([a.family] if a.family else FAMILIES):
        allp = load_pairs(fam, "all", a.dist)
        if not allp:
            print(f"{fam:22s} not in this release"); continue
        strict, core, quick, prim = load_pairs(fam, "strict", a.dist), load_pairs(fam, "core", a.dist), load_pairs(fam, "quick", a.dist), load_pairs(fam, "primary", a.dist)
        with_para = sum(1 for p in allp if p.paraphrase is not None)
        with_state = sum(1 for p in allp if p.has_state)
        test = sum(1 for p in allp if p.split == "test")
        print(f"{fam:22s} primary {len(prim):4d}  strict {len(strict):4d}  core {len(core):4d}  all {len(allp):4d}  quick {len(quick):3d}  with control {with_para:4d}  "
              f"multi-turn {sum(1 for p in allp if p.turns > 1):4d}  with evidence state {with_state:4d}  test split {test:4d}")


def cmd_validate(a):
    """Recompute MANIFEST.json hashes and row counts, and check the structural invariants the data card states."""
    d = find_dist(a.dist); m = load_manifest(d); bad = 0
    for rel, info in m["files"].items():
        p = d / rel
        if not p.exists():
            print("MISSING", rel); bad += 1; continue
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        n = sum(1 for l in p.read_text().splitlines() if l.strip())
        if h != info["sha256"] or n != info["rows"]:
            print("CHANGED", rel, "sha" if h != info["sha256"] else "", "rows" if n != info["rows"] else ""); bad += 1
    for fam in FAMILIES:
        for p in load_pairs(fam, "all", d):
            if p.original[-1]["role"] != "user" or p.perturbed[-1]["role"] != "user":
                print("BAD last role", p.id); bad += 1
            k = p.edited_turn if 0 <= p.edited_turn < len(p.original) else len(p.original) - 1
            if [x["content"] for i, x in enumerate(p.original) if i != k] != [x["content"] for i, x in enumerate(p.perturbed) if i != k]:
                print("OTHER TURNS differ", p.id); bad += 1
            if p.perturbed[k]["content"] == p.original[k]["content"]:
                print("UNCHANGED twin", p.id); bad += 1
            if p.in_core and p.family not in ("salient_distractor", "demographic_control") and p.materiality_majority != 3:
                print("CORE without materiality 3", p.id); bad += 1
            if p.in_strict and not p.in_core:
                print("STRICT outside core", p.id); bad += 1
    # the reference records must reproduce the headline numbers of the reference results
    rr, rs = d / "reference_records.jsonl", d / "reference_results.json"
    if rr.exists() and rs.exists():
        recs = [r for r in load_rows(rr) if r["family"] != "reference"]
        ref = json.loads(rs.read_text())["results"]["majority"]["models"]
        for model, e in ref.items():
            short = model.split(":", 1)[-1]
            s = summarize([r for r in recs if r["model"] == short and r.get("materiality_majority") == 3])
            if (s["adaptation_failure"]["k"], s["adaptation_failure"]["n"]) != (e["adaptation_failure"]["k"], e["adaptation_failure"]["n"]):
                print("REFERENCE mismatch", short, s["adaptation_failure"], e["adaptation_failure"]); bad += 1
    print(f"{'OK' if not bad else 'FAIL'}: {d} version {m['version']}, {m['counts']['twins']} twins, {m['counts']['core']} core, "
          f"{m['counts'].get('strict', 'n/a')} strict, {len(m['files'])} files checked, {bad} problems")
    sys.exit(1 if bad else 0)


def cmd_reference(a):
    d = find_dist(a.dist); j = json.loads((d / "reference_results.json").read_text())
    rule = a.rule; res = j["results"][rule]
    print(f"Reference results ({rule}: {j['materiality_rules'][rule]}), {res['n_twins_selected']} twins selected")
    print(f"{'model':40s} {'pairs':>5} {'adapt.fail':>22} {'spurious':>22} {'unsafe':>7} {'def orig->pert':>15} {'McNemar p':>10}")
    for m, e in res["models"].items():
        af, sp, ua, dr = e["adaptation_failure"], e["spurious_shift"], e["unsafe_action"], e["definitive_rate"]
        print(f"{m:40s} {e['pairs']:>5} {af['rate']:.2f} [{af['wilson95'][0]:.2f}, {af['wilson95'][1]:.2f}]   {sp['rate']:.2f} [{sp['wilson95'][0]:.2f}, {sp['wilson95'][1]:.2f}]   {ua['rate']:>5.2f}   {dr['original']:.2f} -> {dr['perturbed']:.2f}   {dr['mcnemar']['p']:>9.2g}")


def _wrap(text: str, indent: str = "    ") -> str:
    return textwrap.fill(text or "", width=100, initial_indent=indent, subsequent_indent=indent)


def cmd_show(a):
    """Print one pair (or every pair whose id starts with the given prefix): the original and perturbed
    last message, what changed, the expected safe behaviour, the rubric criteria the change touches,
    and, when reference records exist for it, what each reference model did."""
    d = find_dist(a.dist)
    fams = [a.family] if a.family else FAMILIES
    hits = [p for fam in fams for p in load_pairs(fam, "all", d) if p.id.startswith(a.id) or p.source_id.startswith(a.id)]
    if not hits:
        print(f"no pair with id prefix {a.id!r}"); sys.exit(1)
    recs = {}
    rp = d / "reference_records.jsonl"
    if rp.exists():
        for r in load_rows(rp):
            recs.setdefault(r["id"], []).append(r)
    for p in hits[: a.max]:
        print(f"\n=== {p.id}  family={p.family}  layer={'primary' if p.in_primary else 'strict' if p.in_strict else 'core' if p.in_core else 'extended'}  materiality={p.materiality_majority}  turns={p.turns}  group={p.group}")
        if p.turns > 1 and a.context:
            for m in p.original[:-1]:
                print(f"  [{m['role']}]"); print(_wrap(m["content"]))
        print("  ORIGINAL last user message:"); print(_wrap(p.last_user_message))
        print("  PERTURBED:"); print(_wrap(p.perturbed_message))
        if p.paraphrase is not None:
            print("  PARAPHRASE CONTROL:"); print(_wrap(p.paraphrase[-1]["content"]))
        print("  what changed:      ", p.removed_or_changed)
        print("  expected behaviour:", p.expected_safe_behavior)
        if p.frame:
            print("  decision target:   ", p.frame.get("decision_target"))
            print("  supported action:  ", p.frame.get("supported_action"))
        if p.has_state:
            print(f"  evidence state:     {p.evidence_state}{'  (urgent escalation already warranted)' if p.escalation_sufficient else ''}")
            for x in (p.acceptable_actions or [])[:4]:
                print(f"    acceptable: {x[:120]}")
            for x in (p.forbidden_actions or [])[:3]:
                print(f"    forbidden:  {(x.get('action') if isinstance(x, dict) else x)[:120]}")
            for x in (p.decisive_questions or [])[:3]:
                print(f"    decisive question: {x[:120]}")
        if p.split or p.tier:
            print(f"  split={p.split}  tier={p.tier}{'  quick' if p.in_quick else ''}")
        if p.rubric_dependent_criteria is not None:
            print(f"  rubric criteria that depend on the change: {p.rubric_dependent_criteria} of {len(p.rubrics)}")
            for i in p.rubric_dependent_criteria[:6]:
                print(f"    [{i}] ({p.rubrics[i]['points']:+d}) {p.rubrics[i]['criterion'][:110]}")
        for r in recs.get(p.id, []):
            b = r["behavior"]
            line = ", ".join(f"{c}={(b.get(c) or {}).get('stance')}" for c in ("original", "perturbed", "paraphrase") if c in b)
            flags = [k for k in ("names_missing_element", "assumes_missing_element", "unsafe_action") if (b.get("perturbed") or {}).get(k)]
            print(f"  reference {r['model']:28s} {line}{'  perturbed: ' + ', '.join(flags) if flags else ''}")
            if a.replies:
                print(_wrap("perturbed reply: " + (r["replies"].get("perturbed") or "")[: a.chars], indent="      "))
    if len(hits) > a.max:
        print(f"\n... {len(hits) - a.max} more; raise --max")


def cmd_report(a):
    """Recompute summary.json and REPORT.md from a run's records.jsonl (for example after editing or merging records)."""
    d = Path(a.run_dir); records = load_rows(d / "records.jsonl")
    meta = {}
    if (d / "summary.json").exists():
        meta = json.loads((d / "summary.json").read_text()).get("meta", {})
    s = write_run(d, records, meta)
    print(report_markdown(s, meta.get("title", d.name)))
    print("primary hypothesis supported:", primary_hypothesis_supported(s))


def cmd_panel(a):
    """Combine runs of the same pairs judged by different judges into a majority panel, and print the panel next to
    each judge's own values. Absolute levels move a lot with the judge; the panel is the comparable number."""
    runs, names = [], []
    for d in a.runs:
        p = Path(d)
        rs = load_rows(p / "records.jsonl") if p.is_dir() and (p / "records.jsonl").exists() else \
             [r for f in sorted(p.glob("*/records.jsonl")) for r in load_rows(f)] if p.is_dir() else load_rows(p)
        if not rs:
            print(f"no records in {d}", file=sys.stderr); sys.exit(1)
        runs.append(rs); names.append(p.name)
    pan = panel_records(runs)
    keys = ("forbidden_action", "acceptable_action", "decisive_question_hit", "effective_completion",
            "necessary_update", "escalated_when_sufficient", "stable_on_control", "hedged_when_sufficient")
    def row(label, recs):
        s = summarize(recs).get("action", {})
        cells = []
        for k in keys:
            v = s.get(k) or {}
            cells.append(f"{v['rate']:.2f}" if v.get("rate") is not None else " n/a")
        return f"{label:28s} {len(recs):5d}  " + "  ".join(f"{c:>5}" for c in cells)
    print(f"{'judge':28s} {'n':>5}  " + "  ".join(f"{k.split('_')[0][:5]:>5}" for k in keys))
    for n, r in zip(names, runs):
        print(row(n[:28], r))
    print(row("PANEL (majority)", pan))
    print("\ncolumns:", ", ".join(keys))
    if a.out:
        write_run(a.out, pan, {"title": "Keystone panel", "judges": names, "note": "per-flag majority of the judges"})
        print("->", a.out)


def cmd_regress(a):
    """Version regression: two runs of the same pairs (for example two versions of one system, same judge).
    Prints, per outcome, how many items were fixed (bad in A, good in B), regressed (good in A, bad in B)
    and unchanged, with the ids, so a product team can see what a new version changed rather than one score."""
    A = {r["id"]: r for r in load_rows(Path(a.run_a) / "records.jsonl" if Path(a.run_a).is_dir() else Path(a.run_a))}
    B = {r["id"]: r for r in load_rows(Path(a.run_b) / "records.jsonl" if Path(a.run_b).is_dir() else Path(a.run_b))}
    ids = sorted(set(A) & set(B))
    if not ids:
        print("no shared pair ids"); sys.exit(1)
    print(f"{len(ids)} shared pairs  (A = {a.run_a}, B = {a.run_b})")
    def bad_flags(r):
        o = pair_outcomes(r.get("behavior", {}), r.get("family"))
        flags = {"unsupported_action": o.get("unsupported_action"), "adaptation_failure": o.get("adaptation_failure"),
                 "control_drift": o.get("control_drift"), "spurious_shift": o.get("spurious_shift"),
                 "unnecessary_refusal": ((r.get("behavior", {}).get("original") or {}).get("stance") == "abstain_refer") if r.get("behavior", {}).get("original") else None}
        if r.get("action"):
            ao = pair_action_outcomes(r["action"], r.get("family"), r.get("evidence_state"), r.get("escalation_sufficient"))
            flags["forbidden_action"] = ao.get("forbidden_action")
            flags["missed_update"] = (not ao["necessary_update"]) if ao.get("necessary_update") is not None else None
            flags["missed_decisive_question"] = (not ao["decisive_question_hit"]) if ao.get("decisive_question_hit") is not None else None
            flags["failed_completion"] = (not ao["effective_completion"]) if ao.get("effective_completion") is not None else None
        return flags
    fa, fb = {i: bad_flags(A[i]) for i in ids}, {i: bad_flags(B[i]) for i in ids}
    keys = [k for k in ("forbidden_action", "unsupported_action", "adaptation_failure", "missed_update", "missed_decisive_question",
                        "failed_completion", "unnecessary_refusal", "control_drift", "spurious_shift")
            if any(fa[i].get(k) is not None for i in ids)]
    print(f"{'outcome (bad = true)':28s} {'A bad':>6} {'B bad':>6} {'fixed':>6} {'regressed':>9} {'McNemar p':>10}")
    detail = {}
    for k in keys:
        both = [i for i in ids if fa[i].get(k) is not None and fb[i].get(k) is not None]
        fixed = [i for i in both if fa[i][k] and not fb[i][k]]; regr = [i for i in both if not fa[i][k] and fb[i][k]]
        from .metrics import mcnemar_exact
        print(f"{k:28s} {sum(1 for i in both if fa[i][k]):>6} {sum(1 for i in both if fb[i][k]):>6} {len(fixed):>6} {len(regr):>9} {mcnemar_exact(len(fixed), len(regr)):>10.3g}")
        detail[k] = (fixed, regr)
    for k, (fixed, regr) in detail.items():
        if regr:
            print(f"\nregressed on {k} ({len(regr)}):")
            for i in regr[: a.max]:
                sb = (B[i].get("behavior", {}).get("perturbed") or {}).get("stance")
                act = (B[i].get("action", {}).get("perturbed") or {}).get("action_taken") or ""
                print(f"  {i}  B: stance={sb}  {act[:110]}")
        if fixed and a.show_fixed:
            print(f"\nfixed on {k} ({len(fixed)}):")
            for i in fixed[: a.max]:
                print(f"  {i}")


def cmd_compare_judges(a):
    """Agreement between two judges on the same replies: two records.jsonl files from runs of the same model
    with different --judge. Reports Cohen's kappa on stance per condition and on the binary flags."""
    A = {r["id"]: r for r in load_rows(Path(a.records_a))}; B = {r["id"]: r for r in load_rows(Path(a.records_b))}
    ids = sorted(set(A) & set(B))
    if not ids:
        print("no shared pair ids"); sys.exit(1)
    print(f"{len(ids)} shared pairs")
    for cond in ("original", "perturbed", "paraphrase"):
        x = [(A[i]["behavior"].get(cond) or {}).get("stance") for i in ids]; y = [(B[i]["behavior"].get(cond) or {}).get("stance") for i in ids]
        k, po = cohen_kappa(x, y)
        print(f"  stance/{cond:10s} kappa {k:.2f}  agreement {po:.2f}")
    for flag in ("names_missing_element", "assumes_missing_element", "unsafe_action", "asks_any_question"):
        x = [bool((A[i]["behavior"].get("perturbed") or {}).get(flag)) if A[i]["behavior"].get("perturbed") else None for i in ids]
        y = [bool((B[i]["behavior"].get("perturbed") or {}).get(flag)) if B[i]["behavior"].get("perturbed") else None for i in ids]
        k, po = cohen_kappa(x, y)
        print(f"  perturbed/{flag:24s} kappa {k:.2f}  agreement {po:.2f}")
    if any(A[i].get("action") for i in ids):
        for flag in ("acceptable", "forbidden", "asks_decisive_question", "conditional", "escalates"):
            x = [(bool((A[i].get("action", {}).get("perturbed") or {}).get(flag)) if A[i].get("action", {}).get("perturbed") else None) for i in ids]
            y = [(bool((B[i].get("action", {}).get("perturbed") or {}).get(flag)) if B[i].get("action", {}).get("perturbed") else None) for i in ids]
            k, po = cohen_kappa(x, y)
            print(f"  action/{flag:24s} kappa {k:.2f}  agreement {po:.2f}")
    sa, sb = summarize([A[i] for i in ids]), summarize([B[i] for i in ids])
    print(f"  adaptation failure under judge A {sa['adaptation_failure']['rate']}, under judge B {sb['adaptation_failure']['rate']}")
    if sa.get("action") and sb.get("action"):
        for k in ("forbidden_action", "decisive_question_hit", "effective_completion", "necessary_update", "stable_on_control"):
            ra, rb = (sa["action"].get(k) or {}).get("rate"), (sb["action"].get(k) or {}).get("rate")
            if ra is not None and rb is not None:
                print(f"  {k:26s} judge A {ra:.2f}  judge B {rb:.2f}")


def cmd_estimate(a):
    """Rough call and token counts for a run, from character counts (about 3.6 characters per token)."""
    fams = FAMILIES if a.family == "all" else (a.family,)
    for fam in fams:
        pairs = load_pairs(fam, a.layer, a.dist, limit=a.limit, split=a.split)
        if not pairs:
            print(f"{fam} / {a.layer}: not in this release"); continue
        chars_in = sum(len(m["content"]) for p in pairs for c in ("original", "perturbed", "paraphrase") if not (c == "paraphrase" and p.paraphrase is None) for m in p.conversation(c))
        n_replies = sum(3 if p.paraphrase is not None else 2 for p in pairs)
        n_rubric = sum(len(p.rubrics) for p in pairs)
        print(f"{fam} / {a.layer}: {len(pairs)} pairs")
        print(f"  model under test: {n_replies} replies, about {chars_in / 3.6 / 1000:.0f}k input tokens plus up to {n_replies * a.max_tokens / 1000:.0f}k output tokens")
        n_action = sum(1 for p in pairs for c in ("original", "perturbed", "paraphrase") if not (c == "paraphrase" and p.paraphrase is None) and (p.has_state if c == "perturbed" else bool((p.frame or {}).get("acceptable_actions"))))
        print(f"  judge, behaviour only: {n_replies} calls; action judge: + {n_action} calls")
        if a.rubric:
            print(f"  judge, with rubric: + {2 * n_rubric} grader calls + {n_rubric} applicability calls (each re-sends the conversation)")


def cmd_run(a):
    respond = OpenAICompatible(a.model, base_url=a.base_url, max_tokens=a.max_tokens, cache_dir=a.cache)
    judge = OpenAICompatible(a.judge, base_url=a.judge_base_url, max_tokens=600, cache_dir=a.cache)
    if respond.model_id.split("/")[0] == judge.model_id.split("/")[0]:
        print("warning: judge and model under test share a vendor prefix; the protocol asks for different families", file=sys.stderr)
    fams = FAMILIES if a.family == "all" else (a.family,)
    for fam in fams:
        pairs = load_pairs(fam, a.layer, a.dist, limit=a.limit, require_paraphrase=a.require_paraphrase, split=a.split)
        if not pairs:
            print(f"{fam}: no pairs for layer={a.layer} split={a.split}; skipping"); continue
        out = Path(a.out) / fam if (a.out and a.family == "all") else Path(a.out or f"runs/{fam}__{a.layer}__{a.model.replace('/', '_')}")
        out.mkdir(parents=True, exist_ok=True)
        stream = (out / "records.jsonl").open("w")
        def on_record(r):
            stream.write(json.dumps(r, ensure_ascii=False) + "\n"); stream.flush()
            if a.verbose:
                print(r["id"][:8], {c: (b or {}).get("stance") for c, b in r["behavior"].items()})
        records = evaluate(pairs, respond, judge, rubric=a.rubric, workers=a.workers, on_record=on_record, action=not a.no_action)
        stream.close()
        meta = {"title": f"Keystone {fam} ({a.layer}, {a.split}) — {a.model}", "benchmark_version": load_manifest(a.dist)["version"], "family": fam, "layer": a.layer, "split": a.split,
                "model": a.model, "judge": a.judge, "temperature": 0.0, "max_tokens": a.max_tokens, "rubric": a.rubric,
                "usage": {"model": dict(respond.usage), "judge": dict(judge.usage)}}
        summary = write_run(out, records, meta)
        print((out / "REPORT.md").read_text())
        print("primary hypothesis supported:", primary_hypothesis_supported(summary))
        print("->", out)
    print(f"usage: model {respond.usage}; judge {judge.usage}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="keystone", description=f"Keystone {__version__}: paired evidence-perturbation stress tests")
    ap.add_argument("--dist", default=None, help="release directory (default: $KEYSTONE_DIST or the repository's dist/)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("build", help="rebuild the release from HealthBench and the shipped edits (needed once after pip install)")
    s.add_argument("--out", help="where to write it (default: ./dist in a checkout, ~/.cache/keystone/dist otherwise)")
    s.add_argument("--cache", help="path of the HealthBench copy to use or download")
    s.add_argument("--release", help="directory holding metadata.jsonl and edits.jsonl")
    s.add_argument("--check", action="store_true", help="verify an existing release against its MANIFEST"); s.set_defaults(f=cmd_build)
    s = sub.add_parser("pairs", help="count pairs per family and layer"); s.add_argument("--family", choices=FAMILIES); s.set_defaults(f=cmd_pairs)
    s = sub.add_parser("validate", help="check the release against its MANIFEST and structural invariants"); s.set_defaults(f=cmd_validate)
    s = sub.add_parser("reference", help="print the reference results shipped with the release"); s.add_argument("--rule", default="majority", choices=["majority", "both", "author"]); s.set_defaults(f=cmd_reference)
    s = sub.add_parser("show", help="print a pair and what the reference models did on it")
    s.add_argument("id", help="pair id or a prefix of the source id"); s.add_argument("--family", choices=FAMILIES); s.add_argument("--max", type=int, default=4)
    s.add_argument("--context", action="store_true", help="also print earlier turns of multi-turn items"); s.add_argument("--replies", action="store_true", help="print the reference models' perturbed replies")
    s.add_argument("--chars", type=int, default=600); s.set_defaults(f=cmd_show)
    s = sub.add_parser("report", help="recompute summary.json and REPORT.md from a run directory"); s.add_argument("run_dir"); s.set_defaults(f=cmd_report)
    s = sub.add_parser("panel", help="majority panel over runs of the same pairs judged by different judges")
    s.add_argument("runs", nargs="+", help="run directories (or records.jsonl files) of the same model under different judges")
    s.add_argument("--out", help="write the panel records as a run directory"); s.set_defaults(f=cmd_panel)
    s = sub.add_parser("regress", help="what a new version fixed and regressed, item by item, between two runs of the same pairs")
    s.add_argument("run_a"); s.add_argument("run_b"); s.add_argument("--max", type=int, default=15); s.add_argument("--show-fixed", action="store_true"); s.set_defaults(f=cmd_regress)
    s = sub.add_parser("compare-judges", help="agreement between two judges on the same model's replies"); s.add_argument("records_a"); s.add_argument("records_b"); s.set_defaults(f=cmd_compare_judges)
    s = sub.add_parser("estimate", help="calls and tokens a run would take"); s.add_argument("--family", default="missing_evidence", choices=FAMILIES + ("all",)); s.add_argument("--layer", default="core", choices=LAYERS); s.add_argument("--split", default="all", choices=SPLITS)
    s.add_argument("--limit", type=int); s.add_argument("--rubric", action="store_true"); s.add_argument("--max-tokens", type=int, default=1500); s.set_defaults(f=cmd_estimate)
    s = sub.add_parser("run", help="evaluate a model with a judge")
    s.add_argument("--family", default="missing_evidence", choices=FAMILIES + ("all",)); s.add_argument("--layer", default="core", choices=LAYERS)
    s.add_argument("--model", required=True, help="e.g. openrouter/openai/gpt-5.6-terra, openai/gpt-4.1, ollama/llama3.1:8b, or a bare id with --base-url")
    s.add_argument("--judge", required=True, help="e.g. openrouter/openai/gpt-4.1; use a different vendor than --model")
    s.add_argument("--base-url"); s.add_argument("--judge-base-url"); s.add_argument("--limit", type=int); s.add_argument("--rubric", action="store_true", help="also grade with the HealthBench rubric and the applicability judge")
    s.add_argument("--require-paraphrase", action="store_true", help="only pairs that have a released paraphrase control")
    s.add_argument("--split", default="all", choices=SPLITS, help="dev or test split by source (default all)")
    s.add_argument("--no-action", action="store_true", help="skip the action judge (decision-evidence outcomes)")
    s.add_argument("--workers", type=int, default=8); s.add_argument("--max-tokens", type=int, default=1500); s.add_argument("--cache"); s.add_argument("--out"); s.add_argument("--verbose", action="store_true")
    s.set_defaults(f=cmd_run)
    a = ap.parse_args(argv); a.f(a)


if __name__ == "__main__":
    main()
