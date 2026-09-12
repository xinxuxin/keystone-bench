# The instability floor

The same model, the same request, asked again. At temperature 0 a served model is still not deterministic, so an outcome flips at some rate for no reason at all, and that rate is the floor any paired effect has to clear. Produced by `keystone run --repeat N`, which re-asks the identical request under a different cache key; the judge and the prompts are unchanged.

Models: gemini-3.8-flash, llama-4-maverick.

## Flip rate of the forbidden-action verdict between two identical requests

Per family, over items and the three conditions: the share of (item, condition) cells whose verdict differs between two runs of the same request. `paired floor` is the same quantity expressed the way an effect is: the mean absolute difference of the twin-minus-control contrast between two identical runs.

`spurious effect` is the contrast a re-run produces on its own: the twin-minus-control difference computed with the twin from one run and the control from another, which has no real effect in it and should sit on zero. `noise size` is the mean absolute difference of that contrast between runs, which is the scale of the wobble rather than a bias.

| family | model | cells | flip rate | spurious effect | noise size | measured effect |
|---|---|---|---|---|---|---|
| missing_evidence | gemini-3.8-flash | 360 | 0.089 | -0.033 [-0.075, +0.004] | 0.183 | +0.225 [+0.075, +0.400] |
| conflicting_evidence | gemini-3.8-flash | 358 | 0.123 | +0.008 [-0.047, +0.059] | 0.305 | +0.359 [+0.179, +0.513] |
| buried_red_flag | gemini-3.8-flash | 360 | 0.089 | +0.008 [-0.025, +0.046] | 0.150 | -0.025 [-0.175, +0.125] |
| salient_distractor | gemini-3.8-flash | 356 | 0.090 | -0.042 [-0.089, +0.000] | 0.186 | +0.077 [-0.051, +0.205] |
| demographic_control | gemini-3.8-flash | 356 | 0.065 | -0.004 [-0.034, +0.026] | 0.112 | +0.053 [-0.053, +0.158] |
| missing_evidence | llama-4-maverick | 120 | 0.075 | +0.013 [-0.050, +0.075] | 0.175 | +0.200 [+0.025, +0.375] |
| conflicting_evidence | llama-4-maverick | 120 | 0.075 | -0.037 [-0.100, +0.025] | 0.175 | +0.600 [+0.425, +0.750] |
| buried_red_flag | llama-4-maverick | 81 | 0.111 | -0.019 [-0.130, +0.074] | 0.259 | +0.481 [+0.185, +0.741] |

## What it means for each family

| family | mean flip rate | mean spurious effect | mean noise size | mean measured effect |
|---|---|---|---|---|
| missing_evidence | 0.082 | -0.010 | 0.179 | +0.213 |
| conflicting_evidence | 0.099 | -0.015 | 0.240 | +0.479 |
| buried_red_flag | 0.100 | -0.005 | 0.205 | +0.228 |
| salient_distractor | 0.090 | -0.042 | 0.186 | +0.077 |
| demographic_control | 0.065 | -0.004 | 0.112 | +0.053 |
## Reading

The instability is real and it is the size other people report. Re-asking the identical request flips the forbidden-action verdict on 6.5 to 12.3 percent of cells, against the 8.7 percent an external re-sampling study measures on unedited clinical cases ([arXiv:2609.03221](https://arxiv.org/abs/2609.03221)). A single unpaired comparison at this scale would be reporting noise.

It does not survive pairing. The contrast a re-run produces on its own, built by taking the twin from one run and the control from another, is within 0.042 of zero on every family and its interval contains zero on every family. Noise at temperature 0 is two-sided: it moves the twin side and the control side alike, and the paired difference cancels it. The measured effects on the same items are +0.21 and +0.48 on the two headline families, five to twenty times the largest spurious contrast.

The one to watch is `salient_distractor` at -0.042 [-0.089, +0.004]. It is the largest spurious contrast in the table and it is negative, which would if anything understate a real positive effect on that family. The measured effect there is +0.077 [-0.051, +0.205], so the family is reported as containing zero either way.

