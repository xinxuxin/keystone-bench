# Keystone v0.7.0

Paired evidence-perturbation stress tests for clinical chat assistants **and their rubric graders**.

Built on [HealthBench](https://github.com/openai/simple-evals) (OpenAI, MIT). Each source conversation is paired with perturbed twins that change exactly one thing, so that a model's behaviour change can be attributed to that change rather than to rewording. `MANIFEST.json` records row counts and SHA-256 of every file in this directory; `tests/test_dataset.py` in the project repository checks every structural statement on this page against the files.

## What is in here

| File | Rows | Contents |
|---|---|---|
| `keystone_twins.jsonl` | 7,419 | Every twin with full metadata, three independent materiality ratings, mechanical quality flags, paraphrase fidelity |
| `keystone_core.jsonl` | 5,454 | Core layer: perturbation twins rated materiality 3 by a majority of raters, plus the negative controls rated 1, with no mechanical defect |
| (`in_strict` field) | 5252 | Strict layer: core, not rejected by both reviewer models as unnatural or as more than one edit, and the edit is tied to the rubric (at least one criterion depends on it; none for the negative control) |
| `reference_records.jsonl` | 550 | Every reference-pilot reply with its behaviour classification and rubric grades, in the format `keystone run` writes; `keystone show <id>` prints them next to a pair |
| `healthbench_style/<family>__<condition>.jsonl` | 1234 (`original`, `perturbed`) or 1132 (`paraphrase`) per family | HealthBench-compatible format, one file per (family, condition) |
| `healthbench_style/reference__natural_missing.jsonl` | 153 | Reference set: HealthBench `not-enough-context` conversations, unchanged, for how each model behaves when information is missing by nature |
| `reference_results.json` | | Formal pilot results for five assistants under the protocol's rules (see below) |
| `MANIFEST.json` | | Version, build time, per-file row counts and SHA-256 |

## Design

Nine families. Four are applied to every one of the 1234 base source conversations, so they are directly comparable within item; five more are added wherever the source supports them (see *Families in this release* below):

| Family | Operation | Expected safe behaviour | Twins | Core (majority materiality 3, no defect) |
|---|---|---|---|---|
| `missing_evidence` | Remove or neutralise exactly one load-bearing element the rubric relies on | Ask for it, or answer explicitly conditionally | 1234 | 454 |
| `conflicting_evidence` | Add one short credible statement that contradicts something already present | Point out the discrepancy and ask which is right | 1234 | 747 |
| `demographic_shift` | Change only a demographic, comorbidity or care-access attribute | Adjust dose, drug choice, or referral threshold | 1234 | 843 |
| `salient_distractor` | Add one medically salient but irrelevant fact | **Answer unchanged** (negative control) | 1234 | 1213 (rated materiality 1 by all three raters on 1178 items, by the majority on all 1234) |

Plus a **paraphrase control** for 1132 of the 1234 source conversations: the same last user message reworded with no clinical fact added or removed. Without it, a behaviour change under perturbation cannot be attributed to the perturbation ([Compared to What?, COLM 2026](https://arxiv.org/abs/2605.01048)). Paraphrase edits are larger than the removal edits, not matched to them (median relative edit distance 0.39 against 0.10 for `missing_evidence`), which makes the control conservative: a model that holds its stance under a larger rewording and changes it under a smaller removal is reacting to content.

**Source pool.** 1234 perturbable conversations from HealthBench `oss`, drawn from seven physician-agreed strata in which the physicians judged the message complete enough for a definite reply, so that removing or contradicting a piece of evidence should change the safe answer:

| Stratum (`group`) | HealthBench theme ∧ physician tag | Sources | Twins | Core | Strict |
|---|---|---|---|---|---|
| `enough_context` | context_seeking ∧ enough-context | 200 | 1218 | 890 | 867 |
| `cond_emergent` | emergency_referrals ∧ conditionally-emergent | 153 | 930 | 720 | 694 |
| `emergent` | emergency_referrals ∧ emergent | 136 | 703 | 484 | 459 |
| `non_emergent` | emergency_referrals ∧ non-emergent | 118 | 713 | 533 | 513 |
| `data_task` | health_data_tasks ∧ enough-info-to-complete-task | 212 | 1261 | 860 | 817 |
| `reducible_uncertainty` | hedging ∧ any-reducible-uncertainty | 231 | 1416 | 1039 | 1000 |
| `context_matters` | global_health ∧ context-matters-is-clear | 184 | 1152 | 908 | 882 |

4558 twins are single-turn and 2861 are multi-turn (456 of the 1260 sources are multi-turn); in multi-turn items only the edited user message differs from the source, the last one except in `missing_evidence_early` and in the `alternative_evidence_hard` twins whose value sits in an earlier turn, and every other turn is byte-identical to the source (checked by the tests). Paraphrase controls cover 424 of the 456 multi-turn sources. A further 153 `not-enough-context` conversations ship as `healthbench_style/reference__natural_missing.jsonl`, a reference set for how each model behaves when information is missing by nature rather than by construction.

**Label coverage by stratum.** The two original strata (`enough_context`, `cond_emergent`; 355 sources) carry the complete label set: three materiality raters on every twin, two independent naturalness verdicts on every `conflicting_evidence` twin, rubric-dependence labels from two independent models, and a model fidelity check on every paraphrase. The five strata added in 0.3.0 have three materiality raters on every twin; `MANIFEST.json` states the coverage of every label in this release (rubric-dependence labels on 7418 of 7419 twins, fidelity checks on 1234 of 1234 sources, second naturalness verdicts on 1234 of 1234 `conflicting_evidence` twins). A twin without a rubric-dependence label cannot enter the strict layer, and a paraphrase without a passed fidelity check is not released.

## How to run it

Every file in `healthbench_style/` uses HealthBench's own schema (`prompt`, `rubrics`, `example_tags`, `prompt_id`, `ideal_completions_data`), so an existing HealthBench harness runs it unchanged:

```python
# openai/simple-evals, healthbench_eval.py: pass the file as input_path
HealthBenchEval(grader_model=..., input_path="dist/healthbench_style/missing_evidence__perturbed.jsonl")
```

The added `example_tags` (`keystone_family:*`, `keystone_condition:*`, `keystone_materiality:*`, `keystone_turns:*`, `keystone_layer:*`) make simple-evals report per-tag scores for free. Each row also carries a `keystone` block with the source id, family, condition, what was changed, the expected safe behaviour, the three materiality ratings, the reviewer's naturalness and single-edit judgements, mechanical quality flags, and for paraphrase rows the fidelity verdict, so paired analysis is a join on `keystone.source_prompt_id`.

For paired outcomes directly, use the Inspect AI task in the project repository (`keystone/inspect_task.py`) or the `keystone` CLI and Python API (`pip install -e .`, `keystone run --help`): one sample is one (original, perturbed, paraphrase) triple, and the metrics are the protocol's quantities (adaptation-failure rate with Wilson interval, spurious-shift rate, McNemar test on the definitive rate, optional HealthBench rubric score under the stale and the still-applicable criteria). The three graders used in the reference results (official HealthBench rubric grader replicated verbatim, a rubric-applicability judge, and a behaviour classifier) live in `keystone/prompts.py`; the reference pipeline and the Inspect task use the identical text, and the tests check that.

## Reference results

`reference_results.json` holds the formal pilot (2026-09-03) computed with the protocol's rules from the per-reply grades in the project repository. Five assistants answered the 80 `missing_evidence` twins of the pilot set with their originals and paraphrase controls (temperature 0, no system prompt, 1500 output tokens); GPT-4.1 ran the three graders. The primary rule keeps the 32 twins whose median materiality rating is 3; pairs per model are 29 to 32 because 10 empty model outputs are treated as missing data. Rates are over pairs whose original reply was definitive; intervals are Wilson 95%.

| Assistant | Pairs | Adaptation failure | Spurious shift (paraphrase) | Unsafe action | Definitive rate, original → perturbed | McNemar p |
|---|---|---|---|---|---|---|
| `claude-sonnet-5` | 32 | 0.23 [0.10, 0.43] | 0.05 [0.01, 0.23] | 0.50 | 0.69 → 0.38 | 0.021 |
| `deepseek-v4-pro-0813` | 29 | 0.46 [0.30, 0.64] | 0.03 [0.01, 0.17] | 0.36 | 0.97 → 0.55 | 0.00049 |
| `gemini-3.8-flash` | 31 | 0.36 [0.21, 0.54] | 0.00 [0.00, 0.12] | 0.32 | 0.90 → 0.39 | 3.1e-05 |
| `llama-4-maverick` | 32 | 0.57 [0.39, 0.73] | 0.07 [0.02, 0.23] | 0.43 | 0.88 → 0.56 | 0.0063 |
| `gpt-5.6-terra` | 31 | 0.26 [0.13, 0.45] | 0.04 [0.01, 0.18] | 0.33 | 0.87 → 0.32 | 1.5e-05 |

On the 30 items with rubric grading, a mean of 38% to 40% of the original rubric criteria per item were judged inapplicable to the perturbed message, and the stale-rubric score was within 0.12 of the applicable-criteria score for every assistant (the removed criteria are mostly positive points the assistant no longer earns). On the 30 pilot items with rubric grading, the applicability judge marked inapplicable 70 percent of the criteria that an independent labeller tied to the removed element and kept 88 percent of the others (see `results/APPLICABILITY_AGREEMENT.md`; two model judgements, not ground truth). The file also carries two sensitivity rules for materiality, stance distributions, the not-enough-context reference set, and a five-model Kendall tau that the protocol treats as underpowered at this size.

## Ratings and their limits

Materiality (1 = a safe answer should not change, 3 = the original definitive answer is no longer supported) is rated independently by three language models: the authoring model plus two reviewers (`keystone.materiality_raters` names them). `materiality_majority` is the median of the three; over all twins it is 3 for 2824, 2 for 2001, 1 for 2395, and undefined for 199 twins with only two ratings.

**These ratings are not clinician-adjudicated.** Linear-weighted kappa between pairs of raters is 0.13 to 0.53 on the three perturbation families, so materiality is genuinely contested and the majority label should be treated as a screen, not a gold standard. The negative-control family is the exception: all three raters assign 1 on 1178 of 1234 items, so kappa is undefined there by construction. Clinician adjudication runs on a stratified subset and is released as a separate gold layer; rows in this release are silver, so do not describe results on them as clinician-validated.

Two further fields help you choose a stricter subset:

- `reviewer_natural` (does the modified message still read as something a person would send): false for 556 of the 1234 `conflicting_evidence` twins, whose contradictions are by construction unusual, for 38 `salient_distractor` twins and 5 `missing_evidence` twin. A second reviewer model judged naturalness independently on 1218 `conflicting_evidence` twins (`reviewer_natural_codex`): the two reviewers agree on 662 of 1218 (Cohen kappa 0.00) and both mark 0 as unnatural, 0 of them in the core layer. The second verdict uses a writing-only criterion (fluency, register, edit artefacts; a clinical contradiction alone does not make a twin unnatural, since the `conflicting_evidence` family exists to create contradictions). The core layer does not filter on naturalness; `keystone.reviewer_natural` and `keystone.reviewer_natural_codex` are there so you can, and a twin both reviewers reject is the natural first cut.
- `quality_flags`: mechanical checks (`tools/quality_checks.py`), such as an edit that is too large for a minimal perturbation. 280 twins carry a defect flag (69 `missing_evidence`, 15 `conflicting_evidence`); they stay in `keystone_twins.jsonl` for transparency and are excluded from the core layer and marked `in_core: false`.

**Each twin is tied to the rubric.** A reviewer model labelled, for every twin, which criteria of the original physician rubric depend on the edit (`rubric_dependent_criteria`): criteria that presuppose the removed or changed element, or, for `conflicting_evidence`, whose verdict depends on which side of the contradiction is true. Among labelled twins, 86 percent of `missing_evidence`, 95 percent of `conflicting_evidence` and 84 percent of `demographic_shift` twins touch at least one criterion; the negative control touches none on 98 percent of its twins, as intended. A second, independent labeller (Claude Sonnet) answered the same question on 1023 twins: the two agree on whether the edit touches any criterion on 75 percent of them, with a mean per-twin Jaccard of 0.50 between the two criterion sets (`rubric_dependent_criteria_claude`). The **strict layer** (`in_strict`, 5252 twins: 415 missing, 730 conflicting, 776 demographic, 1193 distractor) keeps core twins that pass this check and that the two reviewer models did not both reject as unnatural or as more than one edit; `load_pairs(family, layer="strict")` and `-T layer=strict` select it.

Paraphrase controls were checked for fidelity by a model (`paraphrase_faithful`, `paraphrase_fidelity_severity`). 99 sources whose paraphrase was judged to alter a clinical fact and 17 whose paraphrase changed a number are kept in `keystone_twins.jsonl` with `paraphrase_released: false` and are absent from the `*__paraphrase.jsonl` files; the released 1132 are those judged faithful.

## Licence and provenance

Source conversations and physician-written rubrics are from HealthBench, **MIT**, © OpenAI. Perturbed twins and paraphrase controls in this dataset are model-authored (`keystone.author`, `keystone.paraphrase_author`) and released under the same terms; see `LICENSE` in the repository. The HealthBench canary string is preserved in every row; per OpenAI's request, please do not post examples in plain text on the open web.

This dataset contains no patient data. Results on it do not establish clinical efficacy or patient outcomes, and must not be described as clinical deployment validation.

## Changes

- **0.7.0** (2026-10-19): the additional family `alternative_evidence_hard` (a value crosses a decision threshold); 26 further HealthBench sources that carry it; `demographic_shift` twins built on recurring attribute templates rewritten as revision 2; action lists version 2 on the twins whose state review was adjudicated. See *Release 0.7.0* below.
- **0.2.0** (2026-09-04): paraphrase controls extended from 191 single-turn sources to 328 of 355 sources including multi-turn; model fidelity check on every paraphrase with unfaithful ones withheld; third materiality rating filled where a reviewer had failed to return one; mechanical defects excluded from the core layer and flagged on every row; `ideal_completions_data` added for full HealthBench schema parity; `MANIFEST.json`, integrity tests, and the Inspect AI task added.
- **0.1** (2026-09-04): first export, 1,420 twins, 191 paraphrase controls.

## Decision-evidence layer (0.4.0)

Every released source carries a **decision frame** for its original message (`decision_frames.jsonl`: what is being decided, the action the stated evidence supports, the facts it rests on, whether urgent escalation is already warranted, the acceptable and forbidden reply behaviours), and every twin of the perturbation families carries an **evidence state** for the modified message with its acceptable actions, forbidden actions, decisive questions and the fact a reply must not assume (fields in `docs/SCHEMA.md`). The negative control's state is derived from the frame (the evidence still supports the original action by construction); the state of an `alternative_evidence` twin is derived from its authored alternative. Frames and states are drafted by Claude Sonnet and independently reviewed by Codex; every disagreement is released.

Coverage: decision frames for 1260 of 1260 released sources; evidence states on 7416 twins, of which 4420 annotated by the model and the rest derived; second-vendor review on 3575 annotated twins, agreeing with the evidence state on 73 percent; mechanism labels on 1234 of 1234 `demographic_shift` twins. The `alternative_evidence` family has 390 released twins (359 core, 352 strict). Sources are split 999 dev / 261 test by a hash of the source id; the quick set holds 350 twins. Every row is `tier: silver` (model-drafted, model-reviewed); rows confirmed by clinicians will be `gold`. The grader-validity set (`contrastive_replies.jsonl`) holds six authored replies with intended labels for 123 items.

## Release 0.7.0

<!-- release070:start -->
**`alternative_evidence_hard`**, an additional family (it is not one of the pre-specified confirmatory families). One numeric or time value in the conversation is changed so that it crosses a guideline, product-label or billing threshold, and nothing else in the message points at the change; the correct reply notices the crossing and adopts the action the new value calls for. Each twin records the threshold and where it comes from, the old and the new value, and what each side of the threshold implies (`threshold`, `threshold_value`, `threshold_unit`, `threshold_source`, `old_value`, `new_value`, `old_side`, `new_side`, `value_kind`), and is scored on its own outcome, `hard_outcome` (`necessary_update`). 113 twins (65 core, 64 strict, 52 primary) on 113 sources, 90 dev and 23 test; the changed value is duration time 38, age 26, lab value 26, vital sign 8, gestational age 5, other 4, dose 4, weight 2. 87 of the sources are base sources; 26 are HealthBench `oss` conversations new in this release (`group` `v4_<theme>`), which carry only this family and no paraphrase control, so the release now covers 1260 sources.

**`demographic_shift`, revision 2.** 577 twins whose attribute came from a small set of recurring templates were rewritten with a different attribute that bears on the decision, and every label was redone on the new text (mechanism, `advice_should_change`, evidence state and its review, the three materiality ratings, rubric dependence). The family now has 843 core, 776 strict and 437 primary twins. A rewritten row carries `revision: 2` and `supersedes: 1`; the public id `<source>::<family>::<condition>` always names the current revision, and `deprecated_twins.jsonl` keeps the 2371 superseded rows of this and earlier releases (`deprecated: true`, `superseded_by`) so that a result computed on an earlier release still maps to its text.

**Action lists, version 2.** On 2274 twins the acceptable actions, forbidden actions and decisive questions were reviewed comment by comment: the drafting vendor adjudicated every comment of the state reviewer and a second vendor verified every accepted edit, and only edits both accepted were applied. 1356 of these twins carry at least one of the 2284 applied edits. Such rows have `lists_version: 2` and keep the version-1 lists in `acceptable_actions_v1`, `forbidden_actions_v1` and `decisive_questions_v1`; no layer rule reads the lists, so the layers are unchanged by them.
<!-- release070:end -->

## Families in this release

<!-- families:start -->
| Family | Edit | Correct behaviour | Twins | Core | Strict | Primary |
|---|---|---|---|---|---|---|
| `conflicting_evidence` | add one credible statement that contradicts something present | name the discrepancy and ask which is right | 1234 | 747 | 730 | 499 |
| `demographic_shift` | change one attribute that bears on the decision | adjust the advice | 1234 | 843 | 776 | 437 |
| `missing_evidence` | remove one load-bearing fact from the last user message | ask for it, or answer conditionally on it | 1234 | 454 | 415 | 297 |
| `salient_distractor` | add one salient but irrelevant fact | answer unchanged (negative control) | 1234 | 1213 | 1193 | 1193 |
| `demographic_control` | add one attribute that does not bear on the decision | answer unchanged (negative control) | 948 | 908 | 879 | 879 |
| `buried_red_flag` | mention one red flag in passing, without alarm | advise urgent evaluation as the main answer | 814 | 779 | 767 | 767 |
| `alternative_evidence` | put the removed fact back with a value that supports a different action | change the action | 390 | 359 | 352 | 250 |
| `missing_evidence_early` | remove one load-bearing fact from an earlier user turn | ask for it, or answer conditionally on it | 218 | 86 | 76 | 36 |
| `alternative_evidence_hard` | move one value across a decision threshold, with nothing pointing at the change | notice the crossing and change the action | 113 | 65 | 64 | 52 |
<!-- families:end -->
