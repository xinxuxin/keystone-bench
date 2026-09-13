# The instability floor

The same model, the same request, asked again. At temperature 0 a served model is still not deterministic, so an outcome flips at some rate for no reason at all, and that rate is the floor any paired effect has to clear. Produced by `keystone run --repeat N`, which re-asks the identical request under a different cache key; the judge and the prompts are unchanged.

Models: gemini-3.8-flash, llama-4-maverick.

## Flip rate of the forbidden-action verdict between two identical requests

Per family, over items and the three conditions: the share of (item, condition) cells whose verdict differs between two runs of the same request. `paired floor` is the same quantity expressed the way an effect is: the mean absolute difference of the twin-minus-control contrast between two identical runs.

`spurious effect` is the contrast a re-run produces on its own: the twin-minus-control difference computed with the twin from one run and the control from another, which has no real effect in it and should sit on zero. `noise size` is the mean absolute difference of that contrast between runs, which is the scale of the wobble rather than a bias.

| family | model | cells | flip rate | spurious effect | noise size | measured effect |
|---|---|---|---|---|---|---|
| missing_evidence | gemini-3.8-flash | 360 | 0.089 | -0.033 [-0.071, +0.004] | 0.183 | +0.225 [+0.075, +0.400] |
| conflicting_evidence | gemini-3.8-flash | 358 | 0.123 | +0.008 [-0.042, +0.059] | 0.305 | +0.359 [+0.179, +0.538] |
| buried_red_flag | gemini-3.8-flash | 360 | 0.089 | +0.008 [-0.025, +0.042] | 0.150 | -0.025 [-0.175, +0.125] |
| salient_distractor | gemini-3.8-flash | 356 | 0.090 | -0.042 [-0.089, +0.000] | 0.186 | +0.077 [-0.051, +0.231] |
| demographic_control | gemini-3.8-flash | 356 | 0.065 | -0.004 [-0.034, +0.026] | 0.112 | +0.053 [-0.053, +0.158] |
| missing_evidence | llama-4-maverick | 360 | 0.083 | +0.025 [-0.017, +0.067] | 0.183 | +0.200 [+0.025, +0.375] |
| conflicting_evidence | llama-4-maverick | 360 | 0.072 | -0.042 [-0.079, -0.008] | 0.167 | +0.600 [+0.425, +0.775] |
| buried_red_flag | llama-4-maverick | 360 | 0.122 | -0.017 [-0.062, +0.025] | 0.250 | +0.425 [+0.200, +0.625] |
| salient_distractor | llama-4-maverick | 360 | 0.083 | +0.000 [-0.042, +0.037] | 0.200 | -0.075 [-0.200, +0.050] |
| demographic_control | llama-4-maverick | 360 | 0.122 | +0.058 [+0.013, +0.113] | 0.250 | -0.050 [-0.175, +0.075] |

## What it means for each family

| family | mean flip rate | mean spurious effect | mean noise size | mean measured effect |
|---|---|---|---|---|
| missing_evidence | 0.086 | -0.004 | 0.183 | +0.213 |
| conflicting_evidence | 0.098 | -0.017 | 0.236 | +0.479 |
| buried_red_flag | 0.106 | -0.004 | 0.200 | +0.200 |
| salient_distractor | 0.087 | -0.021 | 0.193 | +0.001 |
| demographic_control | 0.093 | +0.027 | 0.181 | +0.001 |

## Reading

The instability is real and it is the size other people report. Re-asking the identical request flips the forbidden-action verdict on 6.5 to 12.3 percent of cells, against the 8.7 percent an external re-sampling study measures on unedited clinical cases ([arXiv:2609.03221](https://arxiv.org/abs/2609.03221)). A single unpaired comparison at this scale would be reporting noise.

It does not survive pairing. The contrast a re-run produces on its own, built by taking the twin from one run and the control from another, is within 0.058 of zero on every family though not every family's interval clears zero. Noise at temperature 0 is two-sided: it moves the twin side and the control side alike, and the paired difference cancels it. The measured effects on the same items are +0.21 and +0.48 on the two headline families (`missing_evidence`, `conflicting_evidence`), 4 to 8 times the largest spurious contrast.

The one to watch is `demographic_control` at +0.058 [+0.013, +0.113]. It is the largest spurious contrast in the table, it is positive, and unlike most rows its own interval excludes zero; a bias of this sign would if anything overstate a real effect on that family. The measured effect there is -0.050 [-0.175, +0.075], which does contain zero, so the measured effect for this family is not distinguishable from no effect even though this particular noise estimate is.

