# Custodian terms of service — findings

Step 48, and the item the plan itself calls the single thing most likely to
reshape the product. **Nothing in Phase 3 runs against a real custodian until
this table is filled in.**

One row per custodian, filled in from the actual advisor-portal agreement and
any separate automated-access or data policy — not from a support conversation,
and not from what a competitor appears to do.

## What to look for

- Any clause on automated, programmatic, scripted or robotic access
- Any clause on credential sharing, or on access "by any person other than the
  authorised user"
- Any clause on scraping, harvesting, extraction, or systematic downloading
- Any rate limit, or any prohibition on circumventing one
- Whether a sanctioned data feed or API exists, and on what terms
- Whether the firm's aggregator relationship already covers this data

## Findings

| Custodian | Agreement + date read | Automated access | Sanctioned feed? | Verdict | Read by |
|---|---|---|---|---|---|
| Schwab | | | | | |
| Fidelity | | | | | |
| Pershing | | | | | |
| | | | | | |

**Verdict** is one of:

- **permitted** — the agreement allows it, quote the clause
- **prohibited** — it does not, and the agent must not touch this portal
- **silent** — no clause either way, which is not permission; escalate
- **feed available** — use the sanctioned feed instead of the portal

## If a custodian prohibits it

In order of preference:

1. **Use the custodian's own data feed or API.** Sanctioned, and usually better
   data than a page.
2. **Route through the firm's aggregator.** Orion already has a licensed
   relationship for this data; reading it there touches no custodian portal.
3. **Human-assisted retrieval.** The agent prepares and positions — finds the
   account, the period, the right document — and the person clicks download.
   This keeps most of the time saving and all of the defensibility.

Option 3 changes the pitch from "it does the work" to "it removes the
searching". That is a smaller claim and a true one.

## What we will not do

Build evasion. No rotating user agents, no defeating bot detection, no
distributing requests to look human, no working around a rate limit. The agent
paces itself like a person, runs no parallel sessions, is never headless, and
stops on any anti-automation signal rather than routing around it.

If a site is trying to stop us, that is the answer.
