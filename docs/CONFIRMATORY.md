# Confirmatory analysis, held-out split

Core layer, `test` split, 5 evaluated systems (claude-sonnet-5, deepseek-v4-pro, gemini-3.8-flash, gpt-5.6-terra, llama-4-maverick). Every quantity is the mean over sources of the mean over systems of (edited forbidden − paraphrase forbidden), with the source as the unit of resampling. Intervals are 95 percent for C1 and C1b and 90 percent for the equivalence test in C2. Numbers computed on the `quick` layer elsewhere in this repository are exploratory: that layer is drawn from the dev split.

## C1 evidence effect

Prediction: Δ_f > 0 on all three. Decision rule: all three intervals exclude zero after Benjamini-Hochberg across the three families.

| family | sources | risk difference | bootstrap p | BH q | excludes zero |
|---|---|---|---|---|---|
| missing_evidence | 85 | +0.060 [-0.002, +0.124] | 0.0611 | 0.0611 | no |
| conflicting_evidence | 139 | +0.309 [+0.246, +0.372] | 0.0001 | 0.0002 | yes |
| buried_red_flag | 148 | +0.166 [+0.115, +0.219] | 0.0001 | 0.0002 | yes |

**C1: not supported as specified.**

## C1b ceiling-restricted effect

The same three families over the sources whose reply to the *unedited* conversation was not itself a forbidden action, where an effect of editing has room to appear. Reported next to C1; neither is preferred, and a family where they disagree is reported as such.

| family | sources | excluded | risk difference | excludes zero |
|---|---|---|---|---|
| missing_evidence | 85 | 0 | +0.063 [-0.004, +0.130] | no |
| conflicting_evidence | 139 | 0 | +0.353 [+0.290, +0.416] | yes |
| buried_red_flag | 148 | 0 | +0.213 [+0.165, +0.265] | yes |

**C1b: not supported as specified.**

## C2 control invariance

Prediction: |Δ_f| ≤ 0.05 on both negative-control families. This is an equivalence test, so the 90 percent interval has to lie inside the bounds; an interval that merely contains zero does not pass.

| family | sources | risk difference (90%) | inside ±0.05 |
|---|---|---|---|
| salient_distractor | 219 | -0.002 [-0.019, +0.016] | yes |
| demographic_control | 161 | -0.006 [-0.031, +0.019] | yes |

**C2: supported.**

## Per system

Each system's own paired difference on the three C1 families, so that a pooled effect carried by one system is visible.

| system | missing_evidence | conflicting_evidence | buried_red_flag |
|---|---|---|---|
| claude-sonnet-5 | -0.012 [-0.071, +0.048] | +0.108 [+0.022, +0.194] | +0.158 [+0.075, +0.233] |
| deepseek-v4-pro | +0.164 [+0.082, +0.260] | +0.320 [+0.227, +0.414] | +0.176 [+0.096, +0.257] |
| gemini-3.8-flash | +0.143 [+0.036, +0.250] | +0.385 [+0.289, +0.474] | +0.007 [-0.062, +0.076] |
| gpt-5.6-terra | +0.035 [-0.059, +0.129] | +0.268 [+0.188, +0.355] | +0.014 [-0.054, +0.081] |
| llama-4-maverick | +0.000 [-0.118, +0.118] | +0.468 [+0.367, +0.568] | +0.486 [+0.385, +0.581] |

## Reading

Two of the three families hold and one does not, so C1 as specified is not supported and is reported as such. What replaces it is narrower and better attested.

`conflicting_evidence` is the result. +0.309 [+0.246, +0.372] over 139 held-out sources, and every one of the five systems has an interval that excludes zero, from +0.108 to +0.468. It is also the family that held under all three judge vendors and under the own-vendor exclusion on the exploratory layer. Nothing else in this release is attested from that many directions.

`buried_red_flag` holds pooled, +0.166 [+0.115, +0.219], but two of the five systems sit on zero (+0.007 and +0.014) while a third is at +0.486. A pooled interval that excludes zero on a family this heterogeneous describes the set of systems evaluated, not a property of assistants, and is reported that way.

`missing_evidence` does not hold on the held-out split: +0.060 [-0.002, +0.124], with one system at -0.012 and another at +0.164. On the exploratory quick layer the same family is +0.198 [+0.101, +0.305]. The quick layer is 40 items per family drawn from dev, and the gap between the two numbers is the reason a held-out split exists. The exploratory figure is not repeated as a finding.

**C2 is supported**, and it is the clause that makes the rest readable. Both negative controls are inside the equivalence bounds on the same split with the same judge: -0.002 [-0.019, +0.016] and -0.006 [-0.031, +0.019]. Whatever moves `conflicting_evidence` by 0.31 does not move an insertion of the same size that leaves the decision alone.

