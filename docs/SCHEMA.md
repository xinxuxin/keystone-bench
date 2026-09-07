# Release schema

Two layers, both JSON Lines. `tests/test_dataset.py::test_schema_doc_matches_files` checks that the field lists on this page are exactly the fields in the released files.

## `dist/healthbench_style/<family>__<condition>.jsonl`

One row per (source conversation, family, condition). HealthBench's own fields come first, so `openai/simple-evals` reads the file unchanged; Keystone adds `canary` and a `keystone` block.

| Field | Type | Meaning |
|---|---|---|
| `prompt_id` | str | `<source_prompt_id>::<family>::<condition>`; unique within a file |
| `prompt` | list of `{role, content}` | the conversation; the last message is the user's. In `perturbed` and `paraphrase` rows only the last user message differs from the source, earlier turns are byte-identical |
| `rubrics` | list of `{criterion, points, tags}` | the physician rubric of the **source** conversation, unchanged in every condition (that is the point: the stale-rubric score is what a leaderboard would report) |
| `example_tags` | list of str | HealthBench's tags plus `keystone_family:*`, `keystone_condition:*`, `keystone_materiality:*`, `keystone_turns:{single,multi}`, `keystone_layer:{strict,core,extended}` |
| `ideal_completions_data` | null | present for schema parity with HealthBench; Keystone ships no reference completions |
| `canary` | str | the HealthBench canary string, preserved on every row |
| `keystone` | object | see below |

`keystone` block:

| Field | Type | Meaning |
|---|---|---|
| `source_prompt_id` | str | HealthBench `prompt_id` of the source; join key across conditions and families |
| `family` | str | `missing_evidence`, `conflicting_evidence`, `demographic_shift`, `salient_distractor` |
| `condition` | str | `original`, `perturbed`, `paraphrase` |
| `group` | str | source stratum, HealthBench theme ∧ physician-agreed tag: `enough_context` (context_seeking ∧ enough-context), `cond_emergent` (emergency_referrals ∧ conditionally-emergent), `emergent` (emergency_referrals ∧ emergent), `non_emergent` (emergency_referrals ∧ non-emergent), `data_task` (health_data_tasks ∧ enough-info-to-complete-task), `reducible_uncertainty` (hedging ∧ any-reducible-uncertainty), `context_matters` (global_health ∧ context-matters-is-clear) |
| `turns` | int | number of messages in the conversation |
| `in_core` | bool | median materiality 3 (1 for the negative control) and no mechanical defect |
| `in_strict` | bool | `in_core`, and the two reviewer models did not both reject the twin as unnatural or as more than one edit, and the edit is tied to the rubric: at least one criterion in `rubric_dependent_criteria` for the perturbation families, none for the negative control |
| `rubric_dependent_criteria` | list of int or null | indices into `rubrics` of the criteria whose fair judgement depends on the edit (presuppose the removed or changed element; or, for `conflicting_evidence`, would be judged differently depending on which side of the contradiction is true), labelled by a reviewer model (codex) |
| `rubric_dependent_criteria_claude` | list of int or null | the same question answered independently by a second model (Claude Sonnet via a Claude Code sub-agent); released for agreement analysis and filtering, not used in the layer definitions |
| `removed_or_changed` | str | what the twin changes, in the author's words; this is the "missing element" handed to the behaviour classifier |
| `why_load_bearing` | str | why the change decides the answer |
| `expected_safe_behavior` | str | what a safe reply to the perturbed message does |
| `materiality_majority` | int or null | median of the three ratings; null when a rating is missing |
| `materiality_raters` | `{author, reviewer_sonnet, reviewer_codex}` | the three ratings, 1 to 3 |
| `author` | str | the model that wrote the twin |
| `reviewer_natural`, `reviewer_natural_codex` | bool or null | does the perturbed message still read as something a person would write, per two independent reviewer models (the second was run on all `conflicting_evidence` twins and on twins the first rejected) |
| `reviewer_single_edit`, `reviewer_single_edit_codex` | bool or null | was exactly one thing changed, per the same two reviewers |
| `quality_flags` | list of str | mechanical checks from `tools/quality_checks.py` (`C3_edit_too_large`, `C3_missing_grew_a_lot`, `C3_added_but_shorter`, `C5_paraphrase_numbers_changed`, `C5R_paraphrase_negation_count_differs`, `C7_near_duplicate_across_families`, `C8_paraphrase_equals_perturbed`); C5 flags concern the paraphrase, `C5R` is a screen not a defect |
| `paraphrase_author` | str or null | on paraphrase rows, the model that wrote the control |
| `paraphrase_faithful` | bool or null | on paraphrase rows, the fidelity checker's verdict (only faithful controls are released) |

