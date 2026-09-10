# Criterion validity: materiality against measured behaviour

Both other anchors ask whether our labels agree with something physicians wrote. This one asks whether the label predicts what it claims to predict. A twin labelled material is one whose original commitment the evidence no longer supports, so assistants should stop committing on it more often than on a twin labelled immaterial. The replies that test this are already in the release: five assistants on the 80 `missing_evidence` twins of the reference pilot, each reply classified, each item also answered in a paraphrase-only version that changes wording and no evidence.

**Why the paraphrase column decides it.** A label that predicts the drop on both sides is tracking how much the message was disturbed. A label that predicts the drop on the perturbed side only is tracking the evidence. The last column is that difference, per item, and it is the number this page is for.

Rates are computed per item across the five assistants before being averaged, so one item contributes one observation. Intervals are 95 percent bootstrap over items. Empty replies are missing data and enter no denominator.

The fourth column is the release's adaptation-failure outcome under a plainer name, because on an immaterial twin staying definitive is the correct behaviour: that column is a quality measure only where the edit is material, and it is shown across all three levels so the contrast is visible rather than hidden.

### Materiality from the two rubric-blind reviewers, where they agree

| Materiality | Items | Committed on the original | Dropped commitment on the twin | Stayed definitive without naming the change | Dropped on the paraphrase (control) | Evidence effect, twin minus paraphrase |
|---|---|---|---|---|---|---|
| 3 | 17 | 0.812 [0.659, 0.941] | 0.574 [0.419, 0.731] | 0.355 [0.219, 0.499] | 0.075 [0.000, 0.212] | 0.499 [0.280, 0.703] |
| 2 | 30 | 0.887 [0.780, 0.973] | 0.227 [0.121, 0.341] | 0.683 [0.571, 0.791] | 0.034 [0.000, 0.103] | 0.193 [0.101, 0.298] |
| 1 | 11 | 0.709 [0.473, 0.909] | 0.130 [0.000, 0.315] | 0.767 [0.522, 0.944] | 0.139 [0.000, 0.361] | -0.009 [-0.306, 0.269] |

Trend over items: Spearman rho 0.487 on the twin (permutation p 0.00025) against -0.051 on the paraphrase control (p 0.74).
Evidence effect at materiality 3 minus materiality 1: 0.508 [0.161, 0.870].

### Materiality as the three-rater median, for comparison

| Materiality | Items | Committed on the original | Dropped commitment on the twin | Stayed definitive without naming the change | Dropped on the paraphrase (control) | Evidence effect, twin minus paraphrase |
|---|---|---|---|---|---|---|
| 3 | 26 | 0.854 [0.746, 0.938] | 0.579 [0.470, 0.690] | 0.333 [0.232, 0.443] | 0.069 [0.008, 0.165] | 0.510 [0.372, 0.638] |
| 2 | 43 | 0.842 [0.749, 0.926] | 0.232 [0.150, 0.324] | 0.670 [0.574, 0.759] | 0.054 [0.000, 0.127] | 0.178 [0.096, 0.265] |
| 1 | 11 | 0.709 [0.473, 0.909] | 0.130 [0.000, 0.315] | 0.767 [0.522, 0.944] | 0.139 [0.000, 0.361] | -0.009 [-0.306, 0.269] |

Trend over items: Spearman rho 0.536 on the twin (permutation p <5e-05) against 0.013 on the paraphrase control (p 0.86).
Evidence effect at materiality 3 minus materiality 1: 0.519 [0.219, 0.868].

### Per assistant

The same contrast computed inside each assistant's own replies, to show the result is not one model's behaviour.

| Assistant | Items | Dropped on twin, materiality 3 | materiality 1 | Difference |
|---|---|---|---|---|
| `claude-sonnet-5` | 44 | 0.545 (n=11) | 0.143 (n=7) | 0.403 |
| `deepseek-v4-pro-0813` | 48 | 0.500 (n=14) | 0.125 (n=8) | 0.375 |
| `gemini-3.8-flash` | 48 | 0.643 (n=14) | 0.000 (n=9) | 0.643 |
| `llama-4-maverick` | 51 | 0.429 (n=14) | 0.222 (n=9) | 0.206 |
| `gpt-5.6-terra` | 45 | 0.750 (n=12) | 0.000 (n=6) | 0.750 |

### The rubric side

On the 24 items whose replies were also rubric-graded, the share of the physicians' criteria that the applicability judge ruled no longer judgeable tracks materiality at Spearman rho 0.513 (permutation p 0.01). Same labels, a different measured consequence.

## Reading

The label earns its name when the twin column rises with materiality while the paraphrase column stays flat, because that is the difference between a label that tracks evidence and a label that tracks editing. Read the last column of each table first, then the per-assistant table to check that no single model carries it.

Limits worth stating. Eighty items and five assistants from one pilot, so the intervals are wide and the materiality-1 cell is the smallest; the classification of each reply is a model's, the same judge family throughout; and this is the `missing_evidence` family only, because that is the family the pilot covered. Running the other families is the obvious extension and needs model calls rather than new data. A label that predicts behaviour is still a label a model wrote: the release stays `tier: silver`, and `gold` is the tier a clinician-confirmed row carries.

