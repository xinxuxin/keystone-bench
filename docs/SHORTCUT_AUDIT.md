# Does the edit leave a fingerprint a model could answer instead of the evidence

Every paired-perturbation benchmark inherits this objection: the edit changes the surface of the message, so an assistant reacting to "this text was tampered with" scores as though it reacted to the evidence. The paraphrase control answers the behavioural half. This page answers the measurement half, by asking how visible each edit is, whether visibility explains what models did, and what the edits have in common that an authoring pass should remove.

The detector is a bag-of-words logistic regression trained on other sources and scored as a two-alternative forced choice: it sees both versions of a held-out source and picks the edited one, so chance is 0.50. It is a floor on detectability rather than a ceiling, which is why the sections after the first matter more than the first.

## How visible is each edit

Two-alternative forced choice on held-out sources, chance 0.50. `Length only` picks by which version is longer, so it is the part of detectability that needs no vocabulary at all.

| Family | Sources | original vs twin | length only | original vs control | twin vs control | Heaviest tokens in the twin |
|---|---|---|---|---|---|---|
| `alternative_evidence` | 391 | **0.72** | 0.73 | 0.85 | 0.80 | `it's`, `fine`, `month`, `like` |
| `buried_red_flag` | 816 | **1.00** | 1.00 | 0.84 | 0.98 | `though`, `probably`, `yesterday`, `since` |
| `conflicting_evidence` | 1236 | **1.00** | 0.99 | 0.85 | 0.97 | `since`, `last`, `though`, `still` |
| `demographic_control` | 949 | **0.99** | 1.00 | 0.85 | 0.92 | `marathon`, `matters`, `weekends`, `really` |
| `demographic_shift` | 1236 | **0.96** | 0.94 | 0.85 | 0.95 | `pregnant`, `insurance`, `health`, `area` |
| `missing_evidence` | 1236 | **0.91** | 0.93 | 0.84 | 0.89 | `it's`, `don't`, `actually`, `sure` |
| `missing_evidence_early` | 218 | **0.87** | 0.92 | 0.85 | 0.81 | `he's`, `something`, `sometimes`, `feeling` |
| `salient_distractor` | 1236 | **1.00** | 1.00 | 0.85 | 0.97 | `osteoarthritis`, `history`, `father`, `mother` |

## What a policy that never reads the evidence could score

A fixed policy scores exactly zero on the paired difference: it answers the twin and its control the same way, so the difference cancels. That is the point of pairing. The strongest *blind* policy is the one that guesses which side was edited from the surface and then answers to the family's outcome; if it picks the twin with accuracy `a`, its expected paired risk difference is at most `2a - 1`. The detector above measures `a` as the twin-versus-control accuracy, and a frontier model reading the message would do better, so the bound below is a floor.

| Family | twin vs control | blind bound `2a-1` | measured effect | measured / bound |
|---|---|---|---|---|
| `alternative_evidence` | 0.80 | +0.60 | +0.003 | +0.01 |
| `buried_red_flag` | 0.98 | +0.97 | +0.166 | +0.17 |
| `conflicting_evidence` | 0.97 | +0.93 | +0.331 | +0.35 |
| `demographic_control` | 0.92 | +0.84 | -0.011 | -0.01 |
| `demographic_shift` | 0.95 | +0.89 | +0.049 | +0.05 |
| `missing_evidence` | 0.89 | +0.79 | +0.185 | +0.23 |
| `missing_evidence_early` | 0.81 | +0.63 | +0.026 | +0.04 |
| `salient_distractor` | 0.97 | +0.94 | -0.006 | -0.01 |

The bound is above 0.6 on every family, so it does not by itself rule anything out. The last column is what does. A blind policy spends its accuracy the same way everywhere, so its ratio of measured effect to bound would be roughly constant across families. Measured, that ratio is near zero on the two families whose correct answer is to hold the reply and between 0.18 and 0.35 on the families that ask for a change, even though the two negative controls are among the most detectable families in the table. Detectability is available to the models and they are not spending it.


