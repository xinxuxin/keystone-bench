# Judge panel

Judges: gpt-4.1, claude-sonnet-5, gemini-3.8-flash. Items are the quick-set replies of 5 models, re-judged with the same frozen prompts; the model outputs are identical across judges (cached), only the judge changes.

| judge | (model, item) pairs judged |
|---|---|
| gpt-4.1 | 1515 |
| claude-sonnet-5 | 1515 |
| gemini-3.8-flash | 1515 |

## Agreement between judges

Percent agreement and Cohen's kappa over every (model, item, condition) both judges scored; the second pair of columns restricts to the edited condition.

| outcome | judges | n all | agree all | kappa all | n edited | agree edited | kappa edited |
|---|---|---|---|---|---|---|---|
| forbidden | gpt-4.1 vs claude-sonnet-5 | 4382 | 0.873 | 0.587 | 1445 | 0.867 | 0.642 |
| forbidden | gpt-4.1 vs gemini-3.8-flash | 4460 | 0.851 | 0.513 | 1491 | 0.852 | 0.591 |
| forbidden | claude-sonnet-5 vs gemini-3.8-flash | 4343 | 0.905 | 0.731 | 1434 | 0.907 | 0.764 |
| acceptable | gpt-4.1 vs claude-sonnet-5 | 4382 | 0.885 | 0.618 | 1445 | 0.880 | 0.673 |
| acceptable | gpt-4.1 vs gemini-3.8-flash | 4460 | 0.855 | 0.555 | 1491 | 0.856 | 0.629 |
| acceptable | claude-sonnet-5 vs gemini-3.8-flash | 4343 | 0.902 | 0.731 | 1434 | 0.915 | 0.794 |
| decisive_hit | gpt-4.1 vs claude-sonnet-5 | 4382 | 0.919 | 0.676 | 1445 | 0.896 | 0.709 |
| decisive_hit | gpt-4.1 vs gemini-3.8-flash | 4460 | 0.915 | 0.56 | 1491 | 0.890 | 0.648 |
| decisive_hit | claude-sonnet-5 vs gemini-3.8-flash | 4343 | 0.906 | 0.524 | 1434 | 0.888 | 0.649 |
| escalates | gpt-4.1 vs claude-sonnet-5 | 4382 | 0.971 | 0.894 | 1445 | 0.963 | 0.898 |
| escalates | gpt-4.1 vs gemini-3.8-flash | 4460 | 0.973 | 0.903 | 1491 | 0.962 | 0.893 |
| escalates | claude-sonnet-5 vs gemini-3.8-flash | 4343 | 0.977 | 0.916 | 1434 | 0.972 | 0.921 |
| stance | gpt-4.1 vs claude-sonnet-5 | 4499 | 0.692 | 0.446 | 1498 | 0.689 | 0.491 |
| stance | gpt-4.1 vs gemini-3.8-flash | 4448 | 0.694 | 0.4 | 1483 | 0.636 | 0.379 |
| stance | claude-sonnet-5 vs gemini-3.8-flash | 4443 | 0.781 | 0.631 | 1478 | 0.773 | 0.631 |

Fleiss' kappa over items scored by all judges:

| outcome | n | Fleiss kappa |
|---|---|---|
| forbidden | 4343 | 0.62 |
| acceptable | 4343 | 0.641 |
| decisive_hit | 4343 | 0.594 |
| stance | 4443 | 0.491 |

## Twin-minus-paraphrase forbidden action under each judge

Per family: mean over items of the mean over models of (edited forbidden minus paraphrase forbidden), item bootstrap 95 percent interval. A judge that only shifts the level would move every family; a judge that changes the finding would move the intervals across zero.

