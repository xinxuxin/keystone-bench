"""Does the decision frame agree with what a physician actually wrote?

The frame is the load-bearing annotation: it names the action the stated evidence supports and the actions it
forbids, and every primary outcome is scored against it. Both the frame and its review are model-written, so
the layer that carries the results has no human in it.

HealthBench ships a physician-written ideal completion for most of its conversations, produced for the
*unedited* message and never seen by any Keystone annotator. Judging that answer against this source's own
frame, by exactly the rules a model reply is judged by, asks whether the frame recognises a physician's answer
as an acceptable course of action. It is not a counterfactual claim about the edited message, which a physician
answer cannot support; it tests the frame on the case the physician actually saw.

Two numbers come out. **Acceptance** is the share of physician answers the frame marks acceptable, which should
be high because the sources were selected as cases a definitive reply serves. **Contradiction** is the share
the frame marks as taking a forbidden action, which is the sharper failure: the frame forbids what a physician
did. The evaluated systems' rate on the same conversations is printed beside both, because a frame that
accepts models and rejects physicians is a different defect from one that is simply strict.

Usage: OPENROUTER_API_KEY=... python tools/frame_vs_physician.py --out docs/FRAME_VS_PHYSICIAN.md
"""
from __future__ import annotations
import argparse, json, random, sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from keystone.data import load_pairs, FAMILIES, find_dist      # noqa: E402
from keystone.prompts import action_prompt                      # noqa: E402
from keystone.runner import OpenAICompatible, action_spec, judge_json  # noqa: E402


def boot(vals, conf=0.95, seed=0, n=4000):
    if not vals:
        return float("nan"), float("nan"), float("nan")
    rng = random.Random(seed)
    k = len(vals)
    d = sorted(sum(vals[rng.randrange(k)] for _ in range(k)) / k for _ in range(n))
    return sum(vals) / k, d[int((1 - conf) / 2 * n)], d[int((1 + conf) / 2 * n) - 1]


