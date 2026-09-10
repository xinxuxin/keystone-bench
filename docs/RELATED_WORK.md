# Where Keystone sits

Clinical chat evaluation already has strong benchmarks, and two of them perturb cases the way Keystone does. This
page says what each one measures, so that a reader can decide which tool answers their question rather than taking
our word for it.

**Provenance of this table.** Compiled 2026-09-09 from abstracts, project pages and documentation, not from full
texts. Cells marked "not stated" mean the abstract does not say, not that the answer is no. Corrections are welcome
as an issue; we would rather fix this table than defend it.

| Benchmark | What it puts in front of the model | Paired edit of one fact | Negative control | Attribution control | Scores the rubric as well as the model | Who wrote the items |
|---|---|---|---|---|---|---|
| [HealthBench](https://openai.com/index/healthbench/) (OpenAI, 2025) | 5,000 health conversations, one physician rubric each | no | no | no | no, the rubric is the standard | physicians |
| [MedHELM](https://crfm.stanford.edu/helm/medhelm/latest/) (*Nature Medicine*, 2025) | 121 clinical tasks in a clinician-validated taxonomy, 37 evaluations | no | no | no | no | clinicians and existing datasets |
| [MediQ](https://arxiv.org/abs/2406.00922) (NeurIPS 2024) | MedQA and CRAFT-MD cases turned interactive: facts are withheld until the model asks | information is withheld, not edited | no | no | no | derived from existing datasets |
| [CRAFT-MD](https://www.nature.com/articles/s41591-024-03328-5) (*Nature Medicine*, 2025) | simulated patient dialogues, clinician-written vignettes | no | no | no | no | clinicians |
| [AgentClinic](https://arxiv.org/abs/2405.07960) (*npj Digital Medicine*, 2026) | agentic clinical environment, nine specialties, tool use | no | no | no | no | derived from MedQA and NEJM cases |
| [EviMed](https://arxiv.org/abs/2601.19773) (arXiv, 2026) | simulated consultation scored by information coverage | no | no | no | no | not stated |
| [MamaBench](https://arxiv.org/abs/2607.14385) (arXiv, 2026) | 434 maternal and paediatric narratives as 217 counterfactual pairs | **yes, minimal change that shifts the diagnosis** | not stated | not stated | no | **clinicians** |
| [Causal Sensitivity Score](https://arxiv.org/abs/2605.30590) (arXiv, 2026) | 224 oncology tumour-board cases mutated along five dimensions | **yes, with a pre-registered correct direction** | not stated | not stated | no | not stated |
| **Keystone** | 1,236 HealthBench conversations, each with its physician rubric, as 7,318 twins in eight families | yes, one element per twin, eight operations | **yes, two families whose correct behaviour is no change** | **yes, a paraphrase-only twin on 1,119 sources** | **yes, per-criterion applicability after the edit** | models, on physician-written sources and rubrics; clinician panel open |

## What is genuinely ours

**The rubric is measured, not assumed.** Every benchmark in this table treats its rubric or answer key as fixed and
asks how the model scores against it. Keystone asks the second question: after one fact is gone, how much of the
physician's rubric can still be fairly applied to a reply. On the graded pilot items, 35 to 40 percent of criteria
could not, which is a statement about rubric-based clinical evaluation rather than about any model.

**The control structure.** A perturbation benchmark without controls cannot separate "the model reacted to the
evidence" from "the model reacted to being edited". Keystone ships both halves: two families whose correct behaviour
is to answer unchanged, and a paraphrase-only twin that changes the wording and nothing else. In the reference pilot
the paraphrase moved the definitive rate by at most 0.07 while removing an element moved it by 0.31 to 0.55.

**Scale on real messages with a physician standard attached.** The paired counterfactual designs above are clinician-
authored and small, 217 pairs and 224 cases. Keystone is 7,318 twins over 1,236 real HealthBench conversations, each
carrying the rubric its own physicians wrote, which is what makes the applicability question askable at all.

## What is not ours

**Counterfactual perturbation of clinical cases is not a new idea.** MamaBench and the Causal Sensitivity Score work
got there independently, and MamaBench's pairs are written by clinicians while ours are written by models. If your
question is "does this model update its diagnosis when one parameter changes, on cases a clinical team wrote", those
are the better instruments today, and MamaBench's Bias Trap Rate is close in spirit to our forbidden-action outcome.

**Interactive information seeking is not a new idea either.** MediQ, CRAFT-MD and EviMed measure asking behaviour in
multi-turn settings, which Keystone deliberately does not: our twins are single-shot, so we measure what a reply
commits to rather than how a dialogue unfolds.

**The labels in this release are `tier: silver`,** the tier for a label a model wrote and a model from another vendor
reviewed; `gold` is the tier a clinician-confirmed row carries. The two checks in [`RUBRIC_ANCHOR.md`](RUBRIC_ANCHOR.md)
and [`IDEAL_ANSWER_CHECK.md`](IDEAL_ANSWER_CHECK.md) anchor those labels against physician-written artefacts we did not
produce, which is convergent evidence rather than adjudication.
