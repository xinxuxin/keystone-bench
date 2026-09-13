# Rubric applicability after the edit, held-out split

Layer `core`, split `test`, judge `openrouter/openai/gpt-4.1`. Each criterion of a source's physician rubric is judged once against that source's twin: does it still describe a fair standard for the edited message. The verdict depends on the pair, not on any reply, so it does not vary by evaluated system.

The share is per twin, then averaged over twins with the source as the unit of resampling.

| family | twins | criteria | share of criteria no longer applicable |
|---|---|---|---|
| `missing_evidence` | 98 | 1246 | 0.316 [0.270, 0.363] |
| `conflicting_evidence` | 160 | 2083 | 0.151 [0.125, 0.179] |
| `buried_red_flag` | 167 | 2214 | 0.097 [0.076, 0.121] |
| `demographic_shift` | 75 | 1004 | 0.093 [0.064, 0.127] |
| `alternative_evidence` | 78 | 1057 | 0.397 [0.348, 0.449] |
| `missing_evidence_early` | 14 | 208 | 0.222 [0.134, 0.321] |
| `salient_distractor` | 249 | 3171 | 0.010 [0.006, 0.015] |
| `demographic_control` | 186 | 2465 | 0.012 [0.006, 0.020] |
| **all** | 1027 | 13448 | **0.114** [0.103, 0.126] |

## By materiality, perturbation families

| median materiality | twins | share no longer applicable |
|---|---|---|
| 2 | 50 | 0.051 [0.024, 0.081] |
| 3 | 542 | 0.203 [0.185, 0.221] |

