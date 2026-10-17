# Falsification against the physicians' ideal answers

HealthBench ships a physician-written ideal answer for most of its conversations. No Keystone label was produced from it, so it can test the annotations rather than make them. **Engagement** is the share of the edited span's own content terms, meaning terms that appear in the span and nowhere else in the conversation, that also appear in the physicians' answer to the unedited message, each term weighted by how rare it is across all ideal answers so that shared clinical vocabulary earns no credit. The null draws the comparison answer from **other sources in the same HealthBench theme**: a term counts only if physicians writing on the same theme did not use it anyway. No model is called.

Coverage: 1036 of 1234 released sources carry an ideal answer, across 5 themes; 4642 twins scored, 1538 skipped because the edit introduced or removed no term unique to it. Null: 25 draws per twin, intervals 95 percent bootstrap over twins.

## Removal families: does the physicians' answer use the fact the twin removes

These families take a fact out of the message or replace its value, so the fact was there when the physicians wrote. `Opening third` repeats the measure against only the first third of the answer, where physicians put what decides the case.

| Family | Twins | Engagement | Same-theme null | Difference [95%] | Above null | Uniform-null difference | Opening third [95%] |
|---|---|---|---|---|---|---|---|
| `alternative_evidence` | 145 | 0.222 | 0.045 | 0.177 [0.114, 0.240] | 0.23 | 0.177 | 0.146 [0.091, 0.206] |
| `demographic_shift` | 81 | 0.389 | 0.180 | 0.209 [0.103, 0.316] | 0.40 | 0.212 | 0.200 [0.105, 0.295] |
| `missing_evidence` | 732 | 0.483 | 0.060 | 0.423 [0.391, 0.455] | 0.58 | 0.433 | 0.357 [0.324, 0.390] |
| `missing_evidence_early` | 121 | 0.263 | 0.057 | 0.206 [0.137, 0.277] | 0.32 | 0.213 | 0.137 [0.076, 0.200] |

## Insertion families: reported, not predicted

These add text that did not exist when the physicians answered, so low engagement is the expected reading and says nothing about whether the insertion is load-bearing on the twin. For the two controls the number that matters is the contrast below.

| Family | Twins | Engagement | Same-theme null | Difference [95%] | Above null | Uniform-null difference | Opening third [95%] |
|---|---|---|---|---|---|---|---|
| `buried_red_flag` | 697 | 0.047 | 0.024 | 0.023 [0.016, 0.030] | 0.26 | 0.023 | 0.006 [0.002, 0.010] |
| `conflicting_evidence` | 1030 | 0.097 | 0.029 | 0.068 [0.058, 0.077] | 0.39 | 0.070 | 0.031 [0.026, 0.038] |
| `demographic_control` | 805 | 0.022 | 0.014 | 0.008 [0.003, 0.014] | 0.09 | 0.008 | 0.003 [-0.001, 0.007] |
| `salient_distractor` | 1031 | 0.017 | 0.020 | -0.004 [-0.008, 0.001] | 0.09 | -0.002 | -0.004 [-0.006, -0.002] |

## Is the negative control engaged with less than the load-bearing edit

Within a source: the same physicians' answer, the control's insertion against the load-bearing edit's span.

| Control | Compared with | Sources | Mean difference [95%] | Control lower on |
|---|---|---|---|---|
| `salient_distractor` | `missing_evidence` | 732 | -0.426 [-0.457, -0.393] | 0.73 |
| `salient_distractor` | `conflicting_evidence` | 1029 | -0.071 [-0.083, -0.061] | 0.57 |
| `demographic_control` | `missing_evidence` | 572 | -0.420 [-0.457, -0.382] | 0.68 |
| `demographic_control` | `conflicting_evidence` | 802 | -0.058 [-0.071, -0.047] | 0.50 |

## Engagement by materiality, within the removal families

Only the removal families can answer this: an insertion is absent from the original by construction, so pooling the families inverts the comparison rather than testing it.

| Family | Materiality 3 | Materiality 2 | Materiality 1 |
|---|---|---|---|
| `alternative_evidence` | 0.165 [0.093, 0.247] (n=96) | 6 twins, too few | 1 twins, too few |
| `demographic_shift` | 0.201 [0.016, 0.397] (n=28) | 0.332 [0.086, 0.582] (n=13) | 4 twins, too few |
| `missing_evidence` | 0.475 [0.405, 0.547] (n=146) | 0.421 [0.356, 0.481] (n=187) | 0.329 [0.237, 0.421] (n=84) |
| `missing_evidence_early` | 0.191 [0.080, 0.316] (n=36) | 0.210 [0.115, 0.311] (n=64) | 0.219 [0.059, 0.394] (n=21) |

Pooled over the removal families: materiality 3 sits at 0.319 [0.269, 0.369] above the same-theme null against 0.297 [0.223, 0.383] for materiality 1.

## Reading

**Load-bearing, supported.** The removal families engage with the physicians' own answer above a null drawn from the same clinical theme, with rare terms carrying the weight. The fact these twins remove is one the physicians' answer to the unedited message uses, and the text carrying that verdict was never shown to any Keystone rater.

**Controls, supported.** Both negative controls sit far below their own source's load-bearing edit on the same answer. An insertion the physicians engage with as much as the removed fact would not be a control; neither of ours is.

**Materiality is tested in [`BEHAVIOUR_ANCHOR.md`](BEHAVIOUR_ANCHOR.md), not here.** Engagement asks whether the physicians' answer *mentions* the fact. Materiality claims something stronger, that removing it changes what a safe reply may commit to, and word overlap cannot see a change in commitment. The criterion-validity page tests that claim directly against measured model behaviour. Read this page for whether the edits reach what the physicians wrote about, and that one for whether the label means what it says.

**Limits.** Overlap misses a fact the physicians address in other words, ideal answers cover 1036 of 1234 sources, and nothing here bounds whether an edit changes the correct action. It is a falsification instrument rather than adjudication, which is the distinction the `silver` and `gold` tiers carry.

