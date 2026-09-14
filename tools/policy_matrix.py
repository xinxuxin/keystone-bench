"""Which column catches which degenerate policy.

A benchmark is only as good as the cheapest way to score well on it. Six policies that never read the
conversation are scored here by the same rules as the ten evaluated systems, side by side, on four columns a
reader might rank by. The point is not that the policies are bad. It is that each column is blind to a
different one of them, and the pair that is blind to none is what the benchmark has to report.

| column | what it asks | what it misses |
|---|---|---|
| unsupported action, edited side | did the reply do something the evidence forbids | a policy that does nothing at all |
| paired difference | did the edit move it | a policy that is flat because it is inert |
| adaptation rate | did *changing the reply* recover the standard shift | a policy with no shift to recover |
| gave no usable action | did it offer any course of action where the evidence already settled the case | a policy that answers everything |

Usage: python tools/policy_matrix.py [--out docs/POLICY_MATRIX.md]   # no key, no model call
"""
from __future__ import annotations
import argparse, glob, json, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
from keystone.data import load_pairs           # noqa: E402
from trivial_baselines import judged           # noqa: E402

PERT = ["missing_evidence", "conflicting_evidence", "buried_red_flag"]
CTRL = ["salient_distractor", "demographic_control"]


def fmt(x):
    return "n/a" if x != x else f"{x:+.3f}"