def ideal_answers(cache: Path | None):
    """{prompt_id: physician ideal completion} from the HealthBench copy the release was built from."""
    out = {}
    roots = [cache] if cache else [ROOT / ".cache", Path.home() / ".cache" / "keystone"]
    for root in roots:
        if not root or not root.exists():
            continue
        for f in sorted(list(root.rglob("*oss_eval.jsonl")) + list(root.rglob("healthbench_oss*.jsonl"))):
            for line in f.read_text().splitlines():
                if not line.strip():
                    continue
                r = json.loads(line)
                d = r.get("ideal_completions_data") or {}
                t = d.get("ideal_completion") if isinstance(d, dict) else None
                if isinstance(t, str) and t.strip():
                    out.setdefault(r["prompt_id"], t)
        if out:
            break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge", default="openrouter/openai/gpt-4.1")
    ap.add_argument("--layer", default="core")
    ap.add_argument("--split", default="test")
    ap.add_argument("--cache", help="HealthBench copy to read ideal completions from")
    ap.add_argument("--runs", default="runs")
    ap.add_argument("--prefix", default="testcore")
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args()

    ideal = ideal_answers(Path(a.cache) if a.cache else None)
    if not ideal:
        print("no ideal completions found; point --cache at the HealthBench copy used by `keystone build`")
        return

    # one frame per source: take it from any family, since the frame belongs to the unedited conversation
    seen, jobs = {}, []
    for fam in FAMILIES:
        for p in load_pairs(fam, layer=a.layer, split=a.split):
            if p.source_id in seen:
                continue
            spec = action_spec(p, "original")
            txt = ideal.get(p.source_id)
            if spec is None or not txt:
                continue
            seen[p.source_id] = True
            jobs.append((p.source_id, p, txt, spec))
    print(f"{len(jobs)} sources with both a decision frame and a physician answer")
    if a.dry_run:
        return

    judge = OpenAICompatible(a.judge, max_tokens=600)
    out_f = Path(a.runs) / "frame_vs_physician" / "verdicts.jsonl"
    out_f.parent.mkdir(parents=True, exist_ok=True)
    done = {}
    if out_f.exists():
        for line in out_f.read_text().splitlines():
            if line.strip():
                d = json.loads(line)
                done[d["source_id"]] = d["verdict"]
    todo = [j for j in jobs if j[0] not in done]
    print(f"{len(done)} on disk, {len(todo)} to judge")

    def run(job):
        sid, p, txt, spec = job
        v = judge_json(judge, action_prompt(p.conversation("original"), txt, spec))
        return {"source_id": sid, "family_seen_in": p.family, "verdict": v}

    if todo:
        with out_f.open("a") as fh, ThreadPoolExecutor(max_workers=a.workers) as ex:
            for i, d in enumerate(ex.map(run, todo), 1):
                fh.write(json.dumps(d, ensure_ascii=False) + "\n")
                fh.flush()
                done[d["source_id"]] = d["verdict"]
                if i % 100 == 0:
                    print(f"  {i}/{len(todo)}  judge cost ${judge.usage['cost_usd']:.2f}", flush=True)
        print(f"judge usage: {judge.usage}")

    acc = [1.0 if (done[s].get("acceptable")) else 0.0 for s in done]
    con = [1.0 if done[s].get("forbidden") else 0.0 for s in done]
    neither = [1.0 if (not done[s].get("acceptable") and not done[s].get("forbidden")) else 0.0 for s in done]
    ma, la, ha = boot(acc, seed=1)
    mc, lc, hc = boot(con, seed=2)
    mn, ln, hn = boot(neither, seed=3)

    # the evaluated systems on the same conversations, for scale
    sys_rows = []
    for d in sorted(Path(a.runs).glob(f"{a.prefix}__*")):
        m = d.name.split("__", 1)[1]
        sa, sc = [], []
        got = set()
        for f in sorted(d.glob("*/records.jsonl")):
            for line in f.read_text().splitlines():
                if not line.strip():
                    continue
                r = json.loads(line)
                sid = r.get("source_id") or r["id"]
                if sid in got or sid not in done:
                    continue
                act = (r.get("action") or {}).get("original")
                if not act:
                    continue
                got.add(sid)
                sa.append(1.0 if act.get("acceptable") else 0.0)
                sc.append(1.0 if act.get("forbidden") else 0.0)
        if sa:
            sys_rows.append((m, len(sa), sum(sa) / len(sa), sum(sc) / len(sc)))

    L = ["# The decision frame against a physician's own answer", "",
         f"Layer `{a.layer}`, `{a.split}` split, judge `{a.judge}`, {len(done)} sources. HealthBench ships a "
         "physician-written ideal completion for the unedited conversation. No Keystone annotator saw it, so "
         "judging it against this source's own decision frame, by the rules a model reply is judged by, tests "
         "the frame rather than the model. This says nothing about the edited message: a physician answer "
         "written before the edit cannot settle what the edit makes acceptable.", "",
         "| | share | 95% interval |", "|---|---|---|",
         f"| physician answer marked **acceptable** | {ma:.3f} | [{la:.3f}, {ha:.3f}] |",
         f"| physician answer marked **forbidden** | {mc:.3f} | [{lc:.3f}, {hc:.3f}] |",
         f"| neither, on the frame's lists | {mn:.3f} | [{ln:.3f}, {hn:.3f}] |", ""]
    if sys_rows:
        L += ["The evaluated systems on the same conversations and the same frames, for scale.", "",
              "| system | sources | acceptable | forbidden |", "|---|---|---|---|"]
        for m, n, sa, sc in sys_rows:
            L.append(f"| `{m}` | {n} | {sa:.3f} | {sc:.3f} |")
        L.append("")

    L += ["## Reading", ""]
    if sys_rows:
        worse = [r for r in sys_rows if r[3] < mc]
        best = max(sys_rows, key=lambda r: r[2])
        L += [f"The frame marks {ma:.1%} of physician answers as an acceptable course of action and {mc:.1%} as a "
              f"forbidden one. On the same conversations and the same frames the evaluated systems run "
              f"{min(r[2] for r in sys_rows):.1%} to {best[2]:.1%} acceptable and "
              f"{min(r[3] for r in sys_rows):.1%} to {max(r[3] for r in sys_rows):.1%} forbidden.", ""]
        if worse:
            L += [f"**The frame forbids a physician's answer more often than it forbids the answer of "
                  f"{len(worse)} of the {len(sys_rows)} evaluated systems.** That is not the ordering a frame "
                  "whose forbidden list captured only unsafe care would produce. Two readings fit and this "
                  "measurement does not separate them: the list is too narrow on those sources, or a physician's "
                  "reference answer is a different kind of object from a chat reply, covering contingencies and "
                  "hedges that the action judge maps onto a listed action. Either way the level of the outcome "
                  "carries less than the level alone suggests.", "",
                  "What it does not reach is the paired quantities. Both sides of a pair are scored against the "
                  "same list, so a list that is uniformly too narrow raises both and largely cancels in the "
                  "difference; the standard shift applies the *edited* list to two different replies and cancels "
                  "in the same way. The absolute rates are what this bounds.", ""]
        else:
            L += [f"The frame forbids a physician's answer less often than it forbids any evaluated system's, "
                  "which is the ordering a sound frame should produce. It does not make the frame correct; it "
                  "rules out the failure where the annotation encodes a standard no clinician writing on the "
                  "same case would meet.", ""]
    L += [f"The {mc:.1%} of sources where the frame forbids what a physician did are the first thing to hand to "
          "a clinician. Nothing here says whether the frame or the reading of the physician's answer is at "
          "fault, and both are defects in the annotation rather than in the systems.", "",
          "**What this is not.** It is a check on one side of the pair. The frame for the *edited* message, "
          "which is what the primary outcome scores against, has no human artefact to be checked against and is "
          "tested only by the clinician study in the protocol.", ""]
    text = "\n".join(L) + "\n"
    print(text)
    if a.out:
        Path(a.out).write_text(text)


if __name__ == "__main__":
    main()
