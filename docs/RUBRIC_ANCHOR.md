# Convergent validity against the physicians' weights

Materiality in Keystone is rated by models. The rubric it is rated against is not: physicians wrote every criterion and assigned its points. This report asks whether the two rating processes agree on a quantity neither of them assigned, the share of a source's rubric weight that the edited fact carries.

**Specification.** Materiality is taken from the two review models, which see the original message, the modified message and a note on what changed, and never see the rubric; a twin enters only when both agree, the release's own rule for a two-rater label. Weight share is the sum of `|points|` over the criteria a labeller marked as depending on the edit, divided by the sum over all criteria of that source. The two negative-control families are excluded from the primary comparison (their materiality is 1 and their dependence list is empty by construction) and reported separately as a floor. Layer `all`, so the strict layer's own dependence requirement cannot select the result. Regenerate with `python tools/rubric_anchor.py`.

## Primary comparison

Twins where both blind reviewers agree, perturbation families only: **2231** (materiality 3: 1073, 2: 831, 1: 327).

| Blind materiality | Twins | Median share of the physicians' rubric weight |
|---|---|---|
| 3 | 1073 | 0.439 |
| 2 | 831 | 0.160 |
| 1 | 327 | 0.000 |

Cliff's delta (3 versus 1) **0.798** with a 95 percent bootstrap interval [0.757, 0.837], Mann-Whitney p <1e-12; Spearman rho over the three levels 0.570 (p <1e-12).

## By family

Four families carry two blind reviewers, so the primary rule applies. The other four carry one, and the row falls back to that single blind rater, marked `1 rater`. A family whose edit is material by construction has no materiality-1 side to contrast, which the row says instead of a delta.

| Family | Rating | n (3 / 2 / 1) | Median weight share (3 / 2 / 1) | Cliff's delta [95%] | p |
|---|---|---|---|---|---|
| `alternative_evidence` | 2 raters agree | materiality 1 on 2 twins, too few to contrast | | | |
| `buried_red_flag` | 1 rater | materiality 1 on 3 twins, too few to contrast | | | |
| `conflicting_evidence` | 2 raters agree | 358 / 159 / 20 | 0.446 / 0.255 / 0.163 | 0.605 [0.333, 0.840] | 5.1e-06 |
| `demographic_control` | 1 rater | 5 / 38 / 906 | 0.127 / 0.021 / 0.000 | 0.569 [0.162, 0.975] | 1.2e-11 |
| `demographic_shift` | 2 raters agree | 186 / 354 / 189 | 0.324 / 0.117 / 0.000 | 0.884 [0.835, 0.922] | <1e-12 |
| `missing_evidence` | 2 raters agree | 268 / 297 / 116 | 0.492 / 0.163 / 0.135 | 0.626 [0.536, 0.718] | <1e-12 |
| `missing_evidence_early` | 1 rater | 86 / 100 / 32 | 0.218 / 0.095 / 0.103 | 0.380 [0.170, 0.581] | 0.0015 |
| `salient_distractor` | 2 raters agree | materiality 1 on 1230 twins, too few to contrast | | | |

## By source stratum

| Stratum | n (3 / 1) | Median weight share (3 / 1) | Cliff's delta [95%] | p |
|---|---|---|---|---|
| `cond_emergent` | 158 / 26 | 0.573 / 0.000 | 0.810 [0.655, 0.926] | 2.5e-11 |
| `context_matters` | 186 / 20 | 0.379 / 0.126 | 0.697 [0.497, 0.862] | 3.1e-07 |
| `data_task` | 151 / 93 | 0.395 / 0.078 | 0.667 [0.555, 0.773] | <1e-12 |
| `emergent` | 117 / 7 | 0.500 / 0.000 | 0.856 [0.664, 0.974] | 0.00013 |
| `enough_context` | 195 / 53 | 0.452 / 0.097 | 0.854 [0.783, 0.913] | <1e-12 |
| `non_emergent` | 100 / 37 | 0.597 / 0.000 | 0.914 [0.842, 0.974] | <1e-12 |
| `reducible_uncertainty` | 166 / 91 | 0.309 / 0.000 | 0.835 [0.753, 0.909] | <1e-12 |

## Robustness

| Specification | Cliff's delta [95%] | p |
|---|---|---|
| positive points only | 0.770 [0.727, 0.811] | <1e-12 |
| unweighted: share of criteria flagged | 0.797 [0.756, 0.834] | <1e-12 |
| twins with no mechanical defect | 0.795 [0.748, 0.837] | <1e-12 |
| single-turn sources only | 0.802 [0.750, 0.851] | <1e-12 |
| single blind rater, every perturbation family (3312 twins) | 0.713 [0.667, 0.755] | <1e-12 |
| second dependence labeller (Claude, 1065 twins) | 0.542 [0.442, 0.637] | <1e-12 |

