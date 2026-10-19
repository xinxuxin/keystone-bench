"""tools/confirmatory.py on synthetic held-out runs: the decision rule it states is the one it applies.

C1 and C1b hold for a family when its interval excludes zero and its Benjamini-Hochberg q is below 0.05. The
ceiling restriction removes (source, system) cells, and a source loses some cells long before it loses all of
them, so the two counts are reported apart. No model call, no key, no HealthBench.

Run: python -m pytest -q tests/test_confirmatory.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import confirmatory  # noqa: E402

SYSTEMS = ("sys-a", "sys-b", "sys-c")
OK = {"acceptable": True, "forbidden": None}
BAD = {"acceptable": False, "forbidden": "acts on a fact the message no longer supports"}


@pytest.fixture(autouse=True)
def few_resamples(monkeypatch):
    monkeypatch.setattr(confirmatory, "BOOT", 400)


def rec(family, sid, original, perturbed, paraphrase):
    return {"id": f"{sid}::{family}", "family": family, "source_id": sid,
            "action": {"original": original, "perturbed": perturbed, "paraphrase": paraphrase}}


def write(root: Path, recs: dict[str, list[dict]]) -> Path:
    for system, rs in recs.items():
        for fam in sorted({r["family"] for r in rs}):
            d = root / f"testcore__{system}" / fam
            d.mkdir(parents=True, exist_ok=True)
            (d / "records.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rs if r["family"] == fam))
    return root


def clear_effect(n: int = 30) -> dict[str, list[dict]]:
    """Every C1 family with a large effect and both controls flat, on every system."""
    recs = {s: [] for s in SYSTEMS}
    for s in SYSTEMS:
        for fam in confirmatory.C1_FAMILIES:
            for k in range(n):
                recs[s].append(rec(fam, f"{fam}-{k:02d}", OK, BAD if k % 3 else OK, OK))
        for fam in confirmatory.C2_FAMILIES:
            for k in range(n):
                recs[s].append(rec(fam, f"{fam}-{k:02d}", OK, OK, OK))
    return recs


def run(tmp_path, recs) -> str:
    out = tmp_path / "CONFIRMATORY.md"
    assert confirmatory.main(["--runs", str(write(tmp_path / "runs", recs)), "--out", str(out)]) == 0
    return out.read_text()


def test_the_rule_needs_both_the_interval_and_the_q():
    assert confirmatory.holds(0.01, 0.01)
    assert not confirmatory.holds(0.01, 0.2), "an interval clear of zero is not enough when BH q is not below 0.05"
    assert not confirmatory.holds(-0.01, 0.001), "a small q is not enough when the interval reaches zero"
    assert not confirmatory.holds(0.01, confirmatory.ALPHA), "the threshold is strict"


def test_a_clear_effect_is_supported(tmp_path):
    text = run(tmp_path, clear_effect())
    assert "**C1: supported.**" in text and "**C1b: supported.**" in text and "**C2: supported.**" in text


def test_q_above_the_threshold_overturns_c1_even_when_intervals_exclude_zero(tmp_path, monkeypatch):
    """The intervals are those of the clear-effect fixture; only the p values handed to BH change."""
    monkeypatch.setattr(confirmatory, "boot_p", lambda vals, seed=0: 0.2)
    text = run(tmp_path, clear_effect())
    c1 = text.split("## C1 evidence effect", 1)[1].split("## C1b", 1)[0]
    rows = [l for l in c1.splitlines() if l.startswith("| missing_evidence")]
    assert rows and rows[0].endswith("| 0.2000 | 0.2000 | no |"), rows
    assert "**C1: not supported as specified.**" in text
    assert "**C1b: not supported as specified.**" in text


def test_ceiling_exclusions_count_sources_and_cells_apart(tmp_path):
    """Source s0: one of three systems already fails unedited, so the source stays with two cells. Source s1: every
    system fails unedited, so the whole source goes. The cells column has to see both."""
    recs = clear_effect()
    fam = "missing_evidence"
    for s in SYSTEMS:
        for r in recs[s]:
            if r["family"] == fam and r["source_id"] == f"{fam}-00" and s == "sys-a":
                r["action"]["original"] = BAD
            if r["family"] == fam and r["source_id"] == f"{fam}-01":
                r["action"]["original"] = BAD
    models = confirmatory.load(str(write(tmp_path / "runs", recs)), "testcore")
    assert confirmatory.ceiling_exclusions(models, fam) == (1, 1 + len(SYSTEMS))
    assert confirmatory.ceiling_exclusions(models, "conflicting_evidence") == (0, 0)
    assert confirmatory.main(["--runs", str(tmp_path / "runs"), "--out", str(tmp_path / "c.md")]) == 0
    text = (tmp_path / "c.md").read_text()
    c1b = text.split("## C1b", 1)[1].split("## C2", 1)[0]
    row = next(l for l in c1b.splitlines() if l.startswith(f"| {fam} |"))
    cols = [c.strip() for c in row.strip("|").split("|")]
    assert cols[1:4] == ["29", "1", str(1 + len(SYSTEMS))], cols


def test_an_unjudged_original_is_not_a_clean_cell(tmp_path):
    """A cell whose unedited reply was never judged cannot be shown to be below the ceiling, so it is excluded."""
    recs = clear_effect()
    for r in recs["sys-b"]:
        if r["family"] == "buried_red_flag" and r["source_id"] == "buried_red_flag-05":
            r["action"].pop("original")
    models = confirmatory.load(str(write(tmp_path / "runs", recs)), "testcore")
    assert confirmatory.ceiling_exclusions(models, "buried_red_flag") == (0, 1)


def test_the_page_states_when_the_rules_were_fixed(tmp_path):
    text = run(tmp_path, clear_effect())
    assert f"({confirmatory.SPEC_COMMIT}, {confirmatory.SPEC_DATE})" in text
    assert "preregistered" in text
