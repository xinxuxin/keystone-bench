# Results

Every family is reported on the outcome it was designed around, because the families ask for different behaviour: a removal asks the assistant to seek what is missing, an alternative value asks it to change the action, a buried red flag asks it to escalate, and a negative control asks it to do nothing differently. One outcome, **forbidden action**, is defined for every family against that twin's own annotation, so it is the one that compares across them. A row is comparable with another row of the same family, layer and benchmark version, and only if its paraphrase control held.

## Quick set, 5 assistants, 8 families

Benchmark 0.5.0, layer `quick`, judge `gpt-4.1`, temperature 0.0, 1500 output tokens, generated 2026-09-11. The quick set is 40 twins per family from the dev split, each with its original, its twin and its paraphrase-only control.

### What each family asks for

| Family | The behaviour it asks for | claude-sonnet-5 | deepseek-v4-pro-0813 | gemini-3.8-flash | gpt-5.6-terra | llama-4-maverick |
|---|---|---|---|---|---|---|
| `alternative_evidence` | changed the action to the one the new value supports | 0.90 | 0.94 | 0.87 | 0.81 | 0.74 |
| `buried_red_flag` | made urgent evaluation the main answer | 0.72 | 0.74 | 0.85 | 0.93 | 0.35 |
| `conflicting_evidence` | named the contradiction and asked which side is true | 0.61 | 0.42 | 0.42 | 0.47 | 0.26 |
| `demographic_control` | answered unchanged despite the tempting attribute | 0.95 | 0.95 | 0.87 | 0.95 | 0.78 |
| `demographic_shift` | adjusted the advice to the changed attribute | 0.94 | 0.90 | 0.97 | 0.94 | 0.68 |
| `missing_evidence` | asked the question that settles it, or answered conditionally on it | 0.69 | 0.65 | 0.49 | 0.74 | 0.37 |
| `missing_evidence_early` | same, with the fact removed from an earlier turn | 0.76 | 0.48 | 0.57 | 0.76 | 0.38 |
| `salient_distractor` | answered unchanged despite the irrelevant insertion | 0.93 | 0.95 | 0.80 | 0.97 | 0.85 |

### Forbidden action, the cross-family outcome

The share of replies to the twin that take an action the twin's own annotation rules out. Lower is better everywhere, and unlike the table above it means the same thing in every row.

| Family | claude-sonnet-5 | deepseek-v4-pro-0813 | gemini-3.8-flash | gpt-5.6-terra | llama-4-maverick |
|---|---|---|---|---|---|
| `alternative_evidence` | 0.07 (n=40) | 0.08 (n=39) | 0.10 (n=39) | 0.15 (n=40) | 0.33 (n=40) |
| `buried_red_flag` | 0.28 (n=40) | 0.26 (n=38) | 0.15 (n=40) | 0.10 (n=40) | 0.65 (n=40) |
| `conflicting_evidence` | 0.30 (n=40) | 0.39 (n=38) | 0.45 (n=40) | 0.30 (n=40) | 0.78 (n=40) |
| `demographic_control` | n/a | n/a | n/a | n/a | n/a |
| `demographic_shift` | 0.05 (n=40) | 0.10 (n=40) | 0.05 (n=39) | 0.05 (n=40) | 0.42 (n=40) |
| `missing_evidence` | 0.23 (n=40) | 0.23 (n=39) | 0.30 (n=40) | 0.17 (n=40) | 0.35 (n=40) |
| `missing_evidence_early` | 0.04 (n=23) | 0.26 (n=23) | 0.22 (n=23) | 0.13 (n=23) | 0.17 (n=23) |
| `salient_distractor` | n/a | n/a | n/a | n/a | n/a |

### The paraphrase control

Reworded, no evidence changed. A run whose spurious shift exceeds 0.10 on a family does not support attributing that family's effect to the perturbation.

| Family | claude-sonnet-5 | deepseek-v4-pro-0813 | gemini-3.8-flash | gpt-5.6-terra | llama-4-maverick |
|---|---|---|---|---|---|
| `alternative_evidence` | **0.17** | 0.03 | **0.12** | **0.12** | **0.12** |
| `buried_red_flag` | 0.04 | 0.06 | 0.06 | 0.03 | 0.06 |
| `conflicting_evidence` | **0.15** | 0.09 | 0.06 | 0.03 | 0.10 |
| `demographic_control` | **0.19** | 0.00 | **0.16** | **0.15** | **0.15** |
| `demographic_shift` | **0.13** | 0.00 | 0.07 | 0.04 | 0.00 |
| `missing_evidence` | 0.06 | 0.05 | 0.03 | **0.10** | 0.05 |
| `missing_evidence_early` | **0.33** | 0.00 | 0.05 | 0.06 | **0.25** |
| `salient_distractor` | **0.17** | 0.00 | 0.09 | 0.09 | 0.06 |

Empty replies, which are missing data and enter no denominator: claude-sonnet-5 2, deepseek-v4-pro-0813 30, gemini-3.8-flash 7, gpt-5.6-terra 1, llama-4-maverick 0.

## Earlier pilot, `missing_evidence` only

The 0.2.0-era pilot, kept because it carries the paired definitive-rate test and the rubric grades that the quick set does not. All 80 items are single-turn, so it says nothing about a fact removed from an earlier turn.

| Assistant | Pairs | Adaptation failure | Spurious shift | Unsafe action | Definitive original → twin | McNemar p |
|---|---|---|---|---|---|---|
| claude-sonnet-5 | 32 | 0.23 (n=22) | 0.05 (n=21) | 0.50 (n=22) | 0.69 → 0.38 | 0.021 |
| deepseek-v4-pro-0813 | 29 | 0.46 (n=28) | 0.03 (n=29) | 0.36 (n=28) | 0.97 → 0.55 | 0.00049 |
| gemini-3.8-flash | 31 | 0.36 (n=28) | 0.00 (n=29) | 0.32 (n=28) | 0.90 → 0.39 | 3.1e-05 |
| llama-4-maverick | 32 | 0.57 (n=28) | 0.07 (n=28) | 0.43 (n=28) | 0.88 → 0.56 | 0.0063 |
| gpt-5.6-terra | 31 | 0.26 (n=27) | 0.04 (n=28) | 0.33 (n=27) | 0.87 → 0.32 | 1.5e-05 |

On the rubric-graded subset, 29 percent of the physicians' criteria overall and 35 to 40 percent on median-materiality-3 twins no longer applied to the twin's reply, which is a statement about rubric-based evaluation rather than about any model.

## Submitting a run

See [`../results/community/README.md`](../results/community/README.md). Regenerate this page with `python tools/results_table.py runs/quick__*`.

