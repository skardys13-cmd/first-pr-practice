# Fund Economics Framework

**Version:** v1.0 — built 2026-08-12 from the 13 fully-extracted decks.
**Every element traces to course material.** Where the course is silent, that is
marked rather than filled from outside knowledge.

---

## The structure

```
LIMITED PARTNERS                    GENERAL PARTNERS              PORTFOLIO
Pension funds                  →    The VC/PE firm           →    Private
High net worth / family offices     "ideally with more            companies
Insurance companies                  expertise than the LP
Corporate venture arms               could do themselves"
Endowments, sovereign wealth
```
`SRC-P-002`, `SRC-P-008`. **Who LPs actually are** is made concrete by
`SRC-P-010`'s RJR list: Oregon State Treasury, Coca-Cola/Georgia-Pacific/United
Technologies pensions, **MIT and Harvard endowments**, NY State Common Retirement.

## The economics — "2 and 20"

| Term | VC / PE | Hedge fund |
|---|---|---|
| Management fee | **2% of committed capital per year**, irrespective of return | **2% of NAV, marked to market quarterly** |
| Carried interest | **20% of proceeds after the fund is returned** | 20% |
| **GP commitment** | **1% of the fund must be the GP's own money** (`SRC-P-002`) | — |
| Fund life | **10 years** | Open-ended, with lockups/redemptions |

**The hedge fund difference matters** (`SRC-P-014`): a fee on NAV rises and falls
with performance; a fee on committed capital does not.

**When carry starts** (`SRC-P-013`): in **VC**, typically after **payback of fund
and fees**. In some **PE** funds, after a stated **hurdle rate**.

## The clock — and why it drives everything

```
Fund life:                    10 years        (SRC-P-002)
Deal find → diligence → close: 0.5 year       (SRC-P-007)
Time to IPO:                  ~8 years        (SRC-P-002)
Capital required to IPO:      $75M+, 3+ rounds (SRC-P-002)
```
> **~8 years to go public inside a 10-year fund. There is almost no slack.**

`CLAUDE INFERENCE` — this single constraint explains: the exit pressure LPs and
founders complain about (`SRC-P-007`: *"short-term exit pressure, diluted
control"*), why VCs leave boards at exit, why ~90% of companies are sold rather
than taken public, and why the VC Method assumes a ~4-year hold.

## Fund size and survival

- **Median VC fund ~$150M** (`SRC-P-002`)
- **"Bigger is NOT better…..if they do not have good returns"**
- **Top half requires 20%+ IRR on the entire fund** (`SRC-P-001`)
- **"No sufficient returns? No more funds. Many venture firms are one fund and
  done, permanently."**

## The distribution — worked

**Sevin Rosen Fund I** (`SRC-P-007`): **$25M fund**, held **both Compaq and
Lotus**, gross proceeds **~$191M** (`CLAUDE INFERENCE` ≈ 7.6x). GP takes 2%
annual fees and 20% of the carry above return of capital and fees.
`[VISUAL NOT CAPTURED]` — the actual waterfall table is a slide graphic.

## Where the returns actually come from

| Fact | Source |
|---|---|
| **~75% of VC deals do NOT return capital (1.0 MOIC)** | `SRC-P-010` |
| PE loses money on 10–20% of deals in normal years; **32% in 2008, 47% in 2009, 27% in 2020** | `SRC-P-010` |
| **~90% of successful ventures are acquired before IPO** — mostly because they could not scale | `SRC-P-001`, `SRC-P-002` |
| NVIDIA took **$42M** of VC to reach its 1999 IPO | `SRC-P-002` |
| One 24-year, 8-round, ~$150M deal still sold **at a loss** | `SRC-P-002` |

**Both NVIDIA and the loss are the same asset class.** That is the power law,
taught by example rather than by distribution.

## PE-specific additions

- **Fees are charged on TOTAL deal size — debt included.** 1% on a $30M deal
  ($10M equity + $20M debt) = $300,000 (`SRC-P-010`)
- **This stacks with fund-level 2-and-20** — KKR earned **~$1B in fees** on RJR
  *"irrespective of the deal returns,"* which is why they cleared ~14% IRR on a
  deal sold for parts
- **The GP may commit almost nothing:** KKR itself put in **~0.3%** of RJR's
  equity; its LPs co-invested the rest directly

## Real estate funds (`SRC-P-014`)
Same shape, different terms: fund life **7–10 years**, fee **1–2%**, carry
**15–20% after a preferred return hurdle** — and returns come from **dividends
plus appreciation**, where PE has appreciation only.

## What the course does NOT cover
`[NOT PROVIDED]` — capital calls and drawdown mechanics, reserve/follow-on
strategy, recycling, the J-curve, DPI/TVPI/RVPI, and how LPs diligence a GP.
See `EXTERNAL_CONTEXT_Research_Canon.md` gap #2.
