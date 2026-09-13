# Discrimination, and where it stops

A benchmark earns its place by telling systems apart. One that tells them apart everywhere, including on items whose correct answer is the same for everyone, is measuring something other than what it claims.

Both halves are tested the same way. The observed spread is the range of the systems' mean paired differences on that family. The null permutes the system labels **within each source**, which keeps the difficulty of the source and destroys only the identity of the system answering it; the p-value is the share of permutations whose spread reaches the observed one.

The prediction is asymmetric. On a perturbation family, systems should differ: reacting to changed evidence is a capability. On a negative control, where the correct answer is to leave the reply alone, they should not.

Split: held-out. Permutations: 4000.

| family | kind | sources | systems | spread between systems | permutation p |
|---|---|---|---|---|---|
| `missing_evidence` | perturbation | 85 | 5 | 0.176 | 0.0290 |
| `conflicting_evidence` | perturbation | 139 | 5 | 0.360 | 0.0003 |
| `buried_red_flag` | perturbation | 148 | 5 | 0.480 | 0.0003 |
| `salient_distractor` | **negative control** | 219 | 5 | 0.029 | 0.8295 |
| `demographic_control` | **negative control** | 161 | 5 | 0.056 | 0.5082 |

## Reading

Every perturbation family separates the systems: spreads of 0.18, 0.36, 0.48 at p 0.0290, 0.0003, 0.0003. Neither negative control does: spreads of 0.029 and 0.056 at p 0.83 and 0.51.

The two halves use the same items per source, the same judge, the same outcome and the same test. What differs is whether the edit changes what a careful clinician would do. Where it does, the systems come apart; where it does not, they stay together. A benchmark that separated systems on both halves would be separating them on something other than evidence sensitivity, and a benchmark that separated them on neither would not be worth running.

This is also what the per-family spread means for a leaderboard. On `buried_red_flag` the systems run from +0.007 to +0.486 on the same items with the same judge. A single number averaged over families would hide that, and an ordering built from it would be an ordering of one weighted average among many.

