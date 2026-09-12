# Item analysis

Layer `quick`, 319 items over 8 families, evaluated on 5 models (claude-sonnet-5, deepseek-v4-pro, gemini-3.8-flash, gpt-5.6-terra, llama-4-maverick). Every number here is a property of the items, not of a model.

## Discrimination

An item whose primary outcome is the same for every evaluated model separates nothing. `constant` is the share of such items; `item-total r` is the point-biserial correlation between the item's outcome and the model's mean outcome on the rest of the family, averaged over models (higher is better, negative means the item runs against the family).

| family | items | primary outcome | constant | mean item-total r |
|---|---|---|---|---|
| missing_evidence | 40 | decisive question or conditional answer | 0.42 | 0.61 |
| conflicting_evidence | 40 | decisive question or conditional answer | 0.30 | 0.47 |
| buried_red_flag | 40 | escalated when warranted | 0.38 | 0.56 |
| demographic_shift | 40 | necessary update | 0.60 | 0.55 |
| alternative_evidence | 40 | necessary update | 0.55 | 0.34 |
| missing_evidence_early | 39 | decisive question or conditional answer | 0.49 | 0.64 |
| salient_distractor | 40 | stable on control | 0.57 | 0.22 |
| demographic_control | 40 | stable on control | 0.65 | 0.46 |

## Ceiling

An item whose unedited version already draws a forbidden action has no room to show an effect of editing. `original forbidden` is the share of (item, model) cells in that state; the effect is then reported over all items and over the subset where the original was handled correctly.

| family | items | original forbidden | effect, all items | effect, original correct |
|---|---|---|---|---|
| missing_evidence | 40 | 0.07 | +0.198 [+0.101, +0.305] | +0.227 [+0.121, +0.338] (n=39) |
| conflicting_evidence | 40 | 0.10 | +0.311 [+0.211, +0.417] | +0.359 [+0.262, +0.459] (n=38) |
| buried_red_flag | 40 | 0.12 | +0.190 [+0.060, +0.316] | +0.255 [+0.144, +0.369] (n=39) |
| demographic_shift | 40 | 0.06 | +0.100 [+0.040, +0.175] | +0.126 [+0.055, +0.208] (n=40) |
| alternative_evidence | 40 | 0.12 | +0.003 [-0.079, +0.087] | +0.026 [-0.055, +0.115] (n=40) |
| missing_evidence_early | 39 | 0.12 | +0.110 [+0.041, +0.185] | +0.115 [+0.045, +0.187] (n=39) |
| salient_distractor | 40 | 0.10 | +0.009 [-0.033, +0.050] | +0.004 [-0.040, +0.046] (n=40) |
| demographic_control | 40 | 0.08 | -0.001 [-0.043, +0.044] | +0.006 [-0.043, +0.064] (n=40) |

## Items a run needs

Paired items for 80 percent power at two-sided 0.05, from the observed between-item standard deviation of the paired difference. The second column is the family's own effect; the third is a reference effect of 0.10, the smallest difference this benchmark is meant to resolve.

| family | items now | observed effect | sd | n for own effect | n for 0.10 |
|---|---|---|---|---|---|
| missing_evidence | 40 | +0.198 | 0.324 | 22 | 83 |
| conflicting_evidence | 40 | +0.311 | 0.334 | 10 | 88 |
| buried_red_flag | 40 | +0.190 | 0.415 | 38 | 136 |
| demographic_shift | 40 | +0.100 | 0.225 | 40 | 40 |
| alternative_evidence | 40 | +0.003 | 0.259 | 47253 | 53 |
| missing_evidence_early | 39 | +0.110 | 0.225 | 33 | 40 |
| salient_distractor | 40 | +0.009 | 0.128 | 1691 | 13 |
| demographic_control | 40 | -0.001 | 0.136 | 93237 | 15 |

The core layer has between 86 and 1,232 items per family, so the families whose row above asks for more items than the quick layer holds are answerable at full scale; the number is what sets the size of a confirmatory run rather than a reason to read the quick layer differently.


## Is the effect a function of how much text changed

Per family, over items: the relative edit distance between the unedited and edited message against the item's paired effect, and the same edit distance against the annotated materiality. A benchmark that measured the size of the edit would show both columns strongly positive.

| family | items | edit size vs effect (Spearman) | edit size vs materiality | median edit size |
|---|---|---|---|---|
| missing_evidence | 40 | +0.20 | n/a | 0.10 |
| conflicting_evidence | 40 | -0.21 | n/a | 0.19 |
| buried_red_flag | 40 | -0.43 | n/a | 0.25 |
| demographic_shift | 40 | -0.04 | +0.02 | 0.08 |
| alternative_evidence | 40 | +0.17 | n/a | 0.11 |
| missing_evidence_early | 39 | -0.31 | n/a | 0.15 |
| salient_distractor | 40 | +0.16 | n/a | 0.12 |
| demographic_control | 40 | -0.01 | n/a | 0.15 |

The materiality column is `n/a` on the quick layer by construction: it holds only items whose three raters put the edit at the top of the scale, so the label has no variance to correlate with. The effect column is the informative one, and it runs from -0.43 to +0.19 with no family strongly positive.

The paraphrase control is the same check at the level of the design rather than the item: it changes more text than the removal families do (median relative edit distance 0.39 against 0.10) and moves behaviour least, so the ordering of the two controls already runs against an edit-size account.

