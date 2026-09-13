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

`missing_evidence`: leaving the reply unchanged would cost +0.487 [+0.399, +0.572]; the replies systems actually produce recover 84% of it, leaving +0.079 [+0.020, +0.143].

`conflicting_evidence`: leaving the reply unchanged would cost +0.619 [+0.559, +0.679]; the replies systems actually produce recover 54% of it, leaving +0.284 [+0.223, +0.345].

`buried_red_flag`: leaving the reply unchanged would cost +0.786 [+0.742, +0.828]; the replies systems actually produce recover 84% of it, leaving +0.126 [+0.076, +0.177].

The controls hold the standard fixed and change only the wording, so their first term is the judge's own movement rather than a shift: `salient_distractor` +0.002 [-0.007, +0.010], `demographic_control` -0.006 [-0.016, +0.003]. The largest limit is 0.010, and every perturbation family's shift lies above it.

