"""tools/item_select.py on synthetic runs: what the rule keeps, what it never reads, and that it is repeatable.

The fixture is a release of two families and four systems where the right answer is known by construction: items
that separate the systems, items every system answers the same way, an item that runs against its family, an item
already failed unedited, and a control whose paraphrase flips. No model call, no key, no HealthBench.

Run: python -m pytest -q tests/test_item_select.py
"""
from __future__ import annotations

import json
import sys
import zlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import discrimination  # noqa: E402
import item_select  # noqa: E402

SYSTEMS = ("sys-a", "sys-b", "sys-c", "sys-d")       # a and b are the stronger pair on the separating items
PASS = {"acceptable": True, "forbidden": None, "asks_decisive_question": True, "conditional": False, "escalates": False}
FAIL = {"acceptable": False, "forbidden": "commits without the missing fact", "asks_decisive_question": False,
        "conditional": False, "escalates": False}
HOLD = {"acceptable": True, "forbidden": None, "asks_decisive_question": False, "conditional": False, "escalates": False}


@pytest.fixture(autouse=True)
def few_permutations(monkeypatch):
    monkeypatch.setattr(discrimination, "PERM", 200)


def twin(pid, family, split, **kw):
    state = "sufficient_for_original_action" if family in item_select.CONTROLS else "insufficient_ambiguous"
    return {"prompt_id": pid, "family": family, "split": split, "evidence_state": state, "group": "enough_context",
            "turns": 1, "materiality_majority": 3, "state_review_behaviour_agree": True, "revision": 1, **kw}


def record(pid, family, split, original, perturbed, paraphrase):
    t = twin(pid, family, split)
    return {"id": f"{pid}::{family}", "family": family, "source_id": pid, "split": split,
            "evidence_state": t["evidence_state"], "escalation_sufficient": False,
            "action": {"original": original, "perturbed": perturbed, "paraphrase": paraphrase}}


def design(split: str, n_sep: int = 25, n_const: int = 12, n_ctrl: int = 30):
    """{item kind: [pid]} and {system: [record]} for one split."""
    kinds, recs = {}, {s: [] for s in SYSTEMS}
    me = "missing_evidence"
    def add(kind, pid, per_system, family=me):
        kinds.setdefault(kind, []).append(pid)
        for s in SYSTEMS:
            recs[s].append(record(pid, family, split, *per_system(s)))
    for k in range(n_sep):
        add("separating", f"{split}-sep-{k:02d}", lambda s: (HOLD, PASS if s in ("sys-a", "sys-b") else FAIL, HOLD))
    for k in range(n_const):
        add("constant", f"{split}-const-{k:02d}", lambda s: (HOLD, PASS, HOLD))
    # passed by the two weaker systems only: the item runs against the family
    add("against", f"{split}-against", lambda s: (HOLD, FAIL if s in ("sys-a", "sys-b") else PASS, HOLD))
    # three of four systems already take a forbidden action on the unedited conversation
    # (its paraphrase agrees with it, so the control is stable and only the ceiling can exclude it)
    add("ceiling", f"{split}-ceiling", lambda s: (FAIL if s != "sys-a" else HOLD,
                                                  PASS if s in ("sys-a", "sys-b") else FAIL,
                                                  FAIL if s != "sys-a" else HOLD))
    for k in range(n_ctrl):
        add("control", f"{split}-ctrl-{k:02d}", lambda s: (HOLD, HOLD, HOLD), family="salient_distractor")
    # a control whose paraphrase flips the verdict on two systems: measurement noise, not a property of the item
    add("unstable", f"{split}-ctrl-unstable", lambda s: (HOLD, HOLD, FAIL if s in ("sys-c", "sys-d") else HOLD),
        family="salient_distractor")
    return kinds, recs


