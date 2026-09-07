# Applicability judge versus independent dependence labels

30 pilot items of the evidence-removal family with rubric grading; 399 criteria. The applicability judge (GPT-4.1, at pilot time) decided per criterion whether it could still be fairly judged on the perturbed message; an independent labeller (codex, afterwards) marked per criterion whether its judgement depends on the removed element. Both are model judgements, so this is agreement between two independent model verdicts, not accuracy against ground truth.

| Quantity | Value |
|---|---|
| Criteria labelled dependent that the judge marked inapplicable (sensitivity) | 0.70 (76/109) |
| Criteria labelled independent that the judge kept applicable (specificity) | 0.88 (254/290) |
| Judge-inapplicable criteria that are labelled dependent (precision) | 0.68 (76/112) |
| Items where every dependent criterion was marked inapplicable | 0.43 |
| Mean per-item Jaccard between the two sets | 0.52 |

| Source | Criteria | Labelled dependent | Judged inapplicable | Jaccard |
|---|---|---|---|---|
| `118ddcf8` | 12 | [0] | [] | 0.00 |
| `1a928791` | 12 | [10] | [] | 0.00 |
| `20169ed1` | 16 | [14, 15] | [3, 7] | 0.00 |
| `21c77b15` | 20 | [18] | [7, 10, 11, 16] | 0.00 |
| `24730d08` | 11 | [1, 3, 8, 9, 10] | [] | 0.00 |
| `2d4142f9` | 2 | [] | [0, 1] | 0.00 |
| `40c03b3e` | 9 | [1, 2, 7, 8] | [] | 0.00 |
| `0cdca736` | 13 | [5, 9, 11] | [8, 11] | 0.25 |
| `2b7b7bee` | 17 | [3, 9, 15, 16] | [1, 9, 11, 12, 13, 16] | 0.25 |
| `4a8ba3f3` | 21 | [7, 12, 15] | [2, 7, 10, 14, 15, 16] | 0.29 |
| `3b10c909` | 19 | [9, 10, 16] | [6, 8, 9, 10, 11, 16, 17] | 0.43 |
| `0171f86d` | 2 | [0] | [0, 1] | 0.50 |
| `2e5c3600` | 14 | [12] | [12, 13] | 0.50 |
| `40310443` | 14 | [4, 5, 12] | [5, 12, 13] | 0.50 |
| `4e5113ac` | 14 | [0, 1, 4, 5, 7, 8, 9, 11, 12] | [0, 1, 4, 8, 9] | 0.56 |
| `302c36a0` | 20 | [1, 2, 3, 4, 10, 11, 12, 13, 18, 19] | [2, 3, 4, 6, 7, 8, 10, 11, 12, 13, 16, 19] | 0.57 |
| `129057dd` | 12 | [0, 4, 5] | [0, 4, 5, 10, 11] | 0.60 |
| `15c68476` | 16 | [4, 7, 8, 14, 15] | [4, 8, 14] | 0.60 |
| `3599cfcc` | 12 | [2, 4, 7, 10, 11] | [4, 10, 11] | 0.60 |
| `4e60a0fb` | 14 | [4, 12, 13] | [12, 13] | 0.67 |
| `440d0ea5` | 9 | [1, 2, 3, 6, 7, 8] | [0, 1, 2, 3, 6, 7] | 0.71 |
| `4ef89e7b` | 12 | [0, 3, 6, 7, 10, 11] | [0, 2, 3, 7, 10, 11] | 0.71 |
| `29b413d1` | 26 | [0, 1, 2, 6, 7, 8, 9, 11, 12, 14, 15, 16, 17, 18, 19, 20, 22] | [0, 1, 2, 6, 7, 8, 9, 10, 11, 12, 14, 15, 16, 17, 18, 19, 20, 22, 24, 25] | 0.85 |
| `1f1f563f` | 14 | [2, 3, 4, 5, 6, 9, 12] | [2, 3, 4, 5, 6, 8, 9, 12] | 0.88 |
| `00e6749c` | 9 | [] | [] | 1.00 |
| `09a185f7` | 10 | [6] | [6] | 1.00 |
| `0d35086a` | 11 | [] | [] | 1.00 |
| `1f41d182` | 8 | [2] | [2] | 1.00 |
| `1f548d5b` | 19 | [12, 17, 18] | [12, 17, 18] | 1.00 |
| `457ee7d4` | 11 | [4] | [4] | 1.00 |
