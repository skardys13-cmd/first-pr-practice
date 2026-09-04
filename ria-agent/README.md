# RIA operations agent

A locally-installed operations layer for a small registered investment adviser.
It reads the firm's task system, does the retrieval-and-reconciliation work that
consumes staff hours, and returns every action to a human in a reviewable,
provable form.

**Read [CONSTITUTION.md](CONSTITUTION.md) first.** It is the binding rule set,
and each rule names the module that enforces it.

## State

Steps 1–24 of the build plan: the proof layer, the queue, reading the CRM, and
the first read-only hands. Nothing writes to a real system yet, and the pieces
that would talk to Redtail or a custodian sit behind interfaces with
fixture-backed fakes.

| Phase | Steps | What it is |
|---|---|---|
| 0 | 1–6 | Receipt schema and validator, append-only log, exporters, startup checks |
| 1 | 7–11 | The four-lane review queue |
| 2 | 12–17 | Reading the CRM, classifying tasks, shadow mode, the whitelist |
| 3 | 18–24 | Session detection, goal-directed navigation, guardrails, verification |

Findings from the plan review, including the ones deliberately not acted on,
are in [OPEN_FINDINGS.md](OPEN_FINDINGS.md).

## Running it

No runtime dependencies — Python 3.11 and the standard library. That is a
deliberate constraint: this has to install on a staff laptop with no build
tooling (F-40).

    python -m ria_agent.cli --help

Tests need `pytest`:

    pytest

## Layout

    CONSTITUTION.md      the rules, loaded into every system prompt
    OPEN_FINDINGS.md     what the plan review turned up
    ria_agent/
      receipts.py        the schema and the validator
      log_store.py       append-only SQLite plus a JSONL mirror
      export.py          log to CSV and PDF
      plain.py           receipts rendered in plain language
      secrets_posture.py the startup credential check
      startup.py         constitution loading and the startup gate
      stops.py           the stop taxonomy
      queue.py           the four-lane review queue, as a view over the log
      web.py             that queue on localhost
      seeded_errors.py   deliberate faults and the catch rate (off by default)
      synthetic.py       fake data for using the queue before real data exists
      cli.py             serve, seed, export, verify
