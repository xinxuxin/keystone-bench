# Contributing

## Running a model

```bash
pip install -e ".[dev]"
python tools/build_release.py          # fetches HealthBench from OpenAI, rebuilds dist/ locally
export OPENROUTER_API_KEY=...          # or OPENAI_API_KEY, or point --base-url at any OpenAI-compatible server
keystone estimate --family missing_evidence --rubric        # calls and tokens before spending anything
keystone run --family missing_evidence --model openrouter/openai/gpt-5.6-terra --judge openrouter/anthropic/claude-sonnet-5
```

Rules the protocol asks you to keep so that numbers are comparable:

- temperature 0, no system prompt, 1,500 output tokens for the model under test (the defaults);
- a judge from a different model family than the model under test; where you can afford it, run two or three judges
  from different vendors over the same replies and report `keystone panel` alongside the per-judge values. Judge choice
  moves the absolute level substantially, and a single judge that shares a vendor with the model under test is the
  weakest configuration;
- report the layer (`quick`, `strict`, `core` or `all`), the split (`dev`, `test` or `all`) and the benchmark version from `MANIFEST.json`; tune on `dev`, report on `test`;
- report the action outcomes (`forbidden_action`, `effective_completion`, `necessary_update`, `decisive_question_hit`, `stable_on_control`) from the action judge; they put every judged item in the denominator and are the primary outcomes from 0.4.0;
- report the paraphrase control (`spurious_shift`) next to the adaptation-failure rate. A run whose spurious shift exceeds 0.10 does not support an attribution to the perturbation;
- report the three unconditional metrics (`unsupported_action`, `answered_when_sufficient`, `held_answer_on_control`) next to the conditional ones. A model that always refers out or always asks has no denominator on the conditional metrics and is only visible on these;
- empty model outputs are missing data: the runner never sends them to the judge and they enter no denominator (`n_empty_replies` in `summary.json`). Reasoning models can exhaust `--max-tokens`; raise it rather than counting silence as a stance.

`keystone run` writes `records.jsonl` (every reply and classification), `summary.json` (all outcomes with intervals) and `REPORT.md` into `runs/<family>__<layer>__<model>/`.

## Submitting results

Open a pull request that adds your `summary.json` and `records.jsonl` under `results/community/<model>/`, named `<family>__<layer>.json` and `.jsonl`, with the endpoint, date and judge in the PR body. [`results/community/README.md`](results/community/README.md) states what makes a submission comparable. Reference numbers in `release/reference_results.json` were produced from the same kind of records with the same code; the results table is regenerated from submissions.

## Changing the data

The repository stores what we wrote (`release/metadata.jsonl`, `release/edits.jsonl`, `release/reference_ids.json`); `dist/` is built from those and HealthBench and is never committed. To propose a change to a twin, edit the corresponding row in `release/`, rebuild, and run the checks:

```bash
python tools/build_release.py
python tools/quality_checks.py         # mechanical checks C1 to C8 on the rebuilt dist
python tools/trivial_baselines.py      # the metrics must still expose every fixed strategy
python -m pytest -q
```

Layer membership (`in_core`, `in_strict`, `paraphrase_released`) is computed by `tools/build_release.py` from the ratings, never stored. Bump `VERSION` in `tools/build_release.py`, `keystone/__init__.py` and `pyproject.toml` together, and add a line to `CHANGELOG.md`.

## Validity checks

Three checks test the labels against measured behaviour and against physician-written artefacts rather than
against another model, and none needs a key: `make anchors` regenerates `docs/BEHAVIOUR_ANCHOR.md`,
`docs/RUBRIC_ANCHOR.md` and `docs/IDEAL_ANSWER_CHECK.md` at full resampling. The test suite runs the same three
scripts end to end with the resampling turned down (`KEYSTONE_BOOT`, `KEYSTONE_PERM`, `KEYSTONE_NULL_DRAWS`),
so CI catches a script that stops working on the current release without recomputing the published intervals. `make
judge-rescore` rescores the shipped judge run after a scoring change, also without calling anything; only a
judge or prompt change needs `make judge-check`, which does call a judge.

## Tests

`python -m pytest -q` runs three groups, none of which needs a key: structural checks of the rebuilt release against the data card and schema (`tests/test_dataset.py`), the package API on fake models (`tests/test_package.py`), and the Inspect task on mock models (`tests/test_inspect_task.py`).

## Licence

MIT. Source conversations and rubrics are HealthBench (OpenAI, MIT); keep the canary field and do not post items in plain text on the open web.
