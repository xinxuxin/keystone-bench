# Criterion validity: materiality against measured behaviour

The other two anchors ask whether our labels agree with something physicians wrote. This one asks whether the label predicts what it claims to predict: on a twin whose edit is material, assistants should behave differently, and on the paraphrase-only twin of the same item they should not. The second half is what makes this a test rather than a correlation, because a label that predicts both sides is tracking how much the text was disturbed rather than whether the evidence still supports the answer.

Sources: reference_records.jsonl, alternative_evidence, buried_red_flag, conflicting_evidence, demographic_control, demographic_shift, missing_evidence, missing_evidence_early, salient_distractor, alternative_evidence, buried_red_flag, conflicting_evidence, demographic_control, demographic_shift, missing_evidence, missing_evidence_early, salient_distractor, alternative_evidence, buried_red_flag, conflicting_evidence, demographic_control, demographic_shift, missing_evidence, missing_evidence_early, salient_distractor, alternative_evidence, buried_red_flag, conflicting_evidence, demographic_control, demographic_shift, missing_evidence, missing_evidence_early, salient_distractor, alternative_evidence, buried_red_flag, conflicting_evidence, demographic_control, demographic_shift, missing_evidence, missing_evidence_early, salient_distractor. Assistants: claude-sonnet-5, deepseek-v4-pro-0813, gemini-3.8-flash, llama-4-maverick, gpt-5.6-terra, claude-sonnet-5, deepseek-v4-pro-0813, gemini-3.8-flash, llama-4-maverick, gpt-5.6-terra. Families with at least ten items: `alternative_evidence`, `buried_red_flag`, `conflicting_evidence`, `demographic_control`, `demographic_shift`, `missing_evidence`, `missing_evidence_early`, `salient_distractor`.

Rates are computed per item across assistants before being averaged, so one item is one observation. Intervals are 95 percent bootstrap over items; empty replies are missing data and enter no denominator.

### `alternative_evidence`

40 items, 5 assistants, 200 records.

#### Dropped commitment, by rubric-blind materiality

Share of assistants that stopped committing, among those that committed on the original. This is the removal families' prediction; where the correct response is a *different* action rather than none, read the next table instead.

| Materiality | Items | On the twin | On the paraphrase (control) | Evidence effect |
|---|---|---|---|---|
| all | 30 | 0.320 [0.182, 0.463] | 0.198 [0.086, 0.324] | 0.122 [0.052, 0.205] |
| 3 | 30 | 0.320 [0.188, 0.464] | 0.198 [0.089, 0.324] | 0.122 [0.045, 0.204] |
| 2 | 0 | | | |
| 1 | 0 | | | |

This layer admits a single materiality, so the rows below `all` are empty and no trend is defined. The `all` row is the comparison the design rests on: the same item, edited two ways.

#### Forbidden action, by rubric-blind materiality

Share of assistants that took an action this twin's own annotation forbids. Defined for every family, so this is the cross-family outcome.

| Materiality | Items | On the twin | On the paraphrase (control) | Evidence effect |
|---|---|---|---|---|
| all | 30 | 0.142 [0.087, 0.202] | 0.155 [0.075, 0.248] | -0.013 [-0.102, 0.070] |
| 3 | 30 | 0.142 [0.088, 0.198] | 0.155 [0.075, 0.247] | -0.013 [-0.102, 0.068] |
| 2 | 0 | | | |
| 1 | 0 | | | |

This layer admits a single materiality, so the rows below `all` are empty and no trend is defined. The `all` row is the comparison the design rests on: the same item, edited two ways.

#### Per assistant

The twin-side rate inside each assistant's own replies, so the result is not one model's behaviour.

| Assistant | Materiality 3 | Materiality 1 | Difference |
|---|---|---|---|
| `claude-sonnet-5` | too few at one end | | |
| `deepseek-v4-pro-0813` | too few at one end | | |
| `gemini-3.8-flash` | too few at one end | | |
| `llama-4-maverick` | too few at one end | | |
| `gpt-5.6-terra` | too few at one end | | |

### `buried_red_flag`

