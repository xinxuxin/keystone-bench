# Discrimination, and where it stops

A benchmark earns its place by telling systems apart. One that tells them apart everywhere, including on items whose correct answer is the same for everyone, is measuring something other than what it claims.

Both halves are tested the same way. The statistic is the standard deviation of the systems' mean paired differences on that family, which uses every system rather than the two extremes. The null permutes the system labels **within each source**, keeping the difficulty of the source and destroying only the identity of the system answering it; the p-value is the share of permutations reaching the observed spread. The range is given beside it for reading, not for testing.

The prediction is asymmetric. On a perturbation family, systems should differ: reacting to changed evidence is a capability. On a negative control, where the correct answer is to leave the reply alone, they should not.

Split: held-out. Permutations: 4000.

| family | kind | sources | systems | sd between systems (90% CI) | range | permutation p |
|---|---|---|---|---|---|---|
| `missing_evidence` | perturbation | 85 | 10 | 0.069 [0.059, 0.106] | 0.195 | 0.0165 |
| `conflicting_evidence` | perturbation | 139 | 10 | 0.104 [0.091, 0.136] | 0.360 | 0.0003 |
| `buried_red_flag` | perturbation | 148 | 10 | 0.134 [0.117, 0.161] | 0.480 | 0.0003 |
| `demographic_shift` | perturbation | 64 | 10 | 0.075 [0.060, 0.118] | 0.281 | 0.0267 |
| `alternative_evidence` | perturbation | 68 | 10 | 0.039 [0.034, 0.088] | 0.132 | 0.7268 |
| `salient_distractor` | **negative control** | 219 | 10 | 0.015 [0.015, 0.036] | 0.053 | 0.8598 |
| `demographic_control` | **negative control** | 161 | 10 | 0.019 [0.019, 0.044] | 0.056 | 0.8097 |

## Reading

**What this statistic is.** It is the spread between systems in *how much the edit moves them*, not the spread in how well they answer. Two systems whose forbidden-action rates are 0.05 and 0.35 but who both rise by 0.10 under the edit contribute nothing to it. Read it as the heterogeneity of the perturbation effect, and read absolute levels from the per-system table in [`CONFIRMATORY.md`](CONFIRMATORY.md).

Every perturbation family shows heterogeneity: sd 0.069, 0.104, 0.134, 0.075, 0.039 at permutation p 0.0165, 0.0003, 0.0003, 0.0267, 0.7268. On the two negative controls the point estimates are 0.015 and 0.019 with 90 percent upper limits of 0.036 and 0.044.

**The claim the intervals support is a separation, and the intervals say how wide it is.** The controls' 90 percent upper limits are 0.036 and 0.044. 4 of the 5 perturbation families have point estimates above both limits, from 0.069 to 0.134. A large p on a control is the resolution a panel of 10 systems buys, and the separation is stated at that resolution: an equivalence claim on the controls would need a preregistered margin, which the protocol does not set.

**What the permutation null assumes.** Labels are permuted within each source, which holds source difficulty fixed and destroys only which system answered it. That is an exchangeability null, stronger than equality of means: it also fails if systems differ in variance or in which sources they miss. Rejecting it therefore licenses "these systems are not interchangeable on this family", not the narrower "their means differ". The paired difference is permuted as one unit, the system panel is fixed across families, and 4,000 permutations put the smallest reportable p at 1/4001, so the two families at 0.0003 are at that floor and their evidence should not be ranked against each other.

On `buried_red_flag` the systems run from +0.007 to +0.486 on the same items with the same judge. A single number averaged over families would hide that.

