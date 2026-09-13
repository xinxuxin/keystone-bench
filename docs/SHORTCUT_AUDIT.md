# Does the edit leave a fingerprint a model could answer instead of the evidence

Every paired-perturbation benchmark inherits this objection: the edit changes the surface of the message, so an assistant reacting to "this text was tampered with" scores as though it reacted to the evidence. The paraphrase control answers the behavioural half. This page answers the measurement half, by asking how visible each edit is, whether visibility explains what models did, and what the edits have in common that an authoring pass should remove.

The detector is a bag-of-words logistic regression trained on other sources and scored as a two-alternative forced choice: it sees both versions of a held-out source and picks the edited one, so chance is 0.50. It is a floor on detectability rather than a ceiling, which is why the sections after the first matter more than the first.

## How visible is each edit

Two-alternative forced choice on held-out sources, chance 0.50. `Length only` picks by which version is longer, so it is the part of detectability that needs no vocabulary at all.

| Family | Sources | original vs twin | length only | original vs control | twin vs control | Heaviest tokens in the twin |
|---|---|---|---|---|---|---|
| `alternative_evidence` | 390 | **0.72** | 0.73 | 0.86 | 0.80 | `it's`, `fine`, `month`, `like` |
| `buried_red_flag` | 814 | **1.00** | 1.00 | 0.84 | 0.98 | `since`, `yesterday`, `days`, `today` |
| `conflicting_evidence` | 1234 | **1.00** | 0.99 | 0.85 | 0.96 | `since`, `last`, `still`, `morning` |
| `demographic_control` | 948 | **0.99** | 1.00 | 0.85 | 0.91 | `driver`, `truck`, `long`, `haul` |
| `demographic_shift` | 1234 | **0.96** | 0.94 | 0.85 | 0.94 | `pregnant`, `insurance`, `health`, `area` |
| `missing_evidence` | 1234 | **0.91** | 0.93 | 0.85 | 0.89 | `it's`, `don't`, `actually`, `sure` |
| `missing_evidence_early` | 218 | **0.87** | 0.92 | 0.73 | 0.80 | `he's`, `something`, `sometimes`, `feeling` |
| `salient_distractor` | 1234 | **1.00** | 1.00 | 0.85 | 0.96 | `years`, `daily`, `last`, `take` |

## What a policy that never reads the evidence scores

Six fixed policies, scored by the same action rules as a real reply, each side judged against its own annotation. None of them reads the conversation. Held-out split.

| policy | `missing_evidence` | `conflicting_evidence` | `buried_red_flag` | `salient_distractor` | `demographic_control` |
|---|---|---|---|---|---|
| `always_definitive` <br><span style='font-weight:400'>commits to the original action every time</span> | **+0.871** | **+0.993** | **+1.000** | +0.000 | +0.000 |
| `parrot_then_act` <br><span style='font-weight:400'>names the gap, then commits anyway</span> | **+0.871** | **+0.993** | **+1.000** | +0.000 | +0.000 |
| `always_ask` <br><span style='font-weight:400'>asks the decisive question, gives nothing</span> | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| `always_conditional` <br><span style='font-weight:400'>hedges every answer on the unknown</span> | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| `always_escalate` <br><span style='font-weight:400'>sends everyone to urgent evaluation</span> | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| `always_refuse` <br><span style='font-weight:400'>refers out, gives nothing</span> | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |

Bold marks an interval excluding zero.

**On the perturbation families a blind policy scores high, and that is what the outcome is for.** `always_definitive` reaches +0.87 to +1.00: it commits to the same course of action on both sides, and on a perturbation family the edit is precisely what moves that action onto the forbidden list. A system that adapted perfectly would score 0 here and one that never adapted would score what this policy scores, so the policy sets the top of the scale rather than exposing a hole. Evaluated systems score well below this ceiling on the same families; see the per-family risk difference in [`CONFIRMATORY.md`](CONFIRMATORY.md).

**On the negative controls every fixed policy scores exactly +0.000.** The edit leaves the evidence state unchanged, so both sides carry identical acceptable and forbidden lists and any reply, blind or not, is scored the same way twice. This is what rules a blind policy out: the result this benchmark reports is an effect on the perturbation families *together with* zero on the controls, and no policy that ignores the conversation can produce that pair.

Detectability is reported above for the same reason but does not bound this. A measured detector's 
**The adaptation rate rules a blind policy out by construction, not by measurement.** The decomposition in [`CROSS_SCORING.md`](CROSS_SCORING.md) writes the paired outcome as a standard shift plus a reply adaptation, and the second term is the difference between two judgements of the *same text* whenever the policy's reply does not depend on the edit. Every fixed policy in the table above therefore has an adaptation rate of exactly zero, whatever its level on either side. That is an algebraic property of the estimator rather than a number this audit had to go and measure.
accuracy is at most the Bayes accuracy, so a value computed from it is achievable by some blind policy rather than a ceiling on all of them; the controls, not a bound, are what carry the argument.


