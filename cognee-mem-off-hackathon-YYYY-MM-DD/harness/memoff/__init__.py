"""Mem Off harness.

Two pieces sit on top of the ``cognee-report`` skill's ``outcomes`` protocol:

* ``memoff.adapter`` — an *agent adapter*: reads one trial request on stdin, drives
  Claude Code headlessly in the trial workspace, writes one response on stdout.
* ``memoff.sequencer`` — the *sequencer*: chains the eight xitkit issues per arm and
  repeat, kills the agent session between issues, waits for the memory system, and
  writes ``trials.jsonl`` records in the evaluator's schema so
  ``plugin_eval.py outcomes report`` rebuilds ``report.json``.

Everything the stock ``outcomes run`` command does for independent cases (fresh
workspace per trial, shuffled variants, matched hashes) the sequencer does for the
chained sequence; scoring and summarising are imported from the skill, never copied.
"""

__version__ = "0.1.0"
