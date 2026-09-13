# Discrimination, and where it stops

A benchmark earns its place by telling systems apart. One that tells them apart everywhere, including on items whose correct answer is the same for everyone, is measuring something other than what it claims.

Both halves are tested the same way. The statistic is the standard deviation of the systems' mean paired differences on that family, which uses every system rather than the two extremes. The null permutes the system labels **within each source**, keeping the difficulty of the source and destroying only the identity of the system answering it; the p-value is the share of permutations reaching the observed spread. The range is given beside it for reading, not for testing.

The prediction is asymmetric. On a perturbation family, systems should differ: reacting to changed evidence is a capability. On a negative control, where the correct answer is to leave the reply alone, they should not.

Split: held-out. Permutations: 4000.

| family | kind | sources | systems | sd between systems | range | permutation p |
|---|---|---|---|---|---|---|
| `missing_evidence` | perturbation | 85 | 10 | 0.069 | 0.195 | 0.0163 |
| `conflicting_evidence` | perturbation | 139 | 10 | 0.104 | 0.360 | 0.0003 |
| `buried_red_flag` | perturbation | 148 | 10 | 0.134 | 0.480 | 0.0003 |
| `demographic_shift` | perturbation | 64 | 10 | 0.075 | 0.281 | 0.0255 |
| `alternative_evidence` | perturbation | 68 | 10 | 0.039 | 0.132 | 0.7270 |
| `salient_distractor` | **negative control** | 219 | 10 | 0.015 | 0.053 | 0.8592 |
| `demographic_control` | **negative control** | 161 | 10 | 0.019 | 0.056 | 0.8197 |

## Reading

Every perturbation family separates the systems: spreads of 0.07, 0.10, 0.13, 0.07, 0.04 at p 0.0163, 0.0003, 0.0003, 0.0255, 0.7270. Neither negative control does: spreads of 0.015 and 0.019 at p 0.86 and 0.82.

The two halves use the same items per source, the same judge, the same outcome and the same test. What differs is whether the edit changes what a careful clinician would do. Where it does, the systems come apart; where it does not, they stay together. A benchmark that separated systems on both halves would be separating them on something other than evidence sensitivity, and a benchmark that separated them on neither would not be worth running.

This is also what the per-family spread means for a leaderboard. On `buried_red_flag` the systems run from +0.007 to +0.486 on the same items with the same judge. A single number averaged over families would hide that, and an ordering built from it would be an ordering of one weighted average among many.