@pytest.fixture
def release(tmp_path):
    """A dist with a dev and a test half, run directories in both layouts, and the expected item kinds."""
    dev_kinds, dev_recs = design("dev")
    test_kinds, test_recs = design("test")
    dist = tmp_path / "dist"
    dist.mkdir()
    rows = []
    for split, kinds in (("dev", dev_kinds), ("test", test_kinds)):
        for kind, pids in kinds.items():
            fam = "salient_distractor" if kind in ("control", "unstable") else "missing_evidence"
            rows += [twin(p, fam, split) for p in pids]
    (dist / "keystone_twins.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    meta = {"meta": {"benchmark_version": item_select.VERSION}}

    def write_runs(root: Path, prefix: str, recs: dict):
        for s, rs in recs.items():
            for fam in ("missing_evidence", "salient_distractor"):
                d = root / f"{prefix}__{s}" / fam
                d.mkdir(parents=True)
                (d / "records.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rs if r["family"] == fam))
                (d / "summary.json").write_text(json.dumps(meta))

    def write_reference(root: Path, recs: dict):
        for s, rs in recs.items():
            d = root / s
            d.mkdir(parents=True)
            for fam in ("missing_evidence", "salient_distractor"):
                (d / f"{fam}__quick.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rs if r["family"] == fam))
                (d / f"{fam}__quick.json").write_text(json.dumps(meta))

    write_runs(tmp_path / "runs", "devq", dev_recs)
    write_runs(tmp_path / "runs", "testcore", test_recs)
    write_reference(tmp_path / "reference", dev_recs)
    return {"root": tmp_path, "dist": dist, "dev": dev_kinds, "test": test_kinds, "test_recs": test_recs,
            "write_runs": write_runs}


def ids(kinds, kind, family="missing_evidence"):
    return {f"{p}::{family}" for p in kinds[kind]}


def selection(release, prefix="devq"):
    twins = item_select.load_twins(release["dist"])
    items, _, _ = item_select.load(str(release["root"] / "runs"), prefix, "quick", twins)
    dev = {i: v for i, v in items.items() if twins[i]["split"] == "dev"}
    stats = item_select.item_stats(dev, twins)
    return stats, item_select.select(stats)


def test_separating_items_are_kept_and_the_others_dropped(release):
    stats, chosen = selection(release)
    kept = set(chosen["missing_evidence"])
    assert ids(release["dev"], "separating") <= kept
    assert not kept & ids(release["dev"], "constant"), "an item every system answers alike separates nothing"
    assert ids(release["dev"], "against").isdisjoint(kept), "an item with negative item-rest r runs against the family"
    assert ids(release["dev"], "ceiling").isdisjoint(kept), "an item already failed unedited has no room to move"
    sep = next(iter(ids(release["dev"], "separating")))
    assert stats[sep]["item_rest_r"] > 0 and stats[sep]["constant_primary"] is False
    assert stats[next(iter(ids(release["dev"], "against")))]["item_rest_r"] < 0


def test_an_unstable_control_is_the_one_left_out():
    """Twenty-one controls for a floor of twenty: the one that goes must be the one whose paraphrase flips, whatever
    its place in the hash order."""
    kinds, recs = design("dev", n_ctrl=item_select.MIN_ITEMS)
    items: dict = {}
    for sys_, rs in recs.items():
        for r in rs:
            items.setdefault(r["id"], {})[sys_] = r
    twins = {r["id"]: twin(r["source_id"], r["family"], "dev") for rs in recs.values() for r in rs}
    stats = item_select.item_stats(items, twins)
    unstable = next(iter(ids(kinds, "unstable", "salient_distractor")))
    assert stats[unstable]["instability"] > item_select.MAX_INSTABILITY
    ctrl = sorted((i for i, s in stats.items() if s["family"] == "salient_distractor"), key=lambda i: stats[i]["hash"])
    assert ctrl[-1] != unstable, "the fixture must not let hash order do the filter's work"
    chosen = item_select.select(stats)["salient_distractor"]
    assert len(chosen) == item_select.MIN_ITEMS and unstable not in chosen


def test_a_short_family_is_filled_to_the_floor():
    kinds, recs = design("dev", n_sep=5, n_const=20)
    items: dict = {}
    for sys_, rs in recs.items():
        for r in rs:
            items.setdefault(r["id"], {})[sys_] = r
    twins = {r["id"]: twin(r["source_id"], r["family"], "dev") for rs in recs.values() for r in rs}
    chosen = item_select.select(item_select.item_stats(items, twins))
    assert len(chosen["missing_evidence"]) == item_select.MIN_ITEMS
    assert ids(kinds, "separating") <= set(chosen["missing_evidence"]), "informative items come first in a top-up"


def test_controls_keep_their_share_and_lose_the_unstable_item(release):
    stats, chosen = selection(release)
    full = {f: [i for i, s in stats.items() if s["family"] == f] for f in ("missing_evidence", "salient_distractor")}
    share_full = len(full["salient_distractor"]) / sum(len(v) for v in full.values())
    kept_ctrl = len(chosen["salient_distractor"])
    share_kept = kept_ctrl / (kept_ctrl + len(chosen["missing_evidence"]))
    assert kept_ctrl >= item_select.MIN_ITEMS
    assert abs(share_kept - share_full) < 0.1 or kept_ctrl == item_select.MIN_ITEMS
    assert ids(release["dev"], "unstable", "salient_distractor").isdisjoint(chosen["salient_distractor"])


def test_the_test_split_is_never_read_to_choose(release, tmp_path):
    """Selection runs that also hold test items, then the same with every test outcome turned upside down: the chosen
    ids must not move, and none of them may be a test item."""
    root = release["root"]

    def mixed(name: str, test_recs: dict) -> Path:
        out = root / name
        release["write_runs"](out, "devq", test_recs)
        for d in (root / "runs").glob("devq__*"):
            for fam_dir in d.iterdir():
                tgt = out / d.name / fam_dir.name / "records.jsonl"
                tgt.write_text(tgt.read_text() + (fam_dir / "records.jsonl").read_text())
        return out

    flipped = {s: [] for s in release["test_recs"]}
    for s, rs in release["test_recs"].items():
        for r in rs:
            r = json.loads(json.dumps(r))
            r["action"]["perturbed"] = FAIL if r["action"]["perturbed"].get("acceptable") else PASS
            flipped[s].append(r)
    picks = []
    for name, recs in (("mixed", release["test_recs"]), ("flipped", flipped)):
        out = tmp_path / f"{name}.json"
        assert item_select.main(["--runs", str(mixed(name, recs)), "--prefix", "devq", "--dist", str(release["dist"]),
                                 "--ids", str(out)]) == 0
        picks.append(json.loads(out.read_text())["items"])
    assert picks[0] == picks[1]
    assert all(i.startswith("dev-") for v in picks[0].values() for i in v)


def test_report_is_deterministic_and_scores_the_held_out_split(release, tmp_path):
    root = release["root"]
    args = ["--runs", str(root / "runs"), "--prefix", "devq", "--eval-runs", str(root / "runs"),
            "--eval-prefix", "testcore", "--dist", str(release["dist"])]
    a, b = tmp_path / "a.md", tmp_path / "b.md"
    assert item_select.main(args + ["--out", str(a)]) == 0
    assert item_select.main(args + ["--out", str(b)]) == 0
    text = a.read_text()
    assert text == b.read_text(), "the same runs must give the same page"
    assert "## Full set against the subset, held out" in text
    held = text.split("## Full set against the subset, held out", 1)[1]
    assert "`missing_evidence`" in held and "`salient_distractor` (control)" in held


def test_both_run_layouts_load_the_same_items(release):
    twins = item_select.load_twins(release["dist"])
    a, _, _ = item_select.load(str(release["root"] / "runs"), "devq", "quick", twins)
    b, _, _ = item_select.load(str(release["root"] / "reference"), None, "quick", twins)
    assert set(a) == set(b) and all(set(a[i]) == set(b[i]) == set(SYSTEMS) for i in a)


def test_full_set_spread_is_the_discrimination_statistic(release):
    """The full-set columns must be tools/discrimination.py's numbers on the same runs, not a near relative."""
    twins = item_select.load_twins(release["dist"])
    items, _, _ = item_select.load(str(release["root"] / "runs"), "devq", "quick", twins)
    stats = item_select.item_stats(items, twins)
    fam = "missing_evidence"
    row = item_select.family_row(fam, [i for i, s in stats.items() if s["family"] == fam], items, stats)
    per = discrimination.load(str(release["root"] / "runs"), "devq")
    rows = sorted((s, d) for s, d in per[fam].items() if len(d) >= 2)
    sd, p, _, _ = discrimination.spread_and_p(rows, seed=zlib.crc32(fam.encode()) % 1000)
    assert row["sd"] == pytest.approx(sd) and row["p"] == pytest.approx(p)


def test_records_from_an_earlier_version_map_through_the_revision_fields():
    v = item_select.VERSION
    twins = {"a::f": {"revision": 1}, "b::f": {"revision": 2, "inherits_annotations": True},
             "c::f": {"revision": 2, "inherits_annotations": False}}
    assert item_select.current_item("a::f", "0.5.0", twins)[0] == "a::f"
    assert item_select.current_item("b::f", "0.5.0", twins)[0] == "b::f"
    assert item_select.current_item("b::f", "0.5.0", twins, keep_inherited=False)[0] is None
    assert item_select.current_item("c::f", "0.5.0", twins)[0] is None, "a rewritten twin's old replies answered other text"
    assert item_select.current_item("c::f", v, twins)[0] == "c::f", "a run on the current release needs no mapping"
    assert item_select.current_item("gone::f", v, twins)[0] is None
