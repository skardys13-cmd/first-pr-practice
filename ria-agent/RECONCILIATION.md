# What "agree" means

Step 31. The hardest document in the project, and a thinking problem rather than
a coding one. Everything in `ria_agent.reconcile` implements exactly this and
nothing beyond it.

The numbers below are **defaults, not decisions**. They are configured per firm,
in writing, with whoever owns the reconciliation process. Shipping a firm's
tolerance as a guess is how a real break gets called noise.

---

## 1. The asymmetry that decides everything

Two errors are possible:

- **False break** — the agent says these disagree; they actually agree. Cost: a
  person wastes ten minutes.
- **False agreement** — the agent says these agree; they actually disagree. Cost:
  a real break stays hidden, possibly for months, possibly until a client
  notices.

These costs are not comparable, so the defaults are not symmetric. Wherever the
engine is uncertain, it reports a possible break. It never resolves uncertainty
toward "fine".

**The release gate is the false-agreement rate, and it must be zero.** Not low.

## 2. As-of alignment comes before tolerance

A balance is meaningless without the instant it was true. Comparing a custodian
balance at 16:00 against a CRM figure cached at 09:00 does not produce a break
or an agreement; it produces nothing, because the two numbers were never
claiming to describe the same moment.

So:

- Every extracted balance carries its own as-of timestamp, read from the source
  and never inferred from when the agent happened to look.
- If two as-of timestamps differ by more than the alignment window, the verdict
  is **cannot compare**. It is never "agreed", and it is never "disagreed".
- The default alignment window is **zero**: same as-of instant, or no comparison.
- A firm may widen it to same-business-day-close where both systems are known to
  publish an end-of-day figure. That is a deliberate loosening and it is written
  down per system pair, not assumed.
- A balance with no as-of timestamp at all is unusable. The verdict is **source
  unavailable**.

## 3. Tolerance

Two systems holding the same account, as of the same instant, should agree to the
penny. Any difference beyond rounding is a real difference and the point of the
exercise is to find it. Tolerance is therefore small on purpose.

| Pair | Default tolerance | Why |
|---|---|---|
| Custodian ↔ CRM cached balance | **$0.01 flat** | The CRM stores what the custodian told it. Nothing should differ but rounding. |
| Custodian ↔ analytics or performance system | **0.02%, floored at $0.01, capped at $250** | These price independently, so a small pricing difference is expected on illiquid or thinly-priced holdings. |
| Analytics ↔ analytics | **0.02%, floored at $0.01, capped at $250** | Same reason. |

The cap is the asymmetry from §1 applied to a formula, and it is the part that
is easy to get wrong. An uncapped percentage swallows a four-figure break on a
large account: 0.02% of $8m is $1,600, and $1,600 missing is not a rounding
difference. A percentage alone is a tolerance that grows exactly where the money
is.

The cap is a **materiality ceiling**, not a rounding allowance. $250 is a
placeholder. A firm sets it at the number below which it genuinely would not
investigate, and writes down why.

Tolerance is never widened to make a recurring break stop appearing. A break
that recurs is a finding about the firm's process, and hiding it in a threshold
is the one change to this file nobody should make.

## 4. The things that legitimately differ

These are the known causes, and each is a *candidate explanation for a
difference already found* — never a reason to skip the comparison.

**Pending trades.** A trade executed but not settled appears in one system's
holdings and not another's. If the difference equals the pending trade's value,
that is the likely cause. It is still an exception, because "likely" is not
"confirmed", and a pending trade that never settles is a real problem.

**Unsettled cash.** Proceeds from a sale that have not settled. Custodians vary
in whether these show in cash, in a separate unsettled bucket, or nowhere.

**Dividends in transit.** Declared and accrued but not paid. Analytics systems
commonly accrue; custodians commonly do not.

**Fees posted in one system.** An advisory fee debited at the custodian but not
yet reflected, or accrued in the analytics system before it is debited.

**Same-day activity.** Any contribution, distribution, or journal on the as-of
date, where the two systems cut their day at different times. This is the
commonest false break and the reason §2 comes before §3.

**Corporate actions.** A split, merger, or spin-off processed on different days.

**Account not linked.** The account exists in one system and not the other. This
is not a balance difference at all, it is a data problem, and it is the most
common upstream cause of a break nobody can explain. `ria_agent.linkage` checks
for it separately, because finding it is valuable on its own.

**Wrong account mapped.** Two accounts linked to each other in error. Produces a
difference that no amount of timing analysis will explain, and the only cure is
looking at the mapping.

## 5. What the engine may output

Never a number on its own. Always a verdict plus the evidence for it:

- **agreed** — within tolerance, as-of instants aligned. Both values, both
  sources, both timestamps recorded anyway.
- **disagreed by $X** — outside tolerance, as-of aligned. A real break until
  someone explains it.
- **possible break** — something is off but the engine cannot say what. The
  default when uncertain.
- **cannot compare** — as-of instants do not align (§2).
- **source unavailable** — a system could not be read, or gave no timestamp.

## 6. What the engine may never do

**It never writes a correction.** Not to the CRM, not to the analytics system,
not anywhere, for any size of difference, however obvious the fix looks.

Every disagreement produces an exception carrying both values, both sources,
both timestamps, the proposed cause, and a proposed resolution. A human decides.
This is Constitution III, and reconciliation is where it first has teeth.

## 7. The release gate, and why the plan's version was not enough

Step 38 says: one month, zero false agreements.

A month of shadow running is passable by an engine that detects nothing, if
genuine breaks are rare enough that a month produces almost none. Zero out of
zero is not evidence.

So the gate needs a denominator:

- at least **20 real breaks** found by the human reviewer during the shadow
  period, and
- **zero** of them missed by the engine.

If the natural break rate is too low to reach 20, inject known synthetic breaks
into the comparison and count those. An engine that cannot catch a break you
planted will not catch one you did not.
