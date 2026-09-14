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
| missing_evidence | yes | 85 | +0.079 [+0.020, +0.143] | +0.487 [+0.399, +0.572] | -0.408 [-0.482, -0.335] | 0.84 [0.73, 0.96] |
| conflicting_evidence | yes | 139 | +0.284 [+0.223, +0.345] | +0.619 [+0.559, +0.679] | -0.335 [-0.399, -0.275] | 0.54 [0.45, 0.63] |
| buried_red_flag | yes | 148 | +0.126 [+0.076, +0.177] | +0.786 [+0.742, +0.828] | -0.660 [-0.703, -0.613] | 0.84 [0.78, 0.90] |
| salient_distractor | no | 219 | +0.002 [-0.014, +0.019] | +0.002 [-0.007, +0.010] | +0.001 [-0.015, +0.016] | n/a |
| demographic_control | no | 161 | -0.004 [-0.030, +0.022] | -0.006 [-0.016, +0.003] | +0.002 [-0.023, +0.026] | n/a |

## Where the adaptation term is spent

Item by item on the perturbation families, over 3,118 (system, source) cells. `helped` is a cell where the reply the system actually produced clears the edited standard and the frozen control reply would not have. `hurt` is the reverse: the system changed its reply and the change is what put it out of bounds.

| | cells | share |
|---|---|---|
| changing the reply helped | 1,578 | 0.506 |
| changing the reply hurt | 72 | 0.023 |
| the verdict was the same either way | 1,468 | 0.471 |

The pooled term is a net of the first two, 1,578 against 72. A measurement that could only move one way would be a definition rather than a finding; this one moves both ways and the reported quantity is the balance.


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

`missing_evidence`: leaving the reply unchanged would cost +0.487 [+0.399, +0.572]; the replies systems actually produce recover 84% [73%, 96%] of it, leaving +0.079 [+0.020, +0.143].

`conflicting_evidence`: leaving the reply unchanged would cost +0.619 [+0.559, +0.679]; the replies systems actually produce recover 54% [45%, 63%] of it, leaving +0.284 [+0.223, +0.345].

`buried_red_flag`: leaving the reply unchanged would cost +0.786 [+0.742, +0.828]; the replies systems actually produce recover 84% [78%, 90%] of it, leaving +0.126 [+0.076, +0.177].

The controls hold the standard fixed and change only the wording, so their first term is the judge's own movement rather than a shift: `salient_distractor` +0.002 [-0.007, +0.010], `demographic_control` -0.006 [-0.016, +0.003]. The largest limit is 0.010, and every perturbation family's shift lies above it.


## Both orderings, and what separates them

The decomposition is exact in either order. Taking the standard first gives the terms above; taking the reply first gives `f_c(r_e) - f_c(r_c)` and `f_e(r_e) - f_c(r_e)`. The two orders attribute the interaction differently, which is the index-number problem every decomposition of this shape has. The interaction is reported so that the size of the ambiguity is visible rather than absorbed.

| family | sources | shift, standard first | shift, reply first | adaptation, standard first | adaptation, reply first | interaction |
|---|---|---|---|---|---|---|
| `missing_evidence` | 85 | +0.487 [+0.400, +0.573] | -0.017 [-0.078, +0.049] | -0.408 [-0.481, -0.336] | +0.096 [+0.045, +0.147] | -0.504 [-0.602, -0.407] |
| `conflicting_evidence` | 139 | +0.619 [+0.558, +0.679] | +0.110 [+0.039, +0.181] | -0.335 [-0.397, -0.273] | +0.174 [+0.126, +0.222] | -0.509 [-0.595, -0.427] |
| `buried_red_flag` | 148 | +0.786 [+0.742, +0.829] | -0.182 [-0.261, -0.104] | -0.660 [-0.703, -0.612] | +0.308 [+0.253, +0.364] | -0.968 [-1.050, -0.891] |
| `salient_distractor` | 219 | +0.002 [-0.007, +0.010] | +0.003 [-0.006, +0.012] | +0.001 [-0.015, +0.016] | -0.001 [-0.018, +0.016] | +0.001 [-0.011, +0.013] |
| `demographic_control` | 161 | -0.006 [-0.016, +0.003] | -0.001 [-0.012, +0.010] | +0.002 [-0.022, +0.027] | -0.003 [-0.026, +0.019] | +0.006 [-0.009, +0.021] |

The interaction is large on the perturbation families and reaches -0.968 [-1.050, -0.891] on `buried_red_flag`. On the negative controls it is at most 0.006, which is what the machinery produces when both sides carry the same standard.

A large interaction is what adaptation looks like rather than a defect in the split. A reply written for the edited message is judged well by the edited standard and badly by the one it was not written for, so the value of changing the reply depends on which standard is asked, and that dependence is the interaction. The two orderings are therefore not two estimates of one quantity. They are two quantities.

**What the other ordering measures is over-adaptation.** Its adaptation term holds the *control* standard fixed and asks how much worse the edited reply is by it: `missing_evidence` +0.096 [+0.045, +0.147]; `conflicting_evidence` +0.174 [+0.126, +0.222]; `buried_red_flag` +0.308 [+0.253, +0.364]. A system that answers a buried red flag by escalating has done the right thing on the edited message and would have done the wrong thing on the unedited one, and this term is the size of that. It is a cost only if the system cannot tell the two apart, which is what the negative-control families test separately.

The adaptation rate does not depend on the ordering for a policy whose reply ignores the edit: `r_e = r_c` makes both adaptation terms identically zero, so the zero property survives the choice even though the magnitudes do not.

