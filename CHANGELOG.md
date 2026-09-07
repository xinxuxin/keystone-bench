# Changelog

## 0.4.0 (2026-09-06)

- Decision–evidence layer: a decision frame per source and an evidence state with acceptable actions, forbidden actions, decisive questions and the fact a reply must not assume per twin; drafted by Claude Sonnet, reviewed by Codex, every disagreement released; the negative control's state is derived from the frame.
- Fifth family `alternative_evidence` (391 twins): the removed fact put back with a value that supports a different action, so one decision is seen in three evidence states.
- Action judge and action outcomes (forbidden action, effective completion, necessary update, decisive question, escalation, stability), all with every judged item in the denominator; `keystone regress` for version-to-version comparison.
- Layers and splits: `primary` (strict, state-consistent, reviewer agreed with the behaviour the state calls for), `quick` (40 strict dev twins per family), dev/test split by source, `tier` (silver now, gold when clinician-confirmed).
- With two materiality raters the label is defined only when they agree.
- Demographic twins labelled with the mechanism of the change and whether the advice should change.
- Grader-validity set: six authored replies with intended labels per item (`contrastive_replies.jsonl`), and `tools/judge_check.py`.

## 0.3.0 (2026-09-06)

- Renamed from MedVerify to Keystone: the package and CLI are `keystone`, the distribution is `keystone-bench` (PyPI `keystone` belongs to OpenStack).
- Source pool expanded from 355 to 1,236 released conversations across seven physician-agreed strata (the two original strata plus `emergent`, `non_emergent`, `data_task`, `reducible_uncertainty`, `context_matters`): 4,944 twins, all with three materiality raters, 1,788 multi-turn.
- Release rule tightened: a paraphrase control is released only after a model fidelity check passes (unchecked controls are withheld, not assumed faithful).
- Family-aware outcomes: `adaptation_failure` is defined on the three perturbation families only, `control_drift` on the negative control only. Three unconditional metrics added (`unsupported_action`, `answered_when_sufficient`, `held_answer_on_control`) so that a model which always refers out or always asks remains visible; `tools/trivial_baselines.py` checks that no fixed strategy scores well on every axis.
- The behaviour classifier and the applicability judge receive the full conversation, not only the last user message.
- Second, independent rubric-dependence labelling (`rubric_dependent_criteria_claude`) on the 1,420 twins of the original strata, released for agreement analysis.
- Public distribution format: the repository stores the words we wrote plus span references into HealthBench (`release/edits.jsonl`); `tools/build_release.py` rebuilds `dist/` byte for byte from OpenAI's public copy of HealthBench.

## 0.2.0 (2026-09-04)

- Paraphrase controls extended from 191 single-turn sources to 328 of 355 sources including multi-turn; every control checked for fidelity by a model, unfaithful ones withheld.
- Mechanical defects (`quality_flags`) excluded from the core layer; checks for near-duplicate twins across families and for a paraphrase identical to the perturbed message.
- Second, independent naturalness judgement on every `conflicting_evidence` twin (`reviewer_natural_codex`) under a writing-only criterion.
- Per-twin link to the rubric: which criteria depend on the edit (`rubric_dependent_criteria`), for all four families; new `strict` layer.
- Reference set `reference__natural_missing.jsonl` (153 conversations); `MANIFEST.json` with row counts and SHA-256 of every file; `reference_results.json` and `reference_records.jsonl`.
- `keystone` package, CLI, Inspect AI task, and 40+ tests that need no key.

## 0.1 (2026-09-04)

First export: 1,420 twins over 355 sources, 191 paraphrase controls, HealthBench-style files, first data card.
