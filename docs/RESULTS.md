# Results

Rates are over pairs whose original reply was definitive, with Wilson 95% intervals; the definitive-rate change is an exact McNemar test over all pairs. A row is only comparable with another row of the same family, layer and benchmark version, and only if its spurious shift is at most 0.10.

| Model | Family | Layer | Pairs | Adaptation failure | Spurious shift | Unsafe action | Definitive orig → pert | McNemar p | Source |
|---|---|---|---|---|---|---|---|---|---|
| openrouter:anthropic/claude-sonnet-5 | missing_evidence | pilot-80 (majority 3) | 32 | 0.23 [0.10, 0.43] | 0.05 [0.01, 0.23] | 0.50 [0.31, 0.69] | 0.69 → 0.38 | 0.021 | reference pilot 2026-09-06, judge gpt-4.1 |
| openrouter:deepseek/deepseek-v4-pro-0813 | missing_evidence | pilot-80 (majority 3) | 29 | 0.46 [0.30, 0.64] | 0.03 [0.01, 0.17] | 0.36 [0.21, 0.54] | 0.97 → 0.55 | 0.00049 | reference pilot 2026-09-06, judge gpt-4.1 |
| openrouter:google/gemini-3.8-flash | missing_evidence | pilot-80 (majority 3) | 31 | 0.36 [0.21, 0.54] | 0.00 [0.00, 0.12] | 0.32 [0.18, 0.51] | 0.90 → 0.39 | 3.1e-05 | reference pilot 2026-09-06, judge gpt-4.1 |
| openrouter:meta-llama/llama-4-maverick | missing_evidence | pilot-80 (majority 3) | 32 | 0.57 [0.39, 0.73] | 0.07 [0.02, 0.23] | 0.43 [0.27, 0.61] | 0.88 → 0.56 | 0.0063 | reference pilot 2026-09-06, judge gpt-4.1 |
| openrouter:openai/gpt-5.6-terra | missing_evidence | pilot-80 (majority 3) | 31 | 0.26 [0.13, 0.45] | 0.04 [0.01, 0.18] | 0.33 [0.19, 0.52] | 0.87 → 0.32 | 1.5e-05 | reference pilot 2026-09-06, judge gpt-4.1 |

**Scope of these numbers.** All 80 pilot items are single-turn, while 38 percent of the release is multi-turn, so nothing in this table describes what an assistant does when the load-bearing fact sits in an earlier turn. That is what `missing_evidence_early` is for, and no reference run covers it yet. The pilot also predates the 0.3.0 change that gives every judge the full conversation rather than the last user message; the change cannot affect these numbers, because the items are single-turn, and it is noted here so that the two dates are not read as a discrepancy.

No community submissions yet. See [`../results/community/README.md`](../results/community/README.md) for how to add one.

## Unconditional outcomes on the same records

The table above conditions on the original reply being definitive, so each model is scored on its own subset of items and a model that commits less often is scored on fewer of them. The three outcomes below put every median-3 twin in the denominator (Wilson 95% intervals); they are computed from the shipped `reference_records.jsonl` with `keystone.metrics.summarize`, so anyone can reproduce the numbers without a key.

| Model | Unsupported action ↓ | Answered when sufficient ↑ | Adaptation failure (conditional, for reference) |
|---|---|---|---|
| claude-sonnet-5 | 0.50 [0.34, 0.66] (16/32) | 0.81 (26/32) | 0.23 (5/22) |
| gpt-5.6-terra | 0.42 [0.26, 0.59] (13/31) | 0.97 (31/32) | 0.26 (7/27) |
| gemini-3.8-flash | 0.42 [0.26, 0.59] (13/31) | 1.00 (32/32) | 0.36 (10/28) |
| deepseek-v4-pro | 0.60 [0.42, 0.75] (18/30) | 1.00 (31/31) | 0.46 (13/28) |
| llama-4-maverick | 0.69 [0.51, 0.82] (22/32) | 0.94 (30/32) | 0.57 (16/28) |

Read together: the model with the lowest conditional adaptation failure (claude-sonnet-5, 0.23) is also the one that commits least often on the original (answered when sufficient 0.81), and on unsupported action it sits in the middle of the field (0.50) while gemini-3.8-flash and gpt-5.6-terra lead (0.42). A cross-model comparison should be read from the unconditional rows; the conditional rate remains a diagnostic of what a model does when it does commit.
