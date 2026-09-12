# Where Keystone sits

Clinical chat evaluation already has strong benchmarks, and two of them perturb cases the way Keystone does. This
page says what each one measures, so that a reader can decide which tool answers their question rather than taking
our word for it.

**Provenance of this table.** Compiled 2026-09-09, extended 2026-09-12, from abstracts, project pages and documentation, not from full
texts. Every arXiv identifier below was resolved and its title checked. Cells marked "not stated" mean the abstract does not say, not that the answer is no. Corrections are welcome
as an issue; we would rather fix this table than defend it.

| Benchmark | What it puts in front of the model | Paired edit of one fact | Negative control | Attribution control | Scores the rubric as well as the model | Who wrote the items |
|---|---|---|---|---|---|---|
| [HealthBench](https://openai.com/index/healthbench/) (OpenAI, 2025) | 5,000 health conversations, one physician rubric each | no | no | no | no, the rubric is the standard | physicians |
| [MedHELM](https://crfm.stanford.edu/helm/medhelm/latest/) (*Nature Medicine*, 2025) | 121 clinical tasks in a clinician-validated taxonomy, 37 evaluations | no | no | no | no | clinicians and existing datasets |
| [MediQ](https://arxiv.org/abs/2406.00922) (NeurIPS 2024) | MedQA and CRAFT-MD cases turned interactive: facts are withheld until the model asks | information is withheld, not edited | no | no | no | derived from existing datasets |
| [CRAFT-MD](https://www.nature.com/articles/s41591-024-03328-5) (*Nature Medicine*, 2025) | simulated patient dialogues, clinician-written vignettes | no | no | no | no | clinicians |
| [AgentClinic](https://arxiv.org/abs/2405.07960) (*npj Digital Medicine*, 2026) | agentic clinical environment, nine specialties, tool use | no | no | no | no | derived from MedQA and NEJM cases |
| [EviMed](https://arxiv.org/abs/2601.19773) (arXiv, 2026) | simulated consultation scored by information coverage | no | no | no | no | not stated |
| [Premature closure](https://arxiv.org/abs/2605.15000) (arXiv, 2026) | an 861-item HealthBench subset plus MedQA with the correct option removed | no, items are selected by existing labels | no | no | no | derived from existing labels |
| [Missing information, same-provider judges](https://arxiv.org/abs/2607.18828) (arXiv, 2026) | HealthBench conversations with the tail of the last user turn deleted | yes, one deletion operation | no | no | no | automatic deletion |
| [MamaBench](https://arxiv.org/abs/2607.14385) (arXiv, 2026) | 434 maternal and paediatric narratives as 217 counterfactual pairs | **yes, minimal change that shifts the diagnosis** | not stated | not stated | no | **clinicians** |
| [Causal Sensitivity Score](https://arxiv.org/abs/2605.30590) (arXiv, 2026) | 224 oncology tumour-board cases mutated along five dimensions | **yes, with a pre-registered correct direction** | not stated | not stated | no | not stated |
| **Keystone** | 1,236 HealthBench conversations, each with its physician rubric, as 7,318 twins in eight families | yes, one element per twin, eight operations | **yes, two families whose correct behaviour is no change** | **yes, a paraphrase-only twin on 1,119 sources** | **yes, per-criterion applicability after the edit** | models, on physician-written sources and rubrics; clinician panel open |

## The two closest neighbours, and what is different here

**Premature closure on HealthBench** ([arXiv:2605.15000](https://arxiv.org/abs/2605.15000)) asks our question on our
corpus and reports the same direction: on an 861-item HealthBench subset and on MedQA with the correct option removed,
frontier models keep answering definitively at rates from 21 to 45 percent, and up to 81 percent on the multiple-choice
variant. Two things are different here. It selects items using HealthBench's existing labels, so the comparison is
between items; Keystone edits one element of a conversation and compares each item with itself, which is what lets a
paraphrase-only twin absorb the effect of being edited at all. And its outcome is binary, whether a definitive answer
was still given; Keystone's per-item annotation names the decisive question, the acceptable actions and the forbidden
actions, so a reply that asks something can be scored on whether it asked the thing that settles the case.

**Deletion with a judge panel** ([arXiv:2607.18828](https://arxiv.org/abs/2607.18828)) is the only other work that
edits HealthBench conversations directly, and it already shows that apparent safety moves when the judge changes. It
uses one operation, deleting the tail of the last user turn, with no negative control, so a reader cannot separate a
reaction to the missing evidence from a reaction to a truncated message. Keystone's eight operations include two
families built so that the correct behaviour is no change at all, which is the comparison that makes the other six
interpretable.

## What a paired design has to clear

Two 2026 papers argue that counterfactual clinical evaluations report effects they cannot attribute. Re-sampling the
identical unedited case gives an average per-action flip rate of 8.7 percent
([arXiv:2609.03221](https://arxiv.org/abs/2609.03221)), and on MedPerturb a gender swap flips 14.9 percent of answers
against 14.1 percent for a paraphrase that changes nothing
([arXiv:2605.01048](https://arxiv.org/abs/2605.01048)). Both conclude that a perturbation effect is only interpretable
next to a baseline of the same shape. That is the reason Keystone ships two of them rather than one: a paraphrase-only
twin of the same source, and two families whose insertion is the same size as a perturbation family's but whose correct
answer does not move. The floor those papers measure is reported here as its own number, from re-asking the identical
request, alongside every effect.

## What is genuinely ours

**The rubric is measured, not assumed.** Every benchmark in this table treats its rubric or answer key as fixed and
asks how the model scores against it. Keystone asks the second question: after one fact is gone, how much of the
physician's rubric can still be fairly applied to a reply. On the graded pilot items, 29 percent of criteria overall and 35 to 40 percent on median-materiality-3 twins
could not, which is a statement about rubric-based clinical evaluation rather than about any model.

**The control structure.** A perturbation benchmark without controls cannot separate "the model reacted to the
evidence" from "the model reacted to being edited". Keystone ships both halves: two families whose correct behaviour
is to answer unchanged, and a paraphrase-only twin that changes the wording and nothing else. In the reference pilot
the paraphrase moved the definitive rate by at most 0.07 while removing an element moved it by 0.31 to 0.55.

**Scale on HealthBench messages with a physician standard attached.** The paired counterfactual designs above are clinician-
authored and small, 217 pairs and 224 cases. Keystone is 7,318 twins over 1,236 HealthBench conversations (largely synthetic by construction, each with its physician-written rubric), each
carrying the rubric its own physicians wrote, which is what makes the applicability question askable at all.

## What is not ours

**Counterfactual perturbation of clinical cases is not a new idea.** MamaBench and the Causal Sensitivity Score work
got there independently, and MamaBench's pairs are written by clinicians while ours are written by models. If your
question is "does this model update its diagnosis when one parameter changes, on cases a clinical team wrote", those
are the better instruments today, and MamaBench's Bias Trap Rate is close in spirit to our forbidden-action outcome.

**Interactive information seeking is not a new idea either.** MediQ, CRAFT-MD and EviMed measure asking behaviour in
multi-turn settings, which Keystone deliberately does not: our twins are single-shot, so we measure what a reply
commits to rather than how a dialogue unfolds.

**The judges are general-purpose models on purpose.** Medically fine-tuned multimodal models score 54 to 55 percent as
judges of medical replies where general models score 63 to 69 percent, against a three-physician majority
([arXiv:2508.21430](https://arxiv.org/abs/2508.21430)). A review of 49 healthcare judge studies finds 36 reported any
human validation at all, with a median of three experts ([arXiv:2604.25933](https://arxiv.org/abs/2604.25933)). The
three-vendor panel and the judge validity set in [`JUDGE_CHECK.md`](JUDGE_CHECK.md) are what we report instead of a
claim that the judge is reliable.

**HealthBench has moved on, and Keystone sits on the earlier corpus.** HealthBench Professional
([arXiv:2604.27470](https://arxiv.org/abs/2604.27470)) is built from real clinician chats rather than the largely
synthetic conversations of the 2025 release that Keystone perturbs. Running the same construction on that corpus is the
first item of the portability work, not a correction to this release.

**The labels in this release are `tier: silver`,** the tier for a label a model wrote and a model from another vendor
reviewed; `gold` is the tier a clinician-confirmed row carries. The two checks in [`RUBRIC_ANCHOR.md`](RUBRIC_ANCHOR.md)
and [`IDEAL_ANSWER_CHECK.md`](IDEAL_ANSWER_CHECK.md) anchor those labels against physician-written artefacts we did not
produce, which is convergent evidence rather than adjudication.
