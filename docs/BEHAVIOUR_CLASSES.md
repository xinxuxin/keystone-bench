# What the evidence asks for

A family is a unit of construction. What an edit demands is not: removing a decisive fact makes a question necessary, changing an attribute makes a different action correct, mentioning a red flag makes escalation correct, and an irrelevant insertion makes no change correct. Each twin's annotated evidence state already names which, so the same items regroup into four classes with larger cells than any single family holds.

Layer `quick`, run prefix `q060`, 5 systems. The rate is the share of replies to the edited message whose course of action the annotation accepts.

| class | what the evidence asks for | families | items per system | claude-sonnet-5 | deepseek-v4-pro | gemini-3.8-flash | gpt-5.6-terra | llama-4-maverick | pooled |
|---|---|---|---|---|---|---|---|---|---|
| **ask** | a question is needed before committing | 4 | 115 | 0.79 | 0.68 | 0.66 | 0.80 | 0.53 | **0.69** [0.65, 0.73] |
| **change** | a different action is now the right one | 2 | 58 | 0.93 | 0.91 | 0.86 | 0.88 | 0.78 | **0.87** [0.83, 0.91] |
| **escalate** | urgent evaluation is now the answer | 6 | 66 | 0.79 | 0.78 | 0.82 | 0.89 | 0.41 | **0.74** [0.69, 0.78] |
| **hold** | the original answer still stands | 2 | 80 | 0.91 | 0.94 | 0.90 | 0.93 | 0.76 | **0.89** [0.85, 0.91] |

## Ordering

Pooled, the classes rank `ask` (0.69) < `escalate` (0.74) < `change` (0.87) < `hold` (0.89).

The full ordering holds for 2 of 5 systems taken separately, and it is `escalate` that moves: it is the weakest class on llama-4-maverick (0.41) and among the strongest on gpt-5.6-terra (0.89).

What holds on every system is the `ask` class. It is below both `change` and `hold` on 5 of 5 systems, by 0.14 to 0.26 pooled. Asking the question that settles a case is harder for every assistant here than changing an action or holding one, and it is the class where the annotation is most specific about what a correct reply contains: a named decisive question rather than any question at all.

## Read against the family table

A weakness attached to a kind of edit would show up as one family low and its class-mates normal. A weakness attached to a kind of required response shows up here: the class is low and every family in it is low. The per-family rates are in [`RESULTS.md`](RESULTS.md).

