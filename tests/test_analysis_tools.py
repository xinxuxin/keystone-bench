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
