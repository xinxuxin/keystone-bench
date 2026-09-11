# Reference runs

Five assistants over the quick set, eight families, benchmark 0.5.0, judged by GPT-4.1. One pair of files per
model and family: the `summary.json` a run writes, and the `records.jsonl` behind it, which carries every
reply and both judges' verdicts on it.

The records are here so that the judging can be redone without paying to generate the replies again. A new
judge, or a changed prompt, can be scored against exactly these replies:

```bash
python tools/judge_check.py --judge offline --from-records release/judge_check_gpt41.jsonl   # the validity set
keystone report results/reference/<model>                                                    # recompute a summary
```

`docs/RESULTS.md` is generated from these files by `python tools/results_table.py runs/quick__*`, and
`docs/BEHAVIOUR_ANCHOR.md` reads them alongside the earlier pilot.

**On HealthBench text.** These are model outputs, not source items, and an assistant sometimes echoes a clause
of the message it is answering. Measured over a random 358 replies, the longest verbatim run shared with the
source conversation has a median of 19 characters and a maximum of 73, and 0.8 percent of replies exceed 60.
No conversation is reconstructible from them. The source items themselves are still not in this repository:
they are rebuilt from OpenAI's copy by `keystone build`.
