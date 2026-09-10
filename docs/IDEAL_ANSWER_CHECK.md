# Falsification against the physicians' ideal answers

HealthBench ships a physician-written ideal answer for most of its conversations. No Keystone label was produced from it, so it can test the annotations rather than make them. **Engagement** is the share of the edited span's own content terms, meaning terms that appear in the span and nowhere else in the conversation, that also appear in the physicians' answer to the unedited message, each term weighted by how rare it is across all ideal answers so that shared clinical vocabulary earns no credit. The null draws the comparison answer from **other sources in the same HealthBench theme**: a term counts only if physicians writing on the same theme did not use it anyway. No model is called.

Coverage: 1038 of 1236 released sources carry an ideal answer, across 5 themes; 4651 twins scored, 1542 skipped because the edit introduced or removed no term unique to it. Null: 25 draws per twin, intervals 95 percent bootstrap over twins.

## Removal families: does the physicians' answer use the fact the twin removes

These families take a fact out of the message or replace its value, so the fact was there when the physicians wrote. `Opening third` repeats the measure against only the first third of the answer, where physicians put what decides the case.

| Family | Twins | Engagement | Same-theme null | Difference [95%] | Above null | Uniform-null difference | Opening third [95%] |
|---|---|---|---|---|---|---|---|
| `alternative_evidence` | 145 | 0.222 | 0.045 | 0.177 [0.115, 0.240] | 0.23 | 0.178 | 0.145 [0.091, 0.205] |
| `demographic_shift` | 81 | 0.389 | 0.159 | 0.230 [0.128, 0.333] | 0.40 | 0.202 | 0.198 [0.104, 0.293] |
| `missing_evidence` | 733 | 0.484 | 0.060 | 0.424 [0.391, 0.455] | 0.59 | 0.431 | 0.358 [0.326, 0.391] |
| `missing_evidence_early` | 121 | 0.263 | 0.062 | 0.201 [0.130, 0.272] | 0.32 | 0.221 | 0.141 [0.082, 0.204] |

## Insertion families: reported, not predicted

These add text that did not exist when the physicians answered, so low engagement is the expected reading and says nothing about whether the insertion is load-bearing on the twin. For the two controls the number that matters is the contrast below.

| Family | Twins | Engagement | Same-theme null | Difference [95%] | Above null | Uniform-null difference | Opening third [95%] |
|---|---|---|---|---|---|---|---|
| `buried_red_flag` | 699 | 0.052 | 0.026 | 0.026 [0.019, 0.034] | 0.30 | 0.027 | 0.005 [0.001, 0.009] |
| `conflicting_evidence` | 1032 | 0.096 | 0.030 | 0.066 [0.057, 0.075] | 0.38 | 0.069 | 0.032 [0.026, 0.039] |
| `demographic_control` | 807 | 0.017 | 0.011 | 0.007 [0.002, 0.013] | 0.07 | 0.007 | 0.002 [-0.001, 0.005] |
| `salient_distractor` | 1033 | 0.014 | 0.021 | -0.007 [-0.010, -0.003] | 0.07 | -0.006 | -0.007 [-0.008, -0.004] |

## Is the negative control engaged with less than the load-bearing edit

Within a source: the same physicians' answer, the control's insertion against the load-bearing edit's span.

| Control | Compared with | Sources | Mean difference [95%] | Control lower on |
|---|---|---|---|---|
| `salient_distractor` | `missing_evidence` | 733 | -0.431 [-0.463, -0.399] | 0.73 |
| `salient_distractor` | `conflicting_evidence` | 1031 | -0.073 [-0.083, -0.063] | 0.56 |
| `demographic_control` | `missing_evidence` | 573 | -0.423 [-0.461, -0.386] | 0.67 |
| `demographic_control` | `conflicting_evidence` | 804 | -0.057 [-0.069, -0.046] | 0.47 |

## Engagement by materiality, within the removal families

Only the removal families can answer this: an insertion is absent from the original by construction, so pooling the families inverts the comparison rather than testing it.

| Family | Materiality 3 | Materiality 2 | Materiality 1 |
|---|---|---|---|
| `alternative_evidence` | 0.164 [0.094, 0.245] (n=96) | 6 twins, too few | 1 twins, too few |
| `demographic_shift` | 0.233 [0.060, 0.423] (n=28) | 0.326 [0.114, 0.545] (n=13) | 4 twins, too few |
| `missing_evidence` | 0.480 [0.410, 0.551] (n=146) | 0.419 [0.353, 0.478] (n=187) | 0.322 [0.234, 0.410] (n=84) |
| `missing_evidence_early` | 0.186 [0.080, 0.307] (n=36) | 0.202 [0.107, 0.305] (n=64) | 0.221 [0.060, 0.396] (n=21) |

Pooled over the removal families: materiality 3 sits at 0.324 [0.274, 0.372] above the same-theme null against 0.291 [0.219, 0.376] for materiality 1.

## Reading

**Load-bearing, supported.** The removal families engage with the physicians' own answer above a null drawn from the same clinical theme, with rare terms carrying the weight. The fact these twins remove is one the physicians' answer to the unedited message uses, and the text carrying that verdict was never shown to any Keystone rater.

**Controls, supported.** Both negative controls sit far below their own source's load-bearing edit on the same answer. An insertion the physicians engage with as much as the removed fact would not be a control; neither of ours is.

**Materiality is tested in [`BEHAVIOUR_ANCHOR.md`](BEHAVIOUR_ANCHOR.md), not here.** Engagement asks whether the physicians' answer *mentions* the fact. Materiality claims something stronger, that removing it changes what a safe reply may commit to, and word overlap cannot see a change in commitment. The criterion-validity page tests that claim directly against measured model behaviour. Read this page for whether the edits reach what the physicians wrote about, and that one for whether the label means what it says.

**Limits.** Overlap misses a fact the physicians address in other words, ideal answers cover 1038 of 1236 sources, and nothing here bounds whether an edit changes the correct action. It is a falsification instrument rather than adjudication, which is the distinction the `silver` and `gold` tiers carry.

