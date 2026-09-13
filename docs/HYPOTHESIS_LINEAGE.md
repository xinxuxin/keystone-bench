# Hypothesis lineage and endpoint freeze

Which prediction was written down, when, against which data, and what became of it. A reader deciding how much
a confirmatory interval is worth needs to know whether the endpoint that produced it was fixed before or after
the split it was computed on. This page is that record. It is written to be checkable: every date below is a
commit date in this repository's history, and every hypothesis is quoted from the file that carried it.

## The two generations

**Generation one, H1 to H5** ([`PROTOCOL.md` section 2](PROTOCOL.md), first committed 2026-09-07 in 0.4.0).
Written for the pilot: 355 sources carrying four twins each, results reported on the evidence-removal
family with five systems, before any held-out split existed. The outcome those hypotheses name is the *definitive-reply stance*, a
four-way behaviour label.

**Generation two, C1 to C3** (`tools/confirmatory.py`, first committed 2026-09-12). Written for the released
benchmark: 1,234 sources, eight families, a by-source dev/test split, and an outcome defined against the
decision frame rather than against a stance label. The change of outcome is the substantive difference between
the two generations, and it is the reason C1 is not a rerun of H1.

## What happened to each

| | prediction | outcome it names | status |
|---|---|---|---|
| **H1** adaptation failure | twin replies stay definitive without naming the missing element; the control barely moves | stance label | superseded. The stance label has the lowest inter-judge agreement of any layer (pairwise Cohen's kappa 0.379 to 0.631, [`JUDGE_PANEL.md`](JUDGE_PANEL.md)), which is why the primary outcome moved to the action judgement. The quantity is still computed and reported in [`RESULTS.md`](RESULTS.md); it carries no confirmatory claim. |
| **H2** evaluator applicability | the stale score exceeds the score over still-applicable criteria, and at least 20 percent of criteria are inapplicable | rubric score | executed on the held-out split, [`RUBRIC_CONSEQUENCE.md`](RUBRIC_CONSEQUENCE.md). The interval clause is met and the direction written into the protocol is not: dropping the expired criteria *raises* the score. Reported with the sign it has. |
| **H3** ranking stability | rankings on originals and on twins disagree | rubric score | not executed. It needs the original-side replies graded criterion by criterion, a second pass the size of the one H2 required. The ranking quantity in [`RUBRIC_CONSEQUENCE.md`](RUBRIC_CONSEQUENCE.md) holds the replies fixed and changes only the rubric version, which is a different comparison, and it is labelled as an addition rather than as H3. |
| **H4** heterogeneity | paired effects differ across subgroups | any | exploratory in the protocol, exploratory here. [`DISCRIMINATION.md`](DISCRIMINATION.md) tests a related but distinct claim, between-system rather than between-subgroup, with its own preregistered-style rule fixed before the held-out run. |
| **H5** rubric gap | the original rubric assigns little weight to context-seeking behaviour | rubric weights | exploratory, reported in [`RUBRIC_ANCHOR.md`](RUBRIC_ANCHOR.md). |
| **C1** evidence effect | Δ_f > 0 on the three families whose edit removes or contradicts a load-bearing element | annotation-defined unsupported action | supported on the held-out split. |
| **C1b** ceiling-restricted | the same, on sources whose unedited reply was not already out of bounds | same | supported. |
| **C2** control invariance | \|Δ_f\| ≤ 0.05 on both negative controls, as an equivalence test | same | supported. |
| **C3** intervention | one added instruction lowers unsupported action without raising withheld answers past 0.05 | same, plus a withholding outcome | the benefit and the control clause hold for the acknowledgement arm; the gated arm loses joint success. [`INTERVENTION_TEST.md`](INTERVENTION_TEST.md). |

## Endpoint freeze

| date | event |
|---|---|
| 2026-09-07 | H1 to H5 committed in `PROTOCOL.md`; no split exists yet, and the pilot uses all 355 sources |
| 2026-09-10 | the by-source dev/test split is introduced (0.4.1); every source hashes to `dev` or `test` and nothing on `test` is read |
| 2026-09-11 | 0.5.0 changes the `demographic_shift` screen; families and layers reach their released definitions |
| 2026-09-12 | C1, C1b and C2 are written into `tools/confirmatory.py` and the first `test`-split run is executed |
| 2026-09-13 | the cross-scoring decomposition is defined and run on `test`; H2 is executed on `test` |

The two endpoints that were **not** fixed before the data that decided them:

1. **The intervention's cost criterion.** "Withheld a usable answer" replaced "asked an unnecessary question"
   after reading one system's acknowledgement arm, before the other two systems had run. It is reported as an
   exploratory choice, and [`INTERVENTION_TEST.md`](INTERVENTION_TEST.md) gives benefit and cost per system so
   that a criterion favouring the system it was written on would be visible.
2. **The cross-scoring decomposition.** Its definition is algebraic and fixed before the run, but the decision
   to compute it came after the C1 results on `test` were known. It adds a term to an estimand already
   reported; it does not replace a test that had been run and disliked. The held-out sources it uses are the
   same ones C1 used, so it inherits their exposure rather than adding new exposure.

Everything else reported as confirmatory was specified before the `test` split was read, and the `quick` layer
that carries the exploratory numbers elsewhere in this repository is drawn from `dev`.

## Why the outcome changed between generations

H1 scores a reply by its stance: definitive, conditional, seeking, or refusing. Two judges disagree about that
label often enough that a difference of the size the pilot found is inside the disagreement. The action
outcome asks a narrower question with a written answer key per twin, and the same three-vendor panel agrees on
it far more closely. Moving the primary outcome cost the direct comparability of the pilot numbers, which is
why the pilot's figures are not carried forward as findings.