## Weight on top of extent

The weighted and unweighted specifications above give nearly the same delta, so most of the agreement is about **how much of the rubric the edit reaches**. That invites the obvious objection: perhaps the physicians' point allocation adds nothing. Three measures answer it, each holding extent fixed in a different way.

### 1. Reaching the criterion the physicians weighted highest

Per source there is one criterion with the largest absolute points. An edit that touches k of n criteria reaches it with probability k/n by extent alone, so the excess over k/n is weight signal that extent cannot produce.

| Blind materiality | Twins | Reaches the heaviest criterion | Expected from extent alone | Excess [95%] |
|---|---|---|---|---|
| 3 | 1073 | 0.514 | 0.461 | 0.052 [0.027, 0.077] |
| 2 | 831 | 0.230 | 0.230 | 0.000 [-0.025, 0.024] |
| 1 | 327 | 0.098 | 0.104 | -0.006 [-0.033, 0.021] |

Excess at materiality 3 minus materiality 1: 0.059 [0.022, 0.095].

### 2. Weight share within strata of equal extent

Twins are put into five strata by the share of criteria the edit reaches, and the materiality 3 against materiality 1 comparison is run inside each stratum, where extent is held nearly constant by construction.

| Stratum (share of criteria reached) | Twins (3 / 1) | Median weight share (3 / 1) | Cliff's delta [95%] |
|---|---|---|---|
| 0 to 0.08 | 46 / 198 | 0.000 / 0.000 | 0.300 [0.143, 0.464] |
| 0.08 to 0.20 | 128 / 68 | 0.137 / 0.131 | 0.137 [-0.041, 0.307] |
| 0.20 to 0.33 | 219 / 38 | 0.278 / 0.261 | 0.198 [0.016, 0.376] |
| 0.33 to 0.53 | 318 / 15 | 0.447 / 0.446 | -0.003 [-0.321, 0.331] |
| 0.53 to 1 | 362 / 8 | 0.748 / 0.768 | 0.056 [-0.297, 0.395] |

Pooled across strata, weighted by twins: Cliff's delta 0.122 [-0.013, 0.268]. A positive value here cannot come from extent, because extent is what the strata hold fixed.

### 3. Weight per flagged criterion

Among the 4479 twins that flag at least one criterion, `lift` is the mean weight of a flagged criterion divided by the mean weight of every criterion in that source's rubric.

| Blind materiality | Twins | Median lift |
|---|---|---|
| 3 | 1048 | 1.013 |
| 2 | 686 | 0.987 |
| 1 | 162 | 0.962 |

Cliff's delta (3 versus 1) 0.243 [0.129, 0.352], p 6.4e-07. The interval is clear of zero, so a weight signal exists on top of the extent signal, and it is the smaller of the two: material edits reach criteria slightly heavier than their rubric's average, immaterial ones slightly lighter.


## Controls

**Anchoring.** The dependence labeller sees the point values, so flagged criteria could simply be the expensive ones. Within a rubric, the mean weight of a flagged criterion is 6.444 against 6.556 for an unflagged one (Cliff's delta -0.054 [-0.077, -0.031]). A large positive value here would mean part of the primary effect is the labeller preferring heavy criteria rather than the edit reaching them; at this magnitude it does not.

**Negative-control floor.** The two control families carry a median weight share of 0.000 over 2185 twins, against 0.242 over 5132 perturbation twins.

## Reading

What this establishes. A rubric-blind clinical judgement of how much the edit matters, and a separate labeller's reading of which physician-written criteria the edit reaches, move together on every family and stratum that has both ends to compare. The quantity they agree on was set by the physicians who wrote the rubric, not by any Keystone rater.

What the physicians' weights add. Most of the effect is extent, how much of the rubric the edit reaches, and three measures show that the point allocation carries signal of its own. Two of them are clear of zero. A material edit reaches the single criterion the physicians weighted highest more often than its own extent predicts, an immaterial edit does not, and the gap between them is 0.06 wide with an interval above zero. The criteria a material edit reaches are heavier than their rubric's average while an immaterial edit's are lighter. The third measure, stratifying on extent, keeps a positive point estimate but its interval includes zero, because the strata where the edit reaches most of the rubric hold only a handful of immaterial twins. So the supported claim is that a material edit covers more of the rubric and reaches the part the physicians paid most for, with the stratified version of that second half still underpowered.

What it does not establish. Both sides are still models reading a physician-written artefact, so this is convergent validity rather than adjudication, which is the distinction the release's `silver` and `gold` tiers carry, and materiality's behavioural claim is tested separately in [`BEHAVIOUR_ANCHOR.md`](BEHAVIOUR_ANCHOR.md). Read the weakest cells as the work queue, not as noise: the families and strata with the narrowest advantage are where a clinician's first hour is worth most.

