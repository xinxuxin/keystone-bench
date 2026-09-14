# Cross-scoring: standard shift and reply adaptation

Layer `core`, `test` split, 10 systems, judge `openrouter/openai/gpt-4.1`. Every source contributes the mean over systems; the source is the unit of resampling and intervals are 95 percent percentile bootstrap.

The paired outcome moves two things at once, the reply and the standard it is held to. Judging the frozen control reply under the edited standard fills the missing cell of the two-by-two and splits the outcome exactly:

```
  f_e(r_e) - f_c(r_c)  =  [f_e(r_c) - f_c(r_c)]  +  [f_e(r_e) - f_e(r_c)]
        outcome              standard shift          reply adaptation
```

`standard shift` is what an assistant incurs by leaving the reply unchanged: the same words, newly out of bounds. `reply adaptation` is what changing the reply buys back under one standard, negative when adaptation helps. The `adaptation rate` is their ratio, `-adaptation / shift`: zero for any policy whose reply does not depend on the edit, since `r_e = r_c` makes the second term identically zero, and one when the reply recovers the whole shift.

The two negative-control families reuse the source's own decision frame for both sides, so their `standard shift` is not a shift at all: it is the same standard applied twice, and what it measures is how much the judge moves when only the wording of the conversation changes. That is the floor the perturbation families have to clear. The perturbation families carry their own annotation for the edited side.

| family | own annotation | sources | outcome | standard shift | reply adaptation | adaptation rate |
|---|---|---|---|---|---|---|
| missing_evidence | yes | 85 | +0.079 [+0.020, +0.143] | +0.487 [+0.399, +0.572] | -0.408 [-0.482, -0.335] | 0.84 |
| conflicting_evidence | yes | 139 | +0.284 [+0.223, +0.345] | +0.619 [+0.559, +0.679] | -0.335 [-0.399, -0.275] | 0.54 |
| buried_red_flag | yes | 148 | +0.126 [+0.076, +0.177] | +0.786 [+0.742, +0.828] | -0.660 [-0.703, -0.613] | 0.84 |
| salient_distractor | no | 219 | +0.002 [-0.014, +0.019] | +0.002 [-0.007, +0.010] | +0.001 [-0.015, +0.016] | n/a |
| demographic_control | no | 161 | -0.004 [-0.030, +0.022] | -0.006 [-0.016, +0.003] | +0.002 [-0.023, +0.026] | n/a |
| demographic_shift | yes | 64 | +0.055 [-0.007, +0.119] | +0.488 [+0.391, +0.587] | -0.433 [-0.530, -0.338] | 0.89 |
| alternative_evidence | yes | 68 | -0.006 [-0.070, +0.058] | +0.670 [+0.575, +0.760] | -0.677 [-0.754, -0.595] | 1.01 |
| missing_evidence_early | yes | 11 | +0.212 [+0.051, +0.392] | +0.392 [+0.163, +0.635] | -0.180 [-0.298, -0.060] | 0.46 |

## Where the adaptation term is spent

Item by item on the perturbation families, over 4,301 (system, source) cells. `helped` is a cell where the reply the system actually produced clears the edited standard and the frozen control reply would not have. `hurt` is the reverse: the system changed its reply and the change is what put it out of bounds.

| | cells | share |
|---|---|---|
| changing the reply helped | 2,221 | 0.516 |
| changing the reply hurt | 95 | 0.022 |
| the verdict was the same either way | 1,985 | 0.462 |

The pooled term is a net of the first two, 2,221 against 95. A measurement that could only move one way would be a definition rather than a finding; this one moves both ways and the reported quantity is the balance.


## Adaptation rate by system

The share of the standard shift that each system's changed reply recovers, on the families where the edit removes or contradicts a load-bearing element.

| system | missing_evidence | conflicting_evidence | buried_red_flag |
|---|---|---|---|
| claude-opus-5 | 0.87 | 0.80 | 0.89 |
| claude-sonnet-5 | 1.03 | 0.82 | 0.81 |
| deepseek-v4-pro | 0.73 | 0.55 | 0.79 |
| gemini-3.8-flash | 0.74 | 0.42 | 0.99 |
| glm-5.3 | 0.80 | 0.54 | 0.86 |
| gpt-5.6-terra | 0.93 | 0.52 | 0.98 |
| grok-4.3 | 0.67 | 0.48 | 0.99 |
| kimi-k2.6 | 0.81 | 0.52 | 0.93 |
| llama-4-maverick | 1.00 | 0.25 | 0.36 |
| qwen3.8-max | 1.05 | 0.53 | 0.85 |

## Reading

**A paired difference near zero is not the same as a family that asks nothing.** On `demographic_shift`, `alternative_evidence` the outcome interval contains zero, and the standard still shifts by +0.488 and +0.670. Those are families where an unchanged reply would be out of bounds most of the time and the systems change it, which the difference of the two cannot distinguish from a family that makes no demand at all. Separating the terms is what tells them apart.

`missing_evidence`: leaving the reply unchanged would cost +0.487 [+0.399, +0.572]; the replies systems actually produce recover 84% of it, leaving +0.079 [+0.020, +0.143].

`conflicting_evidence`: leaving the reply unchanged would cost +0.619 [+0.559, +0.679]; the replies systems actually produce recover 54% of it, leaving +0.284 [+0.223, +0.345].

`buried_red_flag`: leaving the reply unchanged would cost +0.786 [+0.742, +0.828]; the replies systems actually produce recover 84% of it, leaving +0.126 [+0.076, +0.177].

`demographic_shift`: leaving the reply unchanged would cost +0.488 [+0.391, +0.587]; the replies systems actually produce recover 89% of it, leaving +0.055 [-0.007, +0.119].

`alternative_evidence`: leaving the reply unchanged would cost +0.670 [+0.575, +0.760]; the replies systems actually produce recover 101% of it, leaving -0.006 [-0.070, +0.058]. A rate above one means the edited reply clears the edited standard more often than the control reply cleared its own.

`missing_evidence_early`: leaving the reply unchanged would cost +0.392 [+0.163, +0.635]; the replies systems actually produce recover 46% of it, leaving +0.212 [+0.051, +0.392].

The controls hold the standard fixed and change only the wording, so their first term is the judge's own movement rather than a shift: `salient_distractor` +0.002 [-0.007, +0.010], `demographic_control` -0.006 [-0.016, +0.003]. The largest limit is 0.010, and every perturbation family's shift lies above it.