## What the edits repeat

A family whose insertions reuse the same clinical furniture is learnable in a way no control can fix: a model that sees the same comorbidity in every distractor learns the family, not the reasoning. Per family, the content terms that appear in the edited span and not in the original message, ranked by the share of sources whose edit uses them. `tools/quality_checks.py` turns the same signal into a per-twin screen (`C9R_templated_insertion`, with the terms in `templated_terms`), flagging a term that carries at least 8 percent of a family's insertions and is at least four times commoner there than in the source messages themselves.

| Family | Sources with an edit span | Most repeated inserted terms (share of sources) |
|---|---|---|
| `alternative_evidence` | 345 | `normal` 5.2%, `still` 3.8%, `it's` 3.5%, `right` 3.2%, `little` 3.2% |
| `buried_red_flag` | 815 | `though` 16.9%, `last` 14.4%, `yesterday` 14.4%, `left` 13.7%, `probably` 13.6% |
| `conflicting_evidence` | 1231 | `last` 12.3%, `since` 12.0%, `though` 11.9%, `still` 9.3%, `it's` 8.0% |
| `demographic_control` | 949 | `marathon` 10.7%, `matters` 9.0%, `weekends` 8.7%, `really` 8.7%, `avid` 8.5% |
| `demographic_shift` | 1101 | `pregnant` 19.2%, `insurance` 18.4%, `area` 18.3%, `remote` 17.7%, `health` 16.5% |
| `missing_evidence` | 236 | `it's` 10.6%, `don't` 8.9%, `actually` 6.8%, `sure` 4.7%, `child` 3.8% |
| `missing_evidence_early` | 59 | `it's` 8.5%, `he's` 5.1%, `lately` 5.1%, `sometimes` 5.1%, `kind` 5.1% |
| `salient_distractor` | 1231 | `osteoarthritis` 31.1%, `history` 21.6%, `father` 20.0%, `mother` 13.4%, `knee` 7.8% |

## Does the fingerprint explain the behaviour

The detector's margin on an item is how obviously that item was edited. If assistants were answering the fingerprint, the items with the largest margin would be the items where they changed their answer most often.

On the 75 `missing_evidence` items with reference replies, the correlation between the detector's margin and the share of assistants that dropped their commitment is Spearman rho **-0.260** (permutation p 0.03).

## Reading

**The most detectable edits are the ones where changing your answer is wrong.** The two negative-control families sit at 0.99 and 1.00, the top of the table, because an insertion always lengthens the message. On exactly those families the correct behaviour is to answer unchanged. A model that keys on "something was edited here" therefore fails the controls while passing the perturbations, and the release reports both, so the shortcut is scored rather than rewarded. This is structural: it holds however good the detector gets.

**Visibility is length, and length carries no direction.** The length-only baseline matches the full detector on every insertion family, so what is detectable is that the message got longer, not what the added sentence means. Knowing the message was edited does not tell an assistant whether to ask a question, change the drug, escalate, or hold its answer, which are the four things the families ask for.

**Editing at all is visible, at 0.84 to 0.85.** The paraphrase control changes wording and no evidence and is detectable at that rate in every family, which is the cost of touching the text. In the reference pilot that control moved the definitive rate by at most 0.07 while removing an element moved it by 0.31 to 0.55.

**Visibility does not explain the behaviour, and it runs the wrong way.** The correlation between how obviously an item was edited and how often assistants dropped their commitment on it is -0.260 (permutation p 0.03), negative. The shortcut hypothesis predicts a strong positive correlation. What this says instead is that the surgical edits move models most: taking out one short decisive clause is both the hardest edit to see and the one that changes the answer, while a large removal is obvious and often leaves enough of the message to answer from.

**What it does not settle, and what to do about it.** A bag-of-words detector is a floor, and a frontier assistant reading the message can notice a tell this one misses. The repetition table above is where such a tell would show up first, and it is the authoring queue: a term carrying a large share of one family's insertions should be varied before that family grows.