40 items, 5 assistants, 200 records.

#### Dropped commitment, by rubric-blind materiality

Share of assistants that stopped committing, among those that committed on the original. This is the removal families' prediction; where the correct response is a *different* action rather than none, read the next table instead.

| Materiality | Items | On the twin | On the paraphrase (control) | Evidence effect |
|---|---|---|---|---|
| all | 40 | 0.231 [0.129, 0.345] | 0.064 [0.021, 0.118] | 0.167 [0.060, 0.282] |
| 3 | 40 | 0.231 [0.131, 0.341] | 0.064 [0.021, 0.117] | 0.167 [0.057, 0.287] |
| 2 | 0 | | | |
| 1 | 0 | | | |

This layer admits a single materiality, so the rows below `all` are empty and no trend is defined. The `all` row is the comparison the design rests on: the same item, edited two ways.

#### Forbidden action, by rubric-blind materiality

Share of assistants that took an action this twin's own annotation forbids. Defined for every family, so this is the cross-family outcome.

| Materiality | Items | On the twin | On the paraphrase (control) | Evidence effect |
|---|---|---|---|---|
| all | 40 | 0.291 [0.209, 0.384] | 0.125 [0.060, 0.205] | 0.166 [0.049, 0.279] |
| 3 | 40 | 0.291 [0.208, 0.380] | 0.125 [0.060, 0.205] | 0.166 [0.046, 0.279] |
| 2 | 0 | | | |
| 1 | 0 | | | |

This layer admits a single materiality, so the rows below `all` are empty and no trend is defined. The `all` row is the comparison the design rests on: the same item, edited two ways.

#### Per assistant

The twin-side rate inside each assistant's own replies, so the result is not one model's behaviour.

| Assistant | Materiality 3 | Materiality 1 | Difference |
|---|---|---|---|
| `claude-sonnet-5` | too few at one end | | |
| `deepseek-v4-pro-0813` | too few at one end | | |
| `gemini-3.8-flash` | too few at one end | | |
| `llama-4-maverick` | too few at one end | | |
| `gpt-5.6-terra` | too few at one end | | |

### `conflicting_evidence`

40 items, 5 assistants, 200 records.

#### Dropped commitment, by rubric-blind materiality

Share of assistants that stopped committing, among those that committed on the original. This is the removal families' prediction; where the correct response is a *different* action rather than none, read the next table instead.

| Materiality | Items | On the twin | On the paraphrase (control) | Evidence effect |
|---|---|---|---|---|
| all | 23 | 0.416 [0.278, 0.555] | 0.104 [0.028, 0.211] | 0.312 [0.155, 0.459] |
| 3 | 23 | 0.416 [0.274, 0.558] | 0.104 [0.028, 0.211] | 0.312 [0.158, 0.463] |
| 2 | 0 | | | |
| 1 | 0 | | | |

This layer admits a single materiality, so the rows below `all` are empty and no trend is defined. The `all` row is the comparison the design rests on: the same item, edited two ways.

#### Forbidden action, by rubric-blind materiality

Share of assistants that took an action this twin's own annotation forbids. Defined for every family, so this is the cross-family outcome.

| Materiality | Items | On the twin | On the paraphrase (control) | Evidence effect |
|---|---|---|---|---|
| all | 23 | 0.374 [0.272, 0.478] | 0.083 [0.026, 0.152] | 0.291 [0.191, 0.404] |
| 3 | 23 | 0.374 [0.274, 0.480] | 0.083 [0.026, 0.157] | 0.291 [0.189, 0.402] |
| 2 | 0 | | | |
| 1 | 0 | | | |

This layer admits a single materiality, so the rows below `all` are empty and no trend is defined. The `all` row is the comparison the design rests on: the same item, edited two ways.

#### Per assistant

The twin-side rate inside each assistant's own replies, so the result is not one model's behaviour.

| Assistant | Materiality 3 | Materiality 1 | Difference |
|---|---|---|---|
| `claude-sonnet-5` | too few at one end | | |
| `deepseek-v4-pro-0813` | too few at one end | | |
| `gemini-3.8-flash` | too few at one end | | |
| `llama-4-maverick` | too few at one end | | |
| `gpt-5.6-terra` | too few at one end | | |

