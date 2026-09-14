# Cross-scoring: standard shift and reply adaptation

Layer `core`, `test` split, 3 systems, judge `openrouter/google/gemini-3.8-flash`. Every source contributes the mean over systems; the source is the unit of resampling and intervals are 95 percent percentile bootstrap.

The paired outcome moves two things at once, the reply and the standard it is held to. Judging the frozen control reply under the edited standard fills the missing cell of the two-by-two and splits the outcome exactly:

```
  f_e(r_e) - f_c(r_c)  =  [f_e(r_c) - f_c(r_c)]  +  [f_e(r_e) - f_e(r_c)]
        outcome              standard shift          reply adaptation
```

`standard shift` is what an assistant incurs by leaving the reply unchanged: the same words, newly out of bounds. `reply adaptation` is what changing the reply buys back under one standard, negative when adaptation helps. The `adaptation rate` is their ratio, `-adaptation / shift`: zero for any policy whose reply does not depend on the edit, since `r_e = r_c` makes the second term identically zero, and one when the reply recovers the whole shift.

The two negative-control families reuse the source's own decision frame for both sides, so their `standard shift` is not a shift at all: it is the same standard applied twice, and what it measures is how much the judge moves when only the wording of the conversation changes. That is the floor the perturbation families have to clear. The perturbation families carry their own annotation for the edited side.

| family | own annotation | sources | outcome | standard shift | reply adaptation | adaptation rate |
|---|---|---|---|---|---|---|
| missing_evidence | yes | 50 | +0.007 [-0.100, +0.123] | +0.447 [+0.323, +0.570] | -0.440 [-0.563, -0.313] | 0.99 |
| conflicting_evidence | yes | 50 | +0.247 [+0.133, +0.357] | +0.607 [+0.483, +0.717] | -0.360 [-0.490, -0.227] | 0.59 |
| buried_red_flag | yes | 50 | +0.153 [+0.063, +0.243] | +0.783 [+0.697, +0.863] | -0.630 [-0.713, -0.547] | 0.80 |
| salient_distractor | no | 50 | +0.013 [-0.043, +0.070] | -0.010 [-0.030, +0.000] | +0.023 [-0.040, +0.080] | n/a |

## Adaptation rate by system

The share of the standard shift that each system's changed reply recovers, on the families where the edit removes or contradicts a load-bearing element.

| system | missing_evidence | conflicting_evidence | buried_red_flag |
|---|---|---|---|
| gpt-5.6-terra | 0.90 | 0.70 | 0.93 |
| llama-4-maverick | 1.15 | 0.41 | 0.53 |
| qwen3.8-max | 1.20 | 0.65 | 0.96 |

## Reading

`missing_evidence`: leaving the reply unchanged would cost +0.447 [+0.323, +0.570]; the replies systems actually produce recover 99% of it, leaving +0.007 [-0.100, +0.123].

`conflicting_evidence`: leaving the reply unchanged would cost +0.607 [+0.483, +0.717]; the replies systems actually produce recover 59% of it, leaving +0.247 [+0.133, +0.357].

`buried_red_flag`: leaving the reply unchanged would cost +0.783 [+0.697, +0.863]; the replies systems actually produce recover 80% of it, leaving +0.153 [+0.063, +0.243].

The controls hold the standard fixed and change only the wording, so their first term is the judge's own movement rather than a shift: `salient_distractor` -0.010 [-0.030, +0.000]. The largest limit is 0.000, and every perturbation family's shift lies above it.

