"""Smoke test of the Inspect AI task on mock models (no keys, no network).

Checks that the task loads the released files, the paired solver produces three replies per sample,
the scorer emits every protocol quantity, the metrics aggregate, and the prompts are the package's.
"""
from __future__ import annotations

import json

import pytest

pytest.importorskip("inspect_ai")

from keystone import prompts  # noqa: E402
from keystone.inspect_task import FAMILIES, NA, healthbench_score, load_family, keystone  # noqa: E402

JUDGE_JSON = json.dumps({"stance": "definitive", "names_missing_element": False, "assumes_missing_element": False,
                         "asks_any_question": False, "confidence_language": "high", "unsafe_action": True,
                         "explanation": "mock", "criteria_met": True, "applicable": True})


def test_task_uses_package_prompts():
    import keystone.inspect_task as t
    assert t.BEHAVIOR_TEMPLATE is prompts.BEHAVIOR_TEMPLATE
    assert t.APPLICABILITY_TEMPLATE is prompts.APPLICABILITY_TEMPLATE
    assert t.GRADER_TEMPLATE is prompts.GRADER_TEMPLATE
    assert healthbench_score([{"points": -1}], [True]) == NA


@pytest.mark.parametrize("family", FAMILIES)
def test_load_family(family):
    if not load_family(family, "all"):
        pytest.skip(f"{family} is not in this release")
    core = load_family(family, "core")
    allv = load_family(family, "all")
    assert 0 < len(core) <= len(allv)
    s = core[0]
    assert s.metadata["perturbed_prompt"][-1]["role"] == "user"
    assert s.metadata["rubrics"] and s.metadata["in_core"]
    assert all(x.metadata["in_core"] for x in core)


def test_task_runs_on_mock_models(tmp_path):
    from inspect_ai import eval as inspect_eval
    from inspect_ai.model import ModelOutput, get_model

    judge = get_model("mockllm/model", custom_outputs=[ModelOutput.from_content(model="mockllm/model", content=JUDGE_JSON)] * 5000)
    logs = inspect_eval(keystone(family="missing_evidence", judge=judge, rubric=True, limit=3),
                        model="mockllm/model", log_dir=str(tmp_path), display="none")
    log = logs[0]
    assert log.status == "success", getattr(log, "error", None)
    assert len(log.samples) == 3
    for s in log.samples:
        replies = s.store.get("replies") if hasattr(s.store, "get") else s.store["replies"]
        assert set(replies) >= {"original", "perturbed"}
        v = s.scores["keystone_scorer"].value
        assert v["orig_definitive"] == 1.0 and v["pert_definitive"] == 1.0
        assert v["adaptation_failure"] == 1.0 and v["ack_but_answer"] == 0.0
        assert v["definitive_change"] == 0.0
        # the mock grader marks every criterion met, negative ones included, so the score is
        # (positive minus negative points) / positive points and identical under both rubrics
        assert 0.0 <= v["score_original"] <= 1.0, v
        assert v["score_original"] == v["score_perturbed_stale"], v
        assert v["score_perturbed_applicable"] == v["score_perturbed_stale"]
        assert v["inapplicable_share"] == 0.0
    names = {(sc.name, m) for sc in log.results.scores for m in sc.metrics}
    joined = " ".join(f"{a}/{b}" for a, b in names)
    for key in ("adaptation_failure", "spurious_shift", "definitive_change", "score_perturbed_applicable"):
        assert key in joined, f"metric group {key} missing from {joined}"
    vals = {f"{sc.name}/{m}": em.value for sc in log.results.scores for m, em in sc.metrics.items()}
    af = [v for k, v in vals.items() if "adaptation_failure" in k and k.endswith("rate")]
    assert af and af[0] == 1.0
