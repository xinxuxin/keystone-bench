# The instability floor

The same model, the same request, asked again. At temperature 0 a served model is still not deterministic, so an outcome flips at some rate for no reason at all, and that rate is the floor any paired effect has to clear. Produced by `keystone run --repeat N`, which re-asks the identical request under a different cache key; the judge and the prompts are unchanged.

Models: gemini-3.8-flash.

## Flip rate of the forbidden-action verdict between two identical requests

Per family, over items and the three conditions: the share of (item, condition) cells whose verdict differs between two runs of the same request. `paired floor` is the same quantity expressed the way an effect is: the mean absolute difference of the twin-minus-control contrast between two identical runs.

`spurious effect` is the contrast a re-run produces on its own: the twin-minus-control difference computed with the twin from one run and the control from another, which has no real effect in it and should sit on zero. `noise size` is the mean absolute difference of that contrast between runs, which is the scale of the wobble rather than a bias.

| family | model | cells | flip rate | spurious effect | noise size | measured effect |
|---|---|---|---|---|---|---|
| missing_evidence | gemini-3.8-flash | 360 | 0.089 | -0.033 [-0.071, +0.004] | 0.183 | +0.225 [+0.075, +0.375] |
| conflicting_evidence | gemini-3.8-flash | 189 | 0.127 | +0.016 [-0.056, +0.087] | 0.317 | +0.238 [+0.000, +0.476] |

## What it means for each family

| family | mean flip rate | mean spurious effect | mean noise size | mean measured effect |
|---|---|---|---|---|
| missing_evidence | 0.089 | -0.033 | 0.183 | +0.225 |
| conflicting_evidence | 0.127 | +0.016 | 0.317 | +0.238 |

