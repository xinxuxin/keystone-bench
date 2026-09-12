# Item analysis

Layer `quick`, 303 items over 8 families, evaluated on 5 models (claude-sonnet-5, deepseek-v4-pro, gemini-3.8-flash, gpt-5.6-terra, llama-4-maverick). Every number here is a property of the items, not of a model.

## Discrimination

An item whose primary outcome is the same for every evaluated model separates nothing. `constant` is the share of such items; `item-total r` is the point-biserial correlation between the item's outcome and the model's mean outcome on the rest of the family, averaged over models (higher is better, negative means the item runs against the family).

| family | items | primary outcome | constant | mean item-total r |
|---|---|---|---|---|
| missing_evidence | 40 | decisive question or conditional answer | 0.42 | 0.61 |
| conflicting_evidence | 40 | decisive question or conditional answer | 0.30 | 0.49 |
| buried_red_flag | 40 | escalated when warranted | 0.33 | 0.50 |
| demographic_shift | 40 | necessary update | 0.55 | 0.52 |
| alternative_evidence | 40 | necessary update | 0.55 | 0.34 |
| missing_evidence_early | 23 | decisive question or conditional answer | 0.48 | 0.68 |
| salient_distractor | 40 | stable on control | 0.68 | 0.33 |
| demographic_control | 40 | stable on control | 0.72 | 0.53 |

## Ceiling

An item whose unedited version already draws a forbidden action has no room to show an effect of editing. `original forbidden` is the share of (item, model) cells in that state; the effect is then reported over all items and over the subset where the original was handled correctly.

| family | items | original forbidden | effect, all items | effect, original correct |
|---|---|---|---|---|
| missing_evidence | 40 | 0.08 | +0.185 [+0.091, +0.289] | +0.221 [+0.117, +0.332] (n=39) |
| conflicting_evidence | 40 | 0.11 | +0.331 [+0.230, +0.435] | +0.380 [+0.284, +0.482] (n=38) |
| buried_red_flag | 40 | 0.13 | +0.166 [+0.048, +0.283] | +0.213 [+0.112, +0.325] (n=39) |
| demographic_shift | 40 | 0.11 | +0.049 [-0.010, +0.113] | +0.100 [+0.040, +0.176] (n=40) |
| alternative_evidence | 40 | 0.12 | +0.003 [-0.079, +0.087] | +0.026 [-0.055, +0.115] (n=40) |
| missing_evidence_early | 23 | 0.09 | +0.026 [-0.043, +0.096] | +0.030 [-0.046, +0.108] (n=23) |
| salient_distractor | 40 | 0.10 | -0.006 [-0.046, +0.030] | +0.002 [-0.034, +0.039] (n=40) |
| demographic_control | 40 | 0.08 | -0.011 [-0.058, +0.035] | +0.007 [-0.034, +0.061] (n=40) |

## Items a run needs

Paired items for 80 percent power at two-sided 0.05, from the observed between-item standard deviation of the paired difference. The second column is the family's own effect; the third is a reference effect of 0.10, the smallest difference this benchmark is meant to resolve.

| family | items now | observed effect | sd | n for own effect | n for 0.10 |
|---|---|---|---|---|---|
| missing_evidence | 40 | +0.185 | 0.332 | 26 | 87 |
| conflicting_evidence | 40 | +0.331 | 0.324 | 8 | 83 |
| buried_red_flag | 40 | +0.166 | 0.380 | 42 | 114 |
| demographic_shift | 40 | +0.049 | 0.194 | 125 | 30 |
| alternative_evidence | 40 | +0.003 | 0.259 | 47253 | 53 |
| missing_evidence_early | 23 | +0.026 | 0.180 | 374 | 26 |
| salient_distractor | 40 | -0.006 | 0.125 | 3120 | 13 |
| demographic_control | 40 | -0.011 | 0.143 | 1268 | 17 |

The core layer has between 86 and 1,232 items per family, so the families whose row above asks for more items than the quick layer holds are answerable at full scale; the number is what sets the size of a confirmatory run rather than a reason to read the quick layer differently.