### `demographic_control`

40 items, 5 assistants, 200 records.

#### Dropped commitment, by rubric-blind materiality

Share of assistants that stopped committing, among those that committed on the original. This is the removal families' prediction; where the correct response is a *different* action rather than none, read the next table instead.

| Materiality | Items | On the twin | On the paraphrase (control) | Evidence effect |
|---|---|---|---|---|
| all | 40 | 0.431 [0.304, 0.561] | 0.209 [0.109, 0.318] | 0.223 [0.096, 0.346] |
| 3 | 0 | | | |
| 2 | 0 | | | |
| 1 | 40 | 0.431 [0.304, 0.561] | 0.209 [0.107, 0.321] | 0.223 [0.100, 0.349] |

This layer admits a single materiality, so the rows below `all` are empty and no trend is defined. The `all` row is the comparison the design rests on: the same item, edited two ways.

#### Forbidden action, by rubric-blind materiality

Share of assistants that took an action this twin's own annotation forbids. Defined for every family, so this is the cross-family outcome.

| Materiality | Items | On the twin | On the paraphrase (control) | Evidence effect |
|---|---|---|---|---|
| all | 40 | 0.101 [0.045, 0.171] | 0.113 [0.058, 0.181] | -0.011 [-0.056, 0.033] |
| 3 | 0 | | | |
| 2 | 0 | | | |
| 1 | 40 | 0.101 [0.045, 0.171] | 0.113 [0.056, 0.181] | -0.011 [-0.056, 0.034] |

This layer admits a single materiality, so the rows below `all` are empty and no trend is defined. The `all` row is the comparison the design rests on: the same item, edited two ways.

#### Per assistant

The twin-side rate inside each assistant's own replies, so the result is not one model's behaviour.

| Assistant | Materiality 3 | Materiality 1 | Difference |
|---|---|---|---|
| `claude-sonnet-5` | too few at one end | | |
| `deepseek-v4-pro-0813` | too few at one end | | |
| `gemini-3.8-flash` | too few at one end | | |
| `llama-4-maverick` | too few at one end | | |
| `gpt-5.6-terra` | too few at one end | | |

### `demographic_shift`

40 items, 5 assistants, 200 records.

#### Dropped commitment, by rubric-blind materiality

Share of assistants that stopped committing, among those that committed on the original. This is the removal families' prediction; where the correct response is a *different* action rather than none, read the next table instead.

| Materiality | Items | On the twin | On the paraphrase (control) | Evidence effect |
|---|---|---|---|---|
| all | 32 | 0.340 [0.216, 0.474] | 0.037 [0.000, 0.087] | 0.304 [0.165, 0.440] |
| 3 | 32 | 0.340 [0.221, 0.469] | 0.037 [0.000, 0.086] | 0.304 [0.160, 0.443] |
| 2 | 0 | | | |
| 1 | 0 | | | |

This layer admits a single materiality, so the rows below `all` are empty and no trend is defined. The `all` row is the comparison the design rests on: the same item, edited two ways.

#### Forbidden action, by rubric-blind materiality

Share of assistants that took an action this twin's own annotation forbids. Defined for every family, so this is the cross-family outcome.

| Materiality | Items | On the twin | On the paraphrase (control) | Evidence effect |
|---|---|---|---|---|
| all | 32 | 0.108 [0.064, 0.158] | 0.050 [0.019, 0.088] | 0.058 [0.006, 0.114] |
| 3 | 32 | 0.108 [0.064, 0.158] | 0.050 [0.019, 0.088] | 0.058 [0.006, 0.111] |
| 2 | 0 | | | |
| 1 | 0 | | | |

This layer admits a single materiality, so the rows below `all` are empty and no trend is defined. The `all` row is the comparison the design rests on: the same item, edited two ways.

#### Per assistant

The twin-side rate inside each assistant's own replies, so the result is not one model's behaviour.

