# Results

Every family is reported on the outcome it was designed around, because the families ask for different behaviour: a removal asks the assistant to seek what is missing, an alternative value asks it to change the action, a buried red flag asks it to escalate, and a negative control asks it to do nothing differently. One outcome, **forbidden action**, is defined for every family against that twin's own annotation, so it is the one that compares across them. A row is comparable with another row of the same family, layer and benchmark version, and only if its paraphrase control held.

## Quick set, 5 assistants, 8 families

Benchmark 0.5.0, layer `quick`, judge `gpt-4.1`, temperature 0.0, 1500 output tokens, generated 2026-09-12. The quick set is 40 twins per family from the dev split, each with its original, its twin and its paraphrase-only control.

### What each family asks for

| Family | The behaviour it asks for | claude-sonnet-5 | deepseek-v4-pro-0813 | gemini-3.8-flash | gpt-5.6-terra | llama-4-maverick |
|---|---|---|---|---|---|---|
| `alternative_evidence` | changed the action to the one the new value supports | 0.90 | 0.90 | 0.79 | 0.80 | 0.71 |
| `buried_red_flag` | made urgent evaluation the main answer | 0.50 | 0.67 | 0.72 | 0.82 | 0.28 |
| `conflicting_evidence` | named the contradiction and asked which side is true | 0.34 | 0.32 | 0.22 | 0.26 | 0.16 |
| `demographic_control` | answered unchanged despite the tempting attribute | 0.72 | 0.72 | 0.72 | 0.80 | 0.65 |
| `demographic_shift` | adjusted the advice to the changed attribute | 0.97 | 0.87 | 0.90 | 0.90 | 0.58 |
| `missing_evidence` | asked the question that settles it, or answered conditionally on it | 0.63 | 0.52 | 0.34 | 0.66 | 0.17 |
| `missing_evidence_early` | same, with the fact removed from an earlier turn | 0.48 | 0.38 | 0.24 | 0.57 | 0.29 |
| `salient_distractor` | answered unchanged despite the irrelevant insertion | 0.75 | 0.85 | 0.70 | 0.85 | 0.62 |

### Forbidden action, the cross-family outcome

The share of replies to the twin that take an action the twin's own annotation rules out. Lower is better everywhere, and unlike the table above it means the same thing in every row.

| Family | claude-sonnet-5 | deepseek-v4-pro-0813 | gemini-3.8-flash | gpt-5.6-terra | llama-4-maverick |
|---|---|---|---|---|---|
| `alternative_evidence` | 0.07 (n=40) | 0.10 (n=39) | 0.18 (n=38) | 0.15 (n=39) | 0.25 (n=40) |
| `buried_red_flag` | 0.39 (n=38) | 0.33 (n=36) | 0.17 (n=40) | 0.15 (n=40) | 0.57 (n=40) |
| `conflicting_evidence` | 0.33 (n=40) | 0.31 (n=36) | 0.36 (n=39) | 0.40 (n=40) | 0.68 (n=40) |
| `demographic_control` | n/a | n/a | n/a | n/a | n/a |
| `demographic_shift` | 0.05 (n=39) | 0.12 (n=40) | 0.08 (n=39) | 0.10 (n=39) | 0.40 (n=40) |
| `missing_evidence` | 0.28 (n=40) | 0.32 (n=38) | 0.28 (n=39) | 0.20 (n=40) | 0.40 (n=40) |
| `missing_evidence_early` | 0.35 (n=23) | 0.35 (n=23) | 0.35 (n=23) | 0.22 (n=23) | 0.26 (n=23) |
| `salient_distractor` | n/a | n/a | n/a | n/a | n/a |

### The paraphrase control

Reworded, no evidence changed. A run whose spurious shift exceeds 0.10 on a family does not support attributing that family's effect to the perturbation.

| Family | claude-sonnet-5 | deepseek-v4-pro-0813 | gemini-3.8-flash | gpt-5.6-terra | llama-4-maverick |
|---|---|---|---|---|---|
| `alternative_evidence` | **0.33** | **0.14** | **0.13** | **0.11** | **0.12** |
| `buried_red_flag` | 0.04 | **0.12** | **0.16** | **0.20** | **0.13** |
| `conflicting_evidence` | **0.24** | **0.24** | **0.12** | 0.08 | **0.15** |
| `demographic_control` | **0.11** | 0.05 | **0.11** | 0.06 | **0.16** |
| `demographic_shift` | 0.08 | 0.00 | 0.04 | 0.08 | 0.04 |
| `missing_evidence` | 0.04 | 0.03 | 0.07 | 0.04 | **0.13** |
| `missing_evidence_early` | **0.44** | **0.23** | **0.17** | 0.10 | **0.25** |
| `salient_distractor` | **0.12** | 0.07 | 0.07 | 0.08 | **0.12** |

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

On the rubric-graded subset, 35 to 40 percent of the physicians' criteria no longer applied to the twin's reply, which is a statement about rubric-based evaluation rather than about any model.

## Submitting a run

See [`../results/community/README.md`](../results/community/README.md). Regenerate this page with `python tools/results_table.py runs/quick__*`.


## The checks this table is read against

Every number above is one judge (GPT-4.1) on one layer. Five separate pages say how far it travels.

| check | what it asks | where |
|---|---|---|
| Judge panel | do the same replies score the same under Claude Sonnet and Gemini Flash, and with the model's own vendor removed from its judging | [`JUDGE_PANEL.md`](JUDGE_PANEL.md) |
| Instability floor | how much of a paired contrast a re-run of the identical request produces on its own | [`INSTABILITY_FLOOR.md`](INSTABILITY_FLOOR.md) |
| Item analysis | discrimination, the ceiling from items already mishandled unedited, the item count a confirmatory run needs, and whether the effect tracks the size of the edit | [`ITEM_ANALYSIS.md`](ITEM_ANALYSIS.md) |
| Shortcut audit | how detectable each edit is, what the edits repeat, and what a policy that never reads the evidence could score | [`SHORTCUT_AUDIT.md`](SHORTCUT_AUDIT.md) |
| Intervention | whether a minimal instruction lowers unsupported action without buying it with blind caution | [`INTERVENTION.md`](INTERVENTION.md) |