`reference__natural_missing.jsonl` carries the same HealthBench fields for the 153 `not-enough-context` conversations with `keystone = {source_prompt_id, family: "reference", condition: "natural_missing", group, turns}`.

## `dist/keystone_twins.jsonl` and `dist/keystone_core.jsonl`

One row per twin with everything the pipeline recorded. `keystone_core.jsonl` is the subset with `in_core = true`.

| Field | Meaning |
|---|---|
| `prompt_id`, `family`, `group`, `turns` | as above (`prompt_id` here is the bare source id) |
| `original_prompt`, `perturbed_prompt` | last user message before and after the change |
| `removed_or_changed`, `why_load_bearing`, `expected_safe_behavior` | as above |
| `materiality`, `confidence`, `author` | the author's rating (1 to 3), its self-reported confidence, and the authoring model |
| `reviewer_materiality`, `reviewer_note`, `reviewer_natural`, `reviewer_single_edit` | first reviewer model |
| `codex_materiality`, `codex_materiality_note`, `codex_natural`, `codex_single_edit` | second reviewer model |
| `n_raters`, `materiality_majority` | number of valid ratings and their median (null unless all three are present) |
| `paraphrase_prompt`, `paraphrase_note`, `paraphrase_author` | the paraphrase control (shared by all four twins of a source) |
| `paraphrase_faithful`, `paraphrase_fidelity_severity` | fidelity check: `none`, `minor`, `material`; `material` controls are not released |
| `rubric_dependent_criteria`, `n_rubric_dependent`, `rubric_dependence_rater` | criteria that depend on the edit (primary labeller), their count, and the labeller id |
| `rubric_dependent_criteria_claude` | the second labeller's set |
| `quality_flags`, `in_core`, `in_strict`, `paraphrase_released` | release decisions, computed by `tools/build_release.py` |

## `dist/reference_records.jsonl`

One row per (reference model, source) from the formal pilot, in the format `keystone run` writes: `id`, `family`, `source_id`, `model`, `judge`, `materiality_majority`, `materiality_raters`, `group`, `removed_or_changed`, `replies` (condition → text), `behavior` (condition → classifier JSON), and `rubric` where graded (`score_original`, `score_perturbed_stale`, `score_perturbed_applicable`, `inapplicable_share`, per-criterion `grades`). Rows with `family: "reference"` hold the reference-set replies under condition `natural`. `keystone show <id>` prints them next to the pair.

## `dist/reference_results.json`

The formal pilot under the protocol's rules: `setup` (models, judge, generation settings, outcome definitions), `materiality_rules`, and `results.<rule>.models.<model>` with `adaptation_failure`, `ack_but_answer`, `unsafe_action`, `spurious_shift` as `{k, n, rate, wilson95}`, `definitive_rate` with the exact McNemar test, `stance_counts`, the reference-set behaviour, and `rubric` where graded. `keystone reference` prints it.

## `dist/MANIFEST.json`

`version`, `built`, `counts` (twins, core, strict, sources, sources with a released paraphrase, sources whose paraphrase was fidelity-checked, twins with a defect, twins with rubric-dependence labels from each labeller, conflicting twins with a second naturalness verdict, sources still in progress and not released, per-family and per-stratum counts, rows per file) and `files` with row count and SHA-256 of every released file. `keystone validate` recomputes it.

## Decision-evidence layer (0.4.0)

Every released source carries a **decision frame** for its original message (`dist/decision_frames.jsonl`, one row per source: `prompt_id`, `group`, `frame`, `annotator`), and every twin of the three perturbation families and of `alternative_evidence` carries an **evidence state** for the modified message. Both are model-drafted and model-reviewed (`tier: silver`); a clinician-confirmed row will carry `tier: gold` and `clinician_confirmed: true`.

`frame` fields:

| Field | Type | Meaning |
|---|---|---|
| `decision_target` | str | what the user needs decided or produced now: the decision, not the topic |
| `supported_action` | str | the action a careful clinician would take on exactly the stated evidence |
| `load_bearing_evidence` | list of str | the facts in the message that `supported_action` rests on |
| `escalation_sufficient` | bool | the message already warrants urgent escalation, so asking first would be a delay |
| `acceptable_actions` | list of str | reply behaviours a clinician would accept on the original message |
| `forbidden_actions` | list of {action, why} | behaviours that would be unsafe or wrong on the original message |
| `decisive_questions_original` | list of str | questions that would still change the action on the original (usually empty) |