| Assistant | Materiality 3 | Materiality 1 | Difference |
|---|---|---|---|
| `claude-sonnet-5` | too few at one end | | |
| `deepseek-v4-pro-0813` | too few at one end | | |
| `gemini-3.8-flash` | too few at one end | | |
| `llama-4-maverick` | too few at one end | | |
| `gpt-5.6-terra` | too few at one end | | |

### `missing_evidence`

117 items, 10 assistants, 600 records.

#### Dropped commitment, by rubric-blind materiality

Share of assistants that stopped committing, among those that committed on the original. This is the removal families' prediction; where the correct response is a *different* action rather than none, read the next table instead.

| Materiality | Items | On the twin | On the paraphrase (control) | Evidence effect |
|---|---|---|---|---|
| all | 75 | 0.351 [0.273, 0.433] | 0.061 [0.019, 0.114] | 0.290 [0.201, 0.373] |
| 3 | 34 | 0.520 [0.414, 0.626] | 0.064 [0.012, 0.133] | 0.456 [0.336, 0.574] |
| 2 | 30 | 0.227 [0.121, 0.341] | 0.034 [0.000, 0.103] | 0.193 [0.101, 0.298] |
| 1 | 11 | 0.130 [0.000, 0.315] | 0.139 [0.000, 0.361] | -0.009 [-0.306, 0.269] |

Trend over items: rho 0.482 on the twin (p <5e-05) against 0.038 on the control (p 0.76). Evidence effect at materiality 3 minus 1: 0.466 [0.169, 0.793].

#### Forbidden action, by rubric-blind materiality

Share of assistants that took an action this twin's own annotation forbids. Defined for every family, so this is the cross-family outcome.

| Materiality | Items | On the twin | On the paraphrase (control) | Evidence effect |
|---|---|---|---|---|
| all | 75 | 0.411 [0.242, 0.589] | 0.074 [0.011, 0.168] | 0.337 [0.168, 0.505] |
| 3 | 34 | 0.411 [0.242, 0.589] | 0.074 [0.011, 0.168] | 0.337 [0.179, 0.516] |
| 2 | 30 | n/a | n/a | n/a  |
| 1 | 11 | n/a | n/a | n/a  |

Trend over items: rho 0.000 on the twin (p 1) against 0.000 on the control (p 1). 

#### Per assistant

The twin-side rate inside each assistant's own replies, so the result is not one model's behaviour.

| Assistant | Materiality 3 | Materiality 1 | Difference |
|---|---|---|---|
| `claude-sonnet-5` | 0.545 (n=11) | 0.143 (n=7) | 0.403 |
| `deepseek-v4-pro-0813` | 0.500 (n=14) | 0.125 (n=8) | 0.375 |
| `gemini-3.8-flash` | 0.643 (n=14) | 0.000 (n=9) | 0.643 |
| `llama-4-maverick` | 0.429 (n=14) | 0.222 (n=9) | 0.206 |
| `gpt-5.6-terra` | 0.750 (n=12) | 0.000 (n=6) | 0.750 |
| `claude-sonnet-5` | too few at one end | | |
| `deepseek-v4-pro-0813` | too few at one end | | |
| `gemini-3.8-flash` | too few at one end | | |
| `llama-4-maverick` | too few at one end | | |
| `gpt-5.6-terra` | too few at one end | | |

On the 24 items whose replies were also rubric-graded, the share of the physicians' criteria the applicability judge ruled no longer judgeable tracks the same label at rho 0.513 (p 0.01).

### `missing_evidence_early`

23 items, 5 assistants, 115 records.

#### Dropped commitment, by rubric-blind materiality

Share of assistants that stopped committing, among those that committed on the original. This is the removal families' prediction; where the correct response is a *different* action rather than none, read the next table instead.

| Materiality | Items | On the twin | On the paraphrase (control) | Evidence effect |
|---|---|---|---|---|
| all | 23 | 0.360 [0.225, 0.501] | 0.167 [0.071, 0.283] | 0.193 [0.071, 0.327] |
| 3 | 23 | 0.360 [0.227, 0.505] | 0.167 [0.073, 0.283] | 0.193 [0.070, 0.320] |
| 2 | 0 | | | |
| 1 | 0 | | | |

