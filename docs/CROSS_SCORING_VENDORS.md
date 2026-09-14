# Cross-scoring: standard shift and reply adaptation

Layer `core`, `test` split, 3 systems, judge `openrouter/openai/gpt-4.1`. Every source contributes the mean over systems; the source is the unit of resampling and intervals are 95 percent percentile bootstrap.

The paired outcome moves two things at once, the reply and the standard it is held to. Judging the frozen control reply under the edited standard fills the missing cell of the two-by-two and splits the outcome exactly:

```
  f_e(r_e) - f_c(r_c)  =  [f_e(r_c) - f_c(r_c)]  +  [f_e(r_e) - f_e(r_c)]
        outcome              standard shift          reply adaptation
```

`standard shift` is what an assistant incurs by leaving the reply unchanged: the same words, newly out of bounds. `reply adaptation` is what changing the reply buys back under one standard, negative when adaptation helps. The `adaptation rate` is their ratio, `-adaptation / shift`: zero for any policy whose reply does not depend on the edit, since `r_e = r_c` makes the second term identically zero, and one when the reply recovers the whole shift.

The two negative-control families reuse the source's own decision frame for both sides, so their `standard shift` is not a shift at all: it is the same standard applied twice, and what it measures is how much the judge moves when only the wording of the conversation changes. That is the floor the perturbation families have to clear. The perturbation families carry their own annotation for the edited side.

| family | own annotation | sources | outcome | standard shift | reply adaptation | adaptation rate |
|---|---|---|---|---|---|---|
| missing_evidence | yes | 50 | -0.033 [-0.137, +0.080] | +0.337 [+0.210, +0.463] | -0.370 [-0.483, -0.257] | 1.10 |
| conflicting_evidence | yes | 50 | +0.300 [+0.173, +0.420] | +0.597 [+0.477, +0.710] | -0.297 [-0.423, -0.167] | 0.50 |
| buried_red_flag | yes | 50 | +0.220 [+0.133, +0.307] | +0.760 [+0.657, +0.850] | -0.540 [-0.630, -0.450] | 0.71 |
| salient_distractor | no | 50 | +0.013 [-0.037, +0.063] | +0.013 [-0.013, +0.050] | -0.000 [-0.053, +0.050] | n/a |

## Adaptation rate by system

The share of the standard shift that each system's changed reply recovers, on the families where the edit removes or contradicts a load-bearing element.

| system | missing_evidence | conflicting_evidence | buried_red_flag |
|---|---|---|---|
| gpt-5.6-terra | 1.04 | 0.63 | 1.00 |
| llama-4-maverick | 1.27 | 0.27 | 0.34 |
| qwen3.8-max | 1.50 | 0.59 | 1.00 |

## Reading

`missing_evidence`: leaving the reply unchanged would cost +0.337 [+0.210, +0.463]; the replies systems actually produce recover 110% of it, leaving -0.033 [-0.137, +0.080]. A rate above one means the edited reply clears the edited standard more often than the control reply cleared its own.

`conflicting_evidence`: leaving the reply unchanged would cost +0.597 [+0.477, +0.710]; the replies systems actually produce recover 50% of it, leaving +0.300 [+0.173, +0.420].

`buried_red_flag`: leaving the reply unchanged would cost +0.760 [+0.657, +0.850]; the replies systems actually produce recover 71% of it, leaving +0.220 [+0.133, +0.307].

The controls hold the standard fixed and change only the wording, so their first term is the judge's own movement rather than a shift: `salient_distractor` +0.013 [-0.013, +0.050]. The largest limit is 0.050, and every perturbation family's shift lies above it.


## The same decomposition under a second judge

Every cell recomputed by the judge behind `gemini` on the same systems, families and sources, so the two columns differ only in who judged. The `fe_rc` cell is the one a paired design does not contain, and it is the one this replication exists to check.

| family | standard shift, this judge | standard shift, second judge | rate, this | rate, second |
|---|---|---|---|---|
| `missing_evidence` | +0.337 [+0.210, +0.467] | +0.447 [+0.320, +0.570] | 1.10 | 0.99 |
| `conflicting_evidence` | +0.597 [+0.480, +0.717] | +0.607 [+0.483, +0.717] | 0.50 | 0.59 |
| `buried_red_flag` | +0.760 [+0.663, +0.850] | +0.783 [+0.697, +0.863] | 0.71 | 0.80 |
| `salient_distractor` | +0.013 [-0.013, +0.043] | -0.010 [-0.030, +0.000] | n/a | n/a |

The two judges place the standard shift within 0.110 of each other on the family where they differ most (`missing_evidence`), and closer on the rest. The cell that carries the replication is the one a paired design never computes, so a judge-specific artefact in it would show here as a gap rather than as agreement.

