# Example `results/` folder — smoke run, NOT evidence

Produced by `memoff run --smoke --arms tests/fixtures/arm-noop --repeats 2 --only 1 2` on
the real xitkit checkout: no model ran, the agent changed nothing, and every issue fails
its failure target (11 baseline failures against targets of 6 and 5). It shows the **shape**
of what the GitHub Action attaches to a submission PR, with real `verify/` output from
xitkit's own test suite and real evaluator records.

Every trial carries `no_model_smoke`; CI refuses a submission whose `results/` looks like
this. The `cognee` arm here is the no-op fixture, not the cognee plugin. Transcripts and
injected dumps are absent because no agent session ran.
