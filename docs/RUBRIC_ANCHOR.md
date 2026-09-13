# Convergent validity against the physicians' weights

Materiality in Keystone is rated by models. The rubric it is rated against is not: physicians wrote every criterion and assigned its points. This report asks whether the two rating processes agree on a quantity neither of them assigned, the share of a source's rubric weight that the edited fact carries.

**Specification.** Materiality is taken from the two review models, which see the original message, the modified message and a note on what changed, and never see the rubric; a twin enters only when both agree, the release's own rule for a two-rater label. Weight share is the sum of `|points|` over the criteria a labeller marked as depending on the edit, divided by the sum over all criteria of that source. The two negative-control families are excluded from the primary comparison (their materiality is 1 and their dependence list is empty by construction) and reported separately as a floor. Layer `all`, so the strict layer's own dependence requirement cannot select the result. Regenerate with `python tools/rubric_anchor.py`.

## Primary comparison

Twins where both blind reviewers agree, perturbation families only: **2709** (materiality 3: 1518, 2: 859, 1: 332).

| Blind materiality | Twins | Median share of the physicians' rubric weight |
|---|---|---|
| 3 | 1518 | 0.390 |
| 2 | 859 | 0.163 |
| 1 | 332 | 0.014 |

Cliff's delta (3 versus 1) **0.749** with a 95 percent bootstrap interval [0.703, 0.791], Mann-Whitney p <1e-12; Spearman rho over the three levels 0.497 (p <1e-12).

## By family

Four families carry two blind reviewers, so the primary rule applies. The other four carry one, and the row falls back to that single blind rater, marked `1 rater`. A family whose edit is material by construction has no materiality-1 side to contrast, which the row says instead of a delta.

| Family | Rating | n (3 / 2 / 1) | Median weight share (3 / 2 / 1) | Cliff's delta [95%] | p |
|---|---|---|---|---|---|
| `alternative_evidence` | 2 raters agree | materiality 1 on 2 twins, too few to contrast | | | |
| `buried_red_flag` | 2 raters agree | materiality 1 on 0 twins, too few to contrast | | | |
| `conflicting_evidence` | 2 raters agree | 353 / 173 / 25 | 0.446 / 0.264 / 0.179 | 0.533 [0.287, 0.751] | 8.3e-06 |
| `demographic_control` | 1 rater | materiality 1 on 902 twins, too few to contrast | | | |
| `demographic_shift` | 2 raters agree | 186 / 353 / 189 | 0.324 / 0.116 / 0.000 | 0.884 [0.835, 0.922] | <1e-12 |
| `missing_evidence` | 2 raters agree | 268 / 297 / 116 | 0.492 / 0.163 / 0.135 | 0.626 [0.536, 0.718] | <1e-12 |
| `missing_evidence_early` | 1 rater | 86 / 100 / 32 | 0.218 / 0.095 / 0.103 | 0.380 [0.170, 0.581] | 0.0015 |
| `salient_distractor` | 2 raters agree | materiality 1 on 1178 twins, too few to contrast | | | |

## By source stratum

| Stratum | n (3 / 1) | Median weight share (3 / 1) | Cliff's delta [95%] | p |
|---|---|---|---|---|
| `cond_emergent` | 234 / 26 | 0.562 / 0.000 | 0.824 [0.681, 0.944] | 3.2e-12 |
| `context_matters` | 241 / 20 | 0.305 / 0.126 | 0.582 [0.377, 0.753] | 1.5e-05 |
| `data_task` | 226 / 94 | 0.328 / 0.079 | 0.586 [0.459, 0.700] | <1e-12 |
| `emergent` | 117 / 10 | 0.500 / 0.000 | 0.707 [0.339, 0.962] | 0.00019 |
| `enough_context` | 280 / 53 | 0.379 / 0.097 | 0.732 [0.636, 0.816] | <1e-12 |
| `non_emergent` | 154 / 38 | 0.609 / 0.000 | 0.928 [0.871, 0.973] | <1e-12 |
| `reducible_uncertainty` | 266 / 91 | 0.255 / 0.000 | 0.778 [0.678, 0.865] | <1e-12 |

## Robustness

| Specification | Cliff's delta [95%] | p |
|---|---|---|
| positive points only | 0.719 [0.671, 0.763] | <1e-12 |
| unweighted: share of criteria flagged | 0.752 [0.706, 0.793] | <1e-12 |
| twins with no mechanical defect | 0.625 [0.549, 0.698] | <1e-12 |
| single-turn sources only | 0.769 [0.710, 0.822] | <1e-12 |
| single blind rater, every perturbation family (3229 twins) | 0.712 [0.666, 0.753] | <1e-12 |
| second dependence labeller (Claude, 1059 twins) | 0.539 [0.440, 0.630] | <1e-12 |

## Weight on top of extent

