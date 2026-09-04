# Agentic operations layer — compliance memo

For the firm's principal and whoever owns compliance. Written before permission
was asked for, not after (Step 46). Two pages.

---

## What it is

Software installed on one staff member's machine that performs retrieval,
filing, comparison and drafting work that person already does by hand. It
operates the same systems they operate, under their own login, inside browser
sessions they have already authenticated.

It is not a chatbot, it does not talk to clients, and it makes no decisions.

## What it cannot do

Enforced in code, not by policy. Each rule names the module that enforces it,
and the enforcement is tested.

- **Place a trade, move money, or submit anything to a custodian.** Controls
  matching trade, transfer, wire, submit, authorize, withdraw, delete, change
  address or update banking are refused by the executor above the model's
  decision. A page confirming a financial transaction is an immediate stop.
- **Write anything without approval.** Every change to a record waits in a
  queue. The code path that applies a change looks the approval up in the
  append-only log; there is no way to pass one in.
- **Fix a discrepancy.** When two systems disagree, it records both values, both
  sources, both timestamps, a proposed cause and a proposed resolution. It never
  resolves the difference itself.
- **Send anything to a client.** It drafts. A person sends.
- **Give advice.** It produces no view on suitability, no performance
  commentary, and no recommendation.
- **Log in, or answer an MFA challenge.** It stores no password, no token, no
  cookie and no MFA seed. Startup scans its own storage and refuses to run if a
  credential-shaped value is found there.

## Where data lives

Everything is on the staff member's machine, in a directory the firm's existing
data policy already covers. Nothing is sent to the vendor. There is no central
server, no hosted component, and no phone-home channel.

**One exception, stated plainly.** Content sent to the model provider for
processing leaves the firm's environment. That includes text extracted from
statements and CRM notes. The claim "no client data ever leaves the firm" would
be false and is not made. The accurate claim is: **client data goes only to the
model provider under its retention terms, and never to the vendor or any third
party.** Two things follow, and both are the firm's decision:

1. whether the model provider's terms (retention, training use, sub-processors)
   are acceptable to this firm; and
2. whether ADV disclosures or client agreements need language covering
   AI-assisted operations.

## What the log proves

Every action produces a receipt: timestamp, the person it acted for, the CRM
task, the system touched, what was read, what was proposed or written, the state
before and after, and the evidence — file hashes, source URLs, extracted values
with the page or field they came from, and screenshots.

A receipt claiming success with no evidence is rejected and never stored.

The log is append-only. UPDATE and DELETE abort at the database. A correction is
a new entry referencing the one it corrects; nothing is ever edited or removed.
A mirrored plain-text copy is kept and checked against the database.

Retention is the firm's to set, with 204-2 in mind: five years, the first two
readily accessible, unalterable, exportable. The log should be named as a firm
record with a retention owner.

**Known limitation.** Append-only is enforced by database triggers and by the
absence of any update path in code. Someone with filesystem access and intent
could still edit the file. Hash-chaining each receipt to its predecessor would
make tampering *detectable*; it is designed and not built, and it is recorded as
an open item rather than glossed over.

## What a review looks like

One command exports any date range — filtered by person, workflow or outcome —
to CSV and to a PDF written for someone who has never seen the system. The PDF
states, for the period: every action in order, its evidence, and whether any
write happened without an approval.

If asked "what did the AI do on 3 March", the answer is that export.

## Supervision

Supervision is a person, not a feature. Each install names one operator, and
every approval in the log carries who made it and when. The firm names a
supervisory owner for agent activity before anything runs.

The agent's capabilities are bound to that person's role. It can do only what
someone in that seat already does by hand, and it inherits their permissions: if
they cannot see a household, neither can it.

## What we are asking for

A limited pilot: **one person, one workflow, four weeks.** The proposed workflow
is pre-meeting statement retrieval — read-only, nothing written, and checkable
by eye in seconds.

Before it starts, three things are outstanding and none of them is a coding
task:

1. **Custodian terms of service.** Whether the advisor-portal agreements permit
   automated access is unresolved. It is being read per custodian and written
   down. If a custodian prohibits it, the honest options are the custodian's own
   data feed, routing through the firm's aggregator, or the agent preparing and
   positioning while the person clicks download. We will not build evasion, and
   we stop on any anti-automation signal rather than working around it.
2. **A time baseline.** The pilot is judged on time-to-complete falling by half.
   Nobody has timed the current process, so there is nothing to compare against
   yet. Someone needs to time it by hand first.
3. **Ownership.** What is being built, on whose time and equipment, who owns it,
   and what the firm gets — in writing, before the pilot rather than after it
   works.

## What we are not claiming

That human review guarantees correctness. People approve without reading, and no
queue design eliminates that; the system measures it rather than assuming it
away. The defensible claim is narrower and true: **the log makes errors
findable.**
