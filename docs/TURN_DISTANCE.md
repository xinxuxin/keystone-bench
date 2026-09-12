# Distance to the edited turn

`missing_evidence_early` removes the decisive fact from an earlier user turn, so the same family spans a range of distances between the edit and the message being answered. Attention decay predicts a fall with distance. A different account, that assistants do not re-check earlier turns at all, predicts a flat low level.

| turns between the edit and the question | items x systems | named the missing element | asked the decisive question or answered conditionally | acceptable action |
|---|---|---|---|---|
| 2 | 115 | 0.25 [0.18, 0.34] | 0.46 [0.37, 0.55] | 0.76 [0.67, 0.83] |
| 4 | 70 | 0.20 [0.12, 0.31] | 0.34 [0.24, 0.46] | 0.77 [0.66, 0.85] |
| 6 | 5 | 0.80 [0.38, 0.96] | 0.80 [0.38, 0.96] | 1.00 [0.57, 1.00] |
| 8 | 5 | 0.40 [0.12, 0.77] | 0.60 [0.23, 0.88] | 1.00 [0.57, 1.00] |

Pooled acceptable action on this family: 0.77 over 195 (item, system) cells.

## The same operation, one turn away

`missing_evidence` removes a decisive fact from the last user turn. It is the same edit as the family above, differing only in which turn it lands on, which makes it the right comparison for the level rather than the slope.

| where the fact was removed | items x systems | named the missing element | asked the decisive question | acceptable action |
|---|---|---|---|---|
| the last user turn | 198 | 0.41 [0.34, 0.48] | 0.52 [0.45, 0.58] | 0.74 [0.67, 0.79] |
| an earlier user turn | 195 | 0.25 [0.20, 0.32] | 0.43 [0.36, 0.50] | 0.77 [0.71, 0.83] |

Moving the same removal from the last turn to an earlier one costs 0.16 of the rate at which the missing element is named and 0.08 of the rate at which the decisive question is asked. Within the early family the distance itself does not add to that, on the two distances with enough items to compare: what matters is whether the fact is in the turn being answered, not how far back it is.

