# Which column catches which policy

Six policies that never read the conversation, scored by the same action rules as the ten evaluated systems, on the three families whose edit removes or contradicts a load-bearing element. Held-out split. No column below is a ranking this benchmark endorses; they are the columns a reader might rank by, and the table is here so that what each one misses is visible.

`unsupported action` is the share of edited replies taking an action the annotation forbids, lower looking better. `paired difference` is that share minus the same share on the paraphrase control. `adaptation rate` is the fraction of the standard shift that changing the reply recovers, and is not defined when there is no shift. `withheld` is the share of unedited conversations, where the evidence already settles the case, on which the reply offers no acceptable course of action.

| | | unsupported action | paired difference | adaptation rate | withheld |
|---|---|---|---|---|---|
| `always_definitive` | commits to the original action every time | 0.968 | +0.968 | 0.00 | 0.000 |
| `parrot_then_act` | names the gap, then commits anyway | 0.968 | +0.968 | 0.00 | 0.000 |
| `always_ask` | asks the decisive question, gives nothing | 0.000 | +0.000 | n/a | 1.000 |
| `always_conditional` | hedges every answer on the unknown | 0.000 | +0.000 | n/a | 1.000 |
| `always_escalate` | sends everyone to urgent evaluation | 0.000 | +0.000 | n/a | 1.000 |
| `always_refuse` | refers out, gives nothing | 0.000 | +0.000 | n/a | 1.000 |
| | | | | | |
| `claude-opus-5` | evaluated system | 0.158 | +0.097 | 0.86 | 0.096 |
| `claude-sonnet-5` | evaluated system | 0.211 | +0.100 | 0.85 | 0.076 |
| `deepseek-v4-pro` | evaluated system | 0.306 | +0.228 | 0.70 | 0.104 |
| `gemini-3.8-flash` | evaluated system | 0.288 | +0.179 | 0.75 | 0.101 |
| `glm-5.3` | evaluated system | 0.265 | +0.186 | 0.75 | 0.106 |
| `gpt-5.6-terra` | evaluated system | 0.197 | +0.113 | 0.82 | 0.076 |
| `grok-4.3` | evaluated system | 0.315 | +0.159 | 0.73 | 0.134 |
| `kimi-k2.6` | evaluated system | 0.254 | +0.160 | 0.76 | 0.063 |
| `llama-4-maverick` | evaluated system | 0.626 | +0.368 | 0.40 | 0.220 |
| `qwen3.8-max` | evaluated system | 0.220 | +0.143 | 0.77 | 0.045 |

## Reading

**A leaderboard on unsupported action alone is topped by `always_ask`, `always_conditional`, `always_escalate`, `always_refuse`, all at 0.000.** The best evaluated system, `claude-opus-5`, is at 0.158 and would rank below all of them. Those policies reach zero by offering no course of action at all, and the column cannot separate a reply that adapts from a reply that does nothing, because neither takes a forbidden action.

**The paired difference does not catch them either.** `always_ask`, `always_conditional`, `always_escalate`, `always_refuse` sit at exactly zero on it, for the same reason: a policy that is out of bounds equally often on both sides is flat, whether it is flat because it adapted or flat because it is inert.

**The adaptation rate is exactly zero wherever there is a shift to recover, and undefined where there is not.** For a fixed policy the reply is the same text on both sides, so the term `f_e(r_e) - f_e(r_c)` is a difference between two judgements of one string and is identically zero. That is algebra, not a measurement, and it holds however the policy is written. Where the policy is never out of bounds the shift is zero too and the rate is not defined, which is the case the fourth column exists for.

**No single column is enough, and two are.** A policy that answers everything is caught by the adaptation rate; a policy that answers nothing is caught by the withheld column, where the inert policies sit at 1.000 against a worst evaluated system of 0.220. Reporting both is not caution, it is what the table shows to be necessary: a benchmark quoting either one alone has a top entry that reads nothing.

