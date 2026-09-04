# Pilot scope and sign-off

Step 47. One page, signed before anything runs.

## Scope

| | |
|---|---|
| **Person** | one named staff member |
| **Role** | |
| **Workflow** | pre-meeting statement retrieval, read-only |
| **Custodians** | only those marked *permitted* or *feed available* in CUSTODIAN_TOS.md |
| **Duration** | four weeks |
| **Writes** | none. Nothing is written to any system during the pilot |
| **Client contact** | none. Nothing reaches a client |
| **Supervisory owner** | |

Anything outside this scope is out of scope, including workflows the agent is
technically capable of.

## Before the first run

- [ ] CUSTODIAN_TOS.md filled in, and every custodian in scope marked permitted
      or feed available
- [ ] A manual time baseline recorded for the pilot workflow — timed by hand,
      by the person doing it, at least ten times
- [ ] Ownership agreed in writing: what is being built, on whose time and
      equipment, who owns it, what the firm gets
- [ ] Supervisory owner named above
- [ ] `ria-agent doctor` passes on the install
- [ ] The model version pinned and recorded
- [ ] Retention owner named for the log, and a retention period set

## How it will be judged

The four criteria from the build plan, measured from the log by
`ria-agent pilot`, not by impression:

1. Time-to-complete falls by at least 50% against the recorded baseline
2. Zero unapproved writes
3. Every action has a receipt, and someone unfamiliar with the system can read
   the log and understand what happened
4. In week four, the person prefers using it to not using it — unprompted

Criterion 3 is tested by handing the week's PDF export to someone who has never
seen the system and asking them what happened. Criterion 4 is a question asked
once, in week four, by someone other than the person who built it.

Anything less is a prototype, not a product.

## Stopping

The pilot stops immediately, without discussion, if:

- any write reaches a system without an approval in the log
- the agent interacts with a transaction-capable control
- a custodian flags, throttles or questions the account
- the person running it asks to stop

## Sign-off

| Role | Name | Date |
|---|---|---|
| Firm principal / decision-maker | | |
| Compliance owner (internal or outsourced) | | |
| Supervisory owner for agent activity | | |