## What the edits repeat

A family whose insertions reuse the same clinical furniture is learnable in a way no control can fix: a model that sees the same comorbidity in every distractor learns the family, not the reasoning. Per family, the content terms that appear in the edited span and not in the original message, ranked by the share of sources whose edit uses them. `tools/quality_checks.py` turns the same signal into a per-twin screen (`C9R_templated_insertion`, with the terms in `templated_terms`), flagging a term that carries at least 8 percent of a family's insertions and is at least four times commoner there than in the source messages themselves.

| Family | Sources with an edit span | Most repeated inserted terms (share of sources) |
|---|---|---|
| `alternative_evidence` | 344 | `normal` 5.2%, `still` 3.8%, `it's` 3.5%, `right` 3.2%, `little` 3.2% |
| `buried_red_flag` | 813 | `since` 18.2%, `yesterday` 15.5%, `days` 12.7%, `last` 9.2%, `right` 8.9% |
| `conflicting_evidence` | 1229 | `last` 11.9%, `since` 11.6%, `still` 8.2%, `morning` 7.6%, `every` 7.5% |
| `demographic_control` | 948 | `long` 8.0%, `truck` 7.3%, `driver` 7.3%, `avid` 6.6%, `haul` 6.3% |
| `demographic_shift` | 1099 | `pregnant` 19.2%, `insurance` 18.5%, `area` 18.2%, `remote` 17.7%, `health` 16.6% |
| `missing_evidence` | 235 | `it's` 10.6%, `don't` 8.9%, `actually` 6.8%, `sure` 4.7%, `child` 3.8% |
| `missing_evidence_early` | 59 | `it's` 8.5%, `he's` 5.1%, `lately` 5.1%, `sometimes` 5.1%, `kind` 5.1% |
| `salient_distractor` | 1229 | `years` 13.7%, `last` 9.8%, `daily` 8.9%, `take` 8.2%, `year` 7.1% |

## Does the fingerprint explain the behaviour

The detector's margin on an item is how obviously that item was edited. If assistants were answering the fingerprint, the items with the largest margin would be the items where they changed their answer most often.

On the 74 `missing_evidence` items with reference replies, the correlation between the detector's margin and the share of assistants that dropped their commitment is Spearman rho **-0.238** (permutation p 0.04).

The same reference pilot, per model: the share of originally-definitive replies that no longer commit once the evidence is edited, against the same share when only the wording changes.

| model | dropped commitment, evidence removed | dropped commitment, paraphrase only |
|---|---|---|
| `claude-sonnet-5` | 0.34 | 0.04 |
| `deepseek-v4-pro-0813` | 0.25 | 0.04 |
| `gemini-3.8-flash` | 0.32 | 0.03 |
| `llama-4-maverick` | 0.24 | 0.06 |
| `gpt-5.6-terra` | 0.39 | 0.03 |

## Reading

**The most detectable edits are the ones where changing your answer is wrong.** The two negative-control families sit at 0.99 and 1.00, the top of the table, because an insertion always lengthens the message. On exactly those families the correct behaviour is to answer unchanged. A model that keys on "something was edited here" therefore fails the controls while passing the perturbations, and the release reports both, so the shortcut is scored rather than rewarded. This is structural: it holds however good the detector gets.

**Visibility is length, and length carries no direction.** The length-only baseline matches the full detector on every insertion family, so what is detectable is that the message got longer, not what the added sentence means. Knowing the message was edited does not tell an assistant whether to ask a question, change the drug, escalate, or hold its answer, which are the four things the families ask for.

**Editing at all is visible, from 0.73 to 0.86.** The paraphrase control changes wording and no evidence and is detectable in that range in every family, which is the cost of touching the text. In the reference pilot that control moved the definitive rate by at most 0.06 across evaluated models, while removing an element moved it by 0.24 to 0.39.

**Visibility does not explain the behaviour, and it runs the wrong way.** The correlation between how obviously an item was edited and how often assistants dropped their commitment on it is -0.238 (permutation p 0.04), negative. The shortcut hypothesis predicts a strong positive correlation. What this says instead is that the surgical edits move models most: taking out one short decisive clause is both the hardest edit to see and the one that changes the answer, while a large removal is obvious and often leaves enough of the message to answer from.

**What it does not settle, and what to do about it.** A bag-of-words detector is a floor, and a frontier assistant reading the message can notice a tell this one misses. The repetition table above is where such a tell would show up first, and it is the authoring queue: a term carrying a large share of one family's insertions should be varied before that family grows.

