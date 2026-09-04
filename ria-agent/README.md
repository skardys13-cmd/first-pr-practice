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
| 4 | 25–30 | Naming rules, filing proposals, the executor, reversal, promotion |

Findings from the plan review, including the ones deliberately not acted on,
are in [OPEN_FINDINGS.md](OPEN_FINDINGS.md).

## Running it

No runtime dependencies — Python 3.11 and the standard library. That is a
deliberate constraint: this has to install on a staff laptop with no build
tooling (F-40).

    python -m ria_agent.cli --help

The intended order for a new install:

    ria-agent seed                       # synthetic queue, to live in for a week
    ria-agent serve                      # the review queue on localhost
    ria-agent shadow                     # classify real tasks, act on none
    ria-agent shadow-report --labels ... # score it against a human review
    ria-agent shadow-report --labels ... --write-whitelist
    ria-agent retrieve --account ... --period ...   # one retrieval, receipted
    ria-agent attend --runs 50                      # the supervised gate
    ria-agent promotion statement_retrieval         # may it run unattended yet?

`retrieve`, `attend` and `canary` drive a fake custodian portal, and say so.
The real driver attaches to the operator's already-authenticated browser and
slots in behind `BrowserDriver` with nothing above it changing.

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
      cli.py             serve, seed, shadow, shadow-report, export, verify
      crm.py             read-only CRM interface, and a fixture-backed stand-in
      classifier.py      rules first, model for the tail, unrecognised otherwise
      normalizer.py      task -> resolved intent, with provenance on every value
      matching.py        exact identifier matching; substring matching is banned
      untrusted.py       content from outside, fenced as data
      workflows.py       the six clusters and the workflows in them
      roles.py           what each role's agent may do
      shadow.py          shadow mode and its per-template report
      whitelist.py       the whitelist and the single entry point that enforces it
      browser.py         the browser as an interface, plus a hostile fake portal
      session.py         is there a live session to work in?
      guardrails.py      refusals the executor makes above the model's decision
      navigator.py       observe, decide, act, observe again
      verification.py    is this the artifact that was asked for?
      retrieval.py       statement retrieval end to end, and its receipt
      attended.py        the fifty supervised runs and the unattended gate
      promotion.py       may a workflow run without a person?
      canary.py          portal drift, measured on where it goes not how far
      naming.py          the firm's convention as rules, and a dry run over history
      filing.py          filing proposals and reversal proposals
      executor.py        the only path to a write, and it checks the log first
