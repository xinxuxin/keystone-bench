"""Keystone: paired evidence-perturbation stress tests for clinical chat assistants and their rubric graders.

Public API (stable within 0.x):

    from keystone import load_pairs, evaluate, summarize, OpenAICompatible
    pairs = load_pairs("missing_evidence", layer="core")
    respond = OpenAICompatible("openrouter/openai/gpt-5.6-terra")
    judge = OpenAICompatible("openrouter/openai/gpt-4.1", max_tokens=600)
    records = evaluate(pairs, respond, judge)
    print(summarize(records))

`respond` and `judge` are any callables mapping a list of chat messages to a string, so any
provider or local model can be plugged in without touching the benchmark.
"""
from .data import FAMILIES, CONDITIONS, Pair, find_dist, load_pairs, load_reference, load_manifest
from .prompts import BEHAVIOR_TEMPLATE, APPLICABILITY_TEMPLATE, GRADER_TEMPLATE, parse_json
from .metrics import wilson, mcnemar_exact, healthbench_score, pair_outcomes, summarize, cohen_kappa
from .runner import OpenAICompatible, evaluate, write_run

__version__ = "0.4.1"
__all__ = ["FAMILIES", "CONDITIONS", "Pair", "find_dist", "load_pairs", "load_reference", "load_manifest",
           "BEHAVIOR_TEMPLATE", "APPLICABILITY_TEMPLATE", "GRADER_TEMPLATE", "parse_json",
           "wilson", "mcnemar_exact", "healthbench_score", "pair_outcomes", "summarize", "cohen_kappa",
           "OpenAICompatible", "evaluate", "write_run", "__version__"]