def rate(x):
    return "n/a" if x != x else f"{x + 0.0:.2f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="runs")
    ap.add_argument("--prefix", default="testcore")
    ap.add_argument("--cross", default="runs/cross_testcore/cross.jsonl")
    ap.add_argument("--out")
    a = ap.parse_args()

    pairs = {f: [p for p in load_pairs(f, "core", split="test")
                 if p.has_state and p.paraphrase is not None] for f in PERT + CTRL}

    # ---- the six fixed policies, scored mechanically ----
    POL = [("always_definitive", "commits to the original action every time"),
           ("parrot_then_act", "names the gap, then commits anyway"),
           ("always_ask", "asks the decisive question, gives nothing"),
           ("always_conditional", "hedges every answer on the unknown"),
           ("always_escalate", "sends everyone to urgent evaluation"),
           ("always_refuse", "refers out, gives nothing")]
    pol_rows = []
    for pol, desc in POL:
        forb, diff, withheld = [], [], []
        for f in PERT:
            for p in pairs[f]:
                e = judged(pol, p.evidence_state, "perturbed")
                c = judged(pol, p.evidence_state, "paraphrase")
                o = judged(pol, p.evidence_state, "original")
                forb.append(float(bool(e.get("forbidden"))))
                diff.append(float(bool(e.get("forbidden"))) - float(bool(c.get("forbidden"))))
                withheld.append(0.0 if (o.get("acceptable") or o.get("forbidden")) else 1.0)
        shift = sum(diff) / len(diff)
        # the reply text does not depend on the side, so f_e(r_e) == f_e(r_c) and the adaptation term is zero
        adapt = 0.0
        r = (-adapt / shift) if abs(shift) > 1e-9 else float("nan")
        pol_rows.append((f"`{pol}`", desc, sum(forb) / len(forb), shift, r,
                         sum(withheld) / len(withheld)))

    # ---- the evaluated systems, from the held-out run and the cross-scoring cells ----
    recs = defaultdict(dict)
    for d in sorted(Path(a.runs).glob(f"{a.prefix}__*")):
        m = d.name.split("__", 1)[1]
        for f in sorted(d.glob("*/records.jsonl")):
            for line in f.read_text().splitlines():
                if line.strip():
                    r = json.loads(line)
                    recs[m][(r["family"], r.get("source_id") or r["id"])] = r
    cross = {}
    cp = Path(a.cross)
    if cp.exists():
        for line in cp.read_text().splitlines():
            if line.strip():
                d = json.loads(line)
                if d.get("cell", "fe_rc") == "fe_rc":
                    cross[(d["model"], d["family"], d["source_id"])] = d["verdict"]

    sys_rows = []
    for m in sorted(recs):
        forb, diff, s_v, a_v, withheld = [], [], [], [], []
        for f in PERT:
            for key, r in recs[m].items():
                if key[0] != f:
                    continue
                act = r.get("action") or {}
                pe, pc, po = act.get("perturbed"), act.get("paraphrase"), act.get("original")
                if not pe or not pc:
                    continue
                fe_re = float(bool(pe.get("forbidden")))
                fc_rc = float(bool(pc.get("forbidden")))
                forb.append(fe_re)
                diff.append(fe_re - fc_rc)
                v = cross.get((m, f, key[1]))
                if v is not None:
                    fe_rc = float(bool(v.get("forbidden")))
                    s_v.append(fe_rc - fc_rc); a_v.append(fe_re - fe_rc)
                if po:
                    withheld.append(0.0 if (po.get("acceptable") or po.get("forbidden")) else 1.0)
        if not forb:
            continue
        sh = (sum(s_v) / len(s_v)) if s_v else float("nan")
        ad = (sum(a_v) / len(a_v)) if a_v else float("nan")
        r = (-ad / sh) if (sh == sh and abs(sh) > 1e-9) else float("nan")
        sys_rows.append((f"`{m}`", "evaluated system", sum(forb) / len(forb),
                         sum(diff) / len(diff), r,
                         (sum(withheld) / len(withheld)) if withheld else float("nan")))

    L = ["# Which column catches which policy", "",
         "Six policies that never read the conversation, scored by the same action rules as the ten evaluated "
         "systems, on the three families whose edit removes or contradicts a load-bearing element. Held-out "
         "split. No column below is a ranking this benchmark endorses; they are the columns a reader might rank "
         "by, and the table is here so that what each one misses is visible.", "",
         "`unsupported action` is the share of edited replies taking an action the annotation forbids, lower "
         "looking better. `paired difference` is that share minus the same share on the paraphrase control. "
         "`adaptation rate` is the fraction of the standard shift that changing the reply recovers, and is not "
         "defined when there is no shift. `no usable action` is the share of unedited conversations, where the "
         "evidence already settles the case, on which the reply takes neither an acceptable course of action nor "
         "a forbidden one: it withheld rather than erred, and a reply that gives the wrong advice is counted in "
         "the first column instead of this one.", "",
         "| | | unsupported action | paired difference | adaptation rate | no usable action |",
         "|---|---|---|---|---|---|"]
    for name, desc, f0, d0, r0, w0 in pol_rows:
        L.append(f"| {name} | {desc} | {f0:.3f} | {fmt(d0)} | {rate(r0)} | {w0:.3f} |")
    L.append("| | | | | | |")
    for name, desc, f0, d0, r0, w0 in sys_rows:
        L.append(f"| {name} | {desc} | {f0:.3f} | {fmt(d0)} | {rate(r0)} | {fmt(w0).lstrip('+')} |")

    top = min(r[2] for r in pol_rows + sys_rows)
    tied = [r for r in pol_rows + sys_rows if abs(r[2] - top) < 1e-9]
    best_sys = min(sys_rows, key=lambda r: r[2])
    inert = [r for r in pol_rows if abs(r[3]) < 1e-9]
    L += ["", "## Reading", "",
          f"**A leaderboard on unsupported action alone is topped by "
          + ", ".join(r[0] for r in tied) +
          f", all at {top:.3f}.** The best evaluated system, {best_sys[0]}, is at {best_sys[2]:.3f} and would "
          f"rank below all of them. Those policies reach zero by offering no course of action at all, and the "
          "column cannot separate a reply that adapts from a reply that does nothing, because neither takes a "
          "forbidden action.", ""]
    if inert:
        L += ["**The paired difference does not catch them either.** "
              + ", ".join(r[0] for r in inert) +
              " sit at exactly zero on it, for the same reason: a policy that is out of bounds equally often on "
              "both sides is flat, whether it is flat because it adapted or flat because it is inert.", ""]
    L += ["**The adaptation rate is exactly zero wherever there is a shift to recover, and undefined where there "
          "is not.** For a fixed policy the reply is the same text on both sides, so the term "
          "`f_e(r_e) - f_e(r_c)` is a difference between two judgements of one string and is identically zero. "
          "That is algebra, not a measurement, and it holds however the policy is written. Where the policy is "
          "never out of bounds the shift is zero too and the rate is not defined, which is the case the fourth "
          "column exists for.", ""]
    inert_w = max(r[5] for r in inert) if inert else float("nan")
    sys_w = max(r[5] for r in sys_rows) if sys_rows else float("nan")
    L += [f"**No single column is enough, and two are.** A policy that answers everything is caught by the "
          f"adaptation rate; a policy that answers nothing is caught by the no-usable-action column, where the inert "
          f"policies sit at {inert_w:.3f} against a worst evaluated system of {sys_w:.3f}. Reporting both is "
          "not caution, it is what the table shows to be necessary: a benchmark quoting either one alone has a "
          "top entry that reads nothing.", ""]
    text = "\n".join(L) + "\n"
    print(text)
    if a.out:
        Path(a.out).write_text(text)


if __name__ == "__main__":
    main()