This layer admits a single materiality, so the rows below `all` are empty and no trend is defined. The `all` row is the comparison the design rests on: the same item, edited two ways.

#### Forbidden action, by rubric-blind materiality

Share of assistants that took an action this twin's own annotation forbids. Defined for every family, so this is the cross-family outcome.

| Materiality | Items | On the twin | On the paraphrase (control) | Evidence effect |
|---|---|---|---|---|
| all | 23 | 0.165 [0.087, 0.270] | 0.139 [0.070, 0.217] | 0.026 [-0.043, 0.096] |
| 3 | 23 | 0.165 [0.078, 0.261] | 0.139 [0.070, 0.217] | 0.026 [-0.043, 0.104] |
| 2 | 0 | | | |
| 1 | 0 | | | |

This layer admits a single materiality, so the rows below `all` are empty and no trend is defined. The `all` row is the comparison the design rests on: the same item, edited two ways.

#### Per assistant

The twin-side rate inside each assistant's own replies, so the result is not one model's behaviour.

| Assistant | Materiality 3 | Materiality 1 | Difference |
|---|---|---|---|
| `claude-sonnet-5` | too few at one end | | |
| `deepseek-v4-pro-0813` | too few at one end | | |
| `gemini-3.8-flash` | too few at one end | | |
| `llama-4-maverick` | too few at one end | | |
| `gpt-5.6-terra` | too few at one end | | |

### `salient_distractor`

40 items, 5 assistants, 200 records.

#### Dropped commitment, by rubric-blind materiality

Share of assistants that stopped committing, among those that committed on the original. This is the removal families' prediction; where the correct response is a *different* action rather than none, read the next table instead.

| Materiality | Items | On the twin | On the paraphrase (control) | Evidence effect |
|---|---|---|---|---|
| all | 40 | 0.175 [0.096, 0.263] | 0.118 [0.052, 0.197] | 0.056 [0.007, 0.112] |
| 3 | 0 | | | |
| 2 | 0 | | | |
| 1 | 40 | 0.175 [0.096, 0.263] | 0.118 [0.052, 0.193] | 0.056 [0.006, 0.114] |

This layer admits a single materiality, so the rows below `all` are empty and no trend is defined. The `all` row is the comparison the design rests on: the same item, edited two ways.

#### Forbidden action, by rubric-blind materiality

Share of assistants that took an action this twin's own annotation forbids. Defined for every family, so this is the cross-family outcome.

| Materiality | Items | On the twin | On the paraphrase (control) | Evidence effect |
|---|---|---|---|---|
| all | 40 | 0.101 [0.055, 0.156] | 0.109 [0.058, 0.166] | -0.007 [-0.049, 0.030] |
| 3 | 0 | | | |
| 2 | 0 | | | |
| 1 | 40 | 0.101 [0.055, 0.156] | 0.109 [0.059, 0.165] | -0.007 [-0.045, 0.030] |

This layer admits a single materiality, so the rows below `all` are empty and no trend is defined. The `all` row is the comparison the design rests on: the same item, edited two ways.

#### Per assistant

The twin-side rate inside each assistant's own replies, so the result is not one model's behaviour.

| Assistant | Materiality 3 | Materiality 1 | Difference |
|---|---|---|---|
| `claude-sonnet-5` | too few at one end | | |
| `deepseek-v4-pro-0813` | too few at one end | | |
| `gemini-3.8-flash` | too few at one end | | |
| `llama-4-maverick` | too few at one end | | |
| `gpt-5.6-terra` | too few at one end | | |

## Reading

The label earns its name where the twin column rises with materiality while the paraphrase column stays flat. Read the evidence-effect column first, then the per-assistant table to check that no single model carries it.

`Forbidden action` is the outcome to compare across families: dropping a commitment is the right response only where the evidence went missing, while taking an action the annotation forbids is wrong everywhere.

Limits. Every classification here is a model's, from one judge family. A label that predicts behaviour is still a label a model wrote: the release stays `tier: silver`, and `gold` is the tier a clinician-confirmed row carries.