Per-twin fields, in the `keystone` block of the HealthBench-style rows and at top level in `keystone_twins.jsonl`:

| Field | Type | Meaning |
|---|---|---|
| `evidence_state` | str | one of `sufficient_for_original_action`, `insufficient_ambiguous`, `sufficient_for_alternative_action`, `sufficient_for_escalation`, `contradiction_unresolved` |
| `alternative_action` | str or null | the action the evidence would support if the uncertainty resolved against the original action |
| `acceptable_actions` | list of str | what a safe reply may do on the modified message; conditional answers included when acceptable |
| `forbidden_actions` | list of {action, why} | what would be unsafe or wrong on the modified message; the original action when it is no longer supported |
| `decisive_questions` | list of str | questions whose answer would change the action; generic information gathering is not decisive |
| `absent_is_not_negative` | str or null | the fact a reply must not assume (a fact that is not stated is unknown, not false) |
| `escalation_sufficient` | bool or null | urgent escalation already warranted on the modified message |
| `state_annotator` | str | `cli-claude:sonnet` for annotated twins; `derived:frame` for the negative control (its state is the frame by construction); `derived:author` for `alternative_evidence` |
| `state_review_agree` | bool or null | the second-vendor reviewer agreed with `evidence_state` (`state_review` holds the full review in `keystone_twins.jsonl`) |
| `mechanism` | str or null | `demographic_shift` only: `age`, `sex_gender`, `pregnancy_lactation`, `comorbidity`, `medication`, `allergy`, `access_to_care`, `care_setting`, `social_context`, `other` |
| `advice_should_change` | str or null | `demographic_shift` only: `yes`, `no`, `uncertain` |
| `split` | str | `dev` or `test`, by source (about 20% test); all twins and controls of a source share a side |
| `in_quick` | bool | the fixed quick set: 40 strict, state-consistent dev twins with a control per family |
| `tier` | str | `silver` (model-drafted and model-reviewed) or `gold` (clinician-confirmed) |
| `edited_turn` | int | index of the edited message in the conversation; the last user turn for every family except `missing_evidence_early`, which removes the fact from an earlier user turn. The paraphrase control always rewords the last user turn |
| `state_consistent` | bool or null | the annotated evidence state agrees with what the family's edit is designed to do (missing: ambiguous or escalation; conflicting: contradiction; demographic and alternative evidence: alternative action or escalation; controls: original action). A twin whose edit did not do what its family says is released but flagged |
| `acts_as_control` | bool | `demographic_shift` twin whose attribute does not bear on the decision (`advice_should_change: no`) and whose state keeps the original action: an extra negative control |
| `state_review_behaviour_agree` | bool or null | the second reviewer agreed with the state at the level of the behaviour it calls for (`insufficient_ambiguous` and `contradiction_unresolved` both call for asking; `sufficient_for_alternative_action` for changing the action; `sufficient_for_escalation` for escalating; `sufficient_for_original_action` for holding) |
| `in_primary` | bool | the layer the headline numbers use: strict, state-consistent, and (for an annotated state) the second reviewer agreed with the behaviour the state calls for; a derived state (negative control, `alternative_evidence`) has no review by construction |
| `reviewer_model` | str | which model filled the `reviewer_*` materiality slot |

`alternative_evidence` twins additionally carry `alternative_fact` (the value that replaced the removed fact) and `expected_action` (the action the evidence now supports). Each is derived from a strict `missing_evidence` twin of the same source, so the source is seen in three evidence states: original (supports A), missing (ask or condition), alternative (supports B).

Fields that appear only in `keystone_twins.jsonl` (the full twin record):

| Field | Type | Meaning |
|---|---|---|
| `has_decision_frame` | bool | the source carries a decision frame |
| `state_note` | str or null | the state annotator's one-sentence rationale |
| `state_review` | object or null | the second reviewer's full verdict (`agree_state`, `state_if_different`, `acceptable_actions_wrong`, `acceptable_actions_missing`, `forbidden_actions_wrong`, `forbidden_actions_missing`, `decisive_questions_ok`, `escalation_sufficient`, `materiality`, `note`) |
| `state_reviewer` | str or null | the reviewer's model spec |
| `mechanism_note` | str or null | one clause on the mechanism label |
| `alternative_fact` | str or null | `alternative_evidence`: the value that replaced the removed fact |
| `expected_action` | str or null | `alternative_evidence`: the action the evidence now supports |
| `clinician_confirmed` | bool or null | set when a clinician has confirmed the row (gold tier); null until then |
| `tempting_adjustment` | str or null | `demographic_control`: what an over-adjusting assistant might wrongly change |

