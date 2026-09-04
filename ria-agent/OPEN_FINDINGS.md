# Open findings

Findings from the pressure test of the build plan. Each says what was decided
and where it lives. A finding marked **open** has no code answer yet and is
carried deliberately, not forgotten.

Status key: **folded in** (built), **declined** (considered, not built),
**open** (needs a decision or evidence, not code).

---

### 1. "No client data leaves the firm's environment" is false — status: folded in (as language)

Plan §1.2 makes this claim; §1.9 Step 1 permits calls to the model API. Content
sent to a model provider *is* egress. Section 3 lists fifty failure modes and
this is not among them, so it would have surfaced during the Step 46 compliance
review, after everything was built.

Constitution IX now names it as a claim that must never be made, and gives the
honest version: client data goes only to the model provider under its retention
terms, and never to the vendor or a third party.

**Still open:** whether extraction and vision run against a local model. That is
an architecture decision, and it is cheaper to make before Phase 5 than after.

### 2. The trust metric and the top failure mode produce identical data — status: folded in

F-35 names approval fatigue as the most likely failure of the whole system.
Step 30 promotes a workflow when approval-without-edit exceeds 95%. Approval
fatigue *is* people approving without editing, so the gate as written fires on
the failure it is supposed to guard against.

`ria_agent.promotion` requires a measured seeded-error catch rate alongside the
approval rate, and uses a verification-pass rate rather than an approval rate
for read-only workflows, where there is nothing to edit and the approval metric
is degenerate at 100%.

### 3. "Append-only discipline" is not immutability — status: declined

Step 4 asks for no update or delete paths in code. Anyone with the file can open
it in `sqlite3` and run `UPDATE`; absence of a code path is not a safeguard, and
that is unlikely to satisfy the safeguarding expectation behind F-3.

Proposed and declined: hash-chaining each receipt to its predecessor, so
tampering becomes *detectable*, plus a `verify` command.

Built instead, as the plan specifies: UPDATE and DELETE abort at a database
trigger, and `LogStore.verify_mirror` checks the SQLite store and the JSONL
mirror still agree. Both raise the cost of an edit; neither makes one
detectable if someone drops the trigger and rewrites both copies.

**Revisit before** the Step 46 compliance memo. Adding the chain later means
re-baselining every receipt written before it.

### 4. There is a fourth state — status: folded in

The dangerous case is not "stopped" but "stopped after something already
changed". F-11 and F-28 both describe it, and 4.4's own fix smuggles in a fourth
status the three-lane UI has nowhere to render.

`outcome` has four values. `stopped_cleanup_required` is rejected by the
validator unless it says what was left changed, and it sorts to the top of the
queue.

### 5. Undo is an unapproved write, and may not exist — status: open

Step 28 promises reversal is "one click from the receipt". A reversal is a
write, so either it is approval-gated (and it is not one click) or it is not
(and Constitution II has an exception). Worse, the plan assumes Redtail supports
a clean undo without checking.

Built as a *reversal proposal*: one click prepares it, and a person approves it
like any other write. `ria_agent.filing.propose_reversal` records what it
restores and points at the write it reverses. The plan's "one click from the
receipt" is not what shipped, because it cannot be without an unapproved write
path.

**Still open:** whether Redtail permits a clean undo at all. Unverified, and it
needs API access to answer. If it does not, the compensating action is still
receipted and still visible, which is the part that matters.

### 6. "Zero false agreements" has no denominator — status: folded in

Step 38's gate is passable by an engine that detects nothing, if genuine breaks
are rare enough that a month produces almost none. Zero out of zero is not
evidence.

`ria_agent.recon_scoring` requires twenty real breaks observed *and* zero
missed, and `plant_break` supplies known breaks where the natural rate is too
low. An engine that cannot catch a break you planted will not catch one you did
not.

### 7. Step 16's 2% is an aggregate that hides a broken task type — status: folded in

2% confidently-wrong across all tasks permits one task template to be wrong
every time while the average stays clean. `ria_agent.shadow` reports per task
template as well as in aggregate, and the whitelist is built from per-template
numbers.

### 8. Shadow mode validates the easy half — status: folded in

Step 15 logs classification and confidence, but misclassification is not the
sharp risk — misresolution is. "Retrieve statement", classified perfectly and
pointed at the wrong account, is invisible in a classification-only log. The
shadow log records the full resolved plan: workflow, entities, account, and
period.

### 9. The promotion gate is the wrong shape for read-only work — status: folded in

`ria_agent.promotion` gates read-only workflows on the verification-pass rate
and the count of consecutive clean runs, and write workflows on approval rate
*and* catch rate together. A write workflow at 99% approval with no seeded
errors decided is refused, in as many words: without them, that number is
indistinguishable from nobody reading.

### 10. No baseline measurement step — status: open

§1.10 requires time-to-complete to drop by at least 50%, and no step in Phases
0–7 measures the current time. The baseline has to be captured before the pilot
workflow is automated, by hand, with a stopwatch. It is not a coding task, and
without it the pilot has nothing to subtract from.

### 11. No claim or lease protocol — status: open

The CRM is the coordination mechanism (§1.3), but nothing stops a human from
completing a task while the agent works it. Two workers, one queue, no locking.
Phase 4 concern for writes; harmless while everything is read-only.

### 12. Redaction defeats screenshot-as-evidence — status: folded in

A screenshot with the account number and balance redacted (4.1/F-5) proves
nothing about *which* artifact was retrieved. 4.1's own aside is the default
here: a file hash plus extracted field values with source locations is the
primary evidence, and the screenshot is supporting.

### 13. The canary measures the wrong thing — status: folded in

F-16 alerts on a change in path length, but a goal-directed navigator has
naturally variable path length. The canary would be noisy, the threshold would
be raised, and it would go blind. `ria_agent.canary` asserts on the artifact and on the set of pages visited
instead. A redesign that renames every control does not fire it; a redesign
that routes the agent through a page it has never visited does, whether the
path got longer or shorter.

### 14. Receipt schema gaps — status: partly folded in

`references_receipt_id` (Step 4 corrections), `approver` and
`approval_timestamp` (Step 9), and `confidence` (Steps 13–16) were required by
the plan's own later steps but missing from the Step 3 field list. All added.

`idempotency_key` (F-27) is not added: nothing in Steps 1–24 writes, so it has
no use yet. It belongs in the schema before the first filing in Phase 4.
