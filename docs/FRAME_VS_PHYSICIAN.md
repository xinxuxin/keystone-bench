# The decision frame against a physician's own answer

Layer `core`, `all` split, judge `openrouter/openai/gpt-4.1`, 1034 sources. HealthBench ships a physician-written ideal completion for the unedited conversation. No Keystone annotator saw it, so judging it against this source's own decision frame, by the rules a model reply is judged by, tests the frame rather than the model. This says nothing about the edited message: a physician answer written before the edit cannot settle what the edit makes acceptable.

| | share | 95% interval |
|---|---|---|
| physician answer marked **acceptable** | 0.830 | [0.808, 0.853] |
| physician answer marked **forbidden** | 0.166 | [0.143, 0.190] |
| neither, on the frame's lists | 0.006 | [0.002, 0.011] |

The evaluated systems on the same conversations and the same frames, for scale.

| system | sources | acceptable | forbidden |
|---|---|---|---|
| `claude-opus-5` | 190 | 0.905 | 0.074 |
| `claude-sonnet-5` | 211 | 0.938 | 0.062 |
| `deepseek-v4-pro` | 202 | 0.911 | 0.084 |
| `gemini-3.8-flash` | 210 | 0.900 | 0.100 |
| `glm-5.3` | 115 | 0.896 | 0.104 |
| `gpt-5.6-terra` | 212 | 0.943 | 0.052 |
| `grok-4.3` | 213 | 0.887 | 0.108 |
| `kimi-k2.6` | 187 | 0.920 | 0.080 |
| `llama-4-maverick` | 213 | 0.761 | 0.239 |
| `qwen3.8-max` | 151 | 0.954 | 0.046 |

## Reading

The frame marks 83.0% of physician answers as an acceptable course of action and 16.6% as a forbidden one. On the same conversations and the same frames the evaluated systems run 76.1% to 95.4% acceptable and 4.6% to 23.9% forbidden.

**The frame forbids a physician's answer more often than it forbids the answer of 9 of the 10 evaluated systems.** That is not the ordering a frame whose forbidden list captured only unsafe care would produce. Two readings fit and this measurement does not separate them: the list is too narrow on those sources, or a physician's reference answer is a different kind of object from a chat reply, covering contingencies and hedges that the action judge maps onto a listed action. Either way the level of the outcome carries less than the level alone suggests.

What it does not reach is the paired quantities. Both sides of a pair are scored against the same list, so a list that is uniformly too narrow raises both and largely cancels in the difference; the standard shift applies the *edited* list to two different replies and cancels in the same way. The absolute rates are what this bounds.

The 16.6% of sources where the frame forbids what a physician did are the first thing to hand to a clinician. Nothing here says whether the frame or the reading of the physician's answer is at fault, and both are defects in the annotation rather than in the systems.

**What this is not.** It is a check on one side of the pair. The frame for the *edited* message, which is what the primary outcome scores against, has no human artefact to be checked against and is tested only by the clinician study in the protocol.