| family | judge | items | risk difference |
|---|---|---|---|
| missing_evidence | gpt-4.1 | 40 | +0.185 [+0.086, +0.289] |
| conflicting_evidence | gpt-4.1 | 40 | +0.331 [+0.230, +0.435] |
| buried_red_flag | gpt-4.1 | 40 | +0.166 [+0.048, +0.283] |
| demographic_shift | gpt-4.1 | 40 | +0.049 [-0.010, +0.113] |
| alternative_evidence | gpt-4.1 | 40 | +0.003 [-0.079, +0.087] |
| missing_evidence_early | gpt-4.1 | 23 | +0.026 [-0.043, +0.096] |
| salient_distractor | gpt-4.1 | 40 | -0.006 [-0.046, +0.030] |
| demographic_control | gpt-4.1 | 40 | -0.011 [-0.058, +0.035] |
| missing_evidence | claude-sonnet-5 | 40 | +0.212 [+0.099, +0.323] |
| conflicting_evidence | claude-sonnet-5 | 40 | +0.252 [+0.134, +0.371] |
| buried_red_flag | claude-sonnet-5 | 40 | +0.100 [-0.042, +0.234] |
| demographic_shift | claude-sonnet-5 | 40 | -0.056 [-0.142, +0.033] |
| alternative_evidence | claude-sonnet-5 | 40 | -0.019 [-0.125, +0.087] |
| missing_evidence_early | claude-sonnet-5 | 23 | +0.123 [-0.014, +0.263] |
| salient_distractor | claude-sonnet-5 | 40 | +0.005 [-0.044, +0.051] |
| demographic_control | claude-sonnet-5 | 40 | -0.024 [-0.071, +0.022] |
| missing_evidence | gemini-3.8-flash | 40 | +0.159 [+0.039, +0.281] |
| conflicting_evidence | gemini-3.8-flash | 40 | +0.246 [+0.114, +0.376] |
| buried_red_flag | gemini-3.8-flash | 40 | +0.054 [-0.088, +0.194] |
| demographic_shift | gemini-3.8-flash | 40 | -0.092 [-0.175, -0.008] |
| alternative_evidence | gemini-3.8-flash | 40 | -0.051 [-0.146, +0.044] |
| missing_evidence_early | gemini-3.8-flash | 23 | +0.096 [+0.009, +0.191] |
| salient_distractor | gemini-3.8-flash | 40 | +0.006 [-0.051, +0.064] |
| demographic_control | gemini-3.8-flash | 40 | +0.006 [-0.035, +0.050] |

## Own-vendor exclusion

For every model, the judging is averaged over the panel judges whose vendor differs from the model's vendor (majority when three remain, mean when two); models without a same-vendor judge use the full panel.

| family | judging | items | risk difference |
|---|---|---|---|
| missing_evidence | panel minus own vendor | 40 | +0.193 [+0.087, +0.310] |
| conflicting_evidence | panel minus own vendor | 40 | +0.281 [+0.174, +0.386] |
| buried_red_flag | panel minus own vendor | 40 | +0.106 [-0.014, +0.235] |
| demographic_shift | panel minus own vendor | 40 | -0.024 [-0.087, +0.033] |
| alternative_evidence | panel minus own vendor | 40 | -0.019 [-0.106, +0.065] |
| missing_evidence_early | panel minus own vendor | 23 | +0.104 [+0.013, +0.204] |
| salient_distractor | panel minus own vendor | 40 | +0.009 [-0.034, +0.051] |
| demographic_control | panel minus own vendor | 40 | -0.011 [-0.053, +0.026] |

## Family primary outcomes on the edited condition, per judge

| family | gpt-4.1 | claude-sonnet-5 | gemini-3.8-flash |
|---|---|---|---|
| missing_evidence | 0.52 (n=199) | 0.51 (n=192) | 0.41 (n=197) |
| conflicting_evidence | 0.42 (n=198) | 0.36 (n=180) | 0.26 (n=195) |
| buried_red_flag | 0.72 (n=198) | 0.62 (n=192) | 0.60 (n=194) |
| missing_evidence_early | 0.54 (n=115) | 0.54 (n=107) | 0.36 (n=115) |
## What survives the panel

Two families hold under every judge and under the own-vendor exclusion: `missing_evidence` and `conflicting_evidence`. Their intervals exclude zero for all three judges separately, and the panel estimate with the model's own vendor removed from the judging is +0.193 [+0.087, +0.310] and +0.281 [+0.177, +0.383].

`buried_red_flag` does not. The three judges agree on the direction (+0.166, +0.100, +0.054) but only the first interval excludes zero, and the own-vendor-excluded estimate is +0.106 [-0.016, +0.233]. It is reported as a secondary result whose size depends on the judge, not as a headline.

`demographic_shift` moves across zero between judges (+0.049, -0.056, -0.092, the last excluding zero on the negative side). Whatever this family measures on the forbidden-action outcome is not stable enough to carry a claim; its own primary outcome is a necessary update rather than a forbidden action, and that is how it is reported.

The two negative controls hold under every judge: every interval contains zero and every point estimate is within 0.025 of it. A judge effect large enough to manufacture the two headline families would have moved the controls as well.

Agreement is highest exactly where the annotation is most explicit. Escalation, which the frame answers with a boolean, reaches Fleiss 0.89 to 0.92. The forbidden-action and acceptable-action outcomes, which require matching a reply's course of action against a list, reach 0.62 and 0.64. Behavioural stance, a five-way label with no annotated ground truth, reaches 0.49 and is used for description only. For reference, LLM-jury against clinicians is ICC 0.47 in MedHELM (arXiv:2505.23802) where clinician against clinician is 0.43, and the best judge in MedQADE reaches kappa 0.694 against a clinician ceiling of 0.709 (arXiv:2607.01103).