The weighted and unweighted specifications above give nearly the same delta, so most of the agreement is about **how much of the rubric the edit reaches**. That invites the obvious objection: perhaps the physicians' point allocation adds nothing. Three measures answer it, each holding extent fixed in a different way.

### 1. Reaching the criterion the physicians weighted highest

Per source there is one criterion with the largest absolute points. An edit that touches k of n criteria reaches it with probability k/n by extent alone, so the excess over k/n is weight signal that extent cannot produce.

| Blind materiality | Twins | Reaches the heaviest criterion | Expected from extent alone | Excess [95%] |
|---|---|---|---|---|
| 3 | 1518 | 0.455 | 0.429 | 0.027 [0.005, 0.046] |
| 2 | 859 | 0.231 | 0.235 | -0.004 [-0.028, 0.019] |
| 1 | 332 | 0.105 | 0.108 | -0.003 [-0.029, 0.025] |

Excess at materiality 3 minus materiality 1: 0.030 [-0.005, 0.062].

### 2. Weight share within strata of equal extent

Twins are put into five strata by the share of criteria the edit reaches, and the materiality 3 against materiality 1 comparison is run inside each stratum, where extent is held nearly constant by construction.

| Stratum (share of criteria reached) | Twins (3 / 1) | Median weight share (3 / 1) | Cliff's delta [95%] |
|---|---|---|---|
| 0 to 0.09 | 94 / 210 | 0.052 / 0.000 | 0.484 [0.373, 0.597] |
| 0.09 to 0.20 | 260 / 57 | 0.137 / 0.143 | 0.012 [-0.164, 0.185] |
| 0.20 to 0.33 | 318 / 40 | 0.272 / 0.261 | 0.126 [-0.051, 0.298] |
| 0.33 to 0.53 | 397 / 16 | 0.441 / 0.437 | 0.025 [-0.300, 0.362] |
| 0.53 to 1 | 449 / 9 | 0.754 / 0.791 | -0.012 [-0.351, 0.304] |

Pooled across strata, weighted by twins: Cliff's delta 0.108 [-0.016, 0.231]. A positive value here cannot come from extent, because extent is what the strata hold fixed.

### 3. Weight per flagged criterion

Among the 4470 twins that flag at least one criterion, `lift` is the mean weight of a flagged criterion divided by the mean weight of every criterion in that source's rubric.

| Blind materiality | Twins | Median lift |
|---|---|---|
| 3 | 1489 | 1.000 |
| 2 | 713 | 0.984 |
| 1 | 166 | 0.962 |

Cliff's delta (3 versus 1) 0.160 [0.062, 0.267], p 0.00071. The interval is clear of zero, so a weight signal exists on top of the extent signal, and it is the smaller of the two: material edits reach criteria slightly heavier than their rubric's average, immaterial ones slightly lighter.


## Controls

**Anchoring.** The dependence labeller sees the point values, so flagged criteria could simply be the expensive ones. Within a rubric, the mean weight of a flagged criterion is 6.444 against 6.556 for an unflagged one (Cliff's delta -0.053 [-0.078, -0.028]). A large positive value here would mean part of the primary effect is the labeller preferring heavy criteria rather than the edit reaching them; at this magnitude it does not.

**Negative-control floor.** The two control families carry a median weight share of 0.000 over 2182 twins, against 0.242 over 5123 perturbation twins.

## Reading

What this establishes. A rubric-blind clinical judgement of how much the edit matters, and a separate labeller's reading of which physician-written criteria the edit reaches, move together on every family and stratum that has both ends to compare. The quantity they agree on was set by the physicians who wrote the rubric, not by any Keystone rater.

What the physicians' weights add. Most of the effect is extent, how much of the rubric the edit reaches, and three measures ask whether the point allocation carries signal of its own. One of them is clear of zero. A material edit reaches the single criterion the physicians weighted highest more often than its own extent predicts, an immaterial edit does not, and the gap between them is 0.030 wide, though the interval does not clear zero. The criteria a material edit reaches are heavier than their rubric's average while an immaterial edit's are lighter. The third measure, stratifying on extent, keeps a positive point estimate but its interval includes zero, because the strata where the edit reaches most of the rubric hold only a handful of immaterial twins. So the supported claim rests on the weight of a flagged criterion relative to its rubric's average, which clears zero; reaching the single criterion physicians weighted highest beyond what extent predicts and the stratified comparison that holds extent fixed still keep a positive point estimate without clearing it at this sample size.

What it does not establish. Both sides are still models reading a physician-written artefact, so this is convergent validity rather than adjudication, which is the distinction the release's `silver` and `gold` tiers carry, and materiality's behavioural claim is tested separately in [`BEHAVIOUR_ANCHOR.md`](BEHAVIOUR_ANCHOR.md). Read the weakest cells as the work queue, not as noise: the families and strata with the narrowest advantage are where a clinician's first hour is worth most.

