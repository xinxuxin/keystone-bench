"""Properties the analysis tools must have, checked without a model call or a key.

Two things are worth a test here. The cross-scoring decomposition is an algebraic identity, and a refactor
that broke it would still produce plausible-looking tables. And a report tool that writes a statistic into a
plain string drifts from its own tables the next time the run changes, which is a defect
`tools/doc_numbers.py` exists to catch, so the check itself is pinned.

Run: python -m pytest -q tests/test_analysis_tools.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def test_decomposition_is_exact():
    """outcome == standard shift + reply adaptation, for every assignment of the three cells."""
    for fc_rc in (0.0, 1.0):
        for fe_rc in (0.0, 1.0):
            for fe_re in (0.0, 1.0):
                outcome = fe_re - fc_rc
                shift = fe_rc - fc_rc
                adapt = fe_re - fe_rc
                assert outcome == pytest.approx(shift + adapt)


def test_a_reply_that_ignores_the_edit_has_zero_adaptation():
    """r_e = r_c makes f_e(r_e) = f_e(r_c), so the adaptation term is identically zero whatever the level."""
    for verdict in (0.0, 1.0):
        fe_rc = fe_re = verdict          # the same text under the same standard
        assert fe_re - fe_rc == 0.0


def test_report_tools_carry_no_frozen_statistics():
    """Every number a report tool states in prose has to be recomputed from the run that produced the tables."""
    tools = sorted(str(p) for p in (ROOT / "tools").glob("*.py"))
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "doc_numbers.py"), "--quiet", *tools],
                       capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stdout + r.stderr


def test_cross_scoring_imports_without_a_key():
    """The tool must be importable for --dry-run and for these tests without OPENROUTER_API_KEY set."""
    r = subprocess.run([sys.executable, "-c", "import ast,pathlib;"
                        "ast.parse(pathlib.Path('tools/cross_scoring.py').read_text());"
                        "ast.parse(pathlib.Path('tools/rubric_consequence.py').read_text())"],
                       capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stderr


# ---------------------------------------------------------------------------
# The audit steps have to bite. Each one is fed a table where its condition
# fails, and a table where it holds, so a refactor that makes a step always
# return pass is caught here rather than by a reader who trusted the output.
# ---------------------------------------------------------------------------

def _steps():
    from keystone.cli import (_step_effect, _step_control, _step_separation,
                              _step_adaptation, _step_usability, _step_floor)
    return dict(effect=_step_effect, control=_step_control, separation=_step_separation,
                adaptation=_step_adaptation, usability=_step_usability, floor=_step_floor)


C1_HOLDS = """
| family | sources | risk difference | p | q | excludes zero |
|---|---|---|---|---|---|
| missing_evidence | 85 | +0.079 [+0.018, +0.140] | 0.01 | 0.01 | yes |
| conflicting_evidence | 139 | +0.284 [+0.223, +0.344] | 0.00 | 0.00 | yes |
| buried_red_flag | 148 | +0.126 [+0.076, +0.176] | 0.00 | 0.00 | yes |
"""
C1_FAILS = C1_HOLDS.replace("+0.079 [+0.018, +0.140]", "+0.011 [-0.048, +0.070]")

C2_HOLDS = """
| family | sources | risk difference (90%) | inside |
|---|---|---|---|
| salient_distractor | 219 | +0.002 [-0.012, +0.016] | yes |
| demographic_control | 161 | -0.004 [-0.026, +0.017] | yes |
"""
C2_FAILS = C2_HOLDS.replace("+0.002 [-0.012, +0.016]", "+0.140 [+0.090, +0.190]")

POL_HOLDS = """
| | | unsupported action | paired difference | adaptation rate | withheld |
|---|---|---|---|---|---|
| `always_definitive` | commits every time | 0.968 | +0.968 | 0.00 | 0.000 |
| `parrot_then_act` | names it, commits | 0.968 | +0.968 | 0.00 | 0.000 |
| `always_ask` | asks, gives nothing | 0.000 | +0.000 | n/a | 1.000 |
| `always_conditional` | hedges | 0.000 | +0.000 | n/a | 1.000 |
| `always_escalate` | escalates | 0.000 | +0.000 | n/a | 1.000 |
| `always_refuse` | refers out | 0.000 | +0.000 | n/a | 1.000 |
| `model-a` | evaluated system | 0.158 | +0.097 | 0.86 | 0.096 |
| `model-b` | evaluated system | 0.626 | +0.368 | 0.40 | 0.220 |
"""
# a system that buys its score by answering nothing: the adaptation column still looks fine
POL_INERT_SYSTEM = POL_HOLDS.replace("| `model-b` | evaluated system | 0.626 | +0.368 | 0.40 | 0.220 |",
                                     "| `model-b` | evaluated system | 0.010 | +0.005 | 0.95 | 0.910 |")
# a fixed policy that somehow reports a non-zero adaptation rate: the algebra was broken
POL_BROKEN = POL_HOLDS.replace("| `always_definitive` | commits every time | 0.968 | +0.968 | 0.00 | 0.000 |",
                               "| `always_definitive` | commits every time | 0.968 | +0.968 | 0.44 | 0.000 |")


@pytest.mark.parametrize("step,md,expected", [
    ("effect", C1_HOLDS, True),
    ("effect", C1_FAILS, False),
    ("control", C2_HOLDS, True),
    ("control", C2_FAILS, False),
    ("adaptation", POL_HOLDS, True),
    ("adaptation", POL_BROKEN, False),
    ("usability", POL_HOLDS, True),
    ("usability", POL_INERT_SYSTEM, False),
])
def test_audit_step_verdicts(step, md, expected):
    ok, detail = _steps()[step](md)
    assert ok is expected, f"{step}: got {ok} with {detail!r}"


def test_audit_step_skips_when_the_table_is_absent():
    for name, fn in _steps().items():
        ok, detail = fn("no tables here, just prose")
        assert ok is None, f"{name} returned {ok} on empty input"
        assert detail


EXPIRY_HOLDS = """
| family | sources | criteria dropped | stale | adapted | level shift | ranking flip rate |
|---|---|---|---|---|---|---|
| `missing_evidence` | 85 | 4.2 | 0.443 | 0.499 | +0.056 [+0.025, +0.089] | 0.047 [0.021, 0.079] |
| `conflicting_evidence` | 140 | 1.9 | 0.426 | 0.456 | +0.030 [+0.018, +0.043] | 0.035 [0.019, 0.053] |
| `buried_red_flag` | 148 | 1.1 | 0.396 | 0.419 | +0.024 [+0.013, +0.035] | 0.007 [0.002, 0.013] |
| `salient_distractor` | 100 | 0.1 | 0.469 | 0.474 | +0.005 [+0.001, +0.011] | 0.000 [0.000, 0.000] |
| `demographic_control` | 100 | 0.1 | 0.478 | 0.483 | +0.005 [-0.002, +0.015] | 0.005 [0.000, 0.015] |
"""
# expiry that changes the level and never the ranking: a level shift, not a defect in the instrument
EXPIRY_FAILS = (EXPIRY_HOLDS
                .replace("0.047 [0.021, 0.079]", "0.004 [0.000, 0.010]")
                .replace("0.035 [0.019, 0.053]", "0.003 [0.000, 0.009]")
                .replace("| 0.007 [0.002, 0.013] |", "| 0.002 [0.000, 0.006] |"))


@pytest.mark.parametrize("md,expected", [(EXPIRY_HOLDS, True), (EXPIRY_FAILS, False)])
def test_audit_expiry_step(md, expected):
    from keystone.cli import _step_expiry
    ok, detail = _step_expiry(md)
    assert ok is expected, f"got {ok} with {detail!r}"
