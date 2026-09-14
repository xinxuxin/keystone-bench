# Rubric expiry and the ranking it changes

Layer `core`, `test` split, judge `openrouter/openai/gpt-4.1`, systems `claude-opus-5`, `gpt-5.6-terra`, `llama-4-maverick`, `gemini-3.8-flash`. Each criterion of a source's physician rubric is graded once against that system's reply to the edited conversation. The **stale** score uses the rubric as the physician wrote it. The **adapted** score drops the criteria a second judge marked inapplicable to the edited message. Both read off the same grades, so the only difference is which criteria count.

| family | sources | criteria dropped | stale score | adapted score | level shift | ranking flip rate |
|---|---|---|---|---|---|---|
| `missing_evidence` | 85 | 4.2 | 0.443 | 0.499 | +0.056 [+0.025, +0.089] | 0.047 [0.021, 0.079] |
| `conflicting_evidence` | 140 | 1.9 | 0.426 | 0.456 | +0.030 [+0.018, +0.043] | 0.035 [0.019, 0.053] |
| `buried_red_flag` | 148 | 1.1 | 0.396 | 0.419 | +0.024 [+0.013, +0.035] | 0.007 [0.002, 0.013] |
| `salient_distractor` | 100 | 0.1 | 0.469 | 0.474 | +0.005 [+0.001, +0.011] | 0.000 [0.000, 0.000] |
| `demographic_control` | 100 | 0.1 | 0.478 | 0.483 | +0.005 [-0.002, +0.015] | 0.005 [0.000, 0.015] |

## H2, as preregistered

Protocol section 2 states H2 as: *scoring the twin's reply with the unchanged rubric (stale score) exceeds the score over still-applicable criteria, and at least 20 percent of criteria are judged inapplicable*, decided by a 95 percent bootstrap interval on the paired difference that excludes zero. The prediction is directional, and the table above reports the difference in the direction adapted minus stale, so H2 as written predicts a negative entry.

| family | criteria inapplicable | adapted − stale | interval excludes zero | direction predicted by H2 |
|---|---|---|---|---|
| `missing_evidence` | 0.329 | +0.056 [+0.025, +0.089] | yes | no |
| `conflicting_evidence` | 0.141 | +0.030 [+0.018, +0.043] | yes | no |
| `buried_red_flag` | 0.084 | +0.024 [+0.013, +0.035] | yes | no |

**H2's interval clause holds and its direction does not.** On `missing_evidence`, `conflicting_evidence`, `buried_red_flag` the paired difference excludes zero with the opposite sign: dropping the expired criteria raises the score rather than lowering it. The mechanism is visible in the grades. A criterion that no longer applies is one the edit made unsatisfiable, so the reply is recorded as failing it, and the stale rubric charges the reply for a standard the edit removed. The quantity H2 names is real and the sign written into the protocol was wrong; both are reported.

H3, preregistered as a disagreement between rankings on originals and on twins, is not executed in this release: it needs the original-side replies graded as well, which is a second pass of the same size. The ranking quantity below is a different one, holding the replies fixed and changing only the rubric version, and is reported as an addition to the preregistered set rather than as H3.

## Reading

The controls set the floor. About one criterion in a hundred expires on a negative-control twin, so whatever flip rate they show is what grading noise alone produces: `salient_distractor` 0.000 [0.000, 0.000]; `demographic_control` 0.005 [0.000, 0.015]. The upper limit across the two is 0.015.

`missing_evidence`: 4.2 criteria drop out per twin, the score moves +0.056 [+0.025, +0.089], and 4.7% of the system pairs that the stale rubric orders one way are ordered the other way once the expired criteria are dropped.

`conflicting_evidence`: 1.9 criteria drop out per twin, the score moves +0.030 [+0.018, +0.043], and 3.5% of the system pairs that the stale rubric orders one way are ordered the other way once the expired criteria are dropped.

`buried_red_flag`: 1.1 criteria drop out per twin, the score moves +0.024 [+0.013, +0.035], and 0.7% of the system pairs that the stale rubric orders one way are ordered the other way once the expired criteria are dropped.

The largest effect is on `missing_evidence`, where the flip rate is 0.047 [0.021, 0.079] against a control ceiling of 0.015. A level shift alone changes no decision; a flip changes which system a reader would pick from that item.

