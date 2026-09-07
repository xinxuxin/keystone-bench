"""Three ways to evaluate on Keystone from Python. Run: python examples/quickstart.py

1. Any OpenAI-compatible endpoint through the built-in client (needs a key in the environment).
2. Your own model behind a one-line callable (no provider assumptions).
3. Offline: reproduce the reference numbers from the released per-reply grades.
"""
from __future__ import annotations

import json
import os
import sys

from keystone import OpenAICompatible, evaluate, load_manifest, load_pairs, summarize, write_run
from keystone.metrics import primary_hypothesis_supported
from keystone.runner import report_markdown

pairs = load_pairs("missing_evidence", layer="core", limit=int(os.environ.get("N", "10")))
print(f"{len(pairs)} core pairs; first pair changed: {pairs[0].removed_or_changed!r}")

# --- 1. hosted models --------------------------------------------------------
if os.environ.get("OPENROUTER_API_KEY"):
    respond = OpenAICompatible("openrouter/openai/gpt-5.6-terra")          # model under test, HealthBench settings
    judge = OpenAICompatible("openrouter/anthropic/claude-sonnet-5", max_tokens=600)  # a different vendor from the model
    records = evaluate(pairs, respond, judge, rubric=False, workers=4)
    summary = write_run("runs/quickstart", records, {"title": "quickstart", "model": respond.name, "judge": judge.name})
    print(report_markdown(summary, "quickstart"))
    if summary.get("action"):                                            # decision-evidence outcomes (0.4.0)
        print("forbidden action:", summary["action"]["forbidden_action"], "necessary update:", summary["action"]["necessary_update"])
    print("primary hypothesis supported:", primary_hypothesis_supported(summary))
    print("spend:", respond.usage, judge.usage)
else:
    print("OPENROUTER_API_KEY not set; skipping the hosted example")

# --- 2. your own model ------------------------------------------------------
# Anything that maps a list of {"role", "content"} messages to a string works, so a local model,
# an agent, or a retrieval pipeline can be evaluated without adapters:
#
#   def my_model(messages: list[dict]) -> str:
#       return my_pipeline.chat(messages)
#   records = evaluate(pairs, my_model, judge)

# --- 3. offline ------------------------------------------------------------------
ref = json.load(open(os.path.join(os.path.dirname(__file__), "..", "dist", "reference_results.json")))
print("benchmark", load_manifest()["version"], "| reference adaptation failure (primary rule):",
      {k.split("/")[-1]: round(v["adaptation_failure"]["rate"], 2) for k, v in ref["results"]["majority"]["models"].items()})
