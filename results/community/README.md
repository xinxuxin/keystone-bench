# Community results

A submission is one directory per model, one file per run:

```
results/community/<model>/<family>__<layer>[__<split>].json     # summary.json from the run
results/community/<model>/<family>__<layer>[__<split>].jsonl    # records.jsonl, so the classification can be audited
```

`keystone run` writes both. Copy them here, keep the names, and open a pull request with a note in the PR
body giving the endpoint, the date, and the judge. Nothing else is required.

What a submission needs to be comparable:

- the benchmark `version` from `MANIFEST.json`, which `summary.json` already carries;
- temperature 0, no system prompt, and the output-token budget you used, raised if the model returned
  empty replies (`n_empty_replies` in the summary should be 0 or explained);
- a judge from a different vendor than the model under test;
- the paraphrase control reported next to the headline rate. A run whose `spurious_shift` exceeds 0.10 does
  not support attributing the effect to the perturbation;
- per-family numbers rather than one pooled rate. `summary.json` carries `by_family` and `composition`; the
  negative controls are the largest families in every layer and their correct behaviour is the opposite of
  the perturbation families', so a pooled rate is not comparable with anyone else's.

Runs on the `test` split are the ones worth comparing across submitters, because `dev` is where anyone
iterating on a prompt will have been looking.
